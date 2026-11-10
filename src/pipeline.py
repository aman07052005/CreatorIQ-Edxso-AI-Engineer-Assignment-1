from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "outreach.db"
DATA_PATH = ROOT / "data" / "influencers.csv"

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# The completed campaign category is Technology & Coding Education.
# A creator must show an explicit technology/software/coding signal; generic
# education, finance, food, sport and lifestyle alone do not qualify.
TECH_EDUCATION_TERMS = {
    "technology", "tech", "software", "artificial intelligence", "ai",
    "coding", "programming", "developer", "developer education",
    "computer science", "cybersecurity", "data science", "machine learning",
    "android", "linux", "iot", "engineering", "gadgets", "tech news",
    "tech tips", "product reviews", "excel", "cloud computing",
}



def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip().lower() in {"", "not found", "nan", "none", "null"}


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    """Load creator records and normalize missing fields without inventing data."""
    if not path.exists():
        raise FileNotFoundError(f"Influencer dataset not found: {path}")

    df = pd.read_csv(path)
    required = [
        "name", "platform", "followers", "category",
        "content_themes", "contact_email", "profile_url",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    # Contact provenance columns are intentionally explicit.
    for col in ("email_source_url", "email_verification", "contact_type",
                "engagement_rate", "geography", "source", "source_url"):
        if col not in df.columns:
            df[col] = "Not Found"

    df = df.fillna("Not Found")
    df["followers"] = pd.to_numeric(df["followers"], errors="coerce")
    return df


def _engagement_value(value: Any) -> float | None:
    """Extract a source-reported percentage; never derive it from views/followers."""
    if _is_missing(value):
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", str(value))
    return float(match.group(1)) if match else None


def classify_creator(
    row: pd.Series,
    min_followers: int = 5000,
    max_followers: int = 100000,
) -> tuple[str, str, int]:
    followers = row.get("followers")
    if pd.isna(followers):
        return "PENDING", "Follower count unavailable; verify profile", 0
    if followers < min_followers:
        return "FAIL", f"Below {min_followers:,} follower threshold", 0
    if followers > max_followers:
        return "FAIL", f"Above micro-influencer ceiling ({max_followers:,})", 0

    content = " ".join(
        str(row.get(k, "")) for k in ("category", "content_themes")
    ).lower()
    # Match complete words/phrases only. In particular, `ai` must not match
    # unrelated words such as "said", "retail" or "mail".
    matched = sorted(
        term for term in TECH_EDUCATION_TERMS
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", content)
    )
    if not matched:
        return (
            "PENDING",
            "Follower range fits, but no explicit Technology & Coding Education signal; human review required",
            0,
        )

    engagement = _engagement_value(row.get("engagement_rate"))
    if engagement is None:
        return (
            "PENDING",
            "Technology relevance found; source-reported engagement rate unavailable, so qualification is incomplete",
            min(80, 40 + len(matched) * 5),
        )

    # The source must be cited for the reported rate; this is not an independent audit.
    metrics_source = row.get("metrics_source_url")
    if _is_missing(metrics_source) or not str(metrics_source).startswith(("https://", "http://")):
        return "PENDING", "Technology relevance found; engagement source URL missing", 0

    score = min(100, 60 + len(matched) * 5 + min(engagement, 5))
    missing = []
    if _is_missing(row.get("contact_email")):
        missing.append("public contact email (Not Found; manual DM remains possible)")
    reason = (
        "PASS: follower range, Technology & Coding Education relevance and source-reported engagement rate meet the campaign rule. "
        + ("Contact email: " + ", ".join(missing) + "." if missing else "Contact route recorded; validate before outreach.")
    )
    return "PASS", reason, int(score)


def evaluate(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    values = out.apply(classify_creator, axis=1, result_type="expand")
    out[["computed_status", "computed_reason", "fit_score"]] = values
    return out


def personalized_messages(
    row: pd.Series,
    brand: str = "Edxso",
    campaign: str = "Future-ready learning and institutional growth",
    use_llm: bool = False,
) -> tuple[str, str]:
    """Generate a factual, personalized email and short social message."""
    if use_llm and os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI

            safe_profile = {
                key: str(row.get(key, "Not Found"))
                for key in ("name", "platform", "category", "content_themes")
            }
            prompt = (
                "Create a personalized collaboration email and short social DM. "
                "Return JSON with email_subject, email_body, dm. Email body 60-90 words; "
                "DM 15-30 words. Use only supplied facts. Do not invent recent posts, "
                "audience demographics, metrics, contact details, or claims. "
                "Mention niche/themes naturally. Propose a paid pilot or UGC collaboration. "
                f"Campaign: {campaign}\nProfile: {json.dumps(safe_profile)}"
            )
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "Write truthful, concise creator partnership outreach."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.4,
            )
            payload = json.loads(response.choices[0].message.content)
            body = str(payload["email_body"]).strip()
            subject = str(payload["email_subject"]).strip()
            dm = str(payload["dm"]).strip()
            if 60 <= len(body.split()) <= 90 and 15 <= len(dm.split()) <= 30:
                return f"Subject: {subject}\n\n{body}", dm
        except Exception:
            # Free deterministic fallback is expected when API billing is unavailable.
            pass

    raw_name = str(row.get("name", "there")).strip()
    clean_name = re.sub(r"^(Dr\.?|CA|Mr\.?|Mrs\.?|Ms\.?)\s+", "", raw_name, flags=re.I)
    first_name = clean_name.split()[0] if clean_name and clean_name != "Not Found" else "there"
    themes = str(row.get("content_themes", "education and learning"))
    niche = str(row.get("category", "education"))
    if _is_missing(themes):
        themes = "education and learning"
    if _is_missing(niche):
        niche = "education"
    themes_clean = themes.lower().strip().rstrip(".")
    niche_clean = niche.lower().strip().rstrip(".")
    body = (
        f"Hi {first_name},\n\n"
        f"I noticed your {niche_clean} content around {themes_clean}. These topics "
        f"align with Edxso's work helping education organisations strengthen learning "
        f"outcomes and institutional growth. We would like to explore a paid "
        f"collaboration that turns your expertise into practical content for "
        f"learners, educators or institutional teams. The format, brief and "
        f"deliverables can be shaped around your channel and agreed transparently "
        f"before publication. Would you be open to a short discussion about a "
        f"pilot partnership?\n\n"
        f"Best,\n{brand} Partnerships"
    )
    email = f"Subject: Education collaboration with {first_name} × {brand}\n\n{body}"
    dm = (
        f"Hi {first_name}! Your {niche_clean} content on {themes_clean} stood out. "
        f"Open to a paid education collaboration with {brand}?"
    )
    return email, dm


def is_valid_email(email: str) -> bool:
    """Basic syntax check only; it does not prove mailbox existence."""
    if _is_missing(email):
        return False
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", str(email).strip()))


def _email_has_public_source(row: pd.Series) -> bool:
    source = row.get("email_source_url")
    verification = str(row.get("email_verification", "")).strip().upper()
    return (
        not _is_missing(source)
        and str(source).strip().lower().startswith(("https://", "http://"))
        and verification in {"PUBLICLY_LISTED", "VERIFIED"}
        and str(row.get("contact_type", "")).strip().upper()
            != "THIRD_PARTY_DIRECTORY_CONTACT"
    )


def influencer_key(row: pd.Series) -> str:
    raw = (
        f"{row.get('platform', '')}|{row.get('profile_url', '')}|"
        f"{row.get('name', '')}"
    ).lower().strip()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def init_db(db_path: Path | None = None) -> None:
    """Create the channel-aware table and migrate the earlier single-channel table."""
    db_path = db_path or DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as con:
        tables = {
            r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "outreach" in tables:
            cols = {
                r[1] for r in con.execute("PRAGMA table_info(outreach)").fetchall()
            }
            if "channel" not in cols:
                con.execute("ALTER TABLE outreach RENAME TO outreach_legacy")

        con.execute("""
            CREATE TABLE IF NOT EXISTS outreach (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                influencer_key TEXT NOT NULL,
                influencer_name TEXT NOT NULL,
                channel TEXT NOT NULL,
                email TEXT,
                email_message TEXT,
                dm_message TEXT,
                status TEXT NOT NULL,
                sent_at TEXT,
                mode TEXT NOT NULL,
                source_url TEXT,
                error TEXT,
                UNIQUE(influencer_key, channel)
            )
        """)

        tables = {
            r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "outreach_legacy" in tables:
            legacy_cols = {
                r[1] for r in con.execute("PRAGMA table_info(outreach_legacy)").fetchall()
            }
            required = {"influencer_key", "influencer_name", "email", "email_message",
                        "dm_message", "status", "sent_at", "mode", "error"}
            if required.issubset(legacy_cols):
                con.execute("""
                    INSERT OR IGNORE INTO outreach
                    (influencer_key, influencer_name, channel, email, email_message,
                     dm_message, status, sent_at, mode, source_url, error)
                    SELECT influencer_key, influencer_name, 'EMAIL', email,
                           email_message, dm_message, status, sent_at, mode, NULL, error
                    FROM outreach_legacy
                """)


def send_or_simulate(
    row: pd.Series,
    email_message: str,
    dm_message: str,
    simulate: bool = True,
    channel: str = "EMAIL",
) -> tuple[bool, str]:
    """
    EMAIL: simulation only, requires valid email + public source metadata.
    SOCIAL_DM: records a manual-ready draft; it never sends a platform message.
    """
    init_db(DB_PATH)
    channel = channel.strip().upper()
    if channel not in {"EMAIL", "SOCIAL_DM"}:
        return False, "Unsupported outreach channel."

    qualification, reason, _ = classify_creator(row)
    if qualification != "PASS":
        return False, f"Not queued: creator is not PASS-qualified. {reason}"

    email = str(row.get("contact_email", "")).strip()
    source_url = str(row.get("email_source_url", "")).strip()
    key = influencer_key(row)

    if channel == "EMAIL":
        if not is_valid_email(email):
            return False, "Not queued: no syntactically valid public email address."
        if not _email_has_public_source(row):
            return False, (
                "Not queued: add the public email source URL and set "
                "email_verification to PUBLICLY_LISTED or VERIFIED."
            )
        if not simulate:
            return False, (
                "Live SMTP is disabled in this assignment demo. "
                "No email was sent; use simulation mode."
            )
        status, mode = "SIMULATED", "EMAIL_SIMULATION"
        logged_email = email
        logged_source = source_url
    else:
        if _is_missing(row.get("profile_url")):
            return False, "Not queued: creator profile URL is unavailable."
        status, mode = "READY_FOR_MANUAL_SEND", "MANUAL_PLATFORM_WORKFLOW"
        logged_email = email if is_valid_email(email) else ""
        logged_source = str(row.get("profile_url", ""))

    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        with sqlite3.connect(DB_PATH) as con:
            con.execute("""
                INSERT INTO outreach (
                    influencer_key, influencer_name, channel, email,
                    email_message, dm_message, status, sent_at, mode,
                    source_url, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
            """, (
                key, str(row.get("name", "Unknown")), channel, logged_email,
                email_message if channel == "EMAIL" else "",
                dm_message, status, timestamp, mode, logged_source,
            ))
    except sqlite3.IntegrityError:
        return False, f"Duplicate {channel} outreach prevented for this creator."
    return True, (
        "Email simulation logged. No email was delivered."
        if channel == "EMAIL"
        else "Manual-ready social message logged. No DM was sent."
    )


def outreach_log() -> pd.DataFrame:
    init_db(DB_PATH)
    with sqlite3.connect(DB_PATH) as con:
        return pd.read_sql_query("""
            SELECT influencer_name, channel, email, status, sent_at,
                   mode, source_url, error
            FROM outreach
            ORDER BY id DESC
        """, con)

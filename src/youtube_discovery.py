"""Optional YouTube Data API v3 adapter. Requires a user-provided API key.
Searches public channels and returns channel-level metrics; it does not scrape private data.
"""
import os, requests

BASE = 'https://www.googleapis.com/youtube/v3'

def discover_channels(query: str, max_results: int = 50, region_code: str = 'IN'):
    key = os.getenv('YOUTUBE_API_KEY')
    if not key:
        raise RuntimeError('Set YOUTUBE_API_KEY to enable live YouTube discovery.')
    found, token = [], None
    while len(found) < max_results:
        params = {'part':'snippet','q':query,'type':'channel','regionCode':region_code,
                  'maxResults':min(50,max_results-len(found)),'key':key}
        if token: params['pageToken'] = token
        r = requests.get(f'{BASE}/search', params=params, timeout=25); r.raise_for_status()
        payload = r.json(); ids = [x['id']['channelId'] for x in payload.get('items',[])]
        if ids:
            stats = requests.get(f'{BASE}/channels', params={'part':'snippet,statistics,topicDetails','id':','.join(ids),'key':key}, timeout=25)
            stats.raise_for_status()
            for channel in stats.json().get('items',[]):
                s, st = channel.get('snippet',{}), channel.get('statistics',{})
                found.append({'name':s.get('title','Not Found'),'platform':'YouTube',
                    'profile_url':f"https://www.youtube.com/channel/{channel['id']}",
                    'followers':int(st.get('subscriberCount',0)) if st.get('hiddenSubscriberCount') is False else None,
                    'engagement_rate':'Not Found','category':'Education','content_themes':s.get('description','')[:500],
                    'contact_email':'Not Found','geography':s.get('country','Not Found'),'source':'YouTube Data API v3'})
        token = payload.get('nextPageToken')
        if not token or not ids: break
    return found[:max_results]

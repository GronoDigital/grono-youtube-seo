from googleapiclient.discovery import build
from database import channel_exists, add_channel, get_fetched_channel_ids, log_activity, calculate_priority_score
import time
import re

# ============================
# 🔧 SETUP
# ============================
API_KEY = "AIzaSyAONIZtF-KpxJrTvXm3dtMWh2gRFllWEfs"
YOUTUBE = build("youtube", "v3", developerKey=API_KEY)

# 🌎 Countries to target (Top spending/high-value markets only)
# Optimized for quota efficiency - 6 high-value countries
COUNTRIES = [
    "US",   # United States - Highest spending
    "GB",   # United Kingdom - High spending
    "CA",   # Canada - High spending
    "AU",   # Australia - High spending
    "DE",   # Germany - High spending
    "FR"    # France - High spending
]

# 🔍 Niches to search for (Optimized for 100 channels target)
# Reduced to 10 keywords for quota efficiency
KEYWORDS = [
    "fitness",           # Fitness & Health
    "gaming",            # Tech & Gaming
    "podcast",           # Entertainment
    "education",         # Education
    "tech reviews",      # Tech
    "cooking",           # Lifestyle
    "travel vlog",       # Lifestyle
    "marketing",         # Business
    "photography",       # Creative
    "yoga"               # Health & Wellness
]

def get_channels(keyword, country, max_results=50, order='relevance'):
    """Search YouTube channels by keyword & country with different order options"""
    search_response = YOUTUBE.search().list(
        q=keyword,
        type="channel",
        part="snippet",
        regionCode=country,
        maxResults=max_results,
        order=order  # 'relevance', 'date', 'rating', 'viewCount', 'title'
    ).execute()
    return [item["snippet"]["channelId"] for item in search_response["items"]]

def get_channels_from_videos(keyword, country, max_results=100):
    """Get channels by searching videos first (finds active channels)"""
    try:
        # Search for recent videos
        video_response = YOUTUBE.search().list(
            q=keyword,
            type="video",
            part="snippet",
            regionCode=country,
            maxResults=max_results,
            order='date'  # Get recent videos to find active channels
        ).execute()
        
        # Extract unique channel IDs from videos
        channel_ids = list(set([
            item["snippet"]["channelId"] 
            for item in video_response.get("items", [])
        ]))
        
        return channel_ids
    except Exception as e:
        print(f"   ⚠️  Error in video search: {e}")
        return []

def get_channel_details(channel_ids, max_subscribers=100000):
    """Fetch detailed info for given channel IDs with subscriber filter"""
    channel_data = []
    for i in range(0, len(channel_ids), 50):  # 50 per API call limit
        response = YOUTUBE.channels().list(
            part="snippet,statistics,brandingSettings,topicDetails",
            id=",".join(channel_ids[i:i+50])
        ).execute()

        for item in response.get("items", []):
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            branding = item.get("brandingSettings", {})

            # Convert subscriber count safely
            subs = int(stats.get("subscriberCount", 0))

            # ✅ Skip channels above your threshold
            if subs > max_subscribers:
                continue

            channel_info = {
                "Channel ID": item.get('id'),
                "Title": snippet.get("title"),
                "Description": snippet.get("description"),
                "Country": snippet.get("country"),
                "Subscribers": subs,
                "Total Views": stats.get("viewCount"),
                "Video Count": stats.get("videoCount"),
                "Custom URL": snippet.get("customUrl"),
                "Keywords": branding.get("channel", {}).get("keywords"),
                "Default Language": snippet.get("defaultLanguage"),
                "Channel URL": f"https://www.youtube.com/channel/{item.get('id')}"
            }

            channel_data.append(channel_info)

        time.sleep(1)  # polite delay

    return channel_data

def extract_channel_id(url_or_id):
    """
    Extract YouTube channel ID from various URL formats or return ID if already provided
    Supports:
    - youtube.com/channel/UCxxxxx
    - youtube.com/@username
    - youtube.com/c/username
    - youtube.com/user/username
    - Direct channel ID: UCxxxxx
    """
    if not url_or_id:
        return None
    
    # If it's already a channel ID (starts with UC)
    if re.match(r'^UC[a-zA-Z0-9_-]{22}$', url_or_id):
        return url_or_id
    
    # Extract from various URL formats (handle www. and without)
    patterns = [
        r'(?:www\.)?youtube\.com/channel/([a-zA-Z0-9_-]{24})',  # /channel/UCxxxxx
        r'(?:www\.)?youtube\.com/c/([a-zA-Z0-9_-]+)',           # /c/username
        r'(?:www\.)?youtube\.com/user/([a-zA-Z0-9_-]+)',        # /user/username
        r'(?:www\.)?youtube\.com/@([a-zA-Z0-9_-]+)',            # /@username
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            channel_identifier = match.group(1)
            # If it's a channel ID (starts with UC), return it
            if channel_identifier.startswith('UC') and len(channel_identifier) == 24:
                return channel_identifier
            # Otherwise, it's a username - need to resolve it
            if channel_identifier.startswith('@'):
                channel_identifier = channel_identifier[1:]
            return resolve_username_to_channel_id(channel_identifier)
    
    return None

def resolve_username_to_channel_id(username):
    """Resolve YouTube username/handle to channel ID"""
    try:
        # Remove @ if present
        if username.startswith('@'):
            username = username[1:]
        
        # Method 1: Try to get channel by handle using channels().list with forHandle
        # This is the most direct method for @username format (uses less quota)
        try:
            response = YOUTUBE.channels().list(
                part="id",
                forHandle=username,
                maxResults=1
            ).execute()
            
            if response.get('items'):
                return response['items'][0]['id']
        except Exception as e1:
            # Check if it's a quota error - if so, don't try other methods
            error_str = str(e1)
            if 'quota' in error_str.lower() or 'quotaExceeded' in error_str:
                print(f"API quota exceeded. Cannot resolve username: {username}")
                raise Exception("API quota exceeded")
            # If forHandle doesn't work (maybe not available), try other methods
            pass
        
        # Method 2: Try searching for the handle (uses more quota)
        # Only try this if forHandle didn't work and quota is available
        try:
            response = YOUTUBE.search().list(
                q=f"@{username}",
                type="channel",
                part="snippet",
                maxResults=10
            ).execute()
            
            # Find exact match by checking customUrl
            for item in response.get('items', []):
                snippet = item.get('snippet', {})
                custom_url = snippet.get('customUrl', '')
                channel_id = snippet.get('channelId', '')
                
                # Check if custom URL exactly matches (with or without @)
                if custom_url:
                    # Remove @ and compare
                    clean_custom = custom_url.replace('@', '').lower()
                    clean_username = username.lower()
                    if clean_custom == clean_username or f"@{clean_custom}" == f"@{clean_username}":
                        return channel_id
                
                # Also check if the channel title matches closely
                channel_title = snippet.get('title', '').lower()
                if username.lower() in channel_title:
                    return channel_id
            
            # If no exact match, return first result as fallback
            if response.get('items'):
                return response['items'][0]['snippet']['channelId']
        except Exception as e2:
            error_str = str(e2)
            if 'quota' in error_str.lower() or 'quotaExceeded' in error_str:
                print(f"API quota exceeded in search method")
                raise Exception("API quota exceeded")
            print(f"Error in search method: {e2}")
        
        # Method 3: Try legacy forUsername (deprecated but might work for some)
        try:
            response = YOUTUBE.channels().list(
                part="id",
                forUsername=username,
                maxResults=1
            ).execute()
            
            if response.get('items'):
                return response['items'][0]['id']
        except Exception as e3:
            error_str = str(e3)
            if 'quota' in error_str.lower() or 'quotaExceeded' in error_str:
                raise Exception("API quota exceeded")
            pass
            
    except Exception as e:
        # Re-raise quota errors
        if 'quota' in str(e).lower():
            raise
        print(f"Error resolving username {username}: {e}")
    
    return None

def analyze_channel(channel_url_or_id):
    """
    Analyze a single YouTube channel (public API - no filters)
    Returns channel data with priority score and analysis
    """
    try:
        channel_id = extract_channel_id(channel_url_or_id)
        if not channel_id:
            print(f"Could not extract channel ID from: {channel_url_or_id}")
            return None
    except Exception as e:
        error_str = str(e)
        if 'quota' in error_str.lower():
            raise Exception("API quota exceeded. Please try again later.")
        print(f"Error extracting channel ID: {e}")
        return None
    
    try:
        # Fetch channel details
        response = YOUTUBE.channels().list(
            part="snippet,statistics,brandingSettings,topicDetails,contentDetails",
            id=channel_id
        ).execute()
        
        if not response.get('items'):
            print(f"Channel not found for ID: {channel_id}")
            return None
        
        item = response['items'][0]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        branding = item.get("brandingSettings", {})
        
        # Prepare channel data
        channel_data = {
            "Channel ID": item.get('id'),
            "Title": snippet.get("title"),
            "Description": snippet.get("description", "")[:500],  # Limit description
            "Country": snippet.get("country"),
            "Country Code": snippet.get("country"),
            "Subscribers": int(stats.get("subscriberCount", 0) or 0),
            "Total Views": int(stats.get("viewCount", 0) or 0),
            "Video Count": int(stats.get("videoCount", 0) or 0),
            "Custom URL": snippet.get("customUrl"),
            "Keywords": branding.get("channel", {}).get("keywords"),
            "Default Language": snippet.get("defaultLanguage"),
            "Channel URL": f"https://www.youtube.com/channel/{item.get('id')}",
            "Thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
            "Published At": snippet.get("publishedAt", ""),
        }
        
        # Calculate priority score
        channel_data["Priority Score"] = calculate_priority_score(channel_data)
        
        # Calculate engagement metrics
        subs = channel_data["Subscribers"]
        views = channel_data["Total Views"]
        videos = channel_data["Video Count"]
        
        channel_data["Engagement Rate"] = round((views / subs) if subs > 0 else 0, 2)
        channel_data["Views Per Video"] = round((views / videos) if videos > 0 else 0, 0)
        channel_data["Subscribers Per Video"] = round((subs / videos) if videos > 0 else 0, 0)
        
        # Generate recommendations
        recommendations = []
        if channel_data["Priority Score"] < 50:
            recommendations.append("Focus on increasing subscriber count to improve your priority score")
        if channel_data["Engagement Rate"] < 50:
            recommendations.append("Improve engagement by creating more compelling content")
        if videos < 50:
            recommendations.append("Increase video frequency to boost activity score")
        if not recommendations:
            recommendations.append("Your channel is performing well! Consider optimizing SEO for even better results.")
        
        channel_data["Recommendations"] = recommendations
        
        return channel_data
        
    except Exception as e:
        error_str = str(e)
        # Re-raise quota errors so they can be handled properly
        if 'quota' in error_str.lower() or 'quotaExceeded' in error_str:
            raise Exception("API quota exceeded. Please try again later.")
        print(f"Error analyzing channel: {e}")
        return None

def fetch_new_channels(max_results=100, max_subscribers=100000, target_channels=100, user_id=None):
    """
    Fetch new YouTube channels, skipping ones already in database
    Returns: dict with new_channels count, total_fetched, and skipped count
    """
    # Get already fetched channel IDs
    fetched_ids = get_fetched_channel_ids()
    
    all_new_channels = []
    skipped_count = 0
    total_fetched = 0
    
    print(f"📊 Already have {len(fetched_ids)} channels in database")
    print(f"🎯 Target: Fetch {target_channels} new channels")
    print("🚀 Fetching new channels...\n")
    
    # Use different search strategies to get more diverse channels
    search_orders = ['relevance', 'date', 'viewCount']  # Rotate between strategies
    
    for country in COUNTRIES:
        # Stop if we've reached our target
        if len(all_new_channels) >= target_channels:
            print(f"\n✅ Reached target of {target_channels} channels!")
            break
            
        for keyword in KEYWORDS:
            # Stop if we've reached our target
            if len(all_new_channels) >= target_channels:
                break
            print(f"🌎 Country: {country} | Keyword: '{keyword}'")
            
            # Strategy: Search channels directly (removed video search to save quota)
            # Rotate between different search orders for diversity
            order = search_orders[len(fetched_ids) % len(search_orders)]
            channel_ids = get_channels(keyword, country, max_results=max_results, order=order)
            
            # Use only channel search (removed video search to optimize quota usage)
            all_channel_ids = channel_ids
            
            # Filter out already fetched channels
            new_channel_ids = [cid for cid in all_channel_ids if cid not in fetched_ids]
            skipped = len(all_channel_ids) - len(new_channel_ids)
            skipped_count += skipped
            
            if skipped > 0:
                print(f"   ⏭️  Skipped {skipped} already-fetched channels")
            
            if not new_channel_ids:
                print(f"   ℹ️  No new channels found")
                continue
            
            print(f"   ➤ Fetching details for {len(new_channel_ids)} new channels...")
            data = get_channel_details(new_channel_ids, max_subscribers=max_subscribers)
            
            # Add metadata
            for d in data:
                d["Search Keyword"] = keyword
                d["Country Code"] = country
            
            # Add to database
            new_count = 0
            for channel in data:
                if add_channel(channel):
                    all_new_channels.append(channel)
                    new_count += 1
                    total_fetched += 1
                    # Update fetched_ids to avoid duplicates in same run
                    fetched_ids.add(channel.get('Channel ID'))
            
            print(f"   ✅ Added {new_count} new channels to database")
            time.sleep(1)  # Rate limiting
    
    print(f"\n✅ Done! Added {len(all_new_channels)} new channels")
    print(f"📊 Total in database: {len(fetched_ids) + len(all_new_channels)}")
    print(f"⏭️  Skipped: {skipped_count} already-fetched channels")
    if len(all_new_channels) >= target_channels:
        print(f"🎯 Successfully reached target of {target_channels} channels!")
    
    return {
        'new_channels': len(all_new_channels),
        'total_fetched': total_fetched,
        'skipped': skipped_count,
        'target_reached': len(all_new_channels) >= target_channels
    }

if __name__ == "__main__":
    fetch_new_channels()


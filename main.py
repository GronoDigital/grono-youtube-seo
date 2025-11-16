from googleapiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd
import time
from datetime import datetime

# ============================
# 🔧 SETUP
# ============================
import os
API_KEY = os.environ.get('YOUTUBE_API_KEY', "AIzaSyAONIZtF-KpxJrTvXm3dtMWh2gRFllWEfs")  # 🔹 Uses environment variable or default
YOUTUBE = build("youtube", "v3", developerKey=API_KEY)

# Google Docs setup (optional - only if service account file exists)
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', 'youtube-fetcher-478408-c185198da55b.json')
DOCS_SERVICE = None
DRIVE_SERVICE = None

# Only initialize Google Docs if service account file exists
if os.path.exists(SERVICE_ACCOUNT_FILE):
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        DOCS_SERVICE = build('docs', 'v1', credentials=credentials)
        DRIVE_SERVICE = build('drive', 'v3', credentials=credentials)
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize Google Docs service: {e}")
        print("   Google Docs integration will be disabled.")
else:
    print(f"⚠️  Warning: Service account file not found: {SERVICE_ACCOUNT_FILE}")
    print("   Google Docs integration will be disabled.")

# Google Doc ID (will be created if not exists)
DOCUMENT_ID = None  # Will be set when creating/updating the doc

# 🔹 Optional: Add your email here to automatically share the document
# Leave as None if you don't want to share automatically
YOUR_EMAIL = "arpit88407@gmail.com"  # Example: "your-email@gmail.com"

# 🌎 Countries to target
COUNTRIES = ["US", "GB", "CA", "AU"]   # GB = United Kingdom

# 🔍 Niches to search for (you can expand this list)
KEYWORDS = ["fitness", "gaming", "podcast", "education", "tech reviews"]

def get_channels(keyword, country, max_results=50):
    """Search YouTube channels by keyword & country"""
    search_response = YOUTUBE.search().list(
        q=keyword,
        type="channel",
        part="snippet",
        regionCode=country,
        maxResults=max_results
    ).execute()
    return [item["snippet"]["channelId"] for item in search_response["items"]]


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


def create_or_get_google_doc(doc_title="YouTube Channel Data"):
    """Create a new Google Doc or get existing one"""
    global DOCUMENT_ID
    
    if not DOCS_SERVICE or not DRIVE_SERVICE:
        print("⚠️  Google Docs service not available. Skipping Google Docs integration.")
        return None
    
    # Try to find existing document
    try:
        results = DRIVE_SERVICE.files().list(
            q=f"name='{doc_title}' and mimeType='application/vnd.google-apps.document'",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        items = results.get('files', [])
        
        if items:
            DOCUMENT_ID = items[0]['id']
            print(f"📄 Found existing Google Doc: {doc_title}")
            return DOCUMENT_ID
    except Exception as e:
        print(f"⚠️  Error searching for existing doc: {e}")
    
    # Create new document
    try:
        doc = DOCS_SERVICE.documents().create(body={'title': doc_title}).execute()
        DOCUMENT_ID = doc.get('documentId')
        print(f"✅ Created new Google Doc: {doc_title} (ID: {DOCUMENT_ID})")
        return DOCUMENT_ID
    except Exception as e:
        print(f"❌ Error creating Google Doc: {e}")
        return None


def write_to_google_doc(channel_data):
    """Write channel data to Google Doc"""
    if not DOCS_SERVICE or not DRIVE_SERVICE:
        print("⚠️  Google Docs service not available. Skipping Google Docs integration.")
        return None
    
    if not DOCUMENT_ID:
        print("❌ No document ID available")
        return
    
    try:
        # Clear existing content (optional - comment out if you want to append)
        doc = DOCS_SERVICE.documents().get(documentId=DOCUMENT_ID).execute()
        if doc.get('body', {}).get('content'):
            # Clear document
            requests = [{
                'deleteContentRange': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': doc['body']['content'][-1]['endIndex'] - 1
                    }
                }
            }]
            DOCS_SERVICE.documents().batchUpdate(
                documentId=DOCUMENT_ID, body={'requests': requests}).execute()
        
        # Prepare content
        requests = []
        current_index = 1
        
        # Title
        title_text = f"🎬 YouTube Channel Data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        requests.append({
            'insertText': {
                'location': {'index': current_index},
                'text': title_text
            }
        })
        current_index += len(title_text)
        
        # Format title
        requests.append({
            'updateTextStyle': {
                'range': {
                    'startIndex': 1,
                    'endIndex': current_index - 1
                },
                'textStyle': {
                    'bold': True,
                    'fontSize': {'magnitude': 18, 'unit': 'PT'}
                },
                'fields': 'bold,fontSize'
            }
        })
        
        # Add summary
        summary = f"Total Channels: {len(channel_data)}\n\n"
        requests.append({
            'insertText': {
                'location': {'index': current_index},
                'text': summary
            }
        })
        current_index += len(summary)
        
        # Add channel data
        for idx, channel in enumerate(channel_data, 1):
            channel_text = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            channel_text += f"Channel #{idx}\n\n"
            channel_text += f"📺 Title: {channel.get('Title', 'N/A')}\n"
            channel_text += f"🌍 Country: {channel.get('Country', 'N/A')} ({channel.get('Country Code', 'N/A')})\n"
            channel_text += f"🔍 Keyword: {channel.get('Search Keyword', 'N/A')}\n"
            channel_text += f"👥 Subscribers: {channel.get('Subscribers', 0):,}\n"
            channel_text += f"👁️  Total Views: {channel.get('Total Views', 0):,}\n"
            channel_text += f"📹 Video Count: {channel.get('Video Count', 0):,}\n"
            channel_text += f"🔗 Channel URL: {channel.get('Channel URL', 'N/A')}\n"
            if channel.get('Custom URL'):
                channel_text += f"🔗 Custom URL: {channel.get('Custom URL')}\n"
            if channel.get('Description'):
                desc = channel.get('Description', '')[:200]  # Limit description length
                channel_text += f"📝 Description: {desc}...\n" if len(channel.get('Description', '')) > 200 else f"📝 Description: {desc}\n"
            channel_text += f"\n"
            
            requests.append({
                'insertText': {
                    'location': {'index': current_index},
                    'text': channel_text
                }
            })
            current_index += len(channel_text)
        
        # Execute all requests
        DOCS_SERVICE.documents().batchUpdate(
            documentId=DOCUMENT_ID, body={'requests': requests}).execute()
        
        # Share document with user email if provided
        if YOUR_EMAIL:
            try:
                DRIVE_SERVICE.permissions().create(
                    fileId=DOCUMENT_ID,
                    body={'type': 'user', 'role': 'writer', 'emailAddress': YOUR_EMAIL},
                    fields='id'
                ).execute()
                print(f"📧 Shared document with {YOUR_EMAIL}")
            except Exception as e:
                print(f"⚠️  Could not share document: {e}")
        
        # Get document URL
        doc_url = f"https://docs.google.com/document/d/{DOCUMENT_ID}/edit"
        print(f"✅ Successfully wrote {len(channel_data)} channels to Google Doc!")
        print(f"🔗 Document URL: {doc_url}")
        return doc_url
        
    except Exception as e:
        print(f"❌ Error writing to Google Doc: {e}")
        return None


def main():
    all_channels = []
    print("🚀 Extracting YouTube channel data from US, UK, Canada, Australia...\n")
    
    # Create or get Google Doc
    create_or_get_google_doc("YouTube Channel Data - Live")

    for country in COUNTRIES:
        for keyword in KEYWORDS:
            print(f"🌎 Country: {country} | Searching keyword: '{keyword}'")
            channel_ids = get_channels(keyword, country, max_results=50)
            print(f"   ➤ Found {len(channel_ids)} channels. Fetching details...")
            data = get_channel_details(channel_ids)
            for d in data:
                d["Search Keyword"] = keyword
                d["Country Code"] = country
            all_channels.extend(data)
            time.sleep(1)

    # Save all results to Excel
    df = pd.DataFrame(all_channels)
    df.to_excel("targeted_youtube_channels.xlsx", index=False)
    print("\n✅ Saved Excel file: 'targeted_youtube_channels.xlsx'")
    
    # Write to Google Doc
    print("\n📝 Writing data to Google Docs...")
    doc_url = write_to_google_doc(all_channels)

    print(f"\n✅ Done! Total channels collected: {len(df)}")
    if doc_url:
        print(f"🌐 View your live data at: {doc_url}")


if __name__ == "__main__":
    main()

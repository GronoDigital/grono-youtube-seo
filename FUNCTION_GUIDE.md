# 📚 Complete Function Guide - YouTube SEO Service Manager

## 🏗️ System Architecture

The system consists of **3 main components**:

1. **`database.py`** - Handles all database operations (SQLite)
2. **`youtube_fetcher.py`** - Fetches data from YouTube API
3. **`app.py`** - Flask web server with API endpoints

---

## 📦 1. DATABASE.PY - Database Management

### `get_db()` - Context Manager
**Purpose**: Safely manages database connections
```python
@contextmanager
def get_db():
```
- Opens a connection to SQLite database
- Automatically commits changes on success
- Rolls back on errors
- Always closes connection (even if error occurs)
- **Why**: Prevents database locks and ensures data integrity

---

### `init_db()` - Initialize Database
**Purpose**: Creates the database tables on first run
```python
def init_db():
```
**What it does**:
- Creates `channels` table with all required columns:
  - `id` - Auto-incrementing primary key
  - `channel_id` - Unique YouTube channel ID (prevents duplicates)
  - `title`, `description`, `country`, etc. - Channel info
  - `fetched_at` - When channel was added
  - `emailed` - Boolean (0 or 1) - Has this channel been emailed?
  - `emailed_at` - Timestamp when marked as emailed
  - `notes` - Custom notes you can add
- Creates indexes for faster lookups on `channel_id` and `emailed`
- **Called automatically** when Flask app starts

---

### `channel_exists(channel_id)` - Check Duplicate
**Purpose**: Check if a channel already exists in database
```python
def channel_exists(channel_id):
```
**Returns**: `True` if exists, `False` if new
**Used by**: Prevents adding duplicate channels

---

### `add_channel(channel_data)` - Add New Channel
**Purpose**: Insert a new channel into database
```python
def add_channel(channel_data):
```
**Parameters**: Dictionary with channel information
**Returns**: 
- `True` if successfully added
- `False` if channel already exists (IntegrityError)
**What it does**:
- Inserts channel data into `channels` table
- Handles duplicate errors gracefully
- **Key**: Uses `channel_id` as UNIQUE constraint to prevent duplicates

---

### `get_all_channels()` - Retrieve Channels
**Purpose**: Get channels with filtering and pagination
```python
def get_all_channels(emailed_filter=None, search_query=None, limit=100, offset=0):
```
**Parameters**:
- `emailed_filter` - `True` (emailed), `False` (not emailed), `None` (all)
- `search_query` - Search in title, description, or country
- `limit` - How many channels per page
- `offset` - Skip N channels (for pagination)

**Returns**: List of channel dictionaries
**Used by**: Dashboard to display channels in table

**Example Query Flow**:
```sql
SELECT * FROM channels 
WHERE 1=1 
  AND emailed = 1                    -- if filter applied
  AND (title LIKE '%fitness%' OR ...) -- if search applied
ORDER BY fetched_at DESC 
LIMIT 50 OFFSET 0                    -- pagination
```

---

### `get_channel_count()` - Count Channels
**Purpose**: Get total number of channels (with optional filter)
```python
def get_channel_count(emailed_filter=None):
```
**Returns**: Integer count
**Used by**: Dashboard statistics and pagination

---

### `update_emailed_status()` - Mark as Emailed
**Purpose**: Update email status for one or more channels
```python
def update_emailed_status(channel_ids, emailed=True):
```
**Parameters**:
- `channel_ids` - List of channel IDs to update
- `emailed` - `True` to mark as emailed, `False` to unmark

**What it does**:
- Sets `emailed = 1` and `emailed_at = current timestamp` when marking as emailed
- Sets `emailed = 0` and `emailed_at = NULL` when unmarking
- **Used by**: Checkbox clicks in dashboard

---

### `update_channel_notes()` - Add Notes
**Purpose**: Update custom notes for a channel
```python
def update_channel_notes(channel_id, notes):
```
**Parameters**:
- `channel_id` - Database ID (not YouTube channel ID)
- `notes` - Text notes to save

**Used by**: Notes input field in dashboard

---

### `get_fetched_channel_ids()` - Get All Channel IDs
**Purpose**: Get set of all YouTube channel IDs already in database
```python
def get_fetched_channel_ids():
```
**Returns**: Set of channel ID strings
**Used by**: `fetch_new_channels()` to skip duplicates

**Why Set?**: Fast lookup - O(1) time complexity to check if ID exists

---

## 🎬 2. YOUTUBE_FETCHER.PY - YouTube API Integration

### `get_channels()` - Search YouTube
**Purpose**: Search YouTube for channels by keyword and country
```python
def get_channels(keyword, country, max_results=50):
```
**What it does**:
- Calls YouTube Search API
- Searches for channels matching keyword in specific country
- Returns list of YouTube channel IDs

**API Call**:
```python
YOUTUBE.search().list(
    q=keyword,              # Search term
    type="channel",         # Only channels
    regionCode=country,     # Country filter
    maxResults=max_results
)
```

**Returns**: List of channel ID strings
**Example**: `['UCxxx123', 'UCyyy456', ...]`

---

### `get_channel_details()` - Get Channel Info
**Purpose**: Fetch detailed information for channel IDs
```python
def get_channel_details(channel_ids, max_subscribers=100000):
```
**Parameters**:
- `channel_ids` - List of YouTube channel IDs
- `max_subscribers` - Filter out channels with more subscribers

**What it does**:
- Calls YouTube Channels API (batches of 50 - API limit)
- Extracts: title, description, subscribers, views, video count, etc.
- Filters out channels above subscriber threshold
- Adds 1-second delay between API calls (rate limiting)

**Returns**: List of channel dictionaries with all details

**Data Structure Returned**:
```python
{
    "Channel ID": "UCxxx123",
    "Title": "Fitness Channel",
    "Description": "...",
    "Subscribers": 50000,
    "Total Views": "1000000",
    "Video Count": "150",
    "Channel URL": "https://www.youtube.com/channel/UCxxx123",
    ...
}
```

---

### `fetch_new_channels()` - Main Fetching Function ⭐
**Purpose**: Fetch new channels, automatically skipping duplicates
```python
def fetch_new_channels(max_results=50, max_subscribers=100000):
```

**How it works (Step by Step)**:

1. **Get existing channels**:
   ```python
   fetched_ids = get_fetched_channel_ids()  # Set of all channel IDs in DB
   ```

2. **Loop through countries and keywords**:
   ```python
   for country in COUNTRIES:  # ["US", "GB", "CA", "AU"]
       for keyword in KEYWORDS:  # ["fitness", "gaming", ...]
   ```

3. **Search for channels**:
   ```python
   channel_ids = get_channels(keyword, country, max_results)
   ```

4. **Filter out duplicates**:
   ```python
   new_channel_ids = [cid for cid in channel_ids if cid not in fetched_ids]
   skipped = len(channel_ids) - len(new_channel_ids)
   ```

5. **Get details for new channels only**:
   ```python
   data = get_channel_details(new_channel_ids, max_subscribers)
   ```

6. **Add to database**:
   ```python
   for channel in data:
       if add_channel(channel):  # Returns True if new, False if duplicate
           all_new_channels.append(channel)
           fetched_ids.add(channel.get('Channel ID'))  # Update set
   ```

7. **Return summary**:
   ```python
   return {
       'new_channels': len(all_new_channels),  # How many were added
       'total_fetched': total_fetched,         # Total processed
       'skipped': skipped_count                # How many duplicates skipped
   }
   ```

**Key Feature**: Never fetches the same channel twice! 🎯

---

## 🌐 3. APP.PY - Flask Web Server

### Flask App Setup
```python
app = Flask(__name__)
init_db()  # Initialize database when app starts
```

---

### `@app.route('/')` - Dashboard Page
**Purpose**: Serve the main HTML dashboard
```python
def index():
    return render_template('dashboard.html')
```
- Returns the HTML file from `templates/dashboard.html`
- This is what you see in your browser

---

### `@app.route('/api/channels')` - Get Channels API
**Purpose**: API endpoint to fetch channels with filters
```python
def api_channels():
```

**Query Parameters**:
- `page` - Page number (default: 1)
- `per_page` - Channels per page (default: 50)
- `emailed` - Filter: "true", "false", or not provided (all)
- `search` - Search query string

**Returns JSON**:
```json
{
    "channels": [...],      // Array of channel objects
    "total": 405,           // Total channels matching filter
    "page": 1,              // Current page
    "per_page": 50,         // Channels per page
    "total_pages": 9        // Total pages
}
```

**Used by**: Dashboard JavaScript to load channel table

---

### `@app.route('/api/channels/update-emailed')` - Update Email Status
**Purpose**: Mark channels as emailed/unemailed
```python
def update_emailed():
```

**Request Body (JSON)**:
```json
{
    "channel_ids": [1, 2, 3],  // Database IDs (not YouTube IDs)
    "emailed": true            // true or false
}
```

**Returns**:
```json
{
    "success": true,
    "updated": 3  // Number of channels updated
}
```

**Used by**: Checkbox clicks in dashboard

---

### `@app.route('/api/channels/update-notes')` - Update Notes
**Purpose**: Save notes for a channel
```python
def update_notes():
```

**Request Body (JSON)**:
```json
{
    "channel_id": 123,        // Database ID
    "notes": "Called on Jan 15"  // Notes text
}
```

**Used by**: Notes input field blur event

---

### `@app.route('/api/fetch')` - Trigger Channel Fetch
**Purpose**: Start fetching new channels from YouTube
```python
def fetch_channels():
```

**Request Body (JSON)**:
```json
{
    "max_results": 50  // Optional, defaults to 50
}
```

**Returns**:
```json
{
    "success": true,
    "message": "Successfully fetched 25 new channels",
    "total_fetched": 25,
    "skipped": 180
}
```

**Used by**: "Fetch New Channels" button in dashboard

**Note**: This can take a while (30+ seconds) as it makes many API calls

---

### `@app.route('/api/stats')` - Get Statistics
**Purpose**: Get dashboard statistics
```python
def get_stats():
```

**Returns JSON**:
```json
{
    "total": 405,        // Total channels
    "emailed": 120,      // Channels marked as emailed
    "not_emailed": 285   // Channels not yet emailed
}
```

**Used by**: Dashboard stats cards (auto-refreshes every 30 seconds)

---

## 🔄 Complete Data Flow

### When You Click "Fetch New Channels":

1. **Frontend** (dashboard.html):
   ```javascript
   fetch('/api/fetch', { method: 'POST' })
   ```

2. **Backend** (app.py):
   ```python
   result = fetch_new_channels(max_results=50)
   ```

3. **YouTube Fetcher** (youtube_fetcher.py):
   - Gets all existing channel IDs from database
   - Searches YouTube for each country/keyword combination
   - Filters out duplicates
   - Fetches details for new channels only
   - Adds new channels to database

4. **Database** (database.py):
   - `add_channel()` inserts each new channel
   - UNIQUE constraint on `channel_id` prevents duplicates

5. **Response**:
   - Returns count of new channels added
   - Frontend shows success message
   - Dashboard refreshes to show new channels

---

### When You Check/Uncheck "Emailed" Checkbox:

1. **Frontend**:
   ```javascript
   updateEmailedStatus(channelId, checked)
   ```

2. **API Call**:
   ```javascript
   POST /api/channels/update-emailed
   { "channel_ids": [123], "emailed": true }
   ```

3. **Backend**:
   ```python
   update_emailed_status([123], True)
   ```

4. **Database**:
   ```sql
   UPDATE channels 
   SET emailed = 1, emailed_at = '2024-01-15 10:30:00' 
   WHERE id = 123
   ```

5. **Frontend**:
   - Stats refresh automatically
   - Checkbox shows checked state

---

## 🎯 Key Features Explained

### 1. **No Duplicate Channels**
- Uses `channel_id` (YouTube's unique ID) as UNIQUE constraint
- `get_fetched_channel_ids()` creates a set for fast lookup
- Filters channels before fetching details (saves API calls)

### 2. **Email Tracking**
- `emailed` column: Boolean (0 or 1)
- `emailed_at` column: Timestamp when marked
- Can filter by email status
- Prevents sending duplicate emails

### 3. **Pagination**
- `limit` and `offset` parameters
- Calculates total pages
- Loads 50 channels at a time (faster page loads)

### 4. **Search Functionality**
- Searches in `title`, `description`, and `country` columns
- Uses SQL `LIKE` with wildcards (`%search%`)
- Case-insensitive matching

### 5. **Notes System**
- Each channel can have custom notes
- Saved in `notes` column
- Updated on blur (when you click away from input)

---

## 📊 Database Schema

```sql
CREATE TABLE channels (
    id INTEGER PRIMARY KEY,           -- Auto-increment ID
    channel_id TEXT UNIQUE NOT NULL,  -- YouTube channel ID (prevents duplicates)
    title TEXT,                       -- Channel name
    description TEXT,                 -- Channel description
    country TEXT,                     -- Country name
    country_code TEXT,                -- Country code (US, GB, etc.)
    subscribers INTEGER,              -- Subscriber count
    total_views TEXT,                 -- Total views
    video_count TEXT,                 -- Number of videos
    custom_url TEXT,                  -- Custom YouTube URL
    keywords TEXT,                    -- Channel keywords
    default_language TEXT,            -- Language
    channel_url TEXT,                 -- Full YouTube URL
    search_keyword TEXT,              -- Keyword used to find this channel
    fetched_at TIMESTAMP,             -- When added to database
    emailed BOOLEAN DEFAULT 0,        -- Email status (0 or 1)
    emailed_at TIMESTAMP,             -- When marked as emailed
    notes TEXT                        -- Custom notes
);
```

---

## 🚀 Performance Optimizations

1. **Indexes**: Created on `channel_id` and `emailed` for fast lookups
2. **Set Lookup**: Using Python `set` for O(1) duplicate checking
3. **Pagination**: Only loads 50 channels at a time
4. **Batch API Calls**: Fetches 50 channels per API call (YouTube limit)
5. **Rate Limiting**: 1-second delay between API calls

---

## 🔐 Security Notes

- Database uses SQLite (local file, no network)
- API endpoints don't require authentication (for local use)
- For production, add authentication/authorization
- API key is in code (consider using environment variables)

---

## 📝 Summary

**Main Workflow**:
1. User clicks "Fetch New Channels"
2. System searches YouTube (skips duplicates)
3. New channels added to database
4. User can view, search, filter channels
5. User marks channels as "emailed" to track outreach
6. System prevents duplicate emails

**Key Functions**:
- `fetch_new_channels()` - Main fetching logic
- `add_channel()` - Prevents duplicates
- `get_all_channels()` - Retrieves with filters
- `update_emailed_status()` - Tracks outreach

This system ensures you **never fetch the same channel twice** and **never email the same channel twice**! 🎯


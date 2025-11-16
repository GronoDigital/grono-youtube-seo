# YouTube SEO Service - Channel Manager

A comprehensive web-based dashboard for managing YouTube channel outreach for your SEO service business.

## Features

✅ **Smart Channel Fetching** - Automatically skips channels already in your database  
✅ **Email Tracking** - Mark channels as "emailed" with checkboxes to avoid duplicate outreach  
✅ **Interactive Dashboard** - Beautiful, modern web interface to manage all channels  
✅ **Search & Filter** - Find channels by title, description, country, or email status  
✅ **Notes System** - Add custom notes to each channel  
✅ **Real-time Stats** - Track total channels, emailed, and not-emailed counts  
✅ **Pagination** - Efficiently browse through large channel lists  

## Setup

1. **Install Dependencies**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Initialize Database**
   The database will be automatically initialized when you first run the app.

3. **Start the Web Application**
   ```bash
   source venv/bin/activate
   python app.py
   ```

4. **Access the Dashboard**
   Open your browser and go to: `http://localhost:5000`

## Usage

### Fetching New Channels

1. Click the **"🔄 Fetch New Channels"** button in the dashboard
2. The system will automatically:
   - Search for channels across all configured countries and keywords
   - Skip channels that are already in your database
   - Add only new, unique channels
   - Show you how many new channels were added and how many were skipped

### Managing Channels

- **Mark as Emailed**: Check the checkbox in the "Emailed" column to mark a channel as contacted
- **Filter Channels**: Use the filter buttons (All/Emailed/Not Emailed) to view specific subsets
- **Search**: Type in the search box to find channels by title, description, or country
- **Add Notes**: Click on the notes field and type to add custom notes about each channel
- **View Channel**: Click "View Channel →" to open the YouTube channel in a new tab

### Configuration

Edit `youtube_fetcher.py` to customize:
- **Countries**: Modify the `COUNTRIES` list
- **Keywords**: Modify the `KEYWORDS` list
- **Max Subscribers**: Change the `max_subscribers` parameter in `fetch_new_channels()`

## File Structure

```
Youtube_fetch/
├── app.py                 # Flask web application
├── database.py            # Database operations
├── youtube_fetcher.py     # YouTube API integration
├── main.py                # Original script (legacy)
├── templates/
│   └── dashboard.html     # Web dashboard interface
├── youtube_channels.db    # SQLite database (created automatically)
└── requirements.txt       # Python dependencies
```

## Database Schema

The `channels` table stores:
- Channel information (ID, title, description, URL, etc.)
- Statistics (subscribers, views, video count)
- Metadata (country, keyword, fetched date)
- **Email tracking** (emailed status, emailed date)
- Custom notes

## API Endpoints

- `GET /` - Main dashboard
- `GET /api/channels` - Get channels with pagination and filters
- `POST /api/channels/update-emailed` - Update emailed status
- `POST /api/channels/update-notes` - Update channel notes
- `POST /api/fetch` - Trigger new channel fetch
- `GET /api/stats` - Get dashboard statistics

## Notes

- The system uses SQLite for data storage (no separate database server needed)
- Channels are identified by their unique YouTube Channel ID to prevent duplicates
- The dashboard auto-refreshes stats every 30 seconds
- All data is stored locally in `youtube_channels.db`

## Troubleshooting

**Issue**: "No channels found"  
**Solution**: Click "Fetch New Channels" to populate the database

**Issue**: Flask app won't start  
**Solution**: Make sure you're in the virtual environment and all dependencies are installed

**Issue**: YouTube API errors  
**Solution**: Check that your API key in `youtube_fetcher.py` is valid and has quota remaining


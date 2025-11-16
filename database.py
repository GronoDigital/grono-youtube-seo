import sqlite3
from datetime import datetime
from contextlib import contextmanager
import hashlib
import secrets

DB_NAME = 'youtube_channels.db'

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def migrate_database():
    """Migrate existing database to new schema"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            # Create users table
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
        
        # Check if channels table has required columns
        cursor.execute("PRAGMA table_info(channels)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'emailed_by' not in columns:
            cursor.execute('ALTER TABLE channels ADD COLUMN emailed_by INTEGER')
            print("✅ Added emailed_by column to channels table")
        
        if 'priority_score' not in columns:
            cursor.execute('ALTER TABLE channels ADD COLUMN priority_score REAL DEFAULT 0')
            print("✅ Added priority_score column to channels table")
        
        if 'reply_received' not in columns:
            cursor.execute('ALTER TABLE channels ADD COLUMN reply_received BOOLEAN DEFAULT 0')
            print("✅ Added reply_received column to channels table")
        
        if 'replied_at' not in columns:
            cursor.execute('ALTER TABLE channels ADD COLUMN replied_at TIMESTAMP')
            print("✅ Added replied_at column to channels table")
        
        if 'replied_by' not in columns:
            cursor.execute('ALTER TABLE channels ADD COLUMN replied_by INTEGER')
            print("✅ Added replied_by column to channels table")
        
        # Check if activity_log table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activity_log'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id INTEGER,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            print("✅ Created activity_log table")
        
        # Create indexes if they don't exist
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_emailed_by ON channels(emailed_by)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_priority_score ON channels(priority_score)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_reply_received ON channels(reply_received)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_replied_by ON channels(replied_by)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_log(user_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_log(created_at)
        ''')
        
        print("✅ Database migration completed")

def init_db():
    """Initialize the database with required tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Channels table (updated with user tracking)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE NOT NULL,
                title TEXT,
                description TEXT,
                country TEXT,
                country_code TEXT,
                subscribers INTEGER,
                total_views TEXT,
                video_count TEXT,
                custom_url TEXT,
                keywords TEXT,
                default_language TEXT,
                channel_url TEXT,
                search_keyword TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                emailed BOOLEAN DEFAULT 0,
                emailed_at TIMESTAMP,
                emailed_by INTEGER,
                reply_received BOOLEAN DEFAULT 0,
                replied_at TIMESTAMP,
                replied_by INTEGER,
                notes TEXT,
                priority_score REAL DEFAULT 0,
                FOREIGN KEY (emailed_by) REFERENCES users(id),
                FOREIGN KEY (replied_by) REFERENCES users(id)
            )
        ''')
        
        # Activity log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Migrate existing database first (adds missing columns)
        migrate_database()
        
        # Create indexes for faster lookups (after migration)
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_channel_id ON channels(channel_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_emailed ON channels(emailed)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_emailed_by ON channels(emailed_by)
        ''')
        
        # Create default admin user if no users exist
        cursor.execute('SELECT COUNT(*) FROM users')
        if cursor.fetchone()[0] == 0:
            # Default admin: username=admin, password=admin123 (change this!)
            default_password = hash_password('admin123')
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', ('admin', 'admin@youtubeseo.com', default_password, 'admin'))
            print("✅ Created default admin user: username='admin', password='admin123'")
            print("⚠️  IMPORTANT: Change the default password after first login!")
        
        print("✅ Database initialized successfully")

def channel_exists(channel_id):
    """Check if a channel already exists in the database"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM channels WHERE channel_id = ?', (channel_id,))
        return cursor.fetchone() is not None

def add_channel(channel_data):
    """Add a new channel to the database"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            # Calculate priority score
            priority_score = calculate_priority_score(channel_data)
            
            cursor.execute('''
                INSERT INTO channels (
                    channel_id, title, description, country, country_code,
                    subscribers, total_views, video_count, custom_url,
                    keywords, default_language, channel_url, search_keyword, priority_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                channel_data.get('Channel ID'),
                channel_data.get('Title'),
                channel_data.get('Description'),
                channel_data.get('Country'),
                channel_data.get('Country Code'),
                channel_data.get('Subscribers'),
                channel_data.get('Total Views'),
                channel_data.get('Video Count'),
                channel_data.get('Custom URL'),
                channel_data.get('Keywords'),
                channel_data.get('Default Language'),
                channel_data.get('Channel URL'),
                channel_data.get('Search Keyword'),
                priority_score
            ))
            return True
        except sqlite3.IntegrityError:
            # Channel already exists
            return False

def get_all_channels(emailed_filter=None, search_query=None, limit=100, offset=0, 
                     country_filter=None, keyword_filter=None, min_subscribers=None, 
                     max_subscribers=None, min_score=None, reply_filter=None, 
                     sort_by='fetched_at', sort_order='DESC'):
    """Get all channels with optional filters, including user info"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = '''
            SELECT c.*, 
                   u1.username as emailed_by_username,
                   u2.username as replied_by_username
            FROM channels c
            LEFT JOIN users u1 ON c.emailed_by = u1.id
            LEFT JOIN users u2 ON c.replied_by = u2.id
            WHERE 1=1
        '''
        params = []
        
        if emailed_filter is not None:
            query += ' AND c.emailed = ?'
            params.append(1 if emailed_filter else 0)
        
        if search_query:
            query += ' AND (c.title LIKE ? OR c.description LIKE ? OR c.country LIKE ?)'
            search_term = f'%{search_query}%'
            params.extend([search_term, search_term, search_term])
        
        if country_filter:
            query += ' AND c.country_code = ?'
            params.append(country_filter)
        
        if keyword_filter:
            query += ' AND c.search_keyword = ?'
            params.append(keyword_filter)
        
        if min_subscribers is not None:
            query += ' AND c.subscribers >= ?'
            params.append(min_subscribers)
        
        if max_subscribers is not None:
            query += ' AND c.subscribers <= ?'
            params.append(max_subscribers)
        
        if min_score is not None:
            query += ' AND c.priority_score >= ?'
            params.append(min_score)
        
        if reply_filter is not None:
            query += ' AND c.reply_received = ?'
            params.append(1 if reply_filter else 0)
        
        # Sorting
        valid_sort_fields = ['fetched_at', 'subscribers', 'priority_score', 'emailed_at', 'replied_at']
        if sort_by not in valid_sort_fields:
            sort_by = 'fetched_at'
        sort_order = 'DESC' if sort_order.upper() == 'DESC' else 'ASC'
        query += f' ORDER BY c.{sort_by} {sort_order} LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def get_channel_count(emailed_filter=None, country_filter=None, keyword_filter=None, 
                     min_subscribers=None, max_subscribers=None, min_score=None, reply_filter=None):
    """Get total count of channels with filters"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = 'SELECT COUNT(*) FROM channels WHERE 1=1'
        params = []
        
        if emailed_filter is not None:
            query += ' AND emailed = ?'
            params.append(1 if emailed_filter else 0)
        
        if country_filter:
            query += ' AND country_code = ?'
            params.append(country_filter)
        
        if keyword_filter:
            query += ' AND search_keyword = ?'
            params.append(keyword_filter)
        
        if min_subscribers is not None:
            query += ' AND subscribers >= ?'
            params.append(min_subscribers)
        
        if max_subscribers is not None:
            query += ' AND subscribers <= ?'
            params.append(max_subscribers)
        
        if min_score is not None:
            query += ' AND priority_score >= ?'
            params.append(min_score)
        
        if reply_filter is not None:
            query += ' AND reply_received = ?'
            params.append(1 if reply_filter else 0)
        
        cursor.execute(query, params)
        return cursor.fetchone()[0]

def update_emailed_status(channel_ids, emailed=True, user_id=None):
    """Update emailed status for channels"""
    with get_db() as conn:
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat() if emailed else None
        placeholders = ','.join(['?'] * len(channel_ids))
        if emailed:
            cursor.execute(f'''
                UPDATE channels 
                SET emailed = 1, emailed_at = ?, emailed_by = ? 
                WHERE id IN ({placeholders})
            ''', [timestamp, user_id] + channel_ids)
        else:
            cursor.execute(f'''
                UPDATE channels 
                SET emailed = 0, emailed_at = NULL, emailed_by = NULL 
                WHERE id IN ({placeholders})
            ''', channel_ids)
        return cursor.rowcount

def update_reply_status(channel_id, reply_received=True, user_id=None):
    """Update reply received status for a channel"""
    with get_db() as conn:
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat() if reply_received else None
        if reply_received:
            cursor.execute('''
                UPDATE channels 
                SET reply_received = 1, replied_at = ?, replied_by = ? 
                WHERE id = ?
            ''', (timestamp, user_id, channel_id))
        else:
            cursor.execute('''
                UPDATE channels 
                SET reply_received = 0, replied_at = NULL, replied_by = NULL 
                WHERE id = ?
            ''', (channel_id,))
        return cursor.rowcount > 0

def update_channel_notes(channel_id, notes, user_id=None):
    """Update notes for a channel"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE channels SET notes = ? WHERE id = ?', (notes, channel_id))
        
        # Log activity
        if user_id:
            log_activity(user_id, 'updated_notes', 'channel', channel_id, 
                        f'Updated notes: {notes[:50]}')
        
        return cursor.rowcount

def get_fetched_channel_ids():
    """Get all channel IDs that have already been fetched"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT channel_id FROM channels')
        return set(row[0] for row in cursor.fetchall())

# ==================== USER MANAGEMENT FUNCTIONS ====================

def verify_password(password, password_hash):
    """Verify a password against a hash"""
    return hash_password(password) == password_hash

def create_user(username, email, password, role='user'):
    """Create a new user"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            password_hash = hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            ''', (username, email, password_hash, role))
            return True, cursor.lastrowid
        except sqlite3.IntegrityError as e:
            return False, str(e)

def get_user_by_username(username):
    """Get user by username"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND is_active = 1', (username,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id):
    """Get user by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ? AND is_active = 1', (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_users():
    """Get all users"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, role, created_at, is_active FROM users ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]

def delete_user(user_id):
    """Delete (deactivate) a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
        return cursor.rowcount

def update_user_password(user_id, new_password):
    """Update user password"""
    with get_db() as conn:
        cursor = conn.cursor()
        password_hash = hash_password(new_password)
        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, user_id))
        return cursor.rowcount

def get_user_stats(user_id):
    """Get statistics for a specific user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM channels WHERE emailed_by = ?', (user_id,))
        channels_emailed = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM channels WHERE replied_by = ?', (user_id,))
        replies_received = cursor.fetchone()[0]
        return {
            'channels_emailed': channels_emailed,
            'replies_received': replies_received
        }

def calculate_priority_score(channel):
    """Calculate priority score based on engagement metrics"""
    try:
        subscribers = int(channel.get('subscribers', 0) or 0)
        views = int(channel.get('total_views', 0) or 0)
        videos = int(channel.get('video_count', 0) or 0)
        
        # Score calculation (weighted)
        # Subscriber score (0-40 points): More subscribers = higher score
        sub_score = min(40, subscribers / 2500)  # 100k subs = 40 points
        
        # Engagement score (0-30 points): Views per subscriber ratio
        if subscribers > 0:
            engagement = views / subscribers
            engagement_score = min(30, engagement / 10)  # 100 views/sub = 30 points
        else:
            engagement_score = 0
        
        # Activity score (0-30 points): More videos = more active
        activity_score = min(30, videos / 10)  # 300 videos = 30 points
        
        total_score = sub_score + engagement_score + activity_score
        return round(total_score, 2)
    except:
        return 0.0

def update_channel_priority_scores():
    """Update priority scores for all channels"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM channels')
        channels = cursor.fetchall()
        
        updated = 0
        for channel_row in channels:
            channel = dict(channel_row)
            score = calculate_priority_score(channel)
            cursor.execute('UPDATE channels SET priority_score = ? WHERE id = ?', 
                         (score, channel['id']))
            updated += 1
        
        return updated

def log_activity(user_id, action, entity_type=None, entity_id=None, details=None):
    """Log user activity"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO activity_log (user_id, action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, action, entity_type, entity_id, details))
        return cursor.lastrowid

def get_activity_log(limit=100, user_id=None, action=None):
    """Get activity log entries"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = '''
            SELECT al.*, u.username 
            FROM activity_log al
            LEFT JOIN users u ON al.user_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if user_id:
            query += ' AND al.user_id = ?'
            params.append(user_id)
        
        if action:
            query += ' AND al.action = ?'
            params.append(action)
        
        query += ' ORDER BY al.created_at DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def get_analytics_data():
    """Get analytics data for dashboard"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Daily stats for last 30 days
        cursor.execute('''
            SELECT DATE(fetched_at) as date, COUNT(*) as count
            FROM channels
            WHERE fetched_at >= datetime('now', '-30 days')
            GROUP BY DATE(fetched_at)
            ORDER BY date DESC
        ''')
        daily_fetched = [dict(row) for row in cursor.fetchall()]
        
        # Daily emailed stats
        cursor.execute('''
            SELECT DATE(emailed_at) as date, COUNT(*) as count
            FROM channels
            WHERE emailed_at >= datetime('now', '-30 days')
            AND emailed = 1
            GROUP BY DATE(emailed_at)
            ORDER BY date DESC
        ''')
        daily_emailed = [dict(row) for row in cursor.fetchall()]
        
        # Channels by country
        cursor.execute('''
            SELECT country_code, COUNT(*) as count
            FROM channels
            GROUP BY country_code
            ORDER BY count DESC
        ''')
        by_country = [dict(row) for row in cursor.fetchall()]
        
        # Channels by keyword
        cursor.execute('''
            SELECT search_keyword, COUNT(*) as count
            FROM channels
            WHERE search_keyword IS NOT NULL
            GROUP BY search_keyword
            ORDER BY count DESC
            LIMIT 10
        ''')
        by_keyword = [dict(row) for row in cursor.fetchall()]
        
        # User performance
        cursor.execute('''
            SELECT u.username, COUNT(c.id) as channels_emailed
            FROM users u
            LEFT JOIN channels c ON u.id = c.emailed_by
            WHERE c.emailed = 1
            GROUP BY u.id, u.username
            ORDER BY channels_emailed DESC
        ''')
        user_performance = [dict(row) for row in cursor.fetchall()]
        
        return {
            'daily_fetched': daily_fetched,
            'daily_emailed': daily_emailed,
            'by_country': by_country,
            'by_keyword': by_keyword,
            'user_performance': user_performance
        }


from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from database import (
    init_db, get_all_channels, get_channel_count, update_emailed_status, 
    update_channel_notes, get_fetched_channel_ids, get_user_by_username,
    verify_password, create_user, get_all_users, delete_user, get_user_by_id,
    get_user_stats, update_user_password, log_activity, get_activity_log,
    get_analytics_data, update_channel_priority_scores, update_reply_status
)
import pandas as pd
import io
from youtube_fetcher import fetch_new_channels, analyze_channel
from functools import wraps
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret-key-in-production-12345')

# Initialize database on startup
init_db()

# ==================== AUTHENTICATION HELPERS ====================

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        user = get_user_by_id(session['user_id'])
        if not user or user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# ==================== AUTHENTICATION ROUTES ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        user = get_user_by_username(username)
        if user and verify_password(password, user['password_hash']):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role']
                }
            })
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
    
    # GET request - show login page
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    """Logout handler"""
    session.clear()
    return jsonify({'success': True})

@app.route('/api/me')
@login_required
def get_current_user():
    """Get current logged in user info"""
    user = get_user_by_id(session['user_id'])
    if user:
        stats = get_user_stats(user['id'])
        return jsonify({
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role'],
            'stats': stats
        })
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    """Change current user's password"""
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    user_id = session['user_id']
    
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    if not verify_password(current_password, user['password_hash']):
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
    
    if not new_password or len(new_password) < 6:
        return jsonify({'success': False, 'error': 'New password must be at least 6 characters'}), 400
    
    updated = update_user_password(user_id, new_password)
    if updated:
        log_activity(user_id, 'changed_password', 'user', user_id, 'Password changed')
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Failed to update password'}), 500

# ==================== MAIN ROUTES ====================

@app.route('/')
def index():
    """Public landing page - Channel Analyzer"""
    return render_template('analyzer.html')

@app.route('/dashboard')
def dashboard():
    """Main dashboard page (requires login)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_channel_api():
    """Public API endpoint to analyze a YouTube channel"""
    data = request.json or {}
    channel_url = data.get('channel_url', '').strip()
    
    if not channel_url:
        return jsonify({'success': False, 'error': 'Channel URL is required'}), 400
    
    try:
        channel_data = analyze_channel(channel_url)
        if not channel_data:
            # Provide more helpful error message
            return jsonify({
                'success': False, 
                'error': 'Channel not found or invalid URL. Please check that the URL is correct and try again.'
            }), 404
        
        return jsonify({
            'success': True,
            'channel': channel_data
        })
    except Exception as e:
        error_msg = str(e)
        # Check for quota errors
        if 'quota' in error_msg.lower() or 'quotaExceeded' in error_msg:
            return jsonify({
                'success': False, 
                'error': 'API quota exceeded. Please try again later.'
            }), 503
        return jsonify({'success': False, 'error': f'Error analyzing channel: {error_msg}'}), 500

@app.route('/users')
def users_page():
    """User management page (admin only)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    if not user or user.get('role') != 'admin':
        return redirect(url_for('dashboard'))
    return render_template('users.html')

# ==================== API ROUTES ====================

@app.route('/api/channels')
@login_required
def api_channels():
    """API endpoint to get channels with pagination and advanced filters"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    emailed_filter = request.args.get('emailed')
    search_query = request.args.get('search', '')
    country_filter = request.args.get('country')
    keyword_filter = request.args.get('keyword')
    min_subscribers = request.args.get('min_subscribers', type=int)
    max_subscribers = request.args.get('max_subscribers', type=int)
    min_score = request.args.get('min_score', type=float)
    reply_filter = request.args.get('reply')
    sort_by = request.args.get('sort_by', 'fetched_at')
    sort_order = request.args.get('sort_order', 'DESC')
    
    # Convert emailed filter
    emailed = None
    if emailed_filter == 'true':
        emailed = True
    elif emailed_filter == 'false':
        emailed = False
    
    # Convert reply filter
    reply = None
    if reply_filter == 'true':
        reply = True
    elif reply_filter == 'false':
        reply = False
    
    offset = (page - 1) * per_page
    channels = get_all_channels(
        emailed_filter=emailed, 
        search_query=search_query, 
        limit=per_page, 
        offset=offset,
        country_filter=country_filter,
        keyword_filter=keyword_filter,
        min_subscribers=min_subscribers,
        max_subscribers=max_subscribers,
        min_score=min_score,
        reply_filter=reply,
        sort_by=sort_by,
        sort_order=sort_order
    )
    total_count = get_channel_count(
        emailed_filter=emailed,
        country_filter=country_filter,
        keyword_filter=keyword_filter,
        min_subscribers=min_subscribers,
        max_subscribers=max_subscribers,
        min_score=min_score,
        reply_filter=reply
    )
    
    return jsonify({
        'channels': channels,
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': (total_count + per_page - 1) // per_page
    })

@app.route('/api/channels/update-emailed', methods=['POST'])
@login_required
def update_emailed():
    """Update emailed status for channels"""
    data = request.json
    channel_ids = data.get('channel_ids', [])
    emailed = data.get('emailed', True)
    user_id = session['user_id']
    
    updated = update_emailed_status(channel_ids, emailed, user_id=user_id if emailed else None)
    
    # Log activity
    log_activity(user_id, 'bulk_emailed' if len(channel_ids) > 1 else 'marked_emailed', 
                'channel', None, f'Updated {len(channel_ids)} channels')
    
    return jsonify({'success': True, 'updated': updated})

@app.route('/api/channels/update-notes', methods=['POST'])
@login_required
def update_notes():
    """Update notes for a channel"""
    data = request.json
    channel_id = data.get('channel_id')
    notes = data.get('notes', '')
    user_id = session['user_id']
    
    updated = update_channel_notes(channel_id, notes, user_id=user_id)
    return jsonify({'success': True, 'updated': updated})

@app.route('/api/channels/update-reply', methods=['POST'])
@login_required
def update_reply():
    """Update reply received status for a channel"""
    data = request.json
    channel_id = data.get('channel_id')
    reply_received = data.get('reply_received', True)
    user_id = session['user_id']
    
    updated = update_reply_status(channel_id, reply_received=reply_received, user_id=user_id)
    if updated:
        log_activity(user_id, 'update_reply_status', 'channel', channel_id, 
                    f'Marked channel as {"reply received" if reply_received else "no reply"}')
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Channel not found'}), 404

@app.route('/api/fetch', methods=['POST'])
@admin_required
def fetch_channels():
    """Trigger a new channel fetch (Admin only) - Targets 100 new channels"""
    data = request.json or {}
    max_results = data.get('max_results', 50)  # Reduced to 50 for quota efficiency
    target_channels = data.get('target_channels', 100)  # Default target: 100 channels
    user_id = session['user_id']
    
    try:
        result = fetch_new_channels(max_results=max_results, target_channels=target_channels, user_id=user_id)
        
        # Log activity
        log_activity(user_id, 'fetch_channels', None, None, 
                    f'Fetched {result["new_channels"]} new channels')
        
        # Update priority scores for new channels
        update_channel_priority_scores()
        
        return jsonify({
            'success': True,
            'message': f'Successfully fetched {result["new_channels"]} new channels',
            'total_fetched': result['total_fetched'],
            'skipped': result['skipped'],
            'target_reached': result.get('target_reached', False)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats')
@login_required
def get_stats():
    """Get dashboard statistics"""
    total_channels = get_channel_count()
    emailed_channels = get_channel_count(emailed_filter=True)
    not_emailed_channels = get_channel_count(emailed_filter=False)
    replies_received = get_channel_count(reply_filter=True)
    no_replies = get_channel_count(reply_filter=False)
    
    # Get current user stats
    user_stats = get_user_stats(session['user_id'])
    
    # Calculate reply rate
    reply_rate = round((replies_received / emailed_channels * 100) if emailed_channels > 0 else 0, 1)
    
    return jsonify({
        'total': total_channels,
        'emailed': emailed_channels,
        'not_emailed': not_emailed_channels,
        'replies_received': replies_received,
        'no_replies': no_replies,
        'reply_rate': reply_rate,
        'my_emailed': user_stats['channels_emailed'],
        'my_replies': user_stats.get('replies_received', 0)
    })

@app.route('/api/analytics')
@login_required
def get_analytics():
    """Get analytics data"""
    try:
        data = get_analytics_data()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/filters/options')
@login_required
def get_filter_options():
    """Get available filter options (keywords, countries)"""
    from database import get_db
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get unique keywords
        cursor.execute('SELECT DISTINCT search_keyword FROM channels WHERE search_keyword IS NOT NULL ORDER BY search_keyword')
        keywords = [row[0] for row in cursor.fetchall()]
        
        # Get unique countries
        cursor.execute('SELECT DISTINCT country_code FROM channels WHERE country_code IS NOT NULL ORDER BY country_code')
        countries = [row[0] for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'keywords': keywords,
            'countries': countries
        })

@app.route('/api/activity')
@login_required
def get_activity():
    """Get activity log"""
    limit = int(request.args.get('limit', 100))
    user_id = request.args.get('user_id', type=int)
    action = request.args.get('action')
    
    # Only admins can see all activity
    if user_id and session.get('role') != 'admin':
        user_id = session['user_id']
    
    try:
        activities = get_activity_log(limit=limit, user_id=user_id, action=action)
        return jsonify({'success': True, 'activities': activities})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/export')
@login_required
def export_channels():
    """Export channels to Excel/CSV"""
    format_type = request.args.get('format', 'excel')  # 'excel' or 'csv'
    emailed_filter = request.args.get('emailed')
    search_query = request.args.get('search', '')
    country_filter = request.args.get('country')
    keyword_filter = request.args.get('keyword')
    min_subscribers = request.args.get('min_subscribers', type=int)
    max_subscribers = request.args.get('max_subscribers', type=int)
    min_score = request.args.get('min_score', type=float)
    reply_filter = request.args.get('reply')
    
    # Convert emailed filter
    emailed = None
    if emailed_filter == 'true':
        emailed = True
    elif emailed_filter == 'false':
        emailed = False
    
    # Convert reply filter
    reply = None
    if reply_filter == 'true':
        reply = True
    elif reply_filter == 'false':
        reply = False
    
    # Get all matching channels (no pagination for export)
    channels = get_all_channels(
        emailed_filter=emailed,
        search_query=search_query,
        limit=10000,  # Large limit for export
        offset=0,
        country_filter=country_filter,
        keyword_filter=keyword_filter,
        min_subscribers=min_subscribers,
        max_subscribers=max_subscribers,
        min_score=min_score,
        reply_filter=reply
    )
    
    # Prepare data for export
    export_data = []
    for ch in channels:
        export_data.append({
            'Title': ch.get('title', ''),
            'Channel URL': ch.get('channel_url', ''),
            'Country': ch.get('country', ''),
            'Country Code': ch.get('country_code', ''),
            'Subscribers': ch.get('subscribers', 0),
            'Total Views': ch.get('total_views', 0),
            'Video Count': ch.get('video_count', 0),
            'Search Keyword': ch.get('search_keyword', ''),
            'Priority Score': ch.get('priority_score', 0),
            'Emailed': 'Yes' if ch.get('emailed') else 'No',
            'Emailed By': ch.get('emailed_by_username', ''),
            'Emailed At': ch.get('emailed_at', ''),
            'Reply Received': 'Yes' if ch.get('reply_received') else 'No',
            'Replied By': ch.get('replied_by_username', ''),
            'Replied At': ch.get('replied_at', ''),
            'Notes': ch.get('notes', ''),
            'Fetched At': ch.get('fetched_at', '')
        })
    
    df = pd.DataFrame(export_data)
    
    # Log activity
    log_activity(session['user_id'], 'export_channels', None, None, 
                f'Exported {len(export_data)} channels as {format_type}')
    
    if format_type == 'csv':
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='youtube_channels.csv'
        )
    else:  # excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Channels')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='youtube_channels.xlsx'
        )

@app.route('/analytics')
def analytics_page():
    """Analytics dashboard page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('analytics.html')

@app.route('/activity')
def activity_page():
    """Activity log page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('activity.html')

# ==================== USER MANAGEMENT API (ADMIN ONLY) ====================

@app.route('/api/users', methods=['GET'])
@admin_required
def api_get_users():
    """Get all users (admin only)"""
    users = get_all_users()
    return jsonify({'users': users})

@app.route('/api/users', methods=['POST'])
@admin_required
def api_create_user():
    """Create a new user (admin only)"""
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')
    
    if not username or not email or not password:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    success, result = create_user(username, email, password, role)
    if success:
        return jsonify({'success': True, 'user_id': result})
    return jsonify({'success': False, 'error': result}), 400

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def api_delete_user(user_id):
    """Delete a user (admin only)"""
    if user_id == session['user_id']:
        return jsonify({'success': False, 'error': 'Cannot delete yourself'}), 400
    
    deleted = delete_user(user_id)
    if deleted:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'User not found'}), 404

@app.route('/api/users/<int:user_id>/password', methods=['POST'])
@admin_required
def api_reset_password(user_id):
    """Reset user password (admin only)"""
    data = request.json
    new_password = data.get('password')
    
    if not new_password:
        return jsonify({'success': False, 'error': 'Password required'}), 400
    
    updated = update_user_password(user_id, new_password)
    if updated:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'User not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    print(f"🚀 Starting YouTube SEO Service Manager on http://localhost:{port}")
    app.run(debug=debug, host='0.0.0.0', port=port)

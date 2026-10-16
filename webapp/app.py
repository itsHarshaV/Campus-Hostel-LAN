"""
Campus Hostel LAN – Hostel Management Web Application
======================================================
Flask backend serving Student / Warden / Admin modules
and a Network Dashboard over the Campus LAN.

Run: python app.py
URL: http://localhost:5000  (or http://hostel.local:5000 on the LAN)
"""

import os
import sqlite3
import hashlib
from datetime import datetime, timedelta
from functools import wraps
# pyrefly: ignore [missing-import]
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, jsonify, g)

# ── App setup ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'hostel.db')

app = Flask(__name__)
app.secret_key = 'hostel-lan-secret-2024-cse-pbl'
app.permanent_session_lifetime = timedelta(hours=8)

# ── Database helpers ─────────────────────────────────────────
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv  = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

def execute(sql, args=()):
    db = get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur.lastrowid

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    with app.app_context():
        db = get_db()
        with open(os.path.join(BASE_DIR, 'schema.sql'), 'r') as f:
            db.executescript(f.read())
        db.commit()

# ── Auth decorators ──────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash('Access denied.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator

# ── Context processor ────────────────────────────────────────
@app.context_processor
def inject_globals():
    return dict(now=datetime.now(), session=session)

# ═══════════════════════════════════════════════════════════════
# AUTH ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route('/', methods=['GET','POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        user = query(
            "SELECT * FROM users WHERE username=? AND is_active=1",
            (username,), one=True
        )
        # Check plain text (seed data) or hashed password
        if user and (user['password'] == password or
                     user['password'] == hash_pw(password)):
            session.permanent = True
            session['user_id']   = user['id']
            session['username']  = user['username']
            session['role']      = user['role']
            session['full_name'] = user['full_name']
            flash(f"Welcome, {user['full_name']}!", 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    if role == 'student':
        return redirect(url_for('student_home'))
    elif role == 'warden':
        return redirect(url_for('warden_home'))
    elif role == 'admin':
        return redirect(url_for('admin_home'))
    return redirect(url_for('login'))

# ═══════════════════════════════════════════════════════════════
# STUDENT MODULE
# ═══════════════════════════════════════════════════════════════

@app.route('/student/')
@role_required('student')
def student_home():
    user_id = session['user_id']
    student = query(
        """SELECT s.*, r.room_number, r.block, r.floor, r.room_type,
                  r.amenities, u.full_name, u.email, u.phone
           FROM students s
           JOIN users u ON s.user_id = u.id
           LEFT JOIN rooms r ON s.room_id = r.id
           WHERE s.user_id = ?""",
        (user_id,), one=True
    )
    notices = query(
        "SELECT * FROM notices WHERE target_role IN ('all','student') "
        "AND (expires_at IS NULL OR expires_at > datetime('now')) "
        "ORDER BY priority DESC, created_at DESC LIMIT 5"
    )
    pending_complaints = query(
        "SELECT COUNT(*) as cnt FROM complaints WHERE student_id=? AND status != 'Closed'",
        (student['id'],), one=True
    )
    return render_template('student/home.html',
        student=student, notices=notices,
        pending_complaints=pending_complaints['cnt'])

@app.route('/student/room')
@role_required('student')
def student_room():
    user_id = session['user_id']
    student = query(
        """SELECT s.*, r.room_number, r.block, r.floor, r.capacity,
                  r.occupied, r.room_type, r.status, r.amenities
           FROM students s
           LEFT JOIN rooms r ON s.room_id = r.id
           WHERE s.user_id = ?""",
        (user_id,), one=True
    )
    roommates = []
    if student and student['room_id']:
        roommates = query(
            """SELECT u.full_name, s.roll_number, s.department, s.year
               FROM students s JOIN users u ON s.user_id = u.id
               WHERE s.room_id = ? AND s.user_id != ?""",
            (student['room_id'], user_id)
        )
    return render_template('student/room.html', student=student, roommates=roommates)

@app.route('/student/notices')
@role_required('student')
def student_notices():
    notices = query(
        "SELECT n.*, u.full_name as posted_by_name FROM notices n "
        "JOIN users u ON n.posted_by = u.id "
        "WHERE n.target_role IN ('all','student') "
        "AND (n.expires_at IS NULL OR n.expires_at > datetime('now')) "
        "ORDER BY n.priority DESC, n.created_at DESC"
    )
    return render_template('student/notices.html', notices=notices)

@app.route('/student/complaints', methods=['GET','POST'])
@role_required('student')
def student_complaints():
    user_id = session['user_id']
    student = query("SELECT * FROM students WHERE user_id=?", (user_id,), one=True)
    if request.method == 'POST':
        category    = request.form.get('category')
        subject     = request.form.get('subject','').strip()
        description = request.form.get('description','').strip()
        priority    = request.form.get('priority','Normal')
        if subject and description and category:
            execute(
                """INSERT INTO complaints (student_id,category,subject,description,priority,status)
                   VALUES (?,?,?,?,?,'Pending')""",
                (student['id'], category, subject, description, priority)
            )
            flash('Complaint submitted successfully!', 'success')
        else:
            flash('Please fill in all fields.', 'danger')
        return redirect(url_for('student_complaints'))
    complaints = query(
        "SELECT c.*, w.user_id as warden_user FROM complaints c "
        "LEFT JOIN wardens w ON c.assigned_to = w.id "
        "WHERE c.student_id=? ORDER BY c.created_at DESC",
        (student['id'],)
    )
    categories = ['Maintenance','Cleanliness','Noise','Food',
                  'Water','Electricity','Internet','Security','Other']
    return render_template('student/complaints.html',
        complaints=complaints, categories=categories)

@app.route('/student/mess')
@role_required('student')
def student_mess():
    day = datetime.now().strftime('%A')
    today_menu = query(
        "SELECT * FROM mess_menu WHERE day_of_week=? ORDER BY "
        "CASE meal_type WHEN 'Breakfast' THEN 1 WHEN 'Lunch' THEN 2 "
        "WHEN 'Snacks' THEN 3 WHEN 'Dinner' THEN 4 END",
        (day,)
    )
    full_menu = {}
    for row in query("SELECT * FROM mess_menu ORDER BY day_of_week, "
                     "CASE meal_type WHEN 'Breakfast' THEN 1 WHEN 'Lunch' THEN 2 "
                     "WHEN 'Snacks' THEN 3 WHEN 'Dinner' THEN 4 END"):
        full_menu.setdefault(row['day_of_week'], []).append(row)
    return render_template('student/mess.html',
        today_menu=today_menu, full_menu=full_menu, today=day)

# ═══════════════════════════════════════════════════════════════
# WARDEN MODULE
# ═══════════════════════════════════════════════════════════════

@app.route('/warden/')
@role_required('warden')
def warden_home():
    stats = {
        'total_students':   query("SELECT COUNT(*) as c FROM students", one=True)['c'],
        'pending_complaints': query("SELECT COUNT(*) as c FROM complaints WHERE status='Pending'", one=True)['c'],
        'total_rooms':      query("SELECT COUNT(*) as c FROM rooms", one=True)['c'],
        'available_rooms':  query("SELECT COUNT(*) as c FROM rooms WHERE status='Available'", one=True)['c'],
    }
    recent_complaints = query(
        """SELECT c.*, u.full_name, r.room_number
           FROM complaints c
           JOIN students s ON c.student_id = s.id
           JOIN users u ON s.user_id = u.id
           LEFT JOIN rooms r ON s.room_id = r.id
           ORDER BY c.created_at DESC LIMIT 5"""
    )
    recent_notices = query(
        "SELECT * FROM notices ORDER BY created_at DESC LIMIT 5"
    )
    return render_template('warden/home.html',
        stats=stats, recent_complaints=recent_complaints,
        recent_notices=recent_notices)

@app.route('/warden/students')
@role_required('warden')
def warden_students():
    students = query(
        """SELECT s.*, u.full_name, u.email, u.phone, u.is_active,
                  r.room_number, r.block, r.floor
           FROM students s
           JOIN users u ON s.user_id = u.id
           LEFT JOIN rooms r ON s.room_id = r.id
           ORDER BY u.full_name"""
    )
    return render_template('warden/students.html', students=students)

@app.route('/warden/complaints', methods=['GET','POST'])
@role_required('warden')
def warden_complaints():
    if request.method == 'POST':
        cid      = request.form.get('complaint_id')
        status   = request.form.get('status')
        response = request.form.get('response','').strip()
        resolved_at = "datetime('now')" if status == 'Resolved' else None
        if resolved_at:
            execute(
                "UPDATE complaints SET status=?,response=?,updated_at=datetime('now'),"
                "resolved_at=datetime('now') WHERE id=?",
                (status, response, cid)
            )
        else:
            execute(
                "UPDATE complaints SET status=?,response=?,updated_at=datetime('now') WHERE id=?",
                (status, response, cid)
            )
        flash('Complaint updated.', 'success')
        return redirect(url_for('warden_complaints'))
    status_filter = request.args.get('status', 'all')
    if status_filter == 'all':
        complaints = query(
            """SELECT c.*, u.full_name, r.room_number
               FROM complaints c
               JOIN students s ON c.student_id = s.id
               JOIN users u ON s.user_id = u.id
               LEFT JOIN rooms r ON s.room_id = r.id
               ORDER BY CASE c.priority WHEN 'Urgent' THEN 1 WHEN 'High' THEN 2
                        WHEN 'Normal' THEN 3 ELSE 4 END, c.created_at DESC"""
        )
    else:
        complaints = query(
            """SELECT c.*, u.full_name, r.room_number
               FROM complaints c
               JOIN students s ON c.student_id = s.id
               JOIN users u ON s.user_id = u.id
               LEFT JOIN rooms r ON s.room_id = r.id
               WHERE c.status=?
               ORDER BY c.created_at DESC""", (status_filter,)
        )
    return render_template('warden/complaints.html',
        complaints=complaints, status_filter=status_filter)

@app.route('/warden/notices', methods=['GET','POST'])
@role_required('warden')
def warden_notices():
    if request.method == 'POST':
        title       = request.form.get('title','').strip()
        content     = request.form.get('content','').strip()
        target_role = request.form.get('target_role','all')
        priority    = request.form.get('priority','normal')
        expires_str = request.form.get('expires_at','').strip()
        expires_at  = expires_str if expires_str else None
        if title and content:
            execute(
                "INSERT INTO notices (title,content,posted_by,target_role,priority,expires_at) "
                "VALUES (?,?,?,?,?,?)",
                (title, content, session['user_id'], target_role, priority, expires_at)
            )
            flash('Notice posted successfully!', 'success')
        else:
            flash('Title and content are required.', 'danger')
        return redirect(url_for('warden_notices'))
    notices = query(
        "SELECT n.*, u.full_name as posted_by_name FROM notices n "
        "JOIN users u ON n.posted_by = u.id "
        "ORDER BY n.created_at DESC"
    )
    return render_template('warden/notices.html', notices=notices)

@app.route('/warden/rooms')
@role_required('warden')
def warden_rooms():
    rooms = query(
        """SELECT r.*,
              (SELECT COUNT(*) FROM students WHERE room_id = r.id) as student_count
           FROM rooms r ORDER BY r.block, r.floor, r.room_number"""
    )
    return render_template('warden/rooms.html', rooms=rooms)

# ═══════════════════════════════════════════════════════════════
# ADMIN MODULE
# ═══════════════════════════════════════════════════════════════

@app.route('/admin/')
@role_required('admin')
def admin_home():
    stats = {
        'total_students':  query("SELECT COUNT(*) as c FROM students", one=True)['c'],
        'total_wardens':   query("SELECT COUNT(*) as c FROM wardens", one=True)['c'],
        'total_rooms':     query("SELECT COUNT(*) as c FROM rooms", one=True)['c'],
        'available_rooms': query("SELECT COUNT(*) as c FROM rooms WHERE status='Available'", one=True)['c'],
        'full_rooms':      query("SELECT COUNT(*) as c FROM rooms WHERE status='Full'", one=True)['c'],
        'pending_complaints': query("SELECT COUNT(*) as c FROM complaints WHERE status='Pending'", one=True)['c'],
        'total_devices':   query("SELECT COUNT(*) as c FROM network_devices", one=True)['c'],
        'online_devices':  query("SELECT COUNT(*) as c FROM network_devices WHERE status='Online'", one=True)['c'],
    }
    vlans = [
        {'id':10,'name':'Admin',      'subnet':'192.168.10.0/24','gateway':'192.168.10.1','devices':3},
        {'id':20,'name':'Students',   'subnet':'192.168.20.0/24','gateway':'192.168.20.1','devices':250},
        {'id':30,'name':'Wardens',    'subnet':'192.168.30.0/24','gateway':'192.168.30.1','devices':10},
        {'id':40,'name':'Common/Lab', 'subnet':'192.168.40.0/24','gateway':'192.168.40.1','devices':40},
        {'id':50,'name':'Guest',      'subnet':'192.168.50.0/24','gateway':'192.168.50.1','devices':20},
        {'id':100,'name':'Servers',   'subnet':'192.168.100.0/24','gateway':'192.168.100.1','devices':5},
    ]
    return render_template('admin/home.html', stats=stats, vlans=vlans)

@app.route('/admin/students', methods=['GET','POST'])
@role_required('admin')
def admin_students():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            username  = request.form.get('username','').strip()
            password  = request.form.get('password','').strip()
            full_name = request.form.get('full_name','').strip()
            email     = request.form.get('email','').strip()
            phone     = request.form.get('phone','').strip()
            roll_no   = request.form.get('roll_number','').strip()
            dept      = request.form.get('department','').strip()
            year      = request.form.get('year',1)
            room_id   = request.form.get('room_id') or None
            try:
                uid = execute(
                    "INSERT INTO users (username,password,role,full_name,email,phone) VALUES (?,?,?,?,?,?)",
                    (username, password, 'student', full_name, email, phone)
                )
                execute(
                    "INSERT INTO students (user_id,roll_number,department,year,room_id) VALUES (?,?,?,?,?)",
                    (uid, roll_no, dept, year, room_id)
                )
                if room_id:
                    execute("UPDATE rooms SET occupied = occupied + 1 WHERE id=?", (room_id,))
                flash('Student added successfully!', 'success')
            except Exception as e:
                flash(f'Error: {e}', 'danger')
        elif action == 'delete':
            sid = request.form.get('student_id')
            student = query("SELECT * FROM students WHERE id=?", (sid,), one=True)
            if student and student['room_id']:
                execute("UPDATE rooms SET occupied = MAX(0, occupied-1) WHERE id=?", (student['room_id'],))
            execute("DELETE FROM students WHERE id=?", (sid,))
            flash('Student removed.', 'info')
        elif action == 'toggle':
            uid = request.form.get('user_id')
            execute("UPDATE users SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id=?", (uid,))
            flash('Student status toggled.', 'info')
        return redirect(url_for('admin_students'))
    students = query(
        """SELECT s.*, u.full_name, u.email, u.phone, u.username,
                  u.is_active, r.room_number, r.block
           FROM students s
           JOIN users u ON s.user_id = u.id
           LEFT JOIN rooms r ON s.room_id = r.id
           ORDER BY u.full_name"""
    )
    rooms = query("SELECT * FROM rooms WHERE status != 'Full' OR status = 'Available' ORDER BY block, room_number")
    return render_template('admin/students.html', students=students, rooms=rooms)

@app.route('/admin/rooms', methods=['GET','POST'])
@role_required('admin')
def admin_rooms():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            execute(
                "INSERT INTO rooms (room_number,block,floor,capacity,occupied,room_type,amenities) VALUES (?,?,?,?,0,?,?)",
                (request.form.get('room_number'), request.form.get('block'),
                 request.form.get('floor'), request.form.get('capacity'),
                 request.form.get('room_type'), request.form.get('amenities',''))
            )
            flash('Room added!', 'success')
        elif action == 'update_status':
            execute(
                "UPDATE rooms SET status=? WHERE id=?",
                (request.form.get('status'), request.form.get('room_id'))
            )
            flash('Room status updated.', 'info')
        elif action == 'delete':
            execute("DELETE FROM rooms WHERE id=?", (request.form.get('room_id'),))
            flash('Room deleted.', 'info')
        return redirect(url_for('admin_rooms'))
    rooms = query(
        """SELECT r.*,
              (SELECT COUNT(*) FROM students WHERE room_id = r.id) as student_count
           FROM rooms r ORDER BY block, floor, room_number"""
    )
    return render_template('admin/rooms.html', rooms=rooms)

@app.route('/admin/wardens', methods=['GET','POST'])
@role_required('admin')
def admin_wardens():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            username  = request.form.get('username','').strip()
            password  = request.form.get('password','').strip()
            full_name = request.form.get('full_name','').strip()
            email     = request.form.get('email','').strip()
            emp_id    = request.form.get('employee_id','').strip()
            block     = request.form.get('block','Both')
            try:
                uid = execute(
                    "INSERT INTO users (username,password,role,full_name,email) VALUES (?,?,?,?,?)",
                    (username, password, 'warden', full_name, email)
                )
                execute(
                    "INSERT INTO wardens (user_id,employee_id,block) VALUES (?,?,?)",
                    (uid, emp_id, block)
                )
                flash('Warden added!', 'success')
            except Exception as e:
                flash(f'Error: {e}', 'danger')
        elif action == 'delete':
            wid = request.form.get('warden_id')
            warden = query("SELECT user_id FROM wardens WHERE id=?", (wid,), one=True)
            execute("DELETE FROM wardens WHERE id=?", (wid,))
            if warden:
                execute("DELETE FROM users WHERE id=?", (warden['user_id'],))
            flash('Warden removed.', 'info')
        return redirect(url_for('admin_wardens'))
    wardens = query(
        """SELECT w.*, u.full_name, u.email, u.username, u.phone, u.is_active
           FROM wardens w JOIN users u ON w.user_id = u.id ORDER BY u.full_name"""
    )
    return render_template('admin/wardens.html', wardens=wardens)

@app.route('/admin/network')
@role_required('admin')
def admin_network():
    devices = query("SELECT * FROM network_devices ORDER BY vlan, hostname")
    vlans = [
        {'id':10,'name':'Admin',      'subnet':'192.168.10.0/24','gateway':'192.168.10.1',
         'dhcp_range':'192.168.10.21-254','lease':'1 Day'},
        {'id':20,'name':'Students',   'subnet':'192.168.20.0/24','gateway':'192.168.20.1',
         'dhcp_range':'192.168.20.11-254','lease':'8 Hours'},
        {'id':30,'name':'Wardens',    'subnet':'192.168.30.0/24','gateway':'192.168.30.1',
         'dhcp_range':'192.168.30.11-254','lease':'1 Day'},
        {'id':40,'name':'Common/Lab', 'subnet':'192.168.40.0/24','gateway':'192.168.40.1',
         'dhcp_range':'192.168.40.11-254','lease':'4 Hours'},
        {'id':50,'name':'Guest',      'subnet':'192.168.50.0/24','gateway':'192.168.50.1',
         'dhcp_range':'192.168.50.11-254','lease':'2 Hours'},
        {'id':100,'name':'Servers',   'subnet':'192.168.100.0/24','gateway':'192.168.100.1',
         'dhcp_range':'Static Only','lease':'N/A'},
    ]
    services = [
        {'name':'Web Server',  'ip':'192.168.100.3','port':5000,'url':'http://hostel.local:5000','status':'Online'},
        {'name':'DHCP Server', 'ip':'192.168.100.2','port':67,  'url':'—','status':'Online'},
        {'name':'DNS Server',  'ip':'192.168.100.2','port':53,  'url':'hostel.local','status':'Online'},
        {'name':'Database',    'ip':'192.168.100.4','port':3306, 'url':'—','status':'Online'},
    ]
    return render_template('admin/network.html',
        devices=devices, vlans=vlans, services=services)

# ═══════════════════════════════════════════════════════════════
# NETWORK DASHBOARD (public-ish – accessible on LAN)
# ═══════════════════════════════════════════════════════════════

@app.route('/network-dashboard')
@login_required
def network_dashboard():
    devices  = query("SELECT * FROM network_devices ORDER BY status, vlan")
    online   = sum(1 for d in devices if d['status'] == 'Online')
    offline  = sum(1 for d in devices if d['status'] == 'Offline')
    vlans = [
        {'id':10, 'name':'Admin',      'color':'#6366f1','subnet':'192.168.10.0/24'},
        {'id':20, 'name':'Students',   'color':'#22d3ee','subnet':'192.168.20.0/24'},
        {'id':30, 'name':'Wardens',    'color':'#a78bfa','subnet':'192.168.30.0/24'},
        {'id':40, 'name':'Common/Lab', 'color':'#34d399','subnet':'192.168.40.0/24'},
        {'id':50, 'name':'Guest',      'color':'#fbbf24','subnet':'192.168.50.0/24'},
        {'id':100,'name':'Servers',    'color':'#f87171','subnet':'192.168.100.0/24'},
    ]
    return render_template('network_dashboard.html',
        devices=devices, online=online, offline=offline, vlans=vlans)

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS (JSON)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/network/status')
@login_required
def api_network_status():
    devices = query("SELECT hostname, ip_address, status, device_type, vlan FROM network_devices")
    return jsonify([dict(d) for d in devices])

@app.route('/api/complaints/stats')
@role_required('admin','warden')
def api_complaint_stats():
    data = query(
        "SELECT status, COUNT(*) as count FROM complaints GROUP BY status"
    )
    return jsonify([dict(d) for d in data])

# ── Entry point ──────────────────────────────────────────────
if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print("Initializing database...")
        init_db()
        print("Database ready.")
    else:
        print("Database already exists.")
    print("\n" + "="*55)
    print("  Campus Hostel LAN – Web Application")
    print("  http://localhost:5000")
    print("  http://hostel.local:5000  (on Campus LAN)")
    print("="*55)
    print("  Default credentials:")
    print("    Admin  : admin   / admin123")
    print("    Warden : warden_a / warden123")
    print("    Student: stu001  / student123")
    print("="*55 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)

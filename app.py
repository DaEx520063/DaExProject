from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_cors import CORS
import sqlite3
import os
import pandas as pd
from datetime import datetime, timedelta
import json
import re
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# กำหนดสาขา 11 สาขา
BRANCHES = {
    '520063': 'สาขา 520063',
    '671180': 'สาขา 671180',
    '671181': 'สาขา 671181', 
    '671184': 'สาขา 671184',
    '671189': 'สาขา 671189',
    '871021': 'สาขา 871021',
    '871022': 'สาขา 871022',
    '871023': 'สาขา 871023',
    '871025': 'สาขา 871025',
    '871026': 'สาขา 871026',
    '871027': 'สาขา 871027'
}

app = Flask(__name__)
app.secret_key = 'jms_secret_key_2025'
CORS(app)



# สร้างโฟลเดอร์ database ถ้ายังไม่มี
os.makedirs('database', exist_ok=True)

def init_db():
    """สร้างตารางฐานข้อมูลสำหรับระบบ JMS"""
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    
    # สร้างตารางผู้ใช้งานระบบ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            branch_code TEXT,
            name TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # สร้างตารางข้อมูลพนักงาน
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            branch_code TEXT NOT NULL,
            hire_date TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            salary REAL NOT NULL,
            status TEXT DEFAULT 'active',
            manager_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # สร้างตารางข้อมูลเงินเดือน
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            month TEXT NOT NULL,
            year INTEGER NOT NULL,
            base_salary REAL NOT NULL,
            incentive REAL DEFAULT 0,
            fuel_allowance REAL DEFAULT 0,
            depreciation REAL DEFAULT 0,
            penalty REAL DEFAULT 0,
            net_salary REAL NOT NULL,
            payment_date TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')
    
    # สร้างตารางข้อมูลการลา
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            days_requested INTEGER NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            approved_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')
    
    # สร้างตารางข้อมูลค่าใช้จ่าย
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            expense_date TEXT NOT NULL,
            expense_type TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            receipt_path TEXT,
            status TEXT DEFAULT 'pending',
            approved_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')
    
    # สร้างตารางข้อมูลการทำงาน
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            work_date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            work_hours REAL DEFAULT 0,
            overtime_hours REAL DEFAULT 0,
            status TEXT DEFAULT 'present',
            notes TEXT,
            approved_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')
    
    # สร้างตารางข้อมูลการขอเปิดรหัสพนักงาน
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employee_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            requester_id TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            position TEXT NOT NULL,
            branch_code TEXT NOT NULL,
            hire_date TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            status TEXT DEFAULT 'pending',
            approved_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # สร้างตารางข้อมูลการอัพโหลดเงินเดือน
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salary_uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            batch_id TEXT NOT NULL,
            uploaded_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # สร้างตารางข้อมูลรายละเอียดเงินเดือนพนักงาน
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employee_salary_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_batch_id TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            awb_number TEXT NOT NULL,
            branch_code TEXT NOT NULL,
            weight REAL NOT NULL,
            receive_time TEXT NOT NULL,
            close_date TEXT NOT NULL,
            work_month TEXT NOT NULL,
            total_pieces INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # สร้างตารางข้อมูลสรุปเงินเดือนรายเดือน
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monthly_salary_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            package_count INTEGER DEFAULT 0,
            total_weight REAL DEFAULT 0,
            base_salary REAL DEFAULT 0,
            piece_rate_bonus REAL DEFAULT 0,
            allowance REAL DEFAULT 0,
            total_salary REAL DEFAULT 0,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            range_1_pieces INTEGER DEFAULT 0,
            range_2_pieces INTEGER DEFAULT 0,
            range_3_pieces INTEGER DEFAULT 0,
            range_4_pieces INTEGER DEFAULT 0,
            range_5_pieces INTEGER DEFAULT 0,
            range_6_pieces INTEGER DEFAULT 0,
            range_7_pieces INTEGER DEFAULT 0,
            range_8_pieces INTEGER DEFAULT 0,
            range_9_pieces INTEGER DEFAULT 0,
            range_10_pieces INTEGER DEFAULT 0,
            range_1_amount INTEGER DEFAULT 0,
            range_2_amount INTEGER DEFAULT 0,
            range_3_amount INTEGER DEFAULT 0,
            range_4_amount INTEGER DEFAULT 0,
            range_5_amount INTEGER DEFAULT 0,
            range_6_amount INTEGER DEFAULT 0,
            range_7_amount INTEGER DEFAULT 0,
            range_8_amount INTEGER DEFAULT 0,
            range_9_amount INTEGER DEFAULT 0,
            range_10_amount INTEGER DEFAULT 0,
            position TEXT,
            branch_code TEXT,
            zone TEXT,
            employment_type TEXT
        )
    ''')
    
    # สร้างตารางข้อมูลเรทค่าจ้าง
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS piece_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position TEXT NOT NULL,
            zone TEXT NOT NULL,
            branch_code TEXT NOT NULL,
            base_salary REAL NOT NULL,
            piece_rate_bonus REAL NOT NULL,
            allowance REAL DEFAULT 0,
            weight_range_1 REAL DEFAULT 0,
            weight_range_2 REAL DEFAULT 0,
            weight_range_3 REAL DEFAULT 0,
            weight_range_4 REAL DEFAULT 0,
            weight_range_5 REAL DEFAULT 0,
            weight_range_6 REAL DEFAULT 0,
            weight_range_7 REAL DEFAULT 0,
            weight_range_8 REAL DEFAULT 0,
            weight_range_9 REAL DEFAULT 0,
            weight_range_10 REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # สร้างตารางข้อมูลรายการที่ไม่ตรงกับฐานข้อมูลพนักงาน
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unmatched_salary_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_batch_id TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            awb_number TEXT NOT NULL,
            branch_code TEXT NOT NULL,
            weight REAL NOT NULL,
            receive_time TEXT NOT NULL,
            weight_range_index INTEGER NOT NULL,
            range_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # สร้างตารางข้อมูลการยืนยันการจ่ายเงินเดือน
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_confirmations (
            work_month TEXT PRIMARY KEY,
            is_confirmed BOOLEAN NOT NULL,
            confirmed_by TEXT,
            confirmed_at TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def seed_default_users() -> None:
    """Create default users if they do not already exist so local login works.
    The passwords are plain text here but stored hashed in the database.
    """
    # บัญชีผู้ดูแลระบบ
    admin_users = [
        # username, password, role, branch_code, name, email
        ("GM", "gm123", "GM", "520063", "GM", "gm@jms.com"),
        ("HR", "hr123", "HR", "520063", "HR", "hr@jms.com"),
        ("FINANCE", "finance123", "การเงิน", "520063", "FINANCE", "finance@jms.com"),
        ("SPV671180", "spv123", "SPV", "671180", "SPV 671180", "spv671180@jms.com"),
        ("ADMIN", "admin123", "ADM", "520063", "ADMIN", "admin@jms.com"),
        ("SPT001", "spt123", "SPT", "520063", "SPT001", "spt001@jms.com"),
    ]
    
    # ดึงรหัสพนักงานทั้งหมดจากตาราง employees
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    
    # ตรวจสอบว่าตาราง employees มีอยู่หรือไม่
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
    if cursor.fetchone():
        cursor.execute('SELECT employee_id, name, branch_code FROM employees WHERE status = "active"')
        employee_users = cursor.fetchall()
    else:
        employee_users = []
    
    conn.close()
    
    # รวมบัญชีทั้งหมด
    all_users = admin_users + [
        (emp_id, "123456", "SPT", branch_code, emp_name, f"{emp_id}@jms.com")
        for emp_id, emp_name, branch_code in employee_users
    ]

    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()

    # Ensure table exists even if init_db was not called
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        conn.close()
        init_db()
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()

    for username, plain_password, role, branch_code, name, email in all_users:
        password_hash = generate_password_hash(plain_password)
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        if row is None:
            cursor.execute(
                'INSERT INTO users (username, password_hash, role, branch_code, name, email) VALUES (?, ?, ?, ?, ?, ?)',
                (username, password_hash, role, branch_code, name, email),
            )
        else:
            # Reset password and keep role/branch/name/email in sync for testing
            cursor.execute(
                'UPDATE users SET password_hash = ?, role = ?, branch_code = ?, name = ?, email = ? WHERE username = ?',
                (password_hash, role, branch_code, name, email, username),
            )

    conn.commit()
    conn.close()

# ฟังก์ชันตรวจสอบการล็อกอิน
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"DEBUG: ตรวจสอบ session - user_id: {session.get('user_id')}, user_role: {session.get('user_role')}")
        print(f"DEBUG: Session keys: {list(session.keys())}")
        print(f"DEBUG: Request cookies: {dict(request.cookies)}")
        if 'user_id' not in session:
            print("DEBUG: ไม่พบ user_id ใน session - redirect ไป login")
            return redirect(url_for('login'))
        print("DEBUG: พบ user_id ใน session - ผ่านการตรวจสอบ")
        return f(*args, **kwargs)
    return decorated_function

# ฟังก์ชันตรวจสอบสิทธิ์
def role_required(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_role' not in session:
                return redirect(url_for('login'))
            if session['user_role'] not in required_roles:
                flash('คุณไม่มีสิทธิ์เข้าถึงหน้านี้', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    """หน้าแรก"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """หน้าล็อกอิน"""
    if request.method == 'POST':
        try:
            username = request.form['username'].strip()
            password = request.form['password'].strip()
            
            print(f"DEBUG: พยายามเข้าสู่ระบบ - Username: {username}")
            
            conn = sqlite3.connect('database/daex_system.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, password_hash, role, branch_code, email FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            conn.close()
            
            if user and check_password_hash(user[2], password):
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['user_role'] = user[3]
                session['branch_code'] = user[4]
                session['user_name'] = user[1]
                print(f"DEBUG: เข้าสู่ระบบสำเร็จ - Role: {user[3]}")
                print(f"DEBUG: Session data: {dict(session)}")
                flash('เข้าสู่ระบบสำเร็จ', 'success')
                return redirect(url_for('dashboard'))
            else:
                print(f"DEBUG: เข้าสู่ระบบล้มเหลว - Username: {username}")
                flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')
        except Exception as e:
            print(f"DEBUG: Error ในฟังก์ชัน login: {str(e)}")
            flash('เกิดข้อผิดพลาดในการเข้าสู่ระบบ', 'error')
    
    return render_template('login.html')

@app.route('/mobile/login', methods=['GET', 'POST'])
def mobile_login():
    """หน้าเข้าสู่ระบบสำหรับ Mobile App"""
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password_hash, role, branch_code, email FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['user_role'] = user[3]
            session['branch_code'] = user[4]
            session['user_name'] = user[1]  # ใช้ username แทน name
            print(f"DEBUG: เข้าสู่ระบบ Mobile สำเร็จ - Role: {user[3]}")
            print(f"DEBUG: Session data: {dict(session)}")
            flash('เข้าสู่ระบบสำเร็จ', 'success')
            return redirect(url_for('mobile_app'))
        else:
            flash('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง', 'error')
    
    return render_template('mobile_login.html')

@app.route('/logout')
def logout():
    """ออกจากระบบ"""
    session.clear()
    flash('ออกจากระบบแล้ว', 'info')
    return redirect(url_for('index'))

@app.route('/test-login')
def test_login():
    """ทดสอบการเข้าสู่ระบบ (สำหรับ debug)"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username, role FROM users LIMIT 5')
        users = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': 'Database connection successful',
            'users_found': len(users),
            'sample_users': users
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Database connection failed: {str(e)}'
        })

@app.route('/debug-session')
def debug_session():
    """ดูข้อมูล session (สำหรับ debug)"""
    return jsonify({
        'session_data': dict(session),
        'cookies': dict(request.cookies),
        'headers': dict(request.headers)
    })

@app.route('/test-form')
def test_form():
    """ทดสอบฟอร์ม (สำหรับ debug)"""
    return render_template('test_form.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """แดชบอร์ดหลัก"""
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    
    # ข้อมูลสรุปตาม role
    user_role = session.get('user_role')
    branch_code = session.get('branch_code')
    
    if user_role == 'GM':
        # GM เห็นข้อมูลทั้งหมด
        cursor.execute('SELECT COUNT(*) FROM employees WHERE status = "active"')
        total_employees = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM leave_requests WHERE status = "pending"')
        pending_leaves = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM expenses WHERE status = "pending"')
        pending_expenses = cursor.fetchone()[0]
    
    elif user_role == 'HR':
        # HR เห็นข้อมูลพนักงานทั้งหมด
        cursor.execute('SELECT COUNT(*) FROM employees WHERE status = "active"')
        total_employees = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM leave_requests WHERE status = "pending"')
        pending_leaves = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM employee_requests WHERE status = "pending"')
        pending_requests = cursor.fetchone()[0]
        
    elif user_role == 'การเงิน':
        # การเงินเห็นข้อมูลค่าใช้จ่าย
        cursor.execute('SELECT COUNT(*) FROM expenses WHERE status = "pending"')
        pending_expenses = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(amount) FROM expenses WHERE status = "approved"')
        total_expenses = cursor.fetchone()[0] or 0
        
    elif user_role == 'SPV':
        # SPV เห็นข้อมูลสาขาของตัวเอง
        cursor.execute('SELECT COUNT(*) FROM employees WHERE branch_code = ? AND status = "active"', (branch_code,))
        total_employees = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM leave_requests l JOIN employees e ON l.employee_id = e.employee_id WHERE e.branch_code = ? AND l.status = "pending"', (branch_code,))
        pending_leaves = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM expenses e JOIN employees emp ON e.employee_id = emp.employee_id WHERE emp.branch_code = ? AND e.status = "pending"', (branch_code,))
        pending_expenses = cursor.fetchone()[0]
        
    else:  # ADMIN/SPT
        # เห็นข้อมูลของตัวเอง
        username = session.get('username')
        cursor.execute('SELECT employee_id FROM employees WHERE email = ?', (username,))
        employee_result = cursor.fetchone()
        
        if employee_result:
            employee_id = employee_result[0]
            cursor.execute('SELECT COUNT(*) FROM salaries WHERE employee_id = ?', (employee_id,))
            salary_records = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(penalty) FROM salaries WHERE employee_id = ?', (employee_id,))
            total_penalty = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return render_template('dashboard.html', 
                         user_role=user_role, 
                         branch_code=branch_code,
                         branches=BRANCHES,
                         total_employees=locals().get('total_employees', 0),
                         pending_leaves=locals().get('pending_leaves', 0),
                         pending_expenses=locals().get('pending_expenses', 0),
                         pending_requests=locals().get('pending_requests', 0),
                         total_expenses=locals().get('total_expenses', 0),
                         salary_records=locals().get('salary_records', 0),
                         total_penalty=locals().get('total_penalty', 0))

# GM Routes
@app.route('/gm/permissions')
@login_required
@role_required(['GM', 'MD'])
def gm_permissions():
    """หน้าจัดการสิทธิ์สำหรับ GM"""
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, role, name, email, branch_code FROM users ORDER BY role, username')
    users = cursor.fetchall()
    conn.close()
    return render_template('gm/permissions.html', users=users, branches=BRANCHES)

# HR Routes
@app.route('/hr/employee-requests')
@login_required
@role_required(['HR', 'GM', 'MD'])
def hr_employee_requests():
    """หน้าอนุมัติการขอเปิดรหัสพนักงาน"""
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT er.*, e.name as requester_name 
        FROM employee_requests er 
        JOIN employees e ON er.requester_id = e.employee_id 
        ORDER BY er.created_at DESC
    ''')
    requests = cursor.fetchall()
    conn.close()
    return render_template('hr/employee_requests.html', requests=requests)

@app.route('/hr/employees')
@login_required
@role_required(['HR', 'GM', 'MD'])
def hr_employees():
    """หน้ารายชื่อพนักงานทั้งหมด"""
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.*, m.name as manager_name 
        FROM employees e 
        LEFT JOIN employees m ON e.manager_id = m.employee_id 
        ORDER BY e.branch_code, e.name
    ''')
    employees = cursor.fetchall()
    
    # คำนวณสถิติ
    total_employees = len(employees)
    active_employees = len([e for e in employees if e[9] == 'active'])
    inactive_employees = total_employees - active_employees
    
    # นับจำนวนสาขา
    branch_codes = set([e[4] for e in employees])
    branch_count = len(branch_codes)
    
    conn.close()
    return render_template('hr/employees.html', 
                         employees=employees, 
                         branches=BRANCHES,
                         total_employees=total_employees,
                         active_employees=active_employees,
                         inactive_employees=inactive_employees,
                         branch_count=branch_count)

@app.route('/hr/leave-approvals')
@login_required
@role_required(['HR', 'GM', 'MD'])
def hr_leave_approvals():
    """หน้าอนุมัติการลา"""
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT l.*, e.name as employee_name, e.branch_code 
        FROM leave_requests l 
        JOIN employees e ON l.employee_id = e.employee_id 
        WHERE l.status = 'pending'
        ORDER BY l.created_at DESC
        ''')
    leave_requests = cursor.fetchall()
    conn.close()
    return render_template('hr/leave_approvals.html', leave_requests=leave_requests)
    
@app.route('/hr/upload-salary')
@login_required
@role_required(['HR', 'GM', 'MD'])
def hr_upload_salary():
    """หน้าอัพโหลดไฟล์เงินเดือน"""
    return render_template('salary/upload_salary.html', branches=BRANCHES)

# การเงิน Routes
@app.route('/finance/expense-approvals')
@login_required
@role_required(['การเงิน', 'GM', 'MD'])
def finance_expense_approvals():
    """หน้าอนุมัติการเบิกค่าใช้จ่าย"""
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.*, emp.name as employee_name, emp.branch_code 
        FROM expenses e 
        JOIN employees emp ON e.employee_id = emp.employee_id 
        WHERE e.status = 'pending'
        ORDER BY e.created_at DESC
    ''')
    expenses = cursor.fetchall()
    conn.close()
    return render_template('finance/expense_approvals.html', expenses=expenses)

@app.route('/finance/expense-reports')
@login_required
@role_required(['การเงิน', 'GM', 'MD'])
def finance_expense_reports():
    """หน้ารายการเบิกต่างๆ"""
    expense_type = request.args.get('type', 'all')
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    
    if expense_type == 'all':
        cursor.execute('''
            SELECT e.*, emp.name as employee_name, emp.branch_code 
            FROM expenses e 
            JOIN employees emp ON e.employee_id = emp.employee_id 
            ORDER BY e.expense_date DESC
        ''')
    else:
        cursor.execute('''
            SELECT e.*, emp.name as employee_name, emp.branch_code 
            FROM expenses e 
            JOIN employees emp ON e.employee_id = emp.employee_id 
            WHERE e.expense_type = ?
            ORDER BY e.expense_date DESC
        ''', (expense_type,))
    
    expenses = cursor.fetchall()
    conn.close()
    return render_template('finance/expense_reports.html', expenses=expenses, selected_type=expense_type)

@app.route('/finance/upload-expenses')
@login_required
@role_required(['การเงิน', 'GM', 'MD'])
def finance_upload_expenses():
    """หน้าอัพโหลดไฟล์ค่าใช้จ่าย"""
    return render_template('finance/upload_expenses.html')

@app.route('/finance/expense-summary')
@login_required
@role_required(['การเงิน', 'GM', 'MD'])
def finance_expense_summary():
    """หน้าสรุปรายการค่าใช้จ่าย"""
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    
    # สรุปตามประเภทค่าใช้จ่าย
    cursor.execute('''
        SELECT expense_type, COUNT(*) as count, SUM(amount) as total 
        FROM expenses 
        WHERE status = 'approved' 
        GROUP BY expense_type
    ''')
    expense_summary = cursor.fetchall()
    
    # สรุปตามสาขา
    cursor.execute('''
        SELECT emp.branch_code, COUNT(*) as count, SUM(e.amount) as total 
        FROM expenses e 
        JOIN employees emp ON e.employee_id = emp.employee_id 
        WHERE e.status = 'approved' 
        GROUP BY emp.branch_code
    ''')
    branch_summary = cursor.fetchall()
    
    conn.close()
    return render_template('finance/expense_summary.html', 
                         expense_summary=expense_summary, 
                         branch_summary=branch_summary)

@app.route('/finance/upload-salary')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def finance_upload_salary():
    """หน้าอัพโหลดข้อมูลเงินเดือนสำหรับการเงิน"""
    return render_template('salary/upload_salary.html', branches=BRANCHES)

# API Routes for leave requests
@app.route('/api/leave/my-requests')
@login_required
def api_my_leave_requests():
    """API สำหรับดึงข้อมูลการลาของผู้ใช้"""
    try:
        employee_id = session.get('username')
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, leave_type, start_date, end_date, days_requested, reason, status, created_at
            FROM leave_requests 
            WHERE employee_id = ?
            ORDER BY created_at DESC
        ''', (employee_id,))
        
        requests = cursor.fetchall()
        conn.close()
        
        leave_list = []
        for req in requests:
            leave_list.append({
                'id': req[0],
                'leave_type': req[1],
                'start_date': req[2],
                'end_date': req[3],
                'days_requested': req[4],
                'reason': req[5],
                'status': req[6],
                'created_at': req[7]
            })
        
        return jsonify({'success': True, 'leaves': leave_list})
    except Exception as e:
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})

# API Routes for AJAX content loading
@app.route('/api/content/<content_type>')
@login_required
def api_content(content_type):
    """API สำหรับโหลดเนื้อหาต่างๆ ตามเมนู"""
    user_role = session.get('user_role')
    branch_code = session.get('branch_code')
    
    print(f"DEBUG: api_content called - content_type: {content_type}")
    print(f"DEBUG: user_role: {user_role}")
    print(f"DEBUG: branch_code: {branch_code}")
    
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    
    if content_type == 'employee-management' and user_role in ['HR', 'GM', 'MD']:
        # จัดการพนักงาน - แสดงรายชื่อทั้งหมด พร้อมฟีเจอร์แก้ไขและเปิดรหัส
        cursor.execute('''
            SELECT id, employee_id, name, position, branch_code, hire_date, phone, email, base_salary, status, employment_type, zone, rate_type
            FROM employees 
            ORDER BY name
        ''')
        employees = cursor.fetchall()
        
        # คำนวณสถิติ
        total_employees = len(employees)
        active_employees = sum(1 for emp in employees if emp[9] == 'active')
        inactive_employees = total_employees - active_employees
        branch_count = len(set(emp[4] for emp in employees if emp[4]))
        
        conn.close()
        return render_template('hr/employee_management.html', 
                            employees=employees, 
                            branches=BRANCHES,
                            total_employees=total_employees,
                            active_employees=active_employees,
                            inactive_employees=inactive_employees,
                            branch_count=branch_count)
    
    elif content_type == 'leave-approvals' and user_role in ['HR', 'GM', 'MD']:
        # อนุมัติการลา
        cursor.execute('''
            SELECT lr.id, e.name, lr.leave_type, lr.start_date, lr.end_date, lr.days_requested, lr.reason, lr.status
            FROM leave_requests lr 
            JOIN employees e ON lr.employee_id = e.employee_id 
            WHERE lr.status = 'pending'
            ORDER BY lr.created_at DESC
        ''')
        leave_requests = cursor.fetchall()
        conn.close()
        return render_template('hr/leave_approvals.html', leave_requests=leave_requests, branches=BRANCHES)
    
    elif content_type == 'employee-requests' and user_role in ['HR', 'GM', 'MD']:
        # อนุมัติการขอเปิดรหัสพนักงาน
        cursor.execute('''
            SELECT er.id, er.employee_name, er.position, er.branch_code, er.reason, er.status, er.created_at
            FROM employee_requests er 
            WHERE er.status = 'pending'
            ORDER BY er.created_at DESC
        ''')
        requests = cursor.fetchall()
        conn.close()
        return render_template('hr/employee_requests.html', requests=requests, branches=BRANCHES)
    
    elif content_type == 'expense-approvals' and user_role in ['การเงิน', 'GM', 'MD']:
        # อนุมัติการเบิกค่าใช้จ่าย
        cursor.execute('''
            SELECT ex.id, e.name, ex.expense_date, ex.expense_type, ex.description, ex.amount, ex.status
            FROM expenses ex 
            JOIN employees e ON ex.employee_id = e.employee_id 
            WHERE ex.status = 'pending'
            ORDER BY ex.created_at DESC
        ''')
        expenses = cursor.fetchall()
        conn.close()
        return render_template('finance/expense_approvals.html', expenses=expenses, branches=BRANCHES)
    
    elif content_type == 'expense-reports' and user_role in ['การเงิน', 'GM', 'MD']:
        # รายการเบิกค่าใช้จ่าย
        cursor.execute('''
            SELECT ex.expense_date, e.name, ex.expense_type, ex.description, ex.amount, ex.status
            FROM expenses ex 
            JOIN employees e ON ex.employee_id = e.employee_id 
            ORDER BY ex.expense_date DESC
        ''')
        expenses = cursor.fetchall()
        conn.close()
        return render_template('finance/expense_reports.html', expenses=expenses, branches=BRANCHES)
    
    elif content_type == 'expense-summary' and user_role in ['การเงิน', 'GM', 'MD']:
        # สรุปรายการค่าใช้จ่าย
        cursor.execute('''
            SELECT expense_type, COUNT(*) as count, SUM(amount) as total
            FROM expenses 
            GROUP BY expense_type
        ''')
        summary = cursor.fetchall()
        conn.close()
        return render_template('finance/expense_summary.html', summary=summary, branches=BRANCHES)
    
    elif content_type == 'upload-expenses' and user_role in ['การเงิน', 'GM', 'MD']:
        # อัพโหลดไฟล์ค่าใช้จ่าย
        conn.close()
        return render_template('finance/upload_expenses.html', branches=BRANCHES)
    
    elif content_type == 'upload-salary' and user_role in ['HR', 'GM', 'MD', 'การเงิน']:
        # อัพโหลดข้อมูลเงินเดือน
        conn.close()
        return render_template('salary/upload_salary.html', branches=BRANCHES)
    
    elif content_type == 'request-employee' and user_role in ['SPV', 'MD']:
        # ขอเปิดรหัสพนักงาน
        conn.close()
        return render_template('spv/request_employee.html', branches=BRANCHES)
    
    elif content_type == 'leave-request' and user_role in ['SPV', 'MD']:
        # ขอลา
        conn.close()
        return render_template('spv/leave_request.html', branches=BRANCHES)
    
    elif content_type == 'expense-request' and user_role in ['SPV', 'MD']:
        # ขอเบิกค่าใช้จ่าย
        conn.close()
        return render_template('spv/expense_request.html', branches=BRANCHES)
    
    elif content_type == 'branch-employees' and user_role in ['SPV', 'MD']:
        # รายชื่อพนักงานสาขา
        cursor.execute('''
            SELECT employee_id, name, position, hire_date, phone, email, salary, status
            FROM employees 
            WHERE branch_code = ?
            ORDER BY name
        ''', (branch_code,))
        employees = cursor.fetchall()
        conn.close()
        return render_template('spv/branch_employees.html', employees=employees, branches=BRANCHES)
    
    elif content_type == 'my-salary' and user_role in ['ADMIN', 'SPT', 'MD']:
        # ข้อมูลเงินเดือน
        username = session.get('username')
        cursor.execute('''
            SELECT s.month, s.year, s.base_salary, s.incentive, s.fuel_allowance, s.depreciation, s.penalty, s.net_salary
        FROM salaries s 
        JOIN employees e ON s.employee_id = e.employee_id 
            WHERE e.email = ? OR e.employee_id = ?
        ORDER BY s.year DESC, s.month DESC
        ''', (username, username))
        salaries = cursor.fetchall()
        conn.close()
        return render_template('employee/salary.html', salaries=salaries, branches=BRANCHES)

    elif content_type == 'my-penalties' and user_role in ['ADMIN', 'SPT', 'MD']:
        # ค่าปรับของฉัน
        username = session.get('username')
        cursor.execute('''
            SELECT s.month, s.year, s.penalty
        FROM salaries s 
        JOIN employees e ON s.employee_id = e.employee_id 
            WHERE (e.email = ? OR e.employee_id = ?) AND s.penalty > 0
        ORDER BY s.year DESC, s.month DESC
        ''', (username, username))
        penalties = cursor.fetchall()
        conn.close()
        return render_template('employee/penalties.html', penalties=penalties, branches=BRANCHES)
    
    elif content_type == 'permissions' and user_role in ['GM', 'MD', 'ADM']:
        # มอบสิทธิ์การเข้าถึง
        cursor.execute('SELECT id, username, role, name, email, branch_code FROM users ORDER BY role, username')
        users = cursor.fetchall()
        conn.close()
        return render_template('gm/permissions.html', users=users, branches=BRANCHES)
    
    elif content_type == 'all-leaves' and user_role in ['GM', 'MD']:
        # การขาด/ลา/มาสายทั้งหมด
        cursor.execute('''
            SELECT lr.id, e.name, lr.leave_type, lr.start_date, lr.end_date, lr.days_requested, lr.reason, lr.status
            FROM leave_requests lr 
            JOIN employees e ON lr.employee_id = e.employee_id 
            ORDER BY lr.created_at DESC
        ''')
        leave_requests = cursor.fetchall()
        conn.close()
        return render_template('gm/all_leaves.html', leave_requests=leave_requests, branches=BRANCHES)
    
    elif content_type == 'all-expenses' and user_role in ['GM', 'MD']:
        # ค่าใช้จ่ายทั้งหมด
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.*, emp.name as employee_name, emp.branch_code 
            FROM expenses e 
            JOIN employees emp ON e.employee_id = emp.employee_id 
            ORDER BY e.created_at DESC
        ''')
        expenses = cursor.fetchall()
        
        # คำนวณสถิติ
        total_amount = sum(float(e[6]) for e in expenses if e[6] is not None)
        pending_count = sum(1 for e in expenses if e[7] == 'pending')
        approved_count = sum(1 for e in expenses if e[7] == 'approved')
        rejected_count = sum(1 for e in expenses if e[7] == 'rejected')
        
        conn.close()
        return render_template('gm/all_expenses.html', expenses=expenses, branches=BRANCHES,
                                total_amount=total_amount, pending_count=pending_count,
                                approved_count=approved_count, rejected_count=rejected_count)
    
    elif content_type == 'all-salaries' and user_role in ['GM', 'MD']:
        # เมนูสรุป
        conn.close()
        # คำนวณ total_salary จากข้อมูลจริง
        total_salary = 0  # จะคำนวณจากข้อมูลจริงในอนาคต
        return render_template('gm/all_salaries.html', branches=BRANCHES, total_salary=total_salary)
    
    elif content_type == 'all-penalties' and user_role in ['GM', 'MD']:
        # ค่าปรับทั้งหมด
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.*, e.name as employee_name, e.branch_code 
            FROM penalties p 
            JOIN employees e ON p.employee_id = e.employee_id 
            ORDER BY p.created_at DESC
        ''')
        penalties = cursor.fetchall()
        
        # คำนวณสถิติ
        total_penalty = sum(p[5] for p in penalties if p[5] is not None)
        active_count = sum(1 for p in penalties if p[7] == 'active')
        inactive_count = sum(1 for p in penalties if p[7] == 'inactive')
        employee_count = len(set(p[1] for p in penalties))
        
        conn.close()
        return render_template('gm/all_penalties.html', penalties=penalties, branches=BRANCHES, 
                                total_penalty=total_penalty, active_count=active_count, 
                                inactive_count=inactive_count, employee_count=employee_count)
    
    elif content_type == 'spt-piece-rates' and user_role in ['GM', 'MD', 'HR', 'การเงิน']:
        # การจัดการเรทเงินเดือนพนักงาน
        # ดึงข้อมูล piece_rates จากฐานข้อมูล
        cursor.execute('''
            SELECT * FROM piece_rates 
            ORDER BY zone, branch_code, position
        ''')
        piece_rates = cursor.fetchall()
        
        conn.close()
        return render_template('finance/spt_piece_rates.html', branches=BRANCHES, piece_rates=piece_rates)
    
    elif content_type == 'employee-salary-summary' and user_role in ['GM', 'MD', 'HR', 'การเงิน']:
        # สรุปเงินได้พนักงาน - ดึงข้อมูลจริงจากฐานข้อมูล
        try:
            # ดึงข้อมูลพนักงานทั้งหมด
            cursor.execute('''
                SELECT 
                    e.employee_id,
                    e.name,
                    e.position,
                    e.branch_code,
                    e.employment_type,
                    e.base_salary,
                    e.rate_type,
                    e.status
                FROM employees e
                WHERE e.status = 'active'
            ''')
            employees = cursor.fetchall()
            
            # ดึงข้อมูลการอัพโหลดล่าสุด
            cursor.execute('''
                SELECT 
                    work_month,
                    COUNT(*) as total_records,
                    SUM(total_pieces) as total_pieces,
                    SUM(total_amount) as total_amount
                FROM employee_salary_records 
                GROUP BY work_month
                ORDER BY work_month DESC
                LIMIT 1
            ''')
            latest_upload = cursor.fetchone()
            
            # คำนวณสถิติจากข้อมูลจริง
            total_employees = len(employees)
            assigned_rates = len([emp for emp in employees if emp[6] and emp[6].strip()])  # rate_type
            unassigned_rates = total_employees - assigned_rates
            
            # คำนวณข้อมูลจาก employee_salary_records
            total_packages = 0
            total_calculated_salary = 0
            unmatched_packages = 0
            
            if latest_upload:
                total_packages = latest_upload[2] or 0
                total_calculated_salary = latest_upload[3] or 0
                
                # คำนวณ unmatched packages (ข้อมูลที่ไม่ตรงกับพนักงานในระบบ)
                cursor.execute('''
                    SELECT COUNT(*) 
                    FROM employee_salary_records 
                    WHERE work_month = ? AND employee_id NOT IN (
                        SELECT employee_id FROM employees WHERE status = 'active'
                    )
                ''', (latest_upload[0],))
                unmatched_result = cursor.fetchone()
                unmatched_packages = unmatched_result[0] if unmatched_result else 0
            
            # สร้างข้อมูล stats สำหรับ template
            stats = {
                'total_employees': total_employees,
                'assigned_rates': assigned_rates,
                'unassigned_rates': unassigned_rates,
                'total_packages': total_packages,
                'unmatched_packages': unmatched_packages,
                'total_calculated_salary': total_calculated_salary
            }
            
            conn.close()
            return render_template('finance/employee_salary_summary.html', branches=BRANCHES, stats=stats)
            
        except Exception as e:
            conn.close()
            return render_template('finance/employee_salary_summary.html', branches=BRANCHES, stats={
                'total_employees': 0,
                'assigned_rates': 0,
                'unassigned_rates': 0,
                'total_packages': 0,
                'unmatched_packages': 0,
                'total_calculated_salary': 0
            })
    
    elif content_type == 'weight-distribution' and user_role in ['GM', 'MD', 'การเงิน']:
        # การกระจายน้ำหนัก
        conn.close()
        return render_template('finance/weight_distribution.html', branches=BRANCHES)
    

    
    elif content_type == 'salary-report' and user_role in ['GM', 'MD', 'HR', 'การเงิน']:
        # รายงานเงินเดือน
        conn.close()
        return render_template('salary/salary_report.html', branches=BRANCHES)
    
    elif content_type == 'leave-management' and user_role in ['GM', 'MD', 'HR']:
        # จัดการการลา
        conn.close()
        return render_template('hr/leave_management.html', branches=BRANCHES)
    
    elif content_type == 'vehicle-management' and user_role in ['GM', 'MD', 'HR', 'การเงิน', 'SPV']:
        # ระบบจัดการรถบริษัท
        conn.close()
        return render_template('vehicle_management_content.html')
    elif content_type == 'mobile-app' and user_role in ['GM', 'MD', 'HR', 'การเงิน', 'SPV']:
        # Mobile App สำหรับระบบจัดการรถบริษัท
        conn.close()
        return render_template('mobile_app.html')
    
    else:
        conn.close()
        print(f"DEBUG: ไม่พบ content_type: {content_type} หรือไม่มีสิทธิ์")
        print(f"DEBUG: user_role: {user_role}")
        return '<div class="alert alert-warning">คุณไม่มีสิทธิ์เข้าถึงหน้านี้</div>'

# API Routes for employee management
@app.route('/api/salary/monthly-data')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_salary_monthly_data():
    """API สำหรับดึงข้อมูลเงินเดือนรายเดือน - เชื่อมโยง 4 เมนู"""
    try:
        month = request.args.get('month', '7')
        year = request.args.get('year', '2025')
        branch = request.args.get('branch', '')
        employee_id = request.args.get('employee_id', '')
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงข้อมูลจาก monthly_salary_data (ข้อมูลที่มีช่วงน้ำหนักแยก)
        query = '''
            SELECT 
                msd.employee_id,
                msd.package_count as total_pieces,
                msd.month,
                msd.year,
                e.name,
                e.position,
                e.branch_code,
                e.zone,
                e.rate_type,
                e.base_salary,
                e.status,
                msd.range_1_pieces, msd.range_2_pieces, msd.range_3_pieces, msd.range_4_pieces, msd.range_5_pieces,
                msd.range_6_pieces, msd.range_7_pieces, msd.range_8_pieces, msd.range_9_pieces, msd.range_10_pieces,
                msd.range_1_amount, msd.range_2_amount, msd.range_3_amount, msd.range_4_amount, msd.range_5_amount,
                msd.range_6_amount, msd.range_7_amount, msd.range_8_amount, msd.range_9_amount, msd.range_10_amount
            FROM monthly_salary_data msd
            LEFT JOIN employees e ON msd.employee_id = e.employee_id
            WHERE msd.month = ? AND msd.year = ?
        '''
        params = [month, year]
        
        print(f"🔍 ค้นหาข้อมูลเดือน {month}/{year}")
        
        # เพิ่มเงื่อนไขการกรอง
        if branch and branch != '':
            query += ' AND e.branch_code = ?'
            params.append(branch)
        
        if employee_id:
            query += ' AND msd.employee_id LIKE ?'
            params.append(f'%{employee_id}%')
        
        query += ' ORDER BY e.name'
        
        cursor.execute(query, params)
        salary_data = cursor.fetchall()
        
        print(f"📊 พบข้อมูล {len(salary_data)} รายการ")
        
        # แปลงข้อมูลเป็น format ที่ template ต้องการ
        employee_data = []
        total_packages = 0
        total_amount = 0
        employees_with_rates = 0
        employees_without_rates = 0
        unmatched_packages = 0
        
        print(f"=== แสดงผลลัพธ์ในเมนูสรุปเงินได้พนักงาน ===")
        print(f"📊 ข้อมูลเดือน {month}/{year} - พนักงานทั้งหมด: {len(salary_data)} คน")
        
        for data in salary_data:
            (emp_id, pieces, month, year, name, position, branch_code, zone, 
             emp_type, base_salary, status,
             r1_pieces, r2_pieces, r3_pieces, r4_pieces, r5_pieces,
             r6_pieces, r7_pieces, r8_pieces, r9_pieces, r10_pieces,
             r1_amount, r2_amount, r3_amount, r4_amount, r5_amount,
             r6_amount, r7_amount, r8_amount, r9_amount, r10_amount) = data
            
            print(f"  - {emp_id}: {name}, {pieces} ชิ้น")
            
            # สร้างข้อมูลช่วงน้ำหนักจากข้อมูลที่มีอยู่
            range_names = [
                '0.00-0.50KG', '0.51-1.00KG', '1.01-2.00KG', '2.01-3.00KG', '3.01-5.00KG',
                '5.01-7.00KG', '7.01-10.00KG', '10.01-12.00KG', '12.01-15.00KG', '15.01KG+'
            ]
            
            weight_ranges = []
            for i, range_name in enumerate(range_names):
                pieces_count = [r1_pieces, r2_pieces, r3_pieces, r4_pieces, r5_pieces,
                              r6_pieces, r7_pieces, r8_pieces, r9_pieces, r10_pieces][i] or 0
                weight_ranges.append({
                    'range': range_name,
                    'pieces': pieces_count,
                    'amount': 0
                })
            
            # ใช้ฟังก์ชันการคำนวณแบบรวมศูนย์
            # ตรวจสอบข้อมูลที่จำเป็นสำหรับการคำนวณ
            has_required_data = position and zone  # ต้องมีตำแหน่งและโซน
            salary_type = emp_type if emp_type else 'DEFAULT'  # ถ้าไม่มี rate_type ให้ใช้ DEFAULT
            
            if has_required_data:
                print(f"🔍 DEBUG: Searching rate for position={position}, rate_type={emp_type}, salary_type={salary_type}, zone={zone}, branch={branch_code}")
                
                # หาเรทที่ตรงกับพนักงาน - ใช้ 4 เงื่อนไข: เรทการจ้าง, สาขา, ตำแหน่ง, โซน
                # ลำดับการค้นหา: 1. สาขาเฉพาะ 2. ทุกสาขา (ถ้าไม่เจอสาขาเฉพาะ)
                
                # ขั้นตอนที่ 1: หาเรทของสาขาเฉพาะ
                cursor.execute('''
                    SELECT base_salary, piece_rate_bonus, allowance,
                           weight_range_1, weight_range_2, weight_range_3, weight_range_4, weight_range_5,
                           weight_range_6, weight_range_7, weight_range_8, weight_range_9, weight_range_10,
                           allowance_tiers
                    FROM piece_rates 
                    WHERE position = ? AND salary_type = ? AND zone = ? AND branch_code = ?
                    LIMIT 1
                ''', (position, salary_type, zone, branch_code))
                
                rate_data = cursor.fetchone()
                
                # ขั้นตอนที่ 2: ถ้าไม่เจอเรทของสาขาเฉพาะ ให้หาเรท "ทุกสาขา"
                if not rate_data:
                    print(f"🔍 ไม่เจอเรทของสาขา {branch_code} - หาเรท 'ทุกสาขา' แทน")
                    cursor.execute('''
                        SELECT base_salary, piece_rate_bonus, allowance,
                               weight_range_1, weight_range_2, weight_range_3, weight_range_4, weight_range_5,
                               weight_range_6, weight_range_7, weight_range_8, weight_range_9, weight_range_10,
                               allowance_tiers
                        FROM piece_rates 
                        WHERE position = ? AND salary_type = ? AND zone = ? AND branch_code = 'ทุกสาขา'
                        LIMIT 1
                    ''', (position, salary_type, zone))
                    
                    rate_data = cursor.fetchone()
                    
                    if rate_data:
                        print(f"✅ ใช้เรท 'ทุกสาขา' สำหรับ {emp_id}")
                    else:
                        print(f"❌ ไม่เจอเรท 'ทุกสาขา' สำหรับ {emp_id}")
                else:
                    print(f"✅ ใช้เรทของสาขา {branch_code} สำหรับ {emp_id}")
                
                if not rate_data:
                    print(f"❌ ERROR: No rate found for employee {emp_id} after checking both specific branch and 'ทุกสาขา'")
                    print(f"   - position={position}")
                    print(f"   - salary_type={salary_type}")
                    print(f"   - zone={zone}")
                    print(f"   - branch_code={branch_code}")
                    
                    # ตรวจสอบว่ามีเรทอะไรบ้างในระบบ
                    cursor.execute('''
                        SELECT DISTINCT position, salary_type, zone, branch_code 
                        FROM piece_rates 
                        WHERE position = ? OR salary_type = ? OR zone = ? OR branch_code = ?
                    ''', (position, salary_type, zone, branch_code))
                    available_rates = cursor.fetchall()
                    if available_rates:
                        print(f"   📋 Available rates in system:")
                        for rate in available_rates:
                            print(f"      - position={rate[0]}, salary_type={rate[1]}, zone={rate[2]}, branch={rate[3]}")
                    
                    employees_without_rates += 1
                else:
                    employees_with_rates += 1
                    print(f"✅ Found rate for {emp_id} - ฐาน={rate_data[0]}, ชิ้น={rate_data[1]}, สมทบ={rate_data[2]}")
            else:
                rate_data = None
                employees_without_rates += 1
                print(f"⚠️ WARNING: Missing required data for employee {emp_id} - position={position}, zone={zone}")
            
            # ใช้ฟังก์ชันการคำนวณแบบรวมศูนย์
            salary_calculation = calculate_salary_unified(employee_data, rate_data, pieces or 0)
            base_salary_amount = salary_calculation['base_salary']
            piece_rate_bonus = salary_calculation['piece_rate_bonus']
            allowance = salary_calculation['allowance']
            total_emp_amount = salary_calculation['total_amount']
            
            print(f"    💰 เงินเดือน: ฐาน={base_salary_amount:,.2f}, ชิ้น={piece_rate_bonus:,.2f}, สมทบ={allowance:,.2f}, รวม={total_emp_amount:,.2f}")
            
            employee_info = {
                'employee_id': emp_id,
                'name': name or 'ไม่ระบุชื่อ',
                'position': position or 'ไม่ระบุตำแหน่ง',
                'branch_code': branch_code or 'ไม่ระบุสาขา',
                'zone': zone or 'ไม่ระบุโซน',
                'piece_rate': salary_type or 'ไม่ระบุ',  # ส่งค่า salary_type แทน employment_type
                'base_salary': base_salary_amount,
                'piece_rate_bonus': piece_rate_bonus,
                'allowance': allowance,
                'total_pieces': pieces or 0,
                'total_amount': total_emp_amount,
                'weight_ranges': weight_ranges
            }
            

            
            employee_data.append(employee_info)
            total_packages += pieces or 0
            total_amount += total_emp_amount
        
        # คำนวณ summary จากข้อมูลจริง
        summary = {
            'total_employees': len(employee_data),
            'total_pieces': total_packages,
            'total_salary': total_amount,
            'total_allowance': sum(emp['allowance'] for emp in employee_data),
            'month': month,
            'year': year,
            'employees_with_rates': employees_with_rates,
            'employees_without_rates': employees_without_rates
        }
        
        print(f"📈 สรุป: พนักงาน {len(employee_data)} คน, พัสดุ {total_packages:,} ชิ้น, ยอดรวม ฿{total_amount:,.2f}")
        
        conn.close()
        
        return jsonify({
            'employees': employee_data,
            'summary': summary
        })
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดใน api_salary_monthly_data: {str(e)}")
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'})

@app.route('/api/salary/employee-details/<employee_id>')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_employee_salary_details(employee_id):
    """API สำหรับดึงข้อมูลรายละเอียดเงินเดือนของพนักงานคนเดียว"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงข้อมูลพนักงาน
        cursor.execute('''
            SELECT employee_id, name, position, branch_code, zone, rate_type, base_salary
            FROM employees 
            WHERE employee_id = ?
        ''', (employee_id,))
        employee = cursor.fetchone()
        
        if not employee:
            return jsonify({'error': 'ไม่พบข้อมูลพนักงาน'})
        
        # ใช้ rate_type โดยตรง (ไม่ต้องแปลง)
        rate_type = employee[5]
        
        emp_data = {
            'employee_id': employee[0],
            'name': employee[1],
            'position': employee[2],
            'branch_code': employee[3],
            'zone': employee[4],
            'piece_rate': rate_type,  # ส่งค่า rate_type โดยตรง
            'base_salary': employee[6] or 0
        }
        
        # ดึงข้อมูลพัสดุแยกตามช่วงน้ำหนักจาก monthly_salary_data
        cursor.execute('''
            SELECT 
                range_1_pieces, range_2_pieces, range_3_pieces, range_4_pieces, range_5_pieces,
                range_6_pieces, range_7_pieces, range_8_pieces, range_9_pieces, range_10_pieces,
                range_1_amount, range_2_amount, range_3_amount, range_4_amount, range_5_amount,
                range_6_amount, range_7_amount, range_8_amount, range_9_amount, range_10_amount
            FROM monthly_salary_data 
            WHERE employee_id = ? 
            ORDER BY upload_date DESC 
            LIMIT 1
        ''', (employee_id,))
        weight_data = cursor.fetchone()
        
        if not weight_data:
            return jsonify({'error': 'ไม่พบข้อมูลพัสดุของพนักงาน'})
        
        # สร้างข้อมูลช่วงน้ำหนักจากข้อมูลที่มีอยู่
        range_names = [
            '0.00-0.50KG', '0.51-1.00KG', '1.01-2.00KG', '2.01-3.00KG', '3.01-5.00KG',
            '5.01-7.00KG', '7.01-10.00KG', '10.01-12.00KG', '12.01-15.00KG', '15.01KG+'
        ]
        
        weight_ranges = []
        total_pieces = 0
        
        # ข้อมูลจาก monthly_salary_data
        pieces_data = weight_data[0:10]  # range_1_pieces ถึง range_10_pieces
        
        for i, range_name in enumerate(range_names):
            count = pieces_data[i] or 0
            weight_ranges.append({
                'range': range_name, 
                'count': count,
                'rate': 0,
                'amount': 0
            })
            total_pieces += count
        
        # ดึงข้อมูลเรทที่ตรงกับพนักงาน
        piece_rate_bonus = 0
        allowance = 0
        
        if emp_data['position'] and emp_data['piece_rate'] and emp_data['zone']:
            # ใช้ rate_type โดยตรง (ไม่ต้องแปลง)
            salary_type = emp_data['piece_rate']  # rate_type ตรงกับ salary_type ใน piece_rates
            print(f"🔍 DEBUG: Searching rate for position={emp_data['position']}, rate_type={emp_data['piece_rate']}, salary_type={salary_type}, zone={emp_data['zone']}, branch={emp_data['branch_code']}")
            # ลองหาเรทที่ตรงกับโซนก่อน
            cursor.execute('''
                SELECT base_salary, piece_rate_bonus, allowance,
                       weight_range_1, weight_range_2, weight_range_3, weight_range_4, weight_range_5,
                       weight_range_6, weight_range_7, weight_range_8, weight_range_9, weight_range_10,
                       allowance_tiers
                FROM piece_rates 
                WHERE position = ? AND salary_type = ? AND zone = ? AND (branch_code = ? OR branch_code = 'ทุกสาขา')
                ORDER BY branch_code DESC
                LIMIT 1
            ''', (emp_data['position'], salary_type, emp_data['zone'], emp_data['branch_code']))
            
            rate_data = cursor.fetchone()
            
            # ถ้าไม่พบเรทสำหรับโซนนั้น แสดงว่าข้อมูลพนักงานตั้งผิด
            if not rate_data:
                print(f"❌ ERROR: No rate found for employee {employee_id} - position={emp_data['position']}, salary_type={salary_type}, zone={emp_data['zone']}, branch={emp_data['branch_code']}")
                print(f"   Please check employee data or add corresponding rate in SPT Piece Rates menu")
            
            if rate_data:
                # คำนวณเงินชิ้นตามเรทแต่ละช่วงน้ำหนัก
                piece_rates = rate_data[3:13]  # weight_range_1 ถึง weight_range_10 (รวม weight_range_4 แล้ว)
                # ใช้ piece_rates โดยตรงเพราะมีครบ 10 elements แล้ว
                full_piece_rates = piece_rates
                for i in range(10):
                    # ตั้งอัตราจริงเสมอ ไม่ว่าจะมีชิ้นงานหรือไม่
                    if full_piece_rates[i]:
                        weight_ranges[i]['rate'] = full_piece_rates[i]
                        weight_ranges[i]['amount'] = weight_ranges[i]['count'] * full_piece_rates[i]
                        piece_rate_bonus += weight_ranges[i]['amount']
                    else:
                        weight_ranges[i]['rate'] = 0
                        weight_ranges[i]['amount'] = 0
                
                # คำนวณเงินสมทบตาม allowance_tiers
                allowance = 0
                if rate_data[13]:  # allowance_tiers (index เปลี่ยนเพราะเพิ่ม weight_range_4)
                    try:
                        import json
                        allowance_tiers = json.loads(rate_data[13]) if isinstance(rate_data[13], str) else rate_data[13]
                        if allowance_tiers and isinstance(allowance_tiers, list):
                            # หาเงินสมทบสูงสุดที่ตรงกับจำนวนชิ้น
                            for tier in allowance_tiers:
                                if 'pieces' in tier and 'amount' in tier:
                                    if total_pieces >= tier['pieces']:
                                        allowance = tier['amount']
                    except Exception as e:
                        print(f"❌ Error parsing allowance_tiers: {e}")
                        allowance = rate_data[2] or 0  # fallback to base allowance
                else:
                    allowance = rate_data[2] or 0
            else:
                for i in range(10):
                    weight_ranges[i]['rate'] = 0
                    weight_ranges[i]['amount'] = 0
        else:
            for i in range(10):
                weight_ranges[i]['rate'] = 0
                weight_ranges[i]['amount'] = 0
        
        # คำนวณเงินเดือนรวม
        # ใช้ base_salary จาก piece_rates แทนจาก employees
        base_salary_from_rate = rate_data[0] if rate_data else emp_data['base_salary']
        total_salary = base_salary_from_rate + piece_rate_bonus + allowance
        
        print(f"🔍 DEBUG: weight_ranges for {employee_id}:", weight_ranges)
        print(f"🔍 DEBUG: weight_ranges type: {type(weight_ranges)}")
        print(f"🔍 DEBUG: weight_ranges length: {len(weight_ranges) if weight_ranges else 0}")
        
        result = {
            'employee': emp_data,
            'weight_ranges': weight_ranges,
            'total_pieces': total_pieces,
            'base_salary': base_salary_from_rate,
            'piece_rate_bonus': piece_rate_bonus,
            'allowance': allowance,
            'total_salary': total_salary,
            'has_rate': True  # เนื่องจากใช้ข้อมูลจาก employee_salary_records โดยตรง
        }
        
        print(f"🔍 DEBUG: Final result weight_ranges length: {len(result['weight_ranges'])}")
        print(f"🔍 DEBUG: Final result keys: {list(result.keys())}")
        
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดใน api_employee_salary_details: {str(e)}")
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'})

@app.route('/api/import-employees', methods=['POST'])
@login_required
@role_required(['HR', 'GM', 'MD'])
def api_import_employees():
    """API สำหรับนำเข้าข้อมูลพนักงานจาก Excel"""
    try:
        data = request.get_json()
        employees = data.get('employees', [])
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        success_count = 0
        error_count = 0
        
        for emp in employees:
            try:
                # Check if employee already exists
                cursor.execute('SELECT employee_id FROM employees WHERE employee_id = ?', (emp['employee_id'],))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing employee
                    cursor.execute('''
                        UPDATE employees 
                        SET name = ?, position = ?, branch_code = ?, hire_date = ?, phone = ?, email = ?, status = ?
                        WHERE employee_id = ?
                    ''', (emp['name'], emp['position'], emp['branch_code'], emp['hire_date'], 
                          emp['phone'], emp['email'], emp['status'], emp['employee_id']))
                else:
                    # Insert new employee
                    cursor.execute('''
                        INSERT INTO employees (employee_id, name, position, branch_code, hire_date, phone, email, salary, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (emp['employee_id'], emp['name'], emp['position'], emp['branch_code'], 
                          emp['hire_date'], emp['phone'], emp['email'], 15000, emp['status']))
                
                # Handle password - create default password if not provided
                if emp.get('password') and emp['password'] != '********':
                    # Use provided password
                    password_hash = generate_password_hash(emp['password'])
                    plain_password = emp['password']
                else:
                    # Create default password (employee_id + "123")
                    default_password = f"{emp['employee_id']}123"
                    password_hash = generate_password_hash(default_password)
                    plain_password = default_password
                
                # Insert or update user credentials
                cursor.execute('''
                    INSERT OR REPLACE INTO users (username, password_hash, role, name, email)
                    VALUES (?, ?, ?, ?, ?)
                ''', (emp['employee_id'], password_hash, emp['position'], emp['name'], emp['email']))
                
                # Store plain password for display
                cursor.execute('''
                    INSERT OR REPLACE INTO user_passwords (username, plain_password)
                    VALUES (?, ?)
                ''', (emp['employee_id'], plain_password))
                
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error processing employee {emp.get('employee_id', 'unknown')}: {str(e)}")
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'นำเข้าข้อมูลสำเร็จ {success_count} รายการ, ผิดพลาด {error_count} รายการ'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})

@app.route('/api/update-employee', methods=['POST'])
@login_required
@role_required(['HR', 'GM', 'MD'])
def api_update_employee():
    """API สำหรับอัปเดตข้อมูลพนักงาน"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        old_employee_id = data['employee_id']
        new_employee_id = data.get('new_employee_id', old_employee_id)
        
        # Check if new employee_id already exists (if changing ID)
        if new_employee_id != old_employee_id:
            cursor.execute('SELECT employee_id FROM employees WHERE employee_id = ?', (new_employee_id,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': f'รหัสพนักงาน {new_employee_id} มีอยู่แล้ว'})
        
        # Update employee data
        cursor.execute('''
            UPDATE employees 
            SET employee_id = ?, name = ?, position = ?, branch_code = ?, hire_date = ?, phone = ?, email = ?, employment_type = ?, rate_type = ?, zone = ?, status = ?
            WHERE employee_id = ?
        ''', (new_employee_id, data['name'], data['position'], data['branch_code'], data['hire_date'], 
              data['phone'], data['email'], data.get('employment_type', ''), data.get('rate_type', ''), data.get('zone', ''), data['status'], old_employee_id))
        
        # Update users table if employee_id changed
        if new_employee_id != old_employee_id:
            cursor.execute('''
                UPDATE users 
                SET username = ?
                WHERE username = ?
            ''', (new_employee_id, old_employee_id))
        
        # Update password if provided
        if data.get('password'):
            password_hash = generate_password_hash(data['password'])
            # Check if user exists in users table
            cursor.execute('SELECT username FROM users WHERE username = ?', (new_employee_id,))
            if cursor.fetchone():
                # Update existing user password
                cursor.execute('''
                    UPDATE users 
                    SET password_hash = ?
                    WHERE username = ?
                ''', (password_hash, new_employee_id))
            else:
                # Create new user with password
                cursor.execute('''
                    INSERT INTO users (username, password_hash, role, name, email)
                    VALUES (?, ?, ?, ?, ?)
                ''', (new_employee_id, password_hash, data['position'], data['name'], data['email']))
            
            # เก็บรหัสผ่านที่อ่านได้ในตาราง user_passwords
            cursor.execute('''
                INSERT OR REPLACE INTO user_passwords (username, plain_password)
                VALUES (?, ?)
            ''', (new_employee_id, data['password']))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'อัปเดตข้อมูลพนักงานสำเร็จ'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})

@app.route('/api/activate-employee/<employee_id>', methods=['POST'])
@login_required
@role_required(['HR', 'GM', 'MD'])
def api_activate_employee(employee_id):
    """API สำหรับเปิดรหัสพนักงาน"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE employees 
            SET status = 'active'
            WHERE employee_id = ?
        ''', (employee_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'ไม่พบพนักงาน'})
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'เปิดรหัสพนักงานเรียบร้อยแล้ว'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})

@app.route('/api/deactivate-employee/<employee_id>', methods=['POST'])
@login_required
@role_required(['HR', 'GM', 'MD'])
def api_deactivate_employee(employee_id):
    """API สำหรับปิดรหัสพนักงาน"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE employees 
            SET status = 'inactive'
            WHERE employee_id = ?
        ''', (employee_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'ไม่พบพนักงาน'})
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'ปิดรหัสพนักงานเรียบร้อยแล้ว'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})

@app.route('/api/export-employees')
@login_required
@role_required(['HR', 'GM', 'MD'])
def api_export_employees():
    """API สำหรับ Export ข้อมูลพนักงานเป็น Excel"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # Get all employees with branch names
        cursor.execute('''
            SELECT e.employee_id, e.name, e.position, e.branch_code, e.hire_date, e.phone, e.email, e.status
                        FROM employees e 
            ORDER BY e.name
        ''')
        employees_data = cursor.fetchall()
        
        # Convert to list of dictionaries with branch names
        employees = []
        for emp in employees_data:
            branch_name = BRANCHES.get(emp[3], emp[3])  # Get branch name from BRANCHES dict
            employees.append({
                'employee_id': emp[0],
                'name': emp[1],
                'position': emp[2],
                'branch_code': emp[3],
                'branch_name': branch_name,
                'hire_date': emp[4],
                'phone': emp[5] or '',
                'email': emp[6] or '',
                'status': 'เปิดใช้งาน' if emp[7] == 'active' else 'ปิดใช้งาน'
            })
        
            conn.close()
        
        return jsonify({
            'success': True, 
            'employees': employees
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})

@app.route('/api/get-employee-password/<employee_id>')
@login_required
@role_required(['HR', 'GM', 'MD'])
def api_get_employee_password(employee_id):
    """API สำหรับดึงข้อมูลรหัสผ่านของพนักงาน"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # First try to get password from users table with employee_id as username
        cursor.execute('''
            SELECT password_hash FROM users WHERE username = ?
        ''', (employee_id,))
        
        result = cursor.fetchone()
        
        # If not found, try to find by employee name or create a default password
        if not result:
            # Get employee info to find matching user
            cursor.execute('''
                SELECT name, position FROM employees WHERE employee_id = ?
            ''', (employee_id,))
            
            emp_result = cursor.fetchone()
            if emp_result:
                emp_name, position = emp_result
                
                # Try to find user by name or position
                cursor.execute('''
                    SELECT password_hash FROM users WHERE name = ? OR role = ?
                ''', (emp_name, position))
                
                result = cursor.fetchone()
                
                if not result:
                    # Create a default password for this employee
                    from werkzeug.security import generate_password_hash
                    default_password = f"{employee_id}123"  # Default password: employee_id + 123
                    password_hash = generate_password_hash(default_password)
                
                    # Insert into users table
                cursor.execute('''
                        INSERT INTO users (username, password_hash, role, name, email)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (employee_id, password_hash, position, emp_name, f"{employee_id.lower()}@jms.com"))
        
        conn.commit()
        conn.close()
        
        if result:
            # ตรวจสอบว่ารหัสผ่านในฐานข้อมูลเป็น hash หรือ plain text
            password_hash = result[0]
            
            # ตรวจสอบว่ารหัสผ่านที่แก้ไขแล้วมีอยู่ในฐานข้อมูลหรือไม่
            # ถ้าเป็น hash ให้แสดงรหัสผ่านเริ่มต้น
            if password_hash.startswith('scrypt:') or password_hash.startswith('pbkdf2:'):
                # ตรวจสอบว่ามีรหัสผ่านที่แก้ไขแล้วหรือไม่
                conn = sqlite3.connect('database/daex_system.db')
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT plain_password FROM user_passwords WHERE username = ?
                ''', (employee_id,))
                plain_result = cursor.fetchone()
                conn.close()
                
                if plain_result:
                    readable_password = plain_result[0]
                else:
                    readable_password = f"{employee_id}123"
            else:
                # ถ้าเป็น plain text ให้แสดงตามนั้น
                readable_password = password_hash
            
            return jsonify({
                'success': True,
                'password': readable_password  # Show readable password
            })
        else:
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูลรหัสผ่าน'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })

# SPV Routes
@app.route('/spv/request-employee')
@login_required
@role_required(['SPV'])
def spv_request_employee():
    """หน้าขอเปิดรหัสพนักงาน"""
    if request.method == 'POST':
        employee_name = request.form['employee_name']
        position = request.form['position']
        reason = request.form['reason']
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO employee_requests (requester_id, employee_name, position, branch_code, reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (session.get('username'), employee_name, position, session.get('branch_code'), reason))
            conn.commit()
            flash('ส่งคำขอสำเร็จ', 'success')
        except Exception as e:
            flash('เกิดข้อผิดพลาด', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('spv_request_employee'))
        
    return render_template('spv/request_employee.html')

@app.route('/spv/leave-request')
@login_required
@role_required(['SPV'])
def spv_leave_request():
    """หน้าขอลา"""
    if request.method == 'POST':
        leave_type = request.form['leave_type']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        reason = request.form['reason']
        
        # คำนวณจำนวนวัน
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days_requested = (end - start).days + 1
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, days_requested, reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session.get('username'), leave_type, start_date, end_date, days_requested, reason))
            conn.commit()
            flash('ส่งคำขอการลาสำเร็จ', 'success')
        except Exception as e:
            flash('เกิดข้อผิดพลาด', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('spv_leave_request'))
    
    return render_template('spv/leave_request.html')

@app.route('/spv/expense-request')
@login_required
@role_required(['SPV'])
def spv_expense_request():
    """หน้าขอเบิกค่าใช้จ่าย"""
    if request.method == 'POST':
        expense_type = request.form['expense_type']
        expense_date = request.form['expense_date']
        description = request.form['description']
        amount = float(request.form['amount'])
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO expenses (employee_id, expense_date, expense_type, description, amount)
            VALUES (?, ?, ?, ?, ?)
            ''', (session.get('username'), expense_date, expense_type, description, amount))
            conn.commit()
            flash('ส่งคำขอเบิกค่าใช้จ่ายสำเร็จ', 'success')
        except Exception as e:
            flash('เกิดข้อผิดพลาด', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('spv_expense_request'))
    
    return render_template('spv/expense_request.html')

@app.route('/spv/branch-employees')
@login_required
@role_required(['SPV'])
def spv_branch_employees():
    """หน้ารายชื่อและประวัติพนักงานในสาขา"""
    branch_code = session.get('branch_code')
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT e.*, m.name as manager_name 
        FROM employees e
        LEFT JOIN employees m ON e.manager_id = m.employee_id 
        WHERE e.branch_code = ?
        ORDER BY e.name
    ''', (branch_code,))
    employees = cursor.fetchall()
    
    conn.close()
    return render_template('spv/branch_employees.html', employees=employees)

# ADMIN/SPT Routes
@app.route('/employee/salary')
@login_required
@role_required(['ADMIN', 'SPT'])
def employee_salary():
    """หน้าข้อมูลเงินเดือน"""
    username = session.get('username')
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT employee_id FROM employees WHERE email = ?', (username,))
    employee_result = cursor.fetchone()
    
    if not employee_result:
        flash('ไม่พบข้อมูลพนักงาน', 'error')
        return redirect(url_for('dashboard'))
    
    employee_id = employee_result[0]
    
    cursor.execute('''
        SELECT * FROM salaries 
        WHERE employee_id = ?
        ORDER BY year DESC, month DESC
    ''', (employee_id,))
    salaries = cursor.fetchall()
    
    conn.close()
    return render_template('employee/salary.html', salaries=salaries)

@app.route('/employee/penalties')
@login_required
@role_required(['ADMIN', 'SPT'])
def employee_penalties():
    """หน้าค่าปรับ"""
    username = session.get('username')
    conn = sqlite3.connect('database/daex_system.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT employee_id FROM employees WHERE email = ?', (username,))
    employee_result = cursor.fetchone()
    
    if not employee_result:
        flash('ไม่พบข้อมูลพนักงาน', 'error')
        return redirect(url_for('dashboard'))
    
    employee_id = employee_result[0]
    
    cursor.execute('''
        SELECT * FROM salaries 
        WHERE employee_id = ? AND penalty > 0
        ORDER BY year DESC, month DESC
    ''', (employee_id,))
    penalties = cursor.fetchall()
    
    conn.close()
    return render_template('employee/penalties.html', penalties=penalties)

def extract_month_year_from_data(df, found_columns):
    """อ่านเดือนและปีจากข้อมูลในไฟล์"""
    try:
        # หาคอลัมน์วันที่
        date_column = found_columns.get('time')
        if not date_column:
            print("❌ ไม่พบคอลัมน์วันที่ในไฟล์")
            return None, None
        
        # ตรวจสอบข้อมูลในคอลัมน์วันที่
        date_values = df[date_column].dropna()
        if len(date_values) == 0:
            print("❌ ไม่พบข้อมูลวันที่ในไฟล์")
            return None, None
        
        # แปลงวันที่เป็น datetime
        from datetime import datetime
        import pandas as pd
        
        # ลองแปลงวันที่หลายรูปแบบ
        for date_value in date_values.head(10):  # ตรวจสอบ 10 แถวแรก
            try:
                if pd.isna(date_value):
                    continue
                
                # แปลงเป็น string ก่อน
                date_str = str(date_value)
                
                # ลองรูปแบบต่างๆ
                date_formats = [
                    '%Y-%m-%d',
                    '%d/%m/%Y',
                    '%d-%m-%Y',
                    '%Y/%m/%d',
                    '%d/%m/%y',
                    '%d-%m-%y',
                    '%Y-%m-%d %H:%M:%S',
                    '%d/%m/%Y %H:%M:%S'
                ]
                
                parsed_date = None
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if parsed_date:
                    month = parsed_date.month
                    year = parsed_date.year
                    print(f"✅ อ่านเดือนและปีจากไฟล์: {month}/{year}")
                    return month, year
                    
            except Exception as e:
                print(f"⚠️ ไม่สามารถแปลงวันที่ {date_value}: {e}")
                continue
        
        print("❌ ไม่สามารถอ่านเดือนและปีจากข้อมูลในไฟล์")
        return None, None
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการอ่านเดือนและปี: {e}")
        return None, None

@app.route('/api/upload-salary', methods=['POST'])
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def upload_salary():
    """อัพโหลดข้อมูลเงินเดือน - ใช้ระบบเก่าที่ทำงานได้แล้ว"""
    try:
        print(f"DEBUG: Request files keys: {list(request.files.keys())}")
        print(f"DEBUG: Request form keys: {list(request.form.keys())}")
        
        # ตรวจสอบไฟล์จาก key ที่ถูกต้อง
        if 'salary_file' not in request.files:
            return jsonify({'success': False, 'message': 'ไม่พบไฟล์ที่อัพโหลด'})
        
        file = request.files['salary_file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'กรุณาเลือกไฟล์'})
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'success': False, 'message': 'รองรับเฉพาะไฟล์ Excel (.xlsx, .xls)'})
        
        # อ่านไฟล์ Excel
        try:
            df = pd.read_excel(file)
            print(f"✅ อ่านไฟล์สำเร็จ: {len(df)} แถว, {len(df.columns)} คอลัมน์")
        except Exception as e:
            print(f"❌ ไม่สามารถอ่านไฟล์ได้: {str(e)}")
            return jsonify({'success': False, 'message': f'ไม่สามารถอ่านไฟล์ได้: {str(e)}'})
        
        print(f"คอลัมน์ที่พบในไฟล์: {list(df.columns)}")
        print(f"จำนวนคอลัมน์: {len(df.columns)}")
        
        # ตรวจสอบคอลัมน์ที่จำเป็นแบบยืดหยุ่น
        required_columns = {
            'awb': ['หมายเลข AWB', 'AWB', 'awb', 'หมายเลขพัสดุ', 'เลขที่ AWB', 'เลข AWB', 'AWB Number'],
            'branch': ['หมายเลขสาขา การชำระบัญชี', 'สาขา', 'branch', 'หมายเลขสาขา', 'รหัสสาขา', 'Branch Code', 'สาขาการชำระบัญชี'],
            'weight': ['นํ้าหนักที่ใช้คิดเงิน', 'น้ำหนัก', 'weight', 'น้ำหนักที่ใช้คิดเงิน', 'น้ำหนักรวม', 'Weight', 'น้ำหนักพัสดุ'],
            'time': ['เวลาที่เซ็นรับพัสดุ', 'เวลา', 'time', 'วันที่', 'Date', 'เวลารับพัสดุ', 'วันที่รับพัสดุ'],
            'employee_name': ['พนักงานนำจ่าย', 'พนักงาน', 'employee', 'ชื่อพนักงาน', 'Employee Name', 'ชื่อ-นามสกุล'],
            'employee_id': ['รหัสพนักงาน', 'รหัส', 'employee_id', 'id', 'Employee ID', 'รหัสพนักงานนำจ่าย']
        }
        
        # หาคอลัมน์ที่ตรงกัน
        found_columns = {}
        missing_columns = []
        
        for field, possible_names in required_columns.items():
            found = False
            for col_name in df.columns:
                if col_name in possible_names:
                    found_columns[field] = col_name
                    found = True
                    break
            if not found:
                missing_columns.append(field)
        
        if missing_columns:
            print(f"คอลัมน์ที่ขาดหายไป: {missing_columns}")
            print(f"คอลัมน์ที่พบ: {found_columns}")
            return jsonify({
                'success': False, 
                'message': f'ไฟล์ไม่ตรงกับรูปแบบที่ต้องการ\nคอลัมน์ที่ขาดหายไป: {missing_columns}\nคอลัมน์ที่พบ: {found_columns}'
            })
        
        # อ่านเดือนและปีจากข้อมูลในไฟล์
        month, year = extract_month_year_from_data(df, found_columns)
        
        # ถ้าไม่สามารถอ่านจากไฟล์ได้ ให้ใช้จากฟอร์ม
        if month is None or year is None:
            month = request.form.get('month', 7)
            year = request.form.get('year', 2025)
            
            try:
                month = int(month)
                year = int(year)
            except ValueError:
                return jsonify({'success': False, 'message': 'เดือนและปีไม่ถูกต้อง'})
        
        print(f"📅 อัพโหลดข้อมูลเดือน {month} ปี {year}")
        
        # ใช้ระบบเก่าที่ทำงานได้แล้ว
        return process_salary_upload_old_system(df, file.filename, found_columns, month, year)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})

def sync_monthly_salary_data(batch_id):
    """ซิงค์ข้อมูลจาก employee_salary_records ไปยัง monthly_salary_data"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # คำนวณข้อมูลสรุปจาก employee_salary_records
        cursor.execute('''
            SELECT employee_id, 
                   COUNT(*) as package_count,
                   SUM(total_amount) as total_salary,
                   work_month
            FROM employee_salary_records 
            WHERE upload_batch_id = ?
            GROUP BY employee_id, work_month
        ''', (batch_id,))
        
        employee_summary = cursor.fetchall()
        
        for emp_id, package_count, total_salary, work_month in employee_summary:
            # แยกเดือนและปีจาก work_month (format: '2025-07')
            if work_month and '-' in work_month:
                year, month = work_month.split('-')
                month = int(month)
                year = int(year)
            else:
                # ถ้าไม่มี work_month ให้ใช้เดือนและปีจาก batch_id หรือปัจจุบัน
                import datetime
                now = datetime.datetime.now()
                month = now.month
                year = now.year
            
            # ลบข้อมูลเก่า (ถ้ามี)
            cursor.execute('''
                DELETE FROM monthly_salary_data 
                WHERE employee_id = ? AND month = ? AND year = ?
            ''', (emp_id, month, year))
            
            # บันทึกข้อมูลใหม่
            cursor.execute('''
                INSERT INTO monthly_salary_data 
                (employee_id, month, year, package_count, total_salary)
                VALUES (?, ?, ?, ?, ?)
            ''', (emp_id, month, year, package_count, total_salary))
        
        conn.commit()
        conn.close()
        
        print(f"✅ ซิงค์ข้อมูลสำเร็จ: {len(employee_summary)} พนักงาน")
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการซิงค์ข้อมูล: {str(e)}")
        return False

def process_salary_upload_old_system(df, filename, found_columns, month, year):
    """ประมวลผลข้อมูลเงินเดือนตามขั้นตอนใหม่ - เชื่อมโยง 4 เมนู"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # สร้าง batch_id สำหรับการอัพโหลด
        import datetime
        batch_id = f"batch_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # บันทึกข้อมูลการอัพโหลด
        cursor.execute('''
            INSERT INTO salary_uploads 
            (filename, original_name, month, year, batch_id, uploaded_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            filename, filename, 
            month, year, batch_id, session.get('username'), 
            datetime.datetime.now()
        ))
        
        upload_id = cursor.lastrowid
        
        # เตรียม dict สำหรับสรุปยอด
        employee_summary = {}
        
        # ประมวลผลข้อมูล
        success_count = 0
        error_count = 0
        
        print("=== เริ่มประมวลผลข้อมูลเงินเดือน ===")
        print("ขั้นตอนที่ 1: แยกข้อมูลไฟล์ที่อัพโหลด - ว่าพัสดุแต่ละชิ้นอยู่ในช่วงน้ำหนักไหน")
        
        # เพิ่มตัวแปรสำหรับเก็บข้อมูลที่ไม่ตรงกับฐานข้อมูลพนักงาน
        unmatched_records = []
        unmatched_summary = {
            'total_pieces': 0,
            'pieces_by_range': {f'range_{i+1}': 0 for i in range(10)},
            'amounts_by_range': {f'amount_{i+1}': 0 for i in range(10)}
        }
        
        for index, row in df.iterrows():
            try:
                awb = str(row[found_columns.get('awb', 'หมายเลข AWB')])
                branch_code = str(row[found_columns.get('branch', 'หมายเลขสาขา การชำระบัญชี')])
                weight = float(row[found_columns.get('weight', 'นํ้าหนักที่ใช้คิดเงิน')]) if pd.notna(row[found_columns.get('weight', 'นํ้าหนักที่ใช้คิดเงิน')]) else 0
                receive_time = str(row[found_columns.get('time', 'เวลาที่เซ็นรับพัสดุ')])
                employee_name = str(row[found_columns.get('employee_name', 'พนักงานนำจ่าย')])
                employee_id = str(row[found_columns.get('employee_id', 'รหัสพนักงาน')]).strip()
                
                # ตรวจสอบว่ารหัสพนักงานถูกต้องหรือไม่
                if not employee_id or employee_id == 'nan':
                    print(f"❌ รหัสพนักงานไม่ถูกต้อง: {employee_id}")
                    error_count += 1
                    continue
                
                # ถ้า employee_id เป็น '0' ให้บันทึกเป็น unmatched record
                if employee_id == '0':
                    print(f"⚠️ รหัสพนักงานเป็น 0: {employee_id} - บันทึกเป็น unmatched record")
                    
                    # หาช่วงน้ำหนักที่พัสดุนี้อยู่
                    weight_range_index = None
                    for i, (min_weight, max_weight) in enumerate(weight_ranges):
                        if min_weight <= weight <= max_weight:
                            weight_range_index = i
                            break
                    
                    if weight_range_index is None:
                        weight_range_index = 9
                    
                    range_name = f"{weight_ranges[weight_range_index][0]}-{weight_ranges[weight_range_index][1] if weight_ranges[weight_range_index][1] != float('inf') else '15+'}"
                    
                    # บันทึกข้อมูลที่ไม่ตรงกับฐานข้อมูล
                    unmatched_record = {
                        'employee_id': employee_id,
                        'employee_name': employee_name,
                        'awb': awb,
                        'branch_code': branch_code,
                        'weight': weight,
                        'receive_time': receive_time,
                        'weight_range_index': weight_range_index,
                        'range_name': range_name
                    }
                    unmatched_records.append(unmatched_record)
                    
                    # อัปเดตสรุปข้อมูลที่ไม่ตรง
                    unmatched_summary['total_pieces'] += 1
                    unmatched_summary['pieces_by_range'][f'range_{weight_range_index + 1}'] += 1
                    
                    error_count += 1
                    continue
                
                # ตรวจสอบว่ารหัสพนักงานมีรูปแบบถูกต้อง
                if not employee_id or len(employee_id) < 5:
                    print(f"❌ รหัสพนักงานสั้นเกินไป: {employee_id}")
                    error_count += 1
                    continue
                
                # ขั้นตอนที่ 1: แยกข้อมูลพัสดุแต่ละชิ้นตามช่วงน้ำหนัก
                # ปรับช่วงน้ำหนักให้รองรับทุกน้ำหนัก
                weight_ranges = [
                    (0.00, 0.50), (0.51, 1.00), (1.01, 1.50), (1.51, 2.00), (2.01, 2.50),
                    (2.51, 3.00), (3.01, 5.00), (5.01, 10.00), (10.01, 15.00), (15.00, float('inf'))
                ]
                
                # หาช่วงน้ำหนักที่พัสดุนี้อยู่
                weight_range_index = None
                for i, (min_weight, max_weight) in enumerate(weight_ranges):
                    if min_weight <= weight <= max_weight:  # เปลี่ยนจาก < เป็น <=
                        weight_range_index = i
                        break
                
                # ถ้าไม่พบช่วงน้ำหนัก ให้ใช้ช่วงสุดท้าย (15+ KG)
                if weight_range_index is None:
                    weight_range_index = 9  # ช่วงสุดท้าย
                    print(f"⚠️ น้ำหนัก {weight} ไม่อยู่ในช่วงที่กำหนด ใช้ช่วงสุดท้าย (15+ KG)")
                
                range_name = f"{weight_ranges[weight_range_index][0]}-{weight_ranges[weight_range_index][1] if weight_ranges[weight_range_index][1] != float('inf') else '15+'}"
                print(f"📦 AWB {awb}: น้ำหนัก {weight}กก. → ช่วง {range_name} (ช่วงที่ {weight_range_index + 1})")
                
                # ขั้นตอนที่ 2: มองหารหัสพนักงานที่ตรงกันในฐานข้อมูลพนักงาน
                print(f"🔍 ขั้นตอนที่ 2: ค้นหาพนักงาน {employee_id} ในฐานข้อมูล")
                cursor.execute("""
                    SELECT position, branch_code, zone, employment_type, rate_type, base_salary 
                    FROM employees 
                    WHERE employee_id = ?
                """, (employee_id,))
                
                emp = cursor.fetchone()
                if not emp:
                    print(f"❌ ไม่พบข้อมูลพนักงาน {employee_id} ในฐานข้อมูล")
                    
                    # เก็บข้อมูลที่ไม่ตรงกับฐานข้อมูล
                    unmatched_record = {
                        'employee_id': employee_id,
                        'employee_name': employee_name,
                        'awb': awb,
                        'branch_code': branch_code,
                        'weight': weight,
                        'receive_time': receive_time,
                        'weight_range_index': weight_range_index,
                        'range_name': range_name
                    }
                    unmatched_records.append(unmatched_record)
                    
                    # อัปเดตสรุปข้อมูลที่ไม่ตรง
                    unmatched_summary['total_pieces'] += 1
                    unmatched_summary['pieces_by_range'][f'range_{weight_range_index + 1}'] += 1
                    
                    error_count += 1
                    continue
                
                position, emp_branch_code, zone, emp_type, rate_type, base_salary = emp
                print(f"✅ พบพนักงาน: {employee_id} - ตำแหน่ง: {position}, สาขา: {emp_branch_code}, โซน: {zone}")
                
                # ขั้นตอนที่ 3: จับคู่เรทระหว่างฐานข้อมูลพนักงานและเมนูการจัดการเรทพนักงาน
                print(f"💰 ขั้นตอนที่ 3: จับคู่เรท - ตำแหน่ง: {position}, โซน: {zone}, สาขา: {emp_branch_code}")
                
                # ค้นหาเรทจาก piece_rates ตามตำแหน่ง โซน สาขา
                cursor.execute("""
                    SELECT base_salary, piece_rate_bonus, allowance,
                           weight_range_1, weight_range_2, weight_range_3, weight_range_4, weight_range_5,
                           weight_range_6, weight_range_7, weight_range_8, weight_range_9, weight_range_10
                    FROM piece_rates 
                    WHERE position = ? AND zone = ? AND (branch_code = ? OR branch_code = 'ทุกสาขา')
                    ORDER BY branch_code DESC
                    LIMIT 1
                """, (position, zone, emp_branch_code))
                
                piece_rate_data = cursor.fetchone()
                if not piece_rate_data:
                    print(f"❌ ไม่พบเรทสำหรับ {position} - โซน {zone} - สาขา {emp_branch_code}")
                    error_count += 1
                    continue
                
                base_salary_rate, piece_rate_bonus, allowance = piece_rate_data[0:3]
                weight_ranges_rates = piece_rate_data[3:13]  # เรทตามช่วงน้ำหนัก
                
                # หาเรทที่เหมาะสมตามน้ำหนักของพัสดุนี้
                piece_rate_per_package = weight_ranges_rates[weight_range_index]
                print(f"✅ เรทที่ใช้: {piece_rate_per_package} บาท/ชิ้น (ช่วงที่ {weight_range_index + 1})")
                
                # คำนวณค่าจ้างตามประเภทการจ้าง
                if emp_type == 'piece_rate':
                    amount = piece_rate_per_package  # ค่าชิ้นต่อชิ้น
                    # สำหรับ employee_salary_records: บันทึกเฉพาะเรทต่อชิ้น
                    record_amount = piece_rate_per_package
                else:
                    amount = base_salary_rate
                    record_amount = base_salary_rate
                
                print(f"💰 คำนวณ: เรทต่อชิ้น {piece_rate_per_package} บาท")
                
                # สร้าง work_month จากเดือนและปีที่ถูกต้อง
                work_month = f"{year:04d}-{month:02d}"
                
                # บันทึกข้อมูลรายละเอียด (เฉพาะเรทต่อชิ้น)
                cursor.execute('''
                    INSERT INTO employee_salary_records 
                    (employee_id, awb_number, branch_code, weight, receive_time, close_date, work_month, total_pieces, total_amount, upload_batch_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employee_id, awb, branch_code, weight, receive_time,
                    f'{year:04d}-{month:02d}-31', work_month, 1, record_amount, batch_id
                ))
                
                # รวมยอดสำหรับสรุป
                if employee_id not in employee_summary:
                    employee_summary[employee_id] = {
                        'total_piece_amount': 0,  # รวมเรทต่อชิ้น
                        'total_pieces': 0,
                        'base_salary': base_salary_rate,
                        'allowance': allowance,
                        'position': position,
                        'branch_code': emp_branch_code,
                        'zone': zone,
                        'employment_type': emp_type,
                        'pieces_by_range': {f'range_{i+1}': 0 for i in range(10)},
                        'amounts_by_range': {f'amount_{i+1}': 0 for i in range(10)},
                        'rates_by_range': {f'rate_{i+1}': weight_ranges_rates[i] for i in range(10)}
                    }
                
                employee_summary[employee_id]['total_piece_amount'] += piece_rate_per_package
                employee_summary[employee_id]['total_pieces'] += 1
                
                # รวมจำนวนชิ้นและเงินในแต่ละช่วง
                for i in range(10):
                    range_key = f'range_{i+1}'
                    amount_key = f'amount_{i+1}'
                    if i == weight_range_index:
                        employee_summary[employee_id]['pieces_by_range'][range_key] += 1
                        employee_summary[employee_id]['amounts_by_range'][amount_key] += piece_rate_per_package
                    else:
                        employee_summary[employee_id]['pieces_by_range'][range_key] += 0
                        employee_summary[employee_id]['amounts_by_range'][amount_key] += 0
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"❌ Error processing row {index}: {str(e)}")
                continue
        
        print(f"\n=== ขั้นตอนที่ 4: แสดงผลลัพธ์ในเมนูสรุปเงินได้พนักงาน ===")
        print(f"✅ ประมวลผลสำเร็จ: {success_count} รายการ")
        print(f"❌ ล้มเหลว: {error_count} รายการ")
        
        # บันทึกข้อมูลสรุปใน monthly_salary_data พร้อมข้อมูลแต่ละช่วงน้ำหนัก
        for emp_id, summary in employee_summary.items():
            # คำนวณเงินรวมที่ถูกต้อง: ฐาน + (รวมเรทต่อชิ้น) + สมทบ
            total_salary = summary['base_salary'] + summary['total_piece_amount'] + summary['allowance']
            
            print(f"\n📊 สรุปพนักงาน {emp_id}:")
            print(f"   - จำนวนชิ้น: {summary['total_pieces']}")
            print(f"   - ฐาน: {summary['base_salary']:.2f} บาท")
            print(f"   - รวมเรทต่อชิ้น: {summary['total_piece_amount']:.2f} บาท")
            print(f"   - สมทบ: {summary['allowance']:.2f} บาท")
            print(f"   - เงินรวม: {total_salary:.2f} บาท")
            
            # แสดงจำนวนชิ้นในแต่ละช่วงน้ำหนัก
            for i in range(10):
                pieces = summary['pieces_by_range'][f'range_{i+1}']
                if pieces > 0:
                    rate = summary['rates_by_range'][f'rate_{i+1}']
                    amount = summary['amounts_by_range'][f'amount_{i+1}']
                    print(f"   - ช่วงที่ {i+1}: {pieces} ชิ้น × {rate} บาท = {amount:.2f} บาท")
            
            # บันทึกข้อมูลใน monthly_salary_data
            cursor.execute('''
                INSERT OR REPLACE INTO monthly_salary_data 
                (employee_id, month, year, package_count, total_weight, base_salary, piece_rate_bonus, allowance, total_salary,
                 range_1_pieces, range_2_pieces, range_3_pieces, range_4_pieces, range_5_pieces,
                 range_6_pieces, range_7_pieces, range_8_pieces, range_9_pieces, range_10_pieces,
                 range_1_amount, range_2_amount, range_3_amount, range_4_amount, range_5_amount,
                 range_6_amount, range_7_amount, range_8_amount, range_9_amount, range_10_amount,
                 position, branch_code, zone, employment_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                emp_id, month, year, summary['total_pieces'], 0.0, summary['base_salary'], 
                summary['total_piece_amount'], summary['allowance'], total_salary,
                summary['pieces_by_range']['range_1'], summary['pieces_by_range']['range_2'],
                summary['pieces_by_range']['range_3'], summary['pieces_by_range']['range_4'],
                summary['pieces_by_range']['range_5'], summary['pieces_by_range']['range_6'],
                summary['pieces_by_range']['range_7'], summary['pieces_by_range']['range_8'],
                summary['pieces_by_range']['range_9'], summary['pieces_by_range']['range_10'],
                summary['amounts_by_range']['amount_1'], summary['amounts_by_range']['amount_2'],
                summary['amounts_by_range']['amount_3'], summary['amounts_by_range']['amount_4'],
                summary['amounts_by_range']['amount_5'], summary['amounts_by_range']['amount_6'],
                summary['amounts_by_range']['amount_7'], summary['amounts_by_range']['amount_8'],
                summary['amounts_by_range']['amount_9'], summary['amounts_by_range']['amount_10'],
                summary['position'], summary['branch_code'], summary['zone'], summary['employment_type']
            ))
        
        # บันทึกข้อมูลที่ไม่ตรงกับฐานข้อมูลพนักงาน
        if unmatched_records:
            print(f"\n📋 บันทึกข้อมูลที่ไม่ตรงกับฐานข้อมูลพนักงาน: {len(unmatched_records)} รายการ")
            for record in unmatched_records:
                cursor.execute('''
                    INSERT INTO unmatched_salary_records 
                    (upload_batch_id, employee_id, employee_name, awb_number, branch_code, weight, receive_time, weight_range_index, range_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    batch_id, record['employee_id'], record['employee_name'], record['awb'], 
                    record['branch_code'], record['weight'], record['receive_time'], 
                    record['weight_range_index'], record['range_name']
                ))
            
            print(f"📊 สรุปข้อมูลที่ไม่ตรง:")
            print(f"   - จำนวนชิ้นทั้งหมด: {unmatched_summary['total_pieces']}")
            for i in range(10):
                pieces = unmatched_summary['pieces_by_range'][f'range_{i+1}']
                if pieces > 0:
                    print(f"   - ช่วงที่ {i+1}: {pieces} ชิ้น")
        
        # อัปเดต status และ linkage_status
        cursor.execute('''
            UPDATE salary_uploads 
            SET status = 'completed', employee_linked = 1, rate_linked = 1
            WHERE id = ?
        ''', (upload_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'อัพโหลดข้อมูลเงินเดือนสำเร็จ'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })

@app.route('/api/upload-results/latest')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_upload_results_latest():
    """API สำหรับดึงผลลัพธ์การอัพโหลดล่าสุด"""
    try:
        print("DEBUG: API upload-results/latest called")
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงข้อมูลการอัพโหลดล่าสุด
        cursor.execute('''
            SELECT id, filename, original_name, month, year, batch_id, created_at, status, employee_linked, rate_linked
            FROM salary_uploads 
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        
        upload_info = cursor.fetchone()
        print(f"DEBUG: Upload info: {upload_info}")
        if not upload_info:
            print("DEBUG: No upload info found")
            return jsonify({
                'success': True,
                'upload_info': None,
                'results': {
                    'total_items': 0,
                    'total_employees': 0,
                    'employees': [],
                    'weight_ranges': []
                }
            })
        
        upload_id, filename, original_name, month, year, batch_id, created_at, status, employee_linked, rate_linked = upload_info
        print(f"DEBUG: Batch ID: {batch_id}")
        
        # นับจำนวนรายการทั้งหมด
        cursor.execute('''
            SELECT COUNT(*) FROM employee_salary_records 
            WHERE upload_batch_id = ?
        ''', (batch_id,))
        total_items = cursor.fetchone()[0] or 0
        print(f"DEBUG: Total items: {total_items}")
        
        # นับจำนวนพนักงานที่ไม่ซ้ำกัน
        cursor.execute('''
            SELECT COUNT(DISTINCT employee_id) FROM employee_salary_records 
            WHERE upload_batch_id = ?
        ''', (batch_id,))
        total_employees = cursor.fetchone()[0] or 0
        print(f"DEBUG: Total employees: {total_employees}")
        
        # ดึงข้อมูลสรุปตามพนักงานพร้อมรายละเอียดแต่ละช่วงน้ำหนัก
        cursor.execute('''
            SELECT 
                esr.employee_id, 
                e.name,
                COUNT(*) as total_packages,
                SUM(CASE WHEN weight <= 0.5 THEN 1 ELSE 0 END) as range_1,
                SUM(CASE WHEN weight > 0.5 AND weight <= 1.0 THEN 1 ELSE 0 END) as range_2,
                SUM(CASE WHEN weight > 1.0 AND weight <= 1.5 THEN 1 ELSE 0 END) as range_3,
                SUM(CASE WHEN weight > 1.5 AND weight <= 2.0 THEN 1 ELSE 0 END) as range_4,
                SUM(CASE WHEN weight > 2.0 AND weight <= 2.5 THEN 1 ELSE 0 END) as range_5,
                SUM(CASE WHEN weight > 2.5 AND weight <= 3.0 THEN 1 ELSE 0 END) as range_6,
                SUM(CASE WHEN weight > 3.0 AND weight <= 5.0 THEN 1 ELSE 0 END) as range_7,
                SUM(CASE WHEN weight > 5.0 AND weight <= 10.0 THEN 1 ELSE 0 END) as range_8,
                SUM(CASE WHEN weight > 10.0 AND weight <= 15.0 THEN 1 ELSE 0 END) as range_9,
                SUM(CASE WHEN weight > 15.0 THEN 1 ELSE 0 END) as range_10
            FROM employee_salary_records esr
            LEFT JOIN employees e ON esr.employee_id = e.employee_id
            WHERE esr.upload_batch_id = ?
            GROUP BY esr.employee_id
            ORDER BY esr.employee_id
        ''', (batch_id,))
        
        employees = []
        for row in cursor.fetchall():
            emp_id, name, total_packages, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10 = row
            print(f"DEBUG: Employee {emp_id}: total={total_packages}, r1={r1}, r2={r2}, r3={r3}")
            employees.append({
                'employee_id': emp_id,
                'name': name or emp_id,
                'total_packages': total_packages or 0,
                'weight_ranges': {
                    '0.00-0.50KG': r1 or 0,
                    '0.51-1.00KG': r2 or 0,
                    '1.01-1.50KG': r3 or 0,
                    '1.51-2.00KG': r4 or 0,
                    '2.01-2.50KG': r5 or 0,
                    '2.51-3.00KG': r6 or 0,
                    '3.01-5.00KG': r7 or 0,
                    '5.01-10.00KG': r8 or 0,
                    '10.01-15.00KG': r9 or 0,
                    '15.01KG+': r10 or 0
                }
            })
        
        # ดึงข้อมูลจำนวนชิ้นแยกตามช่วงน้ำหนักทั้งหมด (รวมข้อมูลที่ไม่ตรง)
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN weight <= 0.5 THEN '0.00-0.50KG'
                    WHEN weight <= 1.0 THEN '0.51-1.00KG'
                    WHEN weight <= 1.5 THEN '1.01-1.50KG'
                    WHEN weight <= 2.0 THEN '1.51-2.00KG'
                    WHEN weight <= 2.5 THEN '2.01-2.50KG'
                    WHEN weight <= 3.0 THEN '2.51-3.00KG'
                    WHEN weight <= 5.0 THEN '3.01-5.00KG'
                    WHEN weight <= 10.0 THEN '5.01-10.00KG'
                    WHEN weight <= 15.0 THEN '10.01-15.00KG'
                    ELSE '15.01KG+'
                END as weight_range,
                COUNT(*) as piece_count
            FROM employee_salary_records 
            WHERE upload_batch_id = ?
            GROUP BY weight_range
            ORDER BY MIN(weight)
        ''', (batch_id,))
        
        weight_ranges = []
        for row in cursor.fetchall():
            weight_range, piece_count = row
            weight_ranges.append({
                'range': weight_range,
                'count': piece_count
            })
        
        # นับจำนวนที่ไม่ตรงกับฐานข้อมูลพนักงาน
        cursor.execute('''
            SELECT 
                COUNT(*) as total_unmatched,
                SUM(CASE WHEN weight <= 0.5 THEN 1 ELSE 0 END) as range_1,
                SUM(CASE WHEN weight > 0.5 AND weight <= 1.0 THEN 1 ELSE 0 END) as range_2,
                SUM(CASE WHEN weight > 1.0 AND weight <= 1.5 THEN 1 ELSE 0 END) as range_3,
                SUM(CASE WHEN weight > 1.5 AND weight <= 2.0 THEN 1 ELSE 0 END) as range_4,
                SUM(CASE WHEN weight > 2.0 AND weight <= 2.5 THEN 1 ELSE 0 END) as range_5,
                SUM(CASE WHEN weight > 2.5 AND weight <= 3.0 THEN 1 ELSE 0 END) as range_6,
                SUM(CASE WHEN weight > 3.0 AND weight <= 5.0 THEN 1 ELSE 0 END) as range_7,
                SUM(CASE WHEN weight > 5.0 AND weight <= 10.0 THEN 1 ELSE 0 END) as range_8,
                SUM(CASE WHEN weight > 10.0 AND weight <= 15.0 THEN 1 ELSE 0 END) as range_9,
                SUM(CASE WHEN weight > 15.0 THEN 1 ELSE 0 END) as range_10
            FROM unmatched_salary_records usr
            WHERE usr.upload_batch_id = ?
        ''', (batch_id,))
        
        unmatched_data = cursor.fetchone()
        unmatched_summary = None
        if unmatched_data and unmatched_data[0] > 0:
            total_unmatched, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10 = unmatched_data
            unmatched_summary = {
                'total_packages': total_unmatched,
                'weight_ranges': {
                    '0.00-0.50KG': r1 or 0,
                    '0.51-1.00KG': r2 or 0,
                    '1.01-1.50KG': r3 or 0,
                    '1.51-2.00KG': r4 or 0,
                    '2.01-2.50KG': r5 or 0,
                    '2.51-3.00KG': r6 or 0,
                    '3.01-5.00KG': r7 or 0,
                    '5.01-10.00KG': r8 or 0,
                    '10.01-15.00KG': r9 or 0,
                    '15.01KG+': r10 or 0
                }
            }
        
        conn.close()
        
        print(f"DEBUG: Returning response with {len(employees)} employees")
        response_data = {
            'success': True,
            'upload_info': {
                'id': upload_id,
                'filename': filename,
                'original_name': original_name,
                'month': month,
                'year': year,
                'batch_id': batch_id,
                'created_at': created_at,
                'status': status,
                'employee_linked': employee_linked,
                'rate_linked': rate_linked
            },
            'results': {
                'total_items': total_items,
                'total_employees': total_employees,
                'employees': employees,
                'weight_ranges': weight_ranges,
                'unmatched_records': unmatched_summary
            }
        }
        print(f"DEBUG: Response data: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })

@app.route('/api/upload-results/<int:month>/<int:year>')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_upload_results_by_month_year(month, year):
    """API สำหรับดึงผลลัพธ์การอัพโหลดตามเดือนและปี"""
    try:
        print(f"DEBUG: API upload-results/{month}/{year} called")
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงข้อมูลการอัพโหลดตามเดือนและปี
        cursor.execute('''
            SELECT id, filename, original_name, month, year, batch_id, created_at, status, employee_linked, rate_linked
            FROM salary_uploads 
            WHERE month = ? AND year = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (month, year))
        
        upload_info = cursor.fetchone()
        print(f"DEBUG: Upload info for {month}/{year}: {upload_info}")
        if not upload_info:
            print(f"DEBUG: No upload info found for {month}/{year}")
            return jsonify({
                'success': True,
                'upload_info': None,
                'results': {
                    'total_items': 0,
                    'total_employees': 0,
                    'employees': [],
                    'weight_ranges': []
                }
            })
        
        upload_id, filename, original_name, month, year, batch_id, created_at, status, employee_linked, rate_linked = upload_info
        print(f"DEBUG: Batch ID: {batch_id}")
        
        # นับจำนวนรายการทั้งหมด
        cursor.execute('''
            SELECT COUNT(*) FROM employee_salary_records 
            WHERE upload_batch_id = ?
        ''', (batch_id,))
        total_items = cursor.fetchone()[0] or 0
        print(f"DEBUG: Total items: {total_items}")
        
        # นับจำนวนพนักงานที่ไม่ซ้ำกัน
        cursor.execute('''
            SELECT COUNT(DISTINCT employee_id) FROM employee_salary_records 
            WHERE upload_batch_id = ?
        ''', (batch_id,))
        total_employees = cursor.fetchone()[0] or 0
        print(f"DEBUG: Total employees: {total_employees}")
        
        # ดึงข้อมูลสรุปตามพนักงานพร้อมรายละเอียดแต่ละช่วงน้ำหนัก
        cursor.execute('''
            SELECT 
                esr.employee_id, 
                e.name,
                COUNT(*) as total_packages,
                SUM(CASE WHEN weight <= 0.5 THEN 1 ELSE 0 END) as range_1,
                SUM(CASE WHEN weight > 0.5 AND weight <= 1.0 THEN 1 ELSE 0 END) as range_2,
                SUM(CASE WHEN weight > 1.0 AND weight <= 1.5 THEN 1 ELSE 0 END) as range_3,
                SUM(CASE WHEN weight > 1.5 AND weight <= 2.0 THEN 1 ELSE 0 END) as range_4,
                SUM(CASE WHEN weight > 2.0 AND weight <= 2.5 THEN 1 ELSE 0 END) as range_5,
                SUM(CASE WHEN weight > 2.5 AND weight <= 3.0 THEN 1 ELSE 0 END) as range_6,
                SUM(CASE WHEN weight > 3.0 AND weight <= 5.0 THEN 1 ELSE 0 END) as range_7,
                SUM(CASE WHEN weight > 5.0 AND weight <= 10.0 THEN 1 ELSE 0 END) as range_8,
                SUM(CASE WHEN weight > 10.0 AND weight <= 15.0 THEN 1 ELSE 0 END) as range_9,
                SUM(CASE WHEN weight > 15.0 THEN 1 ELSE 0 END) as range_10
            FROM employee_salary_records esr
            LEFT JOIN employees e ON esr.employee_id = e.employee_id
            WHERE esr.upload_batch_id = ?
            GROUP BY esr.employee_id
            ORDER BY esr.employee_id
        ''', (batch_id,))
        
        employees = []
        for row in cursor.fetchall():
            emp_id, name, total_packages, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10 = row
            print(f"DEBUG: Employee {emp_id}: total={total_packages}, r1={r1}, r2={r2}, r3={r3}")
            employees.append({
                'employee_id': emp_id,
                'name': name or emp_id,
                'total_packages': total_packages or 0,
                'weight_ranges': {
                    '0.00-0.50KG': r1 or 0,
                    '0.51-1.00KG': r2 or 0,
                    '1.01-1.50KG': r3 or 0,
                    '1.51-2.00KG': r4 or 0,
                    '2.01-2.50KG': r5 or 0,
                    '2.51-3.00KG': r6 or 0,
                    '3.01-5.00KG': r7 or 0,
                    '5.01-10.00KG': r8 or 0,
                    '10.01-15.00KG': r9 or 0,
                    '15.01KG+': r10 or 0
                }
            })
        
        # นับจำนวนที่ไม่ตรงกับฐานข้อมูลพนักงาน
        cursor.execute('''
            SELECT 
                COUNT(*) as total_unmatched,
                SUM(CASE WHEN weight <= 0.5 THEN 1 ELSE 0 END) as range_1,
                SUM(CASE WHEN weight > 0.5 AND weight <= 1.0 THEN 1 ELSE 0 END) as range_2,
                SUM(CASE WHEN weight > 1.0 AND weight <= 1.5 THEN 1 ELSE 0 END) as range_3,
                SUM(CASE WHEN weight > 1.5 AND weight <= 2.0 THEN 1 ELSE 0 END) as range_4,
                SUM(CASE WHEN weight > 2.0 AND weight <= 2.5 THEN 1 ELSE 0 END) as range_5,
                SUM(CASE WHEN weight > 2.5 AND weight <= 3.0 THEN 1 ELSE 0 END) as range_6,
                SUM(CASE WHEN weight > 3.0 AND weight <= 5.0 THEN 1 ELSE 0 END) as range_7,
                SUM(CASE WHEN weight > 5.0 AND weight <= 10.0 THEN 1 ELSE 0 END) as range_8,
                SUM(CASE WHEN weight > 10.0 AND weight <= 15.0 THEN 1 ELSE 0 END) as range_9,
                SUM(CASE WHEN weight > 15.0 THEN 1 ELSE 0 END) as range_10
            FROM unmatched_salary_records usr
            WHERE usr.upload_batch_id = ?
        ''', (batch_id,))
        
        unmatched_data = cursor.fetchone()
        unmatched_summary = None
        if unmatched_data and unmatched_data[0] > 0:
            total_unmatched, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10 = unmatched_data
            unmatched_summary = {
                'total_packages': total_unmatched,
                'weight_ranges': {
                    '0.00-0.50KG': r1 or 0,
                    '0.51-1.00KG': r2 or 0,
                    '1.01-1.50KG': r3 or 0,
                    '1.51-2.00KG': r4 or 0,
                    '2.01-2.50KG': r5 or 0,
                    '2.51-3.00KG': r6 or 0,
                    '3.01-5.00KG': r7 or 0,
                    '5.01-10.00KG': r8 or 0,
                    '10.01-15.00KG': r9 or 0,
                    '15.01KG+': r10 or 0
                }
            }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'upload_info': {
                'id': upload_id,
                'filename': filename,
                'original_name': original_name,
                'month': month,
                'year': year,
                'created_at': created_at,
                'status': status,
                'employee_linked': employee_linked,
                'rate_linked': rate_linked
            },
            'results': {
                'total_items': total_items,
                'total_employees': total_employees,
                'employees': employees,
                'unmatched_records': unmatched_summary
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })

@app.route('/api/upload-history/<int:month>/<int:year>')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_upload_history(month, year):
    """API สำหรับดึงประวัติการอัพโหลดตามเดือนและปี"""
    try:
        print(f"DEBUG: API upload-history called with month={month}, year={year}")
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงข้อมูลการอัพโหลดตามเดือนและปี
        cursor.execute('''
            SELECT id, filename, original_name, month, year, batch_id, uploaded_by, created_at, status, employee_linked, rate_linked
            FROM salary_uploads 
            WHERE month = ? AND year = ?
            ORDER BY created_at DESC
        ''', (month, year))
        
        uploads = cursor.fetchall()
        print(f"DEBUG: Found {len(uploads)} uploads for month={month}, year={year}")
        
        uploads_list = []
        for row in uploads:
            upload_id, filename, original_name, month, year, batch_id, uploaded_by, created_at, status, employee_linked, rate_linked = row
            
            # นับจำนวนรายการในแต่ละการอัพโหลด
            cursor.execute('''
                SELECT COUNT(*) FROM employee_salary_records 
                WHERE upload_batch_id = ?
            ''', (batch_id,))
            total_records = cursor.fetchone()[0] or 0
            
            # นับจำนวนพนักงานที่ไม่ซ้ำกัน
            cursor.execute('''
                SELECT COUNT(DISTINCT employee_id) FROM employee_salary_records 
                WHERE upload_batch_id = ?
            ''', (batch_id,))
            total_employees = cursor.fetchone()[0] or 0
            
            uploads_list.append({
                'id': upload_id,
                'filename': filename,
                'original_name': original_name,
                'month': month,
                'year': year,
                'batch_id': batch_id,
                'uploaded_by': uploaded_by,
                'created_at': created_at,
                'total_records': total_records,
                'total_employees': total_employees,
                'status': status,
                'employee_linked': employee_linked,
                'rate_linked': rate_linked
            })
        
        conn.close()
        
        print(f"DEBUG: Returning {len(uploads_list)} uploads")
        return jsonify({
            'success': True,
            'uploads': uploads_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })

@app.route('/api/delete-upload/<int:upload_id>', methods=['DELETE'])
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_delete_upload(upload_id):
    """API สำหรับลบข้อมูลการอัพโหลดและข้อมูลที่เกี่ยวข้อง"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงข้อมูลการอัพโหลด
        cursor.execute('''
            SELECT batch_id, filename FROM salary_uploads 
            WHERE id = ?
        ''', (upload_id,))
        
        upload_data = cursor.fetchone()
        if not upload_data:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูลการอัพโหลดที่ต้องการลบ'
            })
        
        batch_id, filename = upload_data
        
        # เริ่ม transaction
        cursor.execute('BEGIN TRANSACTION')
        
        try:
            # ลบข้อมูลจาก employee_salary_records
            cursor.execute('''
                DELETE FROM employee_salary_records 
                WHERE upload_batch_id = ?
            ''', (batch_id,))
            deleted_records = cursor.rowcount
            
            # ลบข้อมูลจาก monthly_salary_data ที่เกี่ยวข้องกับ batch นี้
            # เนื่องจาก monthly_salary_data ไม่มี upload_batch_id เราต้องลบตาม employee_id ที่อยู่ใน batch นี้
            cursor.execute('''
                SELECT DISTINCT employee_id FROM employee_salary_records 
                WHERE upload_batch_id = ?
            ''', (batch_id,))
            
            employee_ids = [row[0] for row in cursor.fetchall()]
            deleted_monthly = 0
            
            if employee_ids:
                # ลบข้อมูล monthly_salary_data สำหรับพนักงานที่อยู่ใน batch นี้
                placeholders = ','.join(['?' for _ in employee_ids])
                cursor.execute(f'''
                    DELETE FROM monthly_salary_data 
                    WHERE employee_id IN ({placeholders})
                ''', employee_ids)
                deleted_monthly = cursor.rowcount
            
            # ลบข้อมูลจาก salary_uploads
            cursor.execute('''
                DELETE FROM salary_uploads 
                WHERE id = ?
            ''', (upload_id,))
            
            # ลบไฟล์ที่อัพโหลด (ถ้ามี)
            import os
            upload_folder = 'uploads'
            file_path = os.path.join(upload_folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                file_deleted = True
            else:
                file_deleted = False
            
            # commit transaction
            cursor.execute('COMMIT')
            
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'ลบข้อมูลการอัพโหลดเรียบร้อยแล้ว',
                'details': {
                    'upload_id': upload_id,
                    'batch_id': batch_id,
                    'filename': filename,
                    'deleted_records': deleted_records,
                    'deleted_monthly_records': deleted_monthly,
                    'file_deleted': file_deleted
                }
            })
            
        except Exception as e:
            # rollback ในกรณีที่เกิดข้อผิดพลาด
            cursor.execute('ROLLBACK')
            conn.close()
            raise e
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาดในการลบข้อมูล: {str(e)}'
        })

@app.route('/api/salary/confirm-payment', methods=['POST'])
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_confirm_payment():
    """API สำหรับยืนยันการจ่ายเงินเดือน"""
    try:
        data = request.get_json()
        work_month = data.get('work_month')
        
        if not work_month:
            return jsonify({'success': False, 'message': 'กรุณาระบุเดือนและปี'})
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ตรวจสอบว่ามีข้อมูลในเดือนนั้นหรือไม่
        cursor.execute('''
            SELECT COUNT(*) FROM employee_salary_records 
            WHERE work_month = ?
        ''', (work_month,))
        
        record_count = cursor.fetchone()[0]
        
        if record_count == 0:
            return jsonify({'success': False, 'message': 'ไม่พบข้อมูลเงินเดือนในเดือนที่ระบุ'})
        
        # ตรวจสอบว่ายืนยันแล้วหรือยัง
        cursor.execute('''
            SELECT is_confirmed, confirmed_by, confirmed_at 
            FROM payment_confirmations 
            WHERE work_month = ?
        ''', (work_month,))
        
        existing_confirmation = cursor.fetchone()
        
        if existing_confirmation and existing_confirmation[0]:
            return jsonify({'success': False, 'message': 'ยืนยันการจ่ายเงินเดือนในเดือนนี้แล้ว'})
        
        # บันทึกการยืนยัน
        cursor.execute('''
            INSERT OR REPLACE INTO payment_confirmations 
            (work_month, is_confirmed, confirmed_by, confirmed_at)
            VALUES (?, 1, ?, CURRENT_TIMESTAMP)
        ''', (work_month, session.get('username', 'Unknown')))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'ยืนยันการจ่ายเงินเดือนเดือน {work_month} เรียบร้อยแล้ว'
        })
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดใน api_confirm_payment: {str(e)}")
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})

@app.route('/api/salary/payment-status/<work_month>')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_payment_status(work_month):
    """API สำหรับตรวจสอบสถานะการยืนยันการจ่ายเงินเดือน"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ตรวจสอบสถานะการยืนยัน
        cursor.execute('''
            SELECT is_confirmed, confirmed_by, confirmed_at 
            FROM payment_confirmations 
            WHERE work_month = ?
        ''', (work_month,))
        
        confirmation = cursor.fetchone()
        
        if confirmation and confirmation[0]:
            return jsonify({
                'success': True,
                'is_confirmed': True,
                'confirmed_info': {
                    'confirmed_by': confirmation[1],
                    'confirmed_at': confirmation[2]
                }
            })
        else:
            return jsonify({
                'success': True,
                'is_confirmed': False,
                'confirmed_info': None
            })
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดใน api_payment_status: {str(e)}")
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})

@app.route('/api/test-salary-data')
def api_test_salary_data():
    """API endpoint ทดสอบที่ไม่ต้องใช้ authentication"""
    try:
        month = request.args.get('month', '6')
        year = request.args.get('year', '2025')
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงข้อมูลจาก employee_salary_records (ข้อมูลจริงจากการอัพโหลด)
        query = '''
            SELECT 
                esr.employee_id,
                SUM(esr.total_pieces) as total_pieces,
                SUM(esr.total_amount) as total_amount,
                esr.work_month,
                e.name,
                e.position,
                e.branch_code,
                e.employment_type,
                e.base_salary,
                e.rate_type,
                e.status
            FROM employee_salary_records esr
            LEFT JOIN employees e ON esr.employee_id = e.employee_id
            WHERE esr.work_month = ?
            GROUP BY esr.employee_id
        '''
        params = [f"{year}-{month.zfill(2)}"]
        
        print(f"🔍 ทดสอบ API - ค้นหาข้อมูลเดือน {month}/{year} (work_month: {params[0]})")
        
        cursor.execute(query, params)
        salary_data = cursor.fetchall()
        
        print(f"📊 พบข้อมูล {len(salary_data)} รายการ")
        
        # แปลงข้อมูลเป็น format ที่ template ต้องการ
        employee_data = []
        total_packages = 0
        total_amount = 0
        employees_with_rates = 0
        employees_without_rates = 0
        unmatched_packages = 0
        
        print(f"=== แสดงผลลัพธ์ในเมนูสรุปเงินได้พนักงาน ===")
        print(f"📊 ข้อมูลเดือน {month}/{year} - พนักงานทั้งหมด: {len(salary_data)} คน")
        
        for data in salary_data:
            (emp_id, pieces, amount, work_month, name, position, branch_code, 
             emp_type, base_salary, rate_type, status) = data
            
            print(f"  - {emp_id}: {name}, {pieces} ชิ้น, ฿{amount:,.2f}")
            
            # ตรวจสอบสถานะเรท
            rate_status = 'no_rate'
            if rate_type and rate_type.strip():
                rate_status = 'assigned'
                employees_with_rates += 1
            else:
                employees_without_rates += 1
            
            # ตรวจสอบว่าพนักงานอยู่ในระบบหรือไม่
            if not name or status != 'active':
                rate_status = 'unmatched'
                unmatched_packages += pieces or 0
            
            # คำนวณข้อมูลช่วงน้ำหนักจาก weight
            weight_ranges = []
            if emp_id:
                cursor.execute('''
                    SELECT 
                        CASE 
                            WHEN weight <= 0.5 THEN 0
                            WHEN weight <= 1.0 THEN 1
                            WHEN weight <= 1.5 THEN 2
                            WHEN weight <= 2.0 THEN 3
                            WHEN weight <= 2.5 THEN 4
                            WHEN weight <= 3.0 THEN 5
                            WHEN weight <= 5.0 THEN 6
                            WHEN weight <= 10.0 THEN 7
                            WHEN weight <= 15.0 THEN 8
                            ELSE 9
                        END as range_index,
                        COUNT(*) as pieces,
                        SUM(total_amount) as amount
                    FROM employee_salary_records 
                    WHERE employee_id = ? AND work_month = ?
                    GROUP BY range_index
                    ORDER BY range_index
                ''', (emp_id, work_month))
                
                range_data = cursor.fetchall()
                weight_ranges = [{'pieces': 0, 'amount': 0, 'rate': 0}] * 10
                
                for range_index, piece_count, range_amount in range_data:
                    if 0 <= range_index < 10:
                        weight_ranges[range_index] = {
                            'pieces': piece_count,
                            'amount': range_amount or 0,
                            'rate': 0
                        }
            
            # ดึงข้อมูลเรทจาก piece_rates (ถ้ามี)
            piece_rate_bonus = 0
            allowance = 0
            allowance_bonus = 0
            
            if position and emp_type:
                cursor.execute("""
                    SELECT piece_rate_bonus, allowance, allowance_tiers
                    FROM piece_rates 
                    WHERE position = ? AND salary_type = ? 
                    AND (branch_code = ? OR branch_code = 'ทุกสาขา')
                    LIMIT 1
                """, (position, emp_type, branch_code))
                
                rate_data = cursor.fetchone()
                if rate_data:
                    piece_rate_bonus = rate_data[0] or 0
                    allowance = rate_data[1] or 0
                    # คำนวณ allowance_bonus จาก allowance_tiers ถ้ามี
                    if rate_data[2]:
                        try:
                            allowance_tiers = json.loads(rate_data[2])
                            # คำนวณ allowance_bonus ตามจำนวนชิ้น
                            if pieces and allowance_tiers:
                                for tier in allowance_tiers:
                                    if pieces >= tier.get('min_packages', 0):
                                        allowance_bonus = tier.get('bonus', 0)
                        except:
                            pass
            
            # คำนวณยอดรวม - รวมเงินเดือนจากเรทจริง
            base_salary_amount = base_salary or 0
            piece_rate_amount = piece_rate_bonus or 0
            allowance_amount = allowance or 0
            allowance_bonus_amount = allowance_bonus or 0
            
            # คำนวณเงินจากงานชิ้นตามเรทจริง
            piece_work_amount = 0
            if pieces and piece_rate_bonus:
                piece_work_amount = pieces * piece_rate_bonus
            
            # รวมเงินจาก total_amount ในฐานข้อมูล (ถ้ามี)
            piece_work_amount += amount or 0
            
            total_emp_amount = base_salary_amount + piece_rate_amount + allowance_amount + allowance_bonus_amount + piece_work_amount
            
            print(f"    💰 เงินเดือน: ฐาน={base_salary_amount:,.2f}, ชิ้น={piece_rate_amount:,.2f}, สมทบ={allowance_amount:,.2f}, โบนัส={allowance_bonus_amount:,.2f}, งาน={piece_work_amount:,.2f}, รวม={total_emp_amount:,.2f}")
            
            employee_info = {
                'employee_id': emp_id,
                'name': name or 'ไม่ระบุชื่อ',
                'position': position or 'ไม่ระบุตำแหน่ง',
                'branch_code': branch_code or 'ไม่ระบุสาขา',
                'piece_rate': emp_type or 'ไม่ระบุ',  # เปลี่ยนจาก employment_type เป็น piece_rate
                'base_salary': base_salary_amount,
                'piece_rate_bonus': piece_rate_amount,
                'allowance': allowance_amount,
                'allowance_bonus': allowance_bonus_amount,
                'packages': pieces or 0,
                'total_amount': total_emp_amount,
                'weight_ranges': weight_ranges,
                'rate_status': rate_status
            }
            
            employee_data.append(employee_info)
            total_packages += pieces or 0
            total_amount += total_emp_amount
        
        summary = {
            'total_employees': len(employee_data),
            'total_packages': total_packages,
            'total_amount': total_amount,
            'month': month,
            'year': year,
            'employees_with_rates': employees_with_rates,
            'employees_without_rates': employees_without_rates,
            'unmatched_packages': unmatched_packages
        }
        
        conn.close()
        return jsonify({'employees': employee_data, 'summary': summary})
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดใน api_test_salary_data: {str(e)}")
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'})

@app.route('/api/piece-rate/<int:rate_id>')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_get_piece_rate(rate_id):
    """ดึงข้อมูลเรทตาม ID"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, position, zone, branch_code, salary_type, base_salary, 
                   piece_rate_bonus, allowance, allowance_tiers,
                   weight_range_1, weight_range_2, weight_range_3, weight_range_4, weight_range_5,
                   weight_range_6, weight_range_7, weight_range_8, weight_range_9, weight_range_10
            FROM piece_rates 
            WHERE id = ?
        """, (rate_id,))
        
        rate = cursor.fetchone()
        conn.close()
        
        if rate:
            return jsonify({
                'success': True,
                'rate': {
                    'id': rate[0],
                    'position': rate[1],
                    'zone': rate[2],
                    'branch_code': rate[3],
                    'salary_type': rate[4],
                    'base_salary': rate[5],
                    'piece_rate_bonus': rate[6],
                    'allowance': rate[7],
                    'allowance_tiers': rate[8],
                    'weight_range_1': rate[9],
                    'weight_range_2': rate[10],
                    'weight_range_3': rate[11],
                    'weight_range_4': rate[12],
                    'weight_range_5': rate[13],
                    'weight_range_6': rate[14],
                    'weight_range_7': rate[15],
                    'weight_range_8': rate[16],
                    'weight_range_9': rate[17],
                    'weight_range_10': rate[18]
                }
            })
        else:
            return jsonify({'success': False, 'error': 'ไม่พบข้อมูลเรท'}), 404
            
    except Exception as e:
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'}), 500

@app.route('/api/piece-rate/save', methods=['POST'])
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_save_piece_rate():
    """บันทึกข้อมูลเรท"""
    print("API endpoint /api/piece-rate/save called")  # Debug log
    try:
        data = request.get_json()
        print(f"Received data: {data}")  # Debug log
        
        # ตรวจสอบข้อมูลที่จำเป็น
        required_fields = ['position', 'zone', 'branch_code', 'salary_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'ข้อมูล {field} ไม่ครบถ้วน'}), 400
        
        # แปลงข้อมูลให้เป็นตัวเลข
        try:
            base_salary = float(data.get('base_salary', 0))
            piece_rate_bonus = float(data.get('piece_rate_bonus', 0))
            allowance = float(data.get('allowance', 0))
            weight_range_1 = float(data.get('weight_range_1', 0))
            weight_range_2 = float(data.get('weight_range_2', 0))
            weight_range_3 = float(data.get('weight_range_3', 0))
            weight_range_4 = float(data.get('weight_range_4', 0))
            weight_range_5 = float(data.get('weight_range_5', 0))
            weight_range_6 = float(data.get('weight_range_6', 0))
            weight_range_7 = float(data.get('weight_range_7', 0))
            weight_range_8 = float(data.get('weight_range_8', 0))
            weight_range_9 = float(data.get('weight_range_9', 0))
            weight_range_10 = float(data.get('weight_range_10', 0))
        except (ValueError, TypeError) as e:
            return jsonify({'success': False, 'error': f'ข้อมูลตัวเลขไม่ถูกต้อง: {str(e)}'}), 400
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        if data.get('piece_rate_id'):  # ใช้ piece_rate_id แทน id
            # อัปเดตข้อมูลที่มีอยู่
            cursor.execute("""
                UPDATE piece_rates SET
                    position = ?, zone = ?, branch_code = ?, salary_type = ?,
                    base_salary = ?, piece_rate_bonus = ?, allowance = ?, allowance_tiers = ?,
                    weight_range_1 = ?, weight_range_2 = ?, weight_range_3 = ?, weight_range_4 = ?, weight_range_5 = ?,
                    weight_range_6 = ?, weight_range_7 = ?, weight_range_8 = ?, weight_range_9 = ?, weight_range_10 = ?
                WHERE id = ?
            """, (
                data['position'], data['zone'], data['branch_code'], data['salary_type'],
                base_salary, piece_rate_bonus, allowance, data.get('allowance_tiers', ''),
                weight_range_1, weight_range_2, weight_range_3, weight_range_4, weight_range_5,
                weight_range_6, weight_range_7, weight_range_8, weight_range_9, weight_range_10,
                data['piece_rate_id']
            ))
        else:
            # เพิ่มข้อมูลใหม่
            cursor.execute("""
                INSERT INTO piece_rates (
                    position, zone, branch_code, salary_type, base_salary, piece_rate_bonus, 
                    allowance, allowance_tiers, weight_range_1, weight_range_2, weight_range_3, 
                    weight_range_4, weight_range_5, weight_range_6, weight_range_7, weight_range_8, 
                    weight_range_9, weight_range_10
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['position'], data['zone'], data['branch_code'], data['salary_type'],
                base_salary, piece_rate_bonus, allowance, data.get('allowance_tiers', ''),
                weight_range_1, weight_range_2, weight_range_3, weight_range_4, weight_range_5,
                weight_range_6, weight_range_7, weight_range_8, weight_range_9, weight_range_10
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'บันทึกข้อมูลเรทสำเร็จ'})
        
    except Exception as e:
        print(f"Error in api_save_piece_rate: {str(e)}")  # Debug log
        return jsonify({'success': False, 'error': f'เกิดข้อผิดพลาด: {str(e)}'}), 500

@app.route('/api/piece-rate/<int:rate_id>/delete', methods=['DELETE'])
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_delete_piece_rate(rate_id):
    """ลบข้อมูลเรท"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM piece_rates WHERE id = ?", (rate_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'ลบข้อมูลเรทสำเร็จ'})
        
    except Exception as e:
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'}), 500

@app.route('/api/piece-rate/update-field', methods=['POST'])
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_update_piece_rate_field():
    """อัปเดตฟิลด์เดียวของเรท"""
    try:
        data = request.get_json()
        rate_id = data.get('id')
        field = data.get('field')
        value = data.get('value')
        
        if not all([rate_id, field, value]):
            return jsonify({'error': 'ข้อมูลไม่ครบถ้วน'}), 400
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute(f"UPDATE piece_rates SET {field} = ? WHERE id = ?", (value, rate_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'อัปเดตข้อมูลสำเร็จ'})
        
    except Exception as e:
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'}), 500

@app.route('/api/piece-rate/by-zone-branch')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_get_piece_rates_by_zone_branch():
    """ดึงข้อมูลเรทตามโซนและสาขา"""
    try:
        zone = request.args.get('zone', '')
        branch = request.args.get('branch', '')
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        query = """
            SELECT id, position, zone, branch_code, salary_type, base_salary, 
                   piece_rate_bonus, allowance, weight_range_1, weight_range_2, 
                   weight_range_3, weight_range_4, weight_range_5, weight_range_6,
                   weight_range_7, weight_range_8, weight_range_9, weight_range_10,
                   allowance_tiers
            FROM piece_rates 
            WHERE 1=1
        """
        params = []
        
        if zone:
            query += " AND (zone = ? OR zone = 'ทุกสาขา')"
            params.append(zone)
        
        if branch:
            query += " AND (branch_code = ? OR branch_code = 'ทุกสาขา')"
            params.append(branch)
        
        query += " ORDER BY position, zone, branch_code"
        
        cursor.execute(query, params)
        rates = cursor.fetchall()
        conn.close()
        
        result = []
        for rate in rates:
            result.append({
                'id': rate[0],
                'position': rate[1],
                'zone': rate[2],
                'branch_code': rate[3],
                'salary_type': rate[4],
                'base_salary': rate[5],
                'piece_rate_bonus': rate[6],
                'allowance': rate[7],
                'weight_range_1': rate[8],
                'weight_range_2': rate[9],
                'weight_range_3': rate[10],
                'weight_range_4': rate[11],
                'weight_range_5': rate[12],
                'weight_range_6': rate[13],
                'weight_range_7': rate[14],
                'weight_range_8': rate[15],
                'weight_range_9': rate[16],
                'weight_range_10': rate[17],
                'allowance_tiers': rate[18]
            })
        
        return jsonify({'rates': result})
        
    except Exception as e:
        return jsonify({'error': f'เกิดข้อผิดพลาด: {str(e)}'}), 500

@app.route('/api/employee/<employee_id>/rate')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_get_employee_rate(employee_id):
    """ดึงข้อมูลเรทของพนักงาน"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงข้อมูลพนักงาน
        cursor.execute("""
            SELECT employee_id, name, position, branch_code, employment_type, zone, rate_type
            FROM employees 
            WHERE employee_id = ?
        """, (employee_id,))
        
        employee_data = cursor.fetchone()
        if not employee_data:
            return jsonify({'success': False, 'message': 'ไม่พบข้อมูลพนักงาน'})
        
        employee = {
            'employee_id': employee_data[0],
            'name': employee_data[1],
            'position': employee_data[2],
            'branch_code': employee_data[3],
            'employment_type': employee_data[4],
            'zone': employee_data[5],
            'rate_type': employee_data[6]
        }
        
        # ดึงข้อมูลเรทจาก piece_rates
        cursor.execute("""
            SELECT id, base_salary, piece_rate_bonus, allowance, allowance_tiers
            FROM piece_rates 
            WHERE position = ? AND (zone = ? OR zone = 'ทุกสาขา') AND (branch_code = ? OR branch_code = 'ทุกสาขา')
            ORDER BY zone DESC, branch_code DESC
            LIMIT 1
        """, (employee['position'], employee['zone'], employee['branch_code']))
        
        rate_data = cursor.fetchone()
        rate = {
            'id': rate_data[0] if rate_data else None,
            'base_salary': rate_data[1] if rate_data else 0,
            'piece_rate': rate_data[2] if rate_data else 0,
            'allowance': rate_data[3] if rate_data else 0,
            'allowance_tiers': rate_data[4] if rate_data else None,
            'zone': employee['zone'],
            'bonus_rate': 0  # ค่าเริ่มต้น
        }
        
        conn.close()
        
        return jsonify({
            'success': True,
            'employee': employee,
            'rate': rate
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})

@app.route('/api/employee/rate/update', methods=['POST'])
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_update_employee_rate():
    """อัปเดตข้อมูลเรทของพนักงาน"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        zone = data.get('zone')
        employment_type = data.get('employment_type')
        base_salary = data.get('base_salary', 0)
        piece_rate = data.get('piece_rate', 0)
        allowance = data.get('allowance', 0)
        bonus_rate = data.get('bonus_rate', 0)
        
        if not employee_id:
            return jsonify({'success': False, 'message': 'ไม่พบรหัสพนักงาน'})
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # อัปเดตข้อมูลพนักงาน
        cursor.execute("""
            UPDATE employees 
            SET zone = ?, employment_type = ?
            WHERE employee_id = ?
        """, (zone, employment_type, employee_id))
        
        # ดึงข้อมูลตำแหน่งและสาขาของพนักงาน
        cursor.execute("""
            SELECT position, branch_code FROM employees WHERE employee_id = ?
        """, (employee_id,))
        
        emp_data = cursor.fetchone()
        if emp_data:
            position, branch_code = emp_data
            
            # ตรวจสอบว่ามีเรทอยู่แล้วหรือไม่
            cursor.execute("""
                SELECT id FROM piece_rates 
                WHERE position = ? AND zone = ? AND branch_code = ?
            """, (position, zone, branch_code))
            
            existing_rate = cursor.fetchone()
            
            if existing_rate:
                # อัปเดตเรทที่มีอยู่
                cursor.execute("""
                    UPDATE piece_rates 
                    SET base_salary = ?, piece_rate_bonus = ?, allowance = ?
                    WHERE position = ? AND zone = ? AND branch_code = ?
                """, (base_salary, piece_rate, allowance, position, zone, branch_code))
            else:
                # สร้างเรทใหม่
                cursor.execute("""
                    INSERT INTO piece_rates (position, zone, branch_code, salary_type, base_salary, piece_rate_bonus, allowance)
                    VALUES (?, ?, ?, 'piece_rate', ?, ?, ?)
                """, (position, zone, branch_code, base_salary, piece_rate, allowance))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'อัปเดตข้อมูลเรทสำเร็จ'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'})

@app.route('/api/dashboard/summary')
@login_required
def api_dashboard_summary():
    """API สำหรับข้อมูลสรุป dashboard"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # นับจำนวนพนักงานทั้งหมด
        cursor.execute('SELECT COUNT(*) FROM employees WHERE status = "active"')
        total_employees = cursor.fetchone()[0]
        
        # คำนวณเงินเดือนรวม
        cursor.execute('''
            SELECT COALESCE(SUM(net_salary), 0) 
            FROM salaries 
            WHERE status = "confirmed"
        ''')
        total_salary = cursor.fetchone()[0] or 0
        
        # นับจำนวนการลารวม
        cursor.execute('SELECT COUNT(*) FROM leave_requests')
        total_leave = cursor.fetchone()[0]
        
        # นับจำนวนไฟล์อัปโหลด
        cursor.execute('SELECT COUNT(*) FROM salary_uploads')
        total_uploads = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_employees': total_employees,
            'total_salary': total_salary,
            'total_leave': total_leave,
            'total_uploads': total_uploads
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/recent-activity')
@login_required
def api_dashboard_recent_activity():
    """API สำหรับกิจกรรมล่าสุด"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงข้อมูลกิจกรรมล่าสุด (จำลองข้อมูล)
        activities = [
            {
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'description': 'เข้าสู่ระบบสำเร็จ'
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=1)).strftime('%d/%m/%Y %H:%M'),
                'description': 'อัปโหลดข้อมูลเงินเดือน'
            },
            {
                'timestamp': (datetime.now() - timedelta(hours=2)).strftime('%d/%m/%Y %H:%M'),
                'description': 'อัปเดตข้อมูลพนักงาน'
            }
        ]
        
        conn.close()
        
        return jsonify({
            'activities': activities
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ฟังก์ชันการคำนวณเงินเดือนแบบรวมศูนย์ - ใช้สูตรเดียวสำหรับทุกตำแหน่ง
def calculate_salary_unified(employee_data, rate_data, pieces):
    """
    ฟังก์ชันการคำนวณเงินเดือนแบบรวมศูนย์ - ใช้สูตรเดียวกันสำหรับทุกตำแหน่ง
    สูตร: เงินเดือนรวม = ฐานเงินเดือน + เงินชิ้น + เงินสมทบ
    
    Parameters:
    - employee_data: ข้อมูลพนักงาน (dict)
    - rate_data: ข้อมูลเรท (tuple จาก database)
    - pieces: จำนวนชิ้น (int)
    
    Returns:
    - dict: {'base_salary': float, 'piece_rate_bonus': float, 'allowance': float, 'total_amount': float}
    """
    if not rate_data:
        return {
            'base_salary': 0,
            'piece_rate_bonus': 0,
            'allowance': 0,
            'total_amount': 0
        }
    
    try:
        # ดึงข้อมูลจาก rate_data
        base_salary = float(rate_data[0] or 0)  # ฐานเงินเดือน
        piece_rate_bonus = float(rate_data[1] or 0)  # ค่าชิ้นโบนัส (เรทต่อชิ้น)
        allowance = float(rate_data[2] or 0)  # เงินสมทบ
        
        # ดึงข้อมูล weight_range (ช่องแต่ละช่วงน้ำหนัก)
        weight_ranges = []
        for i in range(3, 13):  # weight_range_1 ถึง weight_range_10
            if i < len(rate_data):
                weight_value = float(rate_data[i] or 0)
                weight_ranges.append(weight_value)
        
        # ดึงข้อมูล allowance_tiers (ช่องหมายเหตุ)
        allowance_tiers = rate_data[13] if len(rate_data) > 13 else None
        
        # คำนวณเงินชิ้น - ใช้ weight_range ตามจำนวนชิ้น
        piece_amount = 0
        if pieces > 0 and weight_ranges:
            # ตรวจสอบประเภทเรท
            if employee_data and 'rate_type' in employee_data:
                rate_type = employee_data['rate_type']
                if rate_type == 'piece_rate':
                    # พนักงาน piece_rate: มีแค่เงินชิ้น
                    piece_rate_per_piece = weight_ranges[0]  # ใช้เรทแรกเป็นค่าเริ่มต้น
                    piece_amount = pieces * piece_rate_per_piece
                elif rate_type == 'base_salary':
                    # พนักงาน base_salary: มีแค่ฐานเงินเดือน (ไม่คำนวณเงินชิ้น)
                    piece_amount = 0
                else:
                    # กรณีอื่นๆ: ใช้เรทแรก
                    piece_rate_per_piece = weight_ranges[0]
                    piece_amount = pieces * piece_rate_per_piece
            else:
                # ถ้าไม่มีข้อมูล rate_type: ใช้เรทแรก
                piece_rate_per_piece = weight_ranges[0]
                piece_amount = pieces * piece_rate_per_piece
        
        # คำนวณเงินสมทบตาม allowance_tiers (ช่องหมายเหตุ)
        final_allowance = allowance
        if allowance_tiers:
            try:
                import json
                # ตรวจสอบว่า allowance_tiers เป็น JSON string หรือไม่
                if isinstance(allowance_tiers, str) and allowance_tiers.startswith('['):
                    tiers = json.loads(allowance_tiers)
                else:
                    # ถ้าไม่ใช่ JSON string ให้ใช้ค่าเดิม
                    tiers = allowance_tiers
                
                if tiers and isinstance(tiers, list):
                    # หาเงินสมทบสูงสุดที่ตรงกับจำนวนชิ้น
                    for tier in tiers:
                        if 'pieces' in tier and 'amount' in tier:
                            if pieces >= tier['pieces']:
                                final_allowance = float(tier['amount'])
                                # ไม่ break เพื่อให้ตรวจสอบเกณฑ์ที่สูงกว่าต่อไป
                        elif 'min_pieces' in tier and 'allowance' in tier:
                            if pieces >= tier['min_pieces']:
                                final_allowance = float(tier['allowance'])
                                # ไม่ break เพื่อให้ตรวจสอบเกณฑ์ที่สูงกว่าต่อไป
            except Exception as e:
                print(f"❌ Error parsing allowance_tiers: {e}")
                final_allowance = allowance
        
        # คำนวณเงินรวม
        total_amount = base_salary + piece_amount + final_allowance
        
        return {
            'base_salary': base_salary,
            'piece_rate_bonus': piece_amount,
            'allowance': final_allowance,
            'total_amount': total_amount
        }
        
    except Exception as e:
        print(f"❌ Error in calculate_salary_unified: {e}")
        return {
            'base_salary': 0,
            'piece_rate_bonus': 0,
            'allowance': 0,
            'total_amount': 0
        }

# API endpoints สำหรับจัดการ permissions
@app.route('/api/permissions/<int:user_id>')
@login_required
@role_required(['GM', 'MD'])
def api_get_user_permissions(user_id):
    """ดึงข้อมูลสิทธิ์ของผู้ใช้"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงข้อมูลเมนูทั้งหมด
        cursor.execute('SELECT * FROM menu_items ORDER BY category, display_name')
        menus = cursor.fetchall()
        
        # ดึงข้อมูลสิทธิ์ของผู้ใช้
        cursor.execute('SELECT menu_name, can_access FROM permissions WHERE user_id = ?', (user_id,))
        permissions = cursor.fetchall()
        
        # แปลงเป็นรูปแบบที่ใช้งานง่าย
        menu_list = []
        for menu in menus:
            # ตรวจสอบสิทธิ์ของผู้ใช้สำหรับเมนูนี้
            can_access = 0
            for perm in permissions:
                if perm[0] == menu[1]:  # menu_name
                    can_access = perm[1]
                    break
            
            menu_list.append({
                'id': menu[0],
                'menu_name': menu[1],
                'display_name': menu[2],
                'category': menu[3],
                'is_active': menu[4],
                'can_access': can_access
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'menus': menu_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })

@app.route('/api/permissions/<int:user_id>/update', methods=['POST'])
@login_required
@role_required(['GM', 'MD'])
def api_update_user_permissions(user_id):
    """อัปเดตสิทธิ์ของผู้ใช้"""
    try:
        data = request.get_json()
        permissions = data.get('permissions', [])
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ลบสิทธิ์เดิม
        cursor.execute('DELETE FROM permissions WHERE user_id = ?', (user_id,))
        
        # เพิ่มสิทธิ์ใหม่
        for perm in permissions:
            menu_id = perm.get('menu_id')
            can_access = perm.get('can_access', 0)
            
            if menu_id:
                # ดึง menu_name จาก menu_id
                cursor.execute('SELECT menu_name FROM menu_items WHERE id = ?', (menu_id,))
                menu_result = cursor.fetchone()
                
                if menu_result:
                    menu_name = menu_result[0]
                    cursor.execute('''
                        INSERT INTO permissions (user_id, menu_name, can_access)
                        VALUES (?, ?, ?)
                    ''', (user_id, menu_name, can_access))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'อัปเดตสิทธิ์เรียบร้อย'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })

@app.route('/api/users')
@login_required
@role_required(['GM', 'MD'])
def api_get_users():
    """ดึงรายการผู้ใช้ทั้งหมด"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, role, name, email FROM users ORDER BY role, username')
        users = cursor.fetchall()
        
        user_list = []
        for user in users:
            user_list.append({
                'id': user[0],
                'username': user[1],
                'role': user[2],
                'name': user[3],
                'email': user[4]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'users': user_list
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })

@app.route('/api/users/<username>')
@login_required
@role_required(['GM', 'MD'])
def api_get_user_by_username(username):
    """ดึงข้อมูลผู้ใช้ตาม username"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, role, name, email, branch_code FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            return jsonify({
                'success': True,
                'user': {
                    'id': user[0],
                    'username': user[1],
                    'role': user[2],
                    'name': user[3],
                    'email': user[4],
                    'branch_code': user[5]
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูลผู้ใช้'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })

@app.route('/api/users', methods=['POST'])
@login_required
@role_required(['GM', 'MD'])
def api_create_user():
    """สร้างผู้ใช้ใหม่"""
    try:
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        branch_code = request.form.get('branch_code', '')
        email = request.form.get('email', '')
        
        if not all([username, password, role]):
            return jsonify({
                'success': False,
                'message': 'กรุณากรอกข้อมูลให้ครบถ้วน'
            })
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ตรวจสอบว่ามี username นี้อยู่แล้วหรือไม่
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'มีชื่อผู้ใช้นี้อยู่แล้ว'
            })
        
        # สร้างผู้ใช้ใหม่
        password_hash = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (username, password_hash, role, name, email, branch_code)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, password_hash, role, username, email, branch_code))
        
        user_id = cursor.lastrowid
        
        # สร้างสิทธิ์เริ่มต้นตาม role
        if role in ['GM', 'MD']:
            cursor.execute('SELECT menu_name FROM menu_items WHERE category = "GM/MD"')
        elif role == 'HR':
            cursor.execute('SELECT menu_name FROM menu_items WHERE category = "HR"')
        elif role == 'การเงิน':
            cursor.execute('SELECT menu_name FROM menu_items WHERE category = "การเงิน"')
        elif role == 'SPV':
            cursor.execute('SELECT menu_name FROM menu_items WHERE category = "SPV"')
        elif role in ['ADM', 'SPT']:
            cursor.execute('SELECT menu_name FROM menu_items WHERE category = "SPT"')
        else:
            cursor.execute('SELECT menu_name FROM menu_items WHERE category = "GM/MD"')
        
        menus = cursor.fetchall()
        
        for menu in menus:
            cursor.execute('''
                INSERT INTO permissions (user_id, menu_name, can_access)
                VALUES (?, ?, 1)
            ''', (user_id, menu[0]))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'สร้างผู้ใช้สำเร็จ'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })

@app.route('/api/users/<username>/delete', methods=['DELETE'])
@login_required
@role_required(['GM', 'MD'])
def api_delete_user(username):
    """ลบผู้ใช้"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ตรวจสอบว่ามีผู้ใช้นี้หรือไม่
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูลผู้ใช้'
            })
        
        user_id = user[0]
        
        # ลบสิทธิ์
        cursor.execute('DELETE FROM permissions WHERE user_id = ?', (user_id,))
        
        # ลบผู้ใช้
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'ลบผู้ใช้สำเร็จ'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })

# ==================== VEHICLE MANAGEMENT SYSTEM ====================

@app.route('/vehicle/dashboard')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def vehicle_dashboard():
    """หน้า Dashboard ระบบจัดการรถบริษัท"""
    return render_template('vehicle/dashboard.html')

@app.route('/vehicle/register')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def vehicle_register():
    """หน้าลงทะเบียนใช้งานรถประจำวัน"""
    return render_template('vehicle/register.html')

@app.route('/vehicle/check')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def vehicle_check():
    """หน้าตรวจเช็คสภาพรถประจำสัปดาห์"""
    return render_template('vehicle/check.html')

@app.route('/vehicle/list')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def vehicle_list():
    """หน้ารายการรถบริษัท"""
    return render_template('vehicle/list.html')

@app.route('/vehicle/fuel')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def vehicle_fuel():
    """หน้าประวัติเบิกจ่ายน้ำมัน"""
    return render_template('vehicle/fuel.html')

@app.route('/mobile/app')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def mobile_app():
    """หน้า Mobile App สำหรับระบบจัดการรถบริษัท"""
    return render_template('mobile_app.html')

# Vehicle API Endpoints
@app.route('/api/vehicle/dashboard-stats')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def api_vehicle_dashboard_stats():
    """API สำหรับข้อมูลสถิติ Dashboard รถ"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # นับรถทั้งหมด
        cursor.execute('SELECT COUNT(*) FROM vehicles')
        total_vehicles = cursor.fetchone()[0]
        
        # นับรถที่ใช้งาน
        cursor.execute('SELECT COUNT(*) FROM vehicles WHERE status = "active"')
        active_vehicles = cursor.fetchone()[0]
        
        # นับรถที่รอซ่อม
        cursor.execute('SELECT COUNT(*) FROM vehicles WHERE status = "maintenance"')
        maintenance_vehicles = cursor.fetchone()[0]
        
        # คำนวณค่าใช้จ่ายน้ำมันเดือนนี้
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute('''
            SELECT COALESCE(SUM(total_cost), 0) 
            FROM vehicle_fuel_usage 
            WHERE fuel_date LIKE ?
        ''', (f'{current_month}%',))
        monthly_fuel_cost = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_vehicles': total_vehicles,
            'active_vehicles': active_vehicles,
            'maintenance_vehicles': maintenance_vehicles,
            'monthly_fuel_cost': monthly_fuel_cost
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicle/recent-activities')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def api_vehicle_recent_activities():
    """API สำหรับกิจกรรมล่าสุด"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงข้อมูลการใช้งานล่าสุด
        cursor.execute('''
            SELECT vd.usage_date, vd.purpose, v.license_plate, e.name as driver_name
            FROM vehicle_daily_usage vd
            JOIN vehicles v ON vd.vehicle_id = v.vehicle_id
            JOIN employees e ON vd.driver_id = e.employee_id
            ORDER BY vd.created_at DESC
            LIMIT 10
        ''')
        recent_usage = cursor.fetchall()
        
        # ดึงข้อมูลการตรวจเช็คล่าสุด
        cursor.execute('''
            SELECT vc.check_date, v.license_plate, e.name as inspector_name, vc.overall_status
            FROM vehicle_weekly_checks vc
            JOIN vehicles v ON vc.vehicle_id = v.vehicle_id
            JOIN employees e ON vc.inspector_id = e.employee_id
            ORDER BY vc.created_at DESC
            LIMIT 10
        ''')
        recent_checks = cursor.fetchall()
        
        conn.close()
        
        activities = []
        
        # เพิ่มข้อมูลการใช้งาน
        for usage in recent_usage:
            activities.append({
                'type': 'usage',
                'date': usage[0],
                'description': f'รถ {usage[2]} - {usage[1]}',
                'user': usage[3]
            })
        
        # เพิ่มข้อมูลการตรวจเช็ค
        for check in recent_checks:
            activities.append({
                'type': 'check',
                'date': check[0],
                'description': f'ตรวจเช็ครถ {check[1]} - สภาพ: {check[3]}',
                'user': check[2]
            })
        
        # เรียงลำดับตามวันที่
        activities.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify(activities[:10])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicle/notifications')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def api_vehicle_notifications():
    """API สำหรับการแจ้งเตือน"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงการแจ้งเตือนที่ยังไม่เสร็จสิ้น
        cursor.execute('''
            SELECT vn.title, vn.message, vn.due_date, vn.priority, v.license_plate
            FROM vehicle_notifications vn
            JOIN vehicles v ON vn.vehicle_id = v.vehicle_id
            WHERE vn.status = 'pending'
            ORDER BY vn.due_date ASC
            LIMIT 10
        ''')
        notifications = cursor.fetchall()
        
        conn.close()
        
        result = []
        for notif in notifications:
            result.append({
                'title': notif[0],
                'message': notif[1],
                'due_date': notif[2],
                'priority': notif[3],
                'vehicle': notif[4]
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicle/list')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def api_vehicle_list():
    """API สำหรับรายการรถ"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงพารามิเตอร์การกรอง
        status = request.args.get('status', '')
        branch_code = request.args.get('branch_code', '')
        brand = request.args.get('brand', '')
        fuel_type = request.args.get('fuel_type', '')
        search = request.args.get('search', '')
        
        # สร้าง query
        query = '''
            SELECT v.*, e.name as assigned_driver_name
            FROM vehicles v
            LEFT JOIN employees e ON v.assigned_driver_id = e.employee_id
            WHERE 1=1
        '''
        params = []
        
        if status:
            query += ' AND v.status = ?'
            params.append(status)
        
        if branch_code:
            query += ' AND v.branch_code = ?'
            params.append(branch_code)
        
        if brand:
            query += ' AND v.brand = ?'
            params.append(brand)
        
        if fuel_type:
            query += ' AND v.fuel_type = ?'
            params.append(fuel_type)
        
        if search:
            query += ' AND (v.license_plate LIKE ? OR v.brand LIKE ? OR v.model LIKE ?)'
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        query += ' ORDER BY v.created_at DESC'
        
        cursor.execute(query, params)
        vehicles = cursor.fetchall()
        
        conn.close()
        
        result = []
        for vehicle in vehicles:
            result.append({
                'vehicle_id': vehicle[1],
                'license_plate': vehicle[2],
                'brand': vehicle[3],
                'model': vehicle[4],
                'year': vehicle[5],
                'color': vehicle[6],
                'engine_size': vehicle[7],
                'fuel_type': vehicle[8],
                'transmission': vehicle[9],
                'mileage': vehicle[10],
                'status': vehicle[11],
                'branch_code': vehicle[12],
                'assigned_driver_id': vehicle[13],
                'purchase_date': vehicle[14],
                'purchase_price': vehicle[15],
                'insurance_expiry': vehicle[16],
                'registration_expiry': vehicle[17],
                'assigned_driver_name': vehicle[19]
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicle/statistics')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def api_vehicle_statistics():
    """API สำหรับสถิติรถ"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # นับรถทั้งหมด
        cursor.execute('SELECT COUNT(*) FROM vehicles')
        total_vehicles = cursor.fetchone()[0]
        
        # นับรถที่ใช้งาน
        cursor.execute('SELECT COUNT(*) FROM vehicles WHERE status = "active"')
        active_vehicles = cursor.fetchone()[0]
        
        # นับรถที่รอซ่อม
        cursor.execute('SELECT COUNT(*) FROM vehicles WHERE status = "maintenance"')
        maintenance_vehicles = cursor.fetchone()[0]
        
        # คำนวณไมล์รวม
        cursor.execute('SELECT COALESCE(SUM(mileage), 0) FROM vehicles')
        total_mileage = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'totalVehicles': total_vehicles,
            'activeVehicles': active_vehicles,
            'maintenanceVehicles': maintenance_vehicles,
            'totalMileage': total_mileage
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicle/drivers')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def api_vehicle_drivers():
    """API สำหรับรายการคนขับ"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT employee_id, name FROM employees WHERE status = "active" ORDER BY name')
        drivers = cursor.fetchall()
        
        conn.close()
        
        result = []
        for driver in drivers:
            result.append({
                'employee_id': driver[0],
                'name': driver[1]
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/branches')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def api_branches():
    """API สำหรับรายการสาขา"""
    try:
        result = []
        for code, name in BRANCHES.items():
            result.append({
                'branch_code': code,
                'branch_name': name
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicle/details/<vehicle_id>')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def api_vehicle_details(vehicle_id):
    """API สำหรับรายละเอียดรถ"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงข้อมูลรถ
        cursor.execute('''
            SELECT v.*, e.name as assigned_driver_name
            FROM vehicles v
            LEFT JOIN employees e ON v.assigned_driver_id = e.employee_id
            WHERE v.vehicle_id = ?
        ''', (vehicle_id,))
        vehicle = cursor.fetchone()
        
        if not vehicle:
            return jsonify({'error': 'ไม่พบรถคันนี้'}), 404
        
        # ดึงประวัติการซ่อมบำรุง
        cursor.execute('''
            SELECT maintenance_type, maintenance_date, description, 
                   mileage_at_service, total_cost, status
            FROM vehicle_maintenance
            WHERE vehicle_id = ?
            ORDER BY maintenance_date DESC
        ''', (vehicle_id,))
        maintenance_records = cursor.fetchall()
        
        conn.close()
        
        vehicle_data = {
            'vehicle_id': vehicle[1],
            'license_plate': vehicle[2],
            'brand': vehicle[3],
            'model': vehicle[4],
            'year': vehicle[5],
            'color': vehicle[6],
            'engine_size': vehicle[7],
            'fuel_type': vehicle[8],
            'transmission': vehicle[9],
            'mileage': vehicle[10],
            'status': vehicle[11],
            'branch_code': vehicle[12],
            'assigned_driver_id': vehicle[13],
            'purchase_date': vehicle[14],
            'purchase_price': vehicle[15],
            'insurance_expiry': vehicle[16],
            'registration_expiry': vehicle[17],
            'assigned_driver_name': vehicle[19]
        }
        
        maintenance_data = []
        for record in maintenance_records:
            maintenance_data.append({
                'maintenance_type': record[0],
                'maintenance_date': record[1],
                'description': record[2],
                'mileage_at_service': record[3],
                'total_cost': record[4],
                'status': record[5]
            })
        
        vehicle_data['maintenance_records'] = maintenance_data
        
        return jsonify(vehicle_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicle/add', methods=['POST'])
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_vehicle_add():
    """API สำหรับเพิ่มรถใหม่"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vehicles (
                vehicle_id, license_plate, brand, model, year, color, engine_size,
                fuel_type, transmission, mileage, status, branch_code, assigned_driver_id,
                purchase_date, purchase_price, insurance_expiry, registration_expiry
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], data['license_plate'], data['brand'], data['model'],
            data['year'], data['color'], data['engine_size'], data['fuel_type'],
            data['transmission'], data['mileage'], data['status'], data['branch_code'],
            data['assigned_driver_id'], data['purchase_date'], data['purchase_price'],
            data['insurance_expiry'], data['registration_expiry']
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'เพิ่มรถใหม่สำเร็จ'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/vehicle/delete/<vehicle_id>', methods=['DELETE'])
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_vehicle_delete(vehicle_id):
    """API สำหรับลบรถ"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM vehicles WHERE vehicle_id = ?', (vehicle_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'ลบรถสำเร็จ'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/vehicle/register-usage', methods=['POST'])
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def api_vehicle_register_usage():
    """API สำหรับลงทะเบียนใช้งานรถ"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vehicle_daily_usage (
                vehicle_id, driver_id, usage_date, start_time, end_time,
                purpose, destination, start_mileage, end_mileage, fuel_consumed, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], data['driver_id'], data['usage_date'],
            data['start_time'], data['end_time'], data['purpose'], data['destination'],
            data['start_mileage'], data['end_mileage'], data['fuel_consumed'], data['notes']
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'ลงทะเบียนใช้งานรถสำเร็จ'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/vehicle/check', methods=['POST'])
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def api_vehicle_check():
    """API สำหรับตรวจเช็คสภาพรถ"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vehicle_weekly_checks (
                vehicle_id, inspector_id, check_date, engine_status, engine_notes, engine_image,
                body_status, body_notes, body_image, tires_status, tires_notes, tires_image,
                lights_status, lights_notes, lights_image, brakes_status, brakes_notes, brakes_image,
                interior_status, interior_notes, interior_image, overall_status, overall_notes,
                overall_image, recommendations, next_check_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], data['inspector_id'], data['check_date'],
            data['engine_status'], data['engine_notes'], data['engine_image'],
            data['body_status'], data['body_notes'], data['body_image'],
            data['tires_status'], data['tires_notes'], data['tires_image'],
            data['lights_status'], data['lights_notes'], data['lights_image'],
            data['brakes_status'], data['brakes_notes'], data['brakes_image'],
            data['interior_status'], data['interior_notes'], data['interior_image'],
            data['overall_status'], data['overall_notes'], data['overall_image'],
            data['recommendations'], data['next_check_date']
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'บันทึกการตรวจเช็คสำเร็จ'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/vehicle/fuel-statistics')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def api_fuel_statistics():
    """API สำหรับสถิติน้ำมัน"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # คำนวณค่าใช้จ่ายน้ำมันเดือนนี้
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute('''
            SELECT COALESCE(SUM(total_cost), 0), COALESCE(SUM(quantity), 0)
            FROM vehicle_fuel_usage 
            WHERE fuel_date LIKE ?
        ''', (f'{current_month}%',))
        result = cursor.fetchone()
        monthly_total = result[0]
        total_quantity = result[1]
        
        # นับรถที่ใช้งาน
        cursor.execute('SELECT COUNT(*) FROM vehicles WHERE status = "active"')
        active_vehicles = cursor.fetchone()[0]
        
        # คำนวณราคาเฉลี่ย
        cursor.execute('''
            SELECT COALESCE(AVG(unit_price), 0)
            FROM vehicle_fuel_usage 
            WHERE fuel_date LIKE ?
        ''', (f'{current_month}%',))
        avg_price = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'monthlyTotal': monthly_total,
            'totalQuantity': total_quantity,
            'activeVehicles': active_vehicles,
            'avgPrice': round(avg_price, 2)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicle/fuel-records')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def api_fuel_records():
    """API สำหรับรายการเบิกจ่ายน้ำมัน"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        # ดึงพารามิเตอร์การกรอง
        vehicle_id = request.args.get('vehicle_id', '')
        fuel_type = request.args.get('fuel_type', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        search = request.args.get('search', '')
        
        # สร้าง query
        query = '''
            SELECT vf.*, v.license_plate, v.brand, v.model, e.name as driver_name
            FROM vehicle_fuel_usage vf
            JOIN vehicles v ON vf.vehicle_id = v.vehicle_id
            JOIN employees e ON vf.driver_id = e.employee_id
            WHERE 1=1
        '''
        params = []
        
        if vehicle_id:
            query += ' AND vf.vehicle_id = ?'
            params.append(vehicle_id)
        
        if fuel_type:
            query += ' AND vf.fuel_type = ?'
            params.append(fuel_type)
        
        if start_date:
            query += ' AND vf.fuel_date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND vf.fuel_date <= ?'
            params.append(end_date)
        
        if search:
            query += ' AND (vf.receipt_number LIKE ? OR vf.gas_station LIKE ?)'
            search_param = f'%{search}%'
            params.extend([search_param, search_param])
        
        query += ' ORDER BY vf.fuel_date DESC'
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        conn.close()
        
        result = []
        for record in records:
            result.append({
                'id': record[0],
                'vehicle_id': record[1],
                'driver_id': record[2],
                'fuel_date': record[3],
                'fuel_type': record[4],
                'quantity': record[5],
                'unit_price': record[6],
                'total_cost': record[7],
                'gas_station': record[8],
                'receipt_number': record[9],
                'mileage_at_fuel': record[10],
                'fuel_card_number': record[11],
                'notes': record[12],
                'license_plate': record[14],
                'brand': record[15],
                'model': record[16],
                'driver_name': record[17]
            })
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicle/add-fuel-record', methods=['POST'])
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน', 'SPV'])
def api_add_fuel_record():
    """API สำหรับเพิ่มรายการน้ำมัน"""
    try:
        data = request.get_json()
        
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vehicle_fuel_usage (
                vehicle_id, driver_id, fuel_date, fuel_type, quantity, unit_price,
                total_cost, gas_station, receipt_number, mileage_at_fuel, fuel_card_number, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], data['driver_id'], data['fuel_date'], data['fuel_type'],
            data['quantity'], data['unit_price'], data['total_cost'], data['gas_station'],
            data['receipt_number'], data['mileage_at_fuel'], data['fuel_card_number'], data['notes']
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'เพิ่มรายการน้ำมันสำเร็จ'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/vehicle/delete-fuel-record/<int:record_id>', methods=['DELETE'])
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_delete_fuel_record(record_id):
    """API สำหรับลบรายการน้ำมัน"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM vehicle_fuel_usage WHERE id = ?', (record_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'ลบรายการน้ำมันสำเร็จ'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/vehicle/export-fuel-data')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_export_fuel_data():
    """API สำหรับส่งออกข้อมูลน้ำมัน"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT vf.fuel_date, v.license_plate, v.brand, v.model, e.name as driver_name,
                   vf.fuel_type, vf.quantity, vf.unit_price, vf.total_cost, vf.gas_station,
                   vf.receipt_number, vf.mileage_at_fuel
            FROM vehicle_fuel_usage vf
            JOIN vehicles v ON vf.vehicle_id = v.vehicle_id
            JOIN employees e ON vf.driver_id = e.employee_id
            ORDER BY vf.fuel_date DESC
        ''')
        records = cursor.fetchall()
        
        conn.close()
        
        # สร้างไฟล์ CSV
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'วันที่', 'เลขทะเบียน', 'ยี่ห้อ', 'รุ่น', 'คนขับ', 'ประเภทน้ำมัน',
            'ปริมาณ (ลิตร)', 'ราคาต่อลิตร', 'ยอดรวม', 'สถานีน้ำมัน', 'หมายเลขใบเสร็จ', 'ไมล์'
        ])
        
        for record in records:
            writer.writerow(record)
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=fuel_records.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vehicle/export')
@login_required
@role_required(['GM', 'MD', 'HR', 'การเงิน'])
def api_export_vehicle_data():
    """API สำหรับส่งออกข้อมูลรถ"""
    try:
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT v.vehicle_id, v.license_plate, v.brand, v.model, v.year, v.color,
                   v.engine_size, v.fuel_type, v.transmission, v.mileage, v.status,
                   v.branch_code, e.name as assigned_driver, v.purchase_date, v.purchase_price,
                   v.insurance_expiry, v.registration_expiry
            FROM vehicles v
            LEFT JOIN employees e ON v.assigned_driver_id = e.employee_id
            ORDER BY v.created_at DESC
        ''')
        records = cursor.fetchall()
        
        conn.close()
        
        # สร้างไฟล์ CSV
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'รหัสรถ', 'เลขทะเบียน', 'ยี่ห้อ', 'รุ่น', 'ปี', 'สี', 'ขนาดเครื่องยนต์',
            'เชื้อเพลิง', 'เกียร์', 'ไมล์', 'สถานะ', 'สาขา', 'คนขับ', 'วันที่ซื้อ',
            'ราคาซื้อ', 'ประกันหมด', 'ทะเบียนหมด'
        ])
        
        for record in records:
            writer.writerow(record)
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=vehicles.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    seed_default_users()
    app.run(host='0.0.0.0', port=8080, debug=True)

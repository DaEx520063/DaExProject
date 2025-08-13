#!/usr/bin/env python3
"""
สร้างฐานข้อมูลที่ใช้งานได้จริง
โดยมีข้อมูลเพียงพอสำหรับทุกเมนู แต่ยังคงขนาดไฟล์ไม่เกิน 25MB
"""

import sqlite3
import os
import shutil
from datetime import datetime

def check_backup_files():
    """ตรวจสอบไฟล์สำรองที่มีอยู่"""
    print("📦 ตรวจสอบไฟล์สำรองที่มีอยู่")
    print("=" * 50)
    
    backup_files = [f for f in os.listdir('.') if f.startswith('daex_system') and f.endswith('.db')]
    
    if not backup_files:
        print("❌ ไม่พบไฟล์สำรอง")
        return None
    
    print("📁 ไฟล์สำรองที่พบ:")
    for i, file in enumerate(backup_files, 1):
        file_size = os.path.getsize(file)
        file_size_mb = file_size / (1024 * 1024)
        print(f"  {i}. {file} ({file_size_mb:.2f} MB)")
    
    return backup_files

def create_working_database():
    """สร้างฐานข้อมูลที่ใช้งานได้จริง"""
    print("\n🔧 สร้างฐานข้อมูลที่ใช้งานได้จริง")
    print("=" * 50)
    
    try:
        # หาไฟล์สำรองที่มีข้อมูลครบถ้วน
        backup_files = [f for f in os.listdir('.') if f.startswith('daex_system_full_backup_') and f.endswith('.db')]
        
        if not backup_files:
            print("❌ ไม่พบไฟล์สำรองที่มีข้อมูลครบถ้วน")
            return False
        
        # เลือกไฟล์สำรองล่าสุด
        backup_files.sort(reverse=True)
        source_backup = backup_files[0]
        print(f"📦 ใช้ไฟล์สำรอง: {source_backup}")
        
        # สำรองฐานข้อมูลปัจจุบัน
        current_backup = f'daex_system_before_working_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2('daex_system.db', current_backup)
        print(f"📦 สำรองฐานข้อมูลปัจจุบันเป็น: {current_backup}")
        
        # เชื่อมต่อฐานข้อมูลสำรอง
        source_conn = sqlite3.connect(source_backup)
        source_cursor = source_conn.cursor()
        
        # สร้างฐานข้อมูลใหม่ที่ใช้งานได้
        working_db = 'daex_system_working.db'
        if os.path.exists(working_db):
            os.remove(working_db)
        
        working_conn = sqlite3.connect(working_db)
        working_cursor = working_conn.cursor()
        
        print("🏗️  สร้างฐานข้อมูลที่ใช้งานได้จริง...")
        
        # ตารางที่จำเป็นสำหรับการทำงานของระบบ
        essential_tables = [
            'users',                    # ผู้ใช้ระบบ (จำเป็นสำหรับ login)
            'employees',                # พนักงาน (จำเป็นสำหรับ employee-management)
            'piece_rates',              # อัตราเงินเดือน (จำเป็นสำหรับ spt-piece-rates)
            'menu_items',               # เมนูระบบ (จำเป็นสำหรับ navigation)
            'permissions',              # สิทธิ์การเข้าถึง (จำเป็นสำหรับ permissions)
            'vehicles',                 # ยานพาหนะ (จำเป็นสำหรับ vehicle-management)
            'work_records',             # บันทึกการทำงาน
            'leave_requests',           # คำขอลา
            'expenses',                 # ค่าใช้จ่าย
            'penalties',                # การลงโทษ
            'employee_requests',        # คำขอของพนักงาน
            'salary_rates',             # อัตราเงินเดือน
            'salaries',                 # ข้อมูลเงินเดือน
            'monthly_salary_data',      # ข้อมูลเงินเดือนประจำเดือน
        ]
        
        for table_name in essential_tables:
            try:
                # ดึงโครงสร้างตาราง
                source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                create_sql = source_cursor.fetchone()
                
                if create_sql and create_sql[0]:
                    print(f"  📋 สร้างตาราง: {table_name}")
                    working_cursor.execute(create_sql[0])
                    
                    # ดึงข้อมูลตัวอย่าง (จำกัดจำนวนที่เหมาะสม)
                    source_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    total_count = source_cursor.fetchone()[0]
                    
                    if total_count > 0:
                        # จำกัดจำนวนแถวตามประเภทตาราง
                        if table_name in ['users']:
                            limit = min(100, total_count)  # ผู้ใช้ 100 คน
                        elif table_name in ['employees']:
                            limit = min(300, total_count)  # พนักงาน 300 คน
                        elif table_name in ['permissions']:
                            limit = min(500, total_count)  # สิทธิ์ 500 รายการ
                        elif table_name in ['piece_rates', 'salary_rates']:
                            limit = min(100, total_count)  # อัตรา 100 รายการ
                        elif table_name in ['work_records', 'leave_requests', 'expenses', 'penalties']:
                            limit = min(200, total_count)  # ข้อมูลทั่วไป 200 แถว
                        elif table_name in ['monthly_salary_data', 'salaries']:
                            limit = min(150, total_count)  # ข้อมูลเงินเดือน 150 แถว
                        else:
                            limit = min(200, total_count)  # อื่นๆ 200 แถว
                        
                        source_cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                        rows = source_cursor.fetchall()
                        
                        if rows:
                            # ดึงชื่อคอลัมน์
                            source_cursor.execute(f"PRAGMA table_info({table_name})")
                            columns = [col[1] for col in source_cursor.fetchall()]
                            
                            # เขียนข้อมูล
                            for row in rows:
                                placeholders = ', '.join(['?' for _ in row])
                                working_cursor.execute(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})", row)
                            
                            print(f"    📊 คัดลอกข้อมูล {len(rows)} แถว (จากทั้งหมด {total_count:,} แถว)")
                        else:
                            print(f"    📊 ไม่มีข้อมูล")
                    else:
                        print(f"    📊 ไม่มีข้อมูล")
                
            except Exception as e:
                print(f"    ❌ ไม่สามารถสร้างตาราง {table_name}: {e}")
        
        # สร้างตารางที่จำเป็นอื่นๆ
        additional_tables = [
            'sqlite_sequence',          # สำหรับ auto-increment
        ]
        
        for table_name in additional_tables:
            try:
                source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                create_sql = source_cursor.fetchone()
                
                if create_sql and create_sql[0]:
                    print(f"  📋 สร้างตาราง: {table_name}")
                    working_cursor.execute(create_sql[0])
                    
                    # คัดลอกข้อมูล sequence
                    source_cursor.execute(f"SELECT * FROM {table_name}")
                    rows = source_cursor.fetchall()
                    
                    if rows:
                        source_cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in source_cursor.fetchall()]
                        
                        for row in rows:
                            placeholders = ', '.join(['?' for _ in row])
                            working_cursor.execute(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})", row)
                        
                        print(f"    📊 คัดลอกข้อมูล {len(rows)} แถว")
                
            except Exception as e:
                print(f"    ❌ ไม่สามารถสร้างตาราง {table_name}: {e}")
        
        working_conn.commit()
        working_conn.close()
        source_conn.close()
        
        # ตรวจสอบขนาด
        file_size = os.path.getsize(working_db)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n✅ สร้างฐานข้อมูลที่ใช้งานได้จริงสำเร็จ!")
        print(f"📁 ไฟล์: {working_db}")
        print(f"📊 ขนาด: {file_size_mb:.2f} MB")
        
        if file_size_mb <= 25:
            print(f"✅ ไฟล์มีขนาดเหมาะสมสำหรับอัปโหลด GitHub")
            
            # แทนที่ฐานข้อมูลเดิม
            os.remove('daex_system.db')
            os.rename(working_db, 'daex_system.db')
            print(f"🔄 แทนที่ฐานข้อมูลเดิมด้วยฐานข้อมูลที่ใช้งานได้จริง")
            
        else:
            print(f"⚠️  ไฟล์ยังมีขนาดใหญ่เกิน 25MB")
            print(f"💡 ลองลดจำนวนข้อมูลลงอีก")
        
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def test_database_functionality():
    """ทดสอบการทำงานของฐานข้อมูล"""
    print("\n🧪 ทดสอบการทำงานของฐานข้อมูล")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('daex_system.db')
        cursor = conn.cursor()
        
        # ทดสอบตารางหลัก
        test_tables = [
            ('users', 'ผู้ใช้ระบบ'),
            ('employees', 'พนักงาน'),
            ('piece_rates', 'อัตราเงินเดือน'),
            ('permissions', 'สิทธิ์การเข้าถึง'),
            ('vehicles', 'ยานพาหนะ'),
        ]
        
        print("📋 ทดสอบตารางหลัก:")
        for table_name, description in test_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  ✅ {description}: {count:,} รายการ")
            except Exception as e:
                print(f"  ❌ {description}: ไม่สามารถเข้าถึงได้ - {e}")
        
        # ทดสอบการ query ข้อมูล
        print(f"\n🔍 ทดสอบการ query ข้อมูล:")
        
        # ทดสอบ users
        try:
            cursor.execute("SELECT username, role FROM users LIMIT 5")
            users = cursor.fetchall()
            print(f"  👥 ผู้ใช้ตัวอย่าง: {len(users)} คน")
            for user in users[:3]:
                print(f"    - {user[0]} ({user[1]})")
        except Exception as e:
            print(f"  ❌ ไม่สามารถดึงข้อมูลผู้ใช้: {e}")
        
        # ทดสอบ employees
        try:
            cursor.execute("SELECT name, position FROM employees LIMIT 5")
            employees = cursor.fetchall()
            print(f"  👷 พนักงานตัวอย่าง: {len(employees)} คน")
            for emp in employees[:3]:
                print(f"    - {emp[0]} ({emp[1]})")
        except Exception as e:
            print(f"  ❌ ไม่สามารถดึงข้อมูลพนักงาน: {e}")
        
        # ทดสอบ piece_rates
        try:
            cursor.execute("SELECT COUNT(*) FROM piece_rates")
            count = cursor.fetchone()[0]
            print(f"  💰 อัตราเงินเดือน: {count} รายการ")
        except Exception as e:
            print(f"  ❌ ไม่สามารถดึงข้อมูลอัตราเงินเดือน: {e}")
        
        conn.close()
        
        print(f"\n✅ การทดสอบเสร็จสิ้น")
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการทดสอบ: {e}")
        return False

def main():
    """ฟังก์ชันหลัก"""
    print("🚀 สร้างฐานข้อมูลที่ใช้งานได้จริง")
    print("=" * 60)
    
    while True:
        print("\nเลือกการดำเนินการ:")
        print("1. ตรวจสอบไฟล์สำรอง")
        print("2. สร้างฐานข้อมูลที่ใช้งานได้จริง")
        print("3. ทดสอบการทำงานของฐานข้อมูล")
        print("4. ออกจากโปรแกรม")
        
        try:
            choice = input("\n👉 กรุณาเลือก (1-4): ").strip()
            
            if choice == "1":
                check_backup_files()
            elif choice == "2":
                create_working_database()
            elif choice == "3":
                test_database_functionality()
            elif choice == "4":
                print("👋 ออกจากโปรแกรม")
                break
            else:
                print("❌ กรุณาเลือก 1, 2, 3, หรือ 4")
                
        except KeyboardInterrupt:
            print("\n\n👋 ออกจากโปรแกรม")
            break
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    main()

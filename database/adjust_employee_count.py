#!/usr/bin/env python3
"""
ปรับจำนวนพนักงานให้เหมาะสม
โดยเพิ่มจำนวนพนักงานแต่ยังคงขนาดไฟล์ไม่เกิน 25MB
"""

import sqlite3
import os
import shutil
from datetime import datetime

def check_current_data():
    """ตรวจสอบข้อมูลปัจจุบัน"""
    print("📊 ตรวจสอบข้อมูลปัจจุบัน")
    print("=" * 50)
    
    if not os.path.exists('daex_system.db'):
        print("❌ ไม่พบไฟล์ daex_system.db")
        return False
    
    conn = sqlite3.connect('daex_system.db')
    cursor = conn.cursor()
    
    # ตรวจสอบขนาดไฟล์
    file_size = os.path.getsize('daex_system.db')
    file_size_mb = file_size / (1024 * 1024)
    print(f"📁 ขนาดไฟล์: {file_size_mb:.2f} MB")
    
    # ตรวจสอบจำนวนตาราง
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"🏗️  จำนวนตาราง: {len(tables)} ตาราง")
    print("\n📋 รายละเอียดตารางหลัก:")
    
    important_tables = ['users', 'employees', 'piece_rates', 'menu_items', 'permissions']
    total_rows = 0
    
    for table_name in important_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            total_rows += row_count
            print(f"  📊 {table_name}: {row_count:,} แถว")
        except:
            print(f"  ❌ {table_name}: ไม่มีอยู่")
    
    print(f"\n📈 จำนวนแถวรวมในตารางหลัก: {total_rows:,} แถว")
    
    conn.close()
    return True

def restore_employees_from_backup():
    """กู้คืนข้อมูลพนักงานจากไฟล์สำรอง"""
    print("\n🔄 กู้คืนข้อมูลพนักงานจากไฟล์สำรอง")
    print("=" * 50)
    
    # หาไฟล์สำรองล่าสุด
    backup_files = [f for f in os.listdir('.') if f.startswith('daex_system_full_backup_') and f.endswith('.db')]
    
    if not backup_files:
        print("❌ ไม่พบไฟล์สำรอง")
        return False
    
    # เลือกไฟล์สำรองล่าสุด
    backup_files.sort(reverse=True)
    latest_backup = backup_files[0]
    print(f"📦 ไฟล์สำรองล่าสุด: {latest_backup}")
    
    try:
        # สำรองฐานข้อมูลปัจจุบัน
        current_backup = f'daex_system_before_restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2('daex_system.db', current_backup)
        print(f"📦 สำรองฐานข้อมูลปัจจุบันเป็น: {current_backup}")
        
        # เชื่อมต่อฐานข้อมูลสำรอง
        backup_conn = sqlite3.connect(latest_backup)
        backup_cursor = backup_conn.cursor()
        
        # เชื่อมต่อฐานข้อมูลปัจจุบัน
        current_conn = sqlite3.connect('daex_system.db')
        current_cursor = current_conn.cursor()
        
        # ตรวจสอบจำนวนพนักงานในไฟล์สำรอง
        backup_cursor.execute("SELECT COUNT(*) FROM employees")
        backup_employee_count = backup_cursor.fetchone()[0]
        print(f"📊 จำนวนพนักงานในไฟล์สำรอง: {backup_employee_count:,} คน")
        
        # ตรวจสอบจำนวนพนักงานในฐานข้อมูลปัจจุบัน
        current_cursor.execute("SELECT COUNT(*) FROM employees")
        current_employee_count = current_cursor.fetchone()[0]
        print(f"📊 จำนวนพนักงานในฐานข้อมูลปัจจุบัน: {current_employee_count:,} คน")
        
        # ลบข้อมูลพนักงานปัจจุบัน
        current_cursor.execute("DELETE FROM employees")
        print(f"🗑️  ลบข้อมูลพนักงานปัจจุบัน {current_employee_count:,} คน")
        
        # คัดลอกข้อมูลพนักงานจากไฟล์สำรอง (จำกัดจำนวน)
        target_employee_count = 200  # ตั้งเป้าหมาย 200 คน
        
        if backup_employee_count > target_employee_count:
            print(f"📋 คัดลอกข้อมูลพนักงาน {target_employee_count:,} คน จากไฟล์สำรอง")
            backup_cursor.execute(f"SELECT * FROM employees LIMIT {target_employee_count}")
        else:
            print(f"📋 คัดลอกข้อมูลพนักงานทั้งหมด {backup_employee_count:,} คน จากไฟล์สำรอง")
            backup_cursor.execute("SELECT * FROM employees")
        
        employees = backup_cursor.fetchall()
        
        if employees:
            # ดึงโครงสร้างตาราง
            backup_cursor.execute("PRAGMA table_info(employees)")
            columns = [col[1] for col in backup_cursor.fetchall()]
            
            # เพิ่มข้อมูลพนักงาน
            for employee in employees:
                placeholders = ', '.join(['?' for _ in employee])
                current_cursor.execute(f"INSERT INTO employees ({', '.join(columns)}) VALUES ({placeholders})", employee)
            
            print(f"✅ เพิ่มข้อมูลพนักงานสำเร็จ: {len(employees):,} คน")
        else:
            print("❌ ไม่มีข้อมูลพนักงานในไฟล์สำรอง")
        
        # อัปเดต sqlite_sequence
        current_cursor.execute("DELETE FROM sqlite_sequence WHERE name='employees'")
        current_cursor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES (?, ?)", ('employees', len(employees)))
        
        current_conn.commit()
        current_conn.close()
        backup_conn.close()
        
        # ตรวจสอบขนาดไฟล์
        file_size = os.path.getsize('daex_system.db')
        file_size_mb = file_size / (1024 * 1024)
        print(f"\n📁 ขนาดไฟล์หลังกู้คืน: {file_size_mb:.2f} MB")
        
        if file_size_mb <= 25:
            print(f"✅ ไฟล์มีขนาดเหมาะสมสำหรับอัปโหลด GitHub")
        else:
            print(f"⚠️  ไฟล์ยังมีขนาดใหญ่เกิน 25MB")
            print("💡 ต้องลดจำนวนพนักงานลงอีก")
        
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def create_balanced_database():
    """สร้างฐานข้อมูลที่สมดุล"""
    print("\n⚖️  สร้างฐานข้อมูลที่สมดุล")
    print("=" * 50)
    
    try:
        # สำรองฐานข้อมูลเดิม
        backup_file = f'daex_system_before_balance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2('daex_system.db', backup_file)
        print(f"📦 สำรองฐานข้อมูลเดิมเป็น: {backup_file}")
        
        # เชื่อมต่อฐานข้อมูลหลัก
        conn = sqlite3.connect('daex_system.db')
        cursor = conn.cursor()
        
        # สร้างฐานข้อมูลใหม่ที่สมดุล
        balanced_db = 'daex_system_balanced.db'
        if os.path.exists(balanced_db):
            os.remove(balanced_db)
        
        balanced_conn = sqlite3.connect(balanced_db)
        balanced_cursor = balanced_conn.cursor()
        
        print("🏗️  สร้างฐานข้อมูลที่สมดุล...")
        
        # ตารางที่สำคัญ
        important_tables = [
            'users',           # ผู้ใช้ระบบ
            'employees',       # พนักงาน
            'piece_rates',     # อัตราเงินเดือน
            'menu_items',      # เมนูระบบ
            'permissions',     # สิทธิ์การเข้าถึง
            'vehicles',        # ยานพาหนะ
            'work_records',    # บันทึกการทำงาน
            'leave_requests',  # คำขอลา
            'expenses',        # ค่าใช้จ่าย
            'penalties'        # การลงโทษ
        ]
        
        for table_name in important_tables:
            try:
                # ดึงโครงสร้างตาราง
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                create_sql = cursor.fetchone()
                
                if create_sql and create_sql[0]:
                    print(f"  📋 สร้างตาราง: {table_name}")
                    balanced_cursor.execute(create_sql[0])
                    
                    # ดึงข้อมูลตัวอย่าง (จำกัดจำนวนที่สมดุล)
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    total_count = cursor.fetchone()[0]
                    
                    if total_count > 0:
                        # จำกัดจำนวนแถวตามประเภทตาราง
                        if table_name in ['users']:
                            limit = min(50, total_count)  # ผู้ใช้ 50 คน
                        elif table_name in ['employees']:
                            limit = min(150, total_count)  # พนักงาน 150 คน
                        elif table_name in ['permissions']:
                            limit = min(200, total_count)  # สิทธิ์ 200 รายการ
                        elif table_name in ['work_records', 'leave_requests', 'expenses', 'penalties']:
                            limit = min(100, total_count)  # ข้อมูลทั่วไป 100 แถว
                        else:
                            limit = min(150, total_count)  # อื่นๆ 150 แถว
                        
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                        rows = cursor.fetchall()
                        
                        if rows:
                            # ดึงชื่อคอลัมน์
                            cursor.execute(f"PRAGMA table_info({table_name})")
                            columns = [col[1] for col in cursor.fetchall()]
                            
                            # เขียนข้อมูล
                            for row in rows:
                                placeholders = ', '.join(['?' for _ in row])
                                balanced_cursor.execute(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})", row)
                            
                            print(f"    📊 คัดลอกข้อมูล {len(rows)} แถว (จากทั้งหมด {total_count:,} แถว)")
                        else:
                            print(f"    📊 ไม่มีข้อมูล")
                    else:
                        print(f"    📊 ไม่มีข้อมูล")
                
            except Exception as e:
                print(f"    ❌ ไม่สามารถสร้างตาราง {table_name}: {e}")
        
        balanced_conn.commit()
        balanced_conn.close()
        conn.close()
        
        # ตรวจสอบขนาด
        file_size = os.path.getsize(balanced_db)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n✅ สร้างฐานข้อมูลที่สมดุลสำเร็จ!")
        print(f"📁 ไฟล์: {balanced_db}")
        print(f"📊 ขนาด: {file_size_mb:.2f} MB")
        
        if file_size_mb <= 25:
            print(f"✅ ไฟล์มีขนาดเหมาะสมสำหรับอัปโหลด GitHub")
            
            # แทนที่ฐานข้อมูลเดิม
            os.remove('daex_system.db')
            os.rename(balanced_db, 'daex_system.db')
            print(f"🔄 แทนที่ฐานข้อมูลเดิมด้วยฐานข้อมูลที่สมดุล")
            
        else:
            print(f"⚠️  ไฟล์ยังมีขนาดใหญ่เกิน 25MB")
            print(f"💡 ลองลดจำนวนข้อมูลลงอีก")
        
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def main():
    """ฟังก์ชันหลัก"""
    print("🚀 ปรับจำนวนพนักงานให้เหมาะสม")
    print("=" * 60)
    
    while True:
        print("\nเลือกการดำเนินการ:")
        print("1. ตรวจสอบข้อมูลปัจจุบัน")
        print("2. กู้คืนข้อมูลพนักงานจากไฟล์สำรอง")
        print("3. สร้างฐานข้อมูลที่สมดุล")
        print("4. ออกจากโปรแกรม")
        
        try:
            choice = input("\n👉 กรุณาเลือก (1-4): ").strip()
            
            if choice == "1":
                check_current_data()
            elif choice == "2":
                restore_employees_from_backup()
            elif choice == "3":
                create_balanced_database()
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

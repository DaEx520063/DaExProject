#!/usr/bin/env python3
"""
แก้ไขฐานข้อมูลสำหรับ Heroku
โดยสร้างฐานข้อมูลที่มีข้อมูลเพียงพอสำหรับการทำงานจริง
"""

import sqlite3
import os
import shutil
from datetime import datetime

def build_heroku_database():
    """สร้างฐานข้อมูลสำหรับ Heroku"""
    print("🔧 สร้างฐานข้อมูลสำหรับ Heroku")
    print("=" * 50)
    
    try:
        # หาไฟล์สำรองที่มีข้อมูลครบถ้วน
        backup_files = [f for f in os.listdir('.') if f.startswith('daex_system_full_backup_') and f.endswith('.db')]
        
        if not backup_files:
            print("❌ ไม่พบไฟล์สำรองที่มีข้อมูลครบถ้วน")
            print("💡 ต้องมีไฟล์ daex_system_full_backup_*.db")
            return False
        
        # เลือกไฟล์สำรองล่าสุด
        backup_files.sort(reverse=True)
        source_backup = backup_files[0]
        print(f"📦 ใช้ไฟล์สำรอง: {source_backup}")
        
        # สำรองฐานข้อมูลปัจจุบัน
        current_backup = f'daex_system_before_heroku_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2('daex_system.db', current_backup)
        print(f"📦 สำรองฐานข้อมูลปัจจุบันเป็น: {current_backup}")
        
        # เชื่อมต่อฐานข้อมูลสำรอง
        source_conn = sqlite3.connect(source_backup)
        source_cursor = source_conn.cursor()
        
        # สร้างฐานข้อมูลใหม่สำหรับ Heroku
        heroku_db = 'daex_system_heroku.db'
        if os.path.exists(heroku_db):
            os.remove(heroku_db)
        
        heroku_conn = sqlite3.connect(heroku_db)
        heroku_cursor = heroku_conn.cursor()
        
        print("🏗️  สร้างฐานข้อมูลสำหรับ Heroku...")
        
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
            'vehicle_daily_usage',      # การใช้งานยานพาหนะประจำวัน
            'vehicle_fuel_usage',       # การใช้เชื้อเพลิง
            'vehicle_maintenance',      # การบำรุงรักษา
            'vehicle_weekly_checks',    # การตรวจสอบรายสัปดาห์
        ]
        
        total_rows_copied = 0
        
        for table_name in essential_tables:
            try:
                # ดึงโครงสร้างตาราง
                source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                create_sql = source_cursor.fetchone()
                
                if create_sql and create_sql[0]:
                    print(f"  📋 สร้างตาราง: {table_name}")
                    heroku_cursor.execute(create_sql[0])
                    
                    # ดึงข้อมูลตัวอย่าง (จำกัดจำนวนที่เหมาะสม)
                    source_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    total_count = source_cursor.fetchone()[0]
                    
                    if total_count > 0:
                        # จำกัดจำนวนแถวตามประเภทตาราง
                        if table_name in ['users']:
                            limit = min(150, total_count)  # ผู้ใช้ 150 คน
                        elif table_name in ['employees']:
                            limit = min(500, total_count)  # พนักงาน 500 คน
                        elif table_name in ['permissions']:
                            limit = min(800, total_count)  # สิทธิ์ 800 รายการ
                        elif table_name in ['piece_rates', 'salary_rates']:
                            limit = min(200, total_count)  # อัตรา 200 รายการ
                        elif table_name in ['work_records', 'leave_requests', 'expenses', 'penalties']:
                            limit = min(300, total_count)  # ข้อมูลทั่วไป 300 แถว
                        elif table_name in ['monthly_salary_data', 'salaries']:
                            limit = min(250, total_count)  # ข้อมูลเงินเดือน 250 แถว
                        elif table_name in ['vehicles']:
                            limit = min(50, total_count)   # ยานพาหนะ 50 คัน
                        elif table_name in ['vehicle_daily_usage', 'vehicle_fuel_usage', 'vehicle_maintenance', 'vehicle_weekly_checks']:
                            limit = min(100, total_count)  # ข้อมูลยานพาหนะ 100 แถว
                        else:
                            limit = min(300, total_count)  # อื่นๆ 300 แถว
                        
                        source_cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                        rows = source_cursor.fetchall()
                        
                        if rows:
                            # ดึงชื่อคอลัมน์
                            source_cursor.execute(f"PRAGMA table_info({table_name})")
                            columns = [col[1] for col in source_cursor.fetchall()]
                            
                            # เขียนข้อมูล
                            for row in rows:
                                placeholders = ', '.join(['?' for _ in row])
                                heroku_cursor.execute(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})", row)
                            
                            total_rows_copied += len(rows)
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
                    heroku_cursor.execute(create_sql[0])
                    
                    # คัดลอกข้อมูล sequence
                    source_cursor.execute(f"SELECT * FROM {table_name}")
                    rows = source_cursor.fetchall()
                    
                    if rows:
                        source_cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [col[1] for col in source_cursor.fetchall()]
                        
                        for row in rows:
                            placeholders = ', '.join(['?' for _ in row])
                            heroku_cursor.execute(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})", row)
                        
                        print(f"    📊 คัดลอกข้อมูล {len(rows)} แถว")
                
            except Exception as e:
                print(f"    ❌ ไม่สามารถสร้างตาราง {table_name}: {e}")
        
        heroku_conn.commit()
        heroku_conn.close()
        source_conn.close()
        
        # ตรวจสอบขนาด
        file_size = os.path.getsize(heroku_db)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n✅ สร้างฐานข้อมูลสำหรับ Heroku สำเร็จ!")
        print(f"📁 ไฟล์: {heroku_db}")
        print(f"📊 ขนาด: {file_size_mb:.2f} MB")
        print(f"📈 จำนวนแถวที่คัดลอก: {total_rows_copied:,} แถว")
        
        if file_size_mb <= 25:
            print(f"✅ ไฟล์มีขนาดเหมาะสมสำหรับอัปโหลด GitHub")
            
            # แทนที่ฐานข้อมูลเดิม
            os.remove('daex_system.db')
            os.rename(heroku_db, 'daex_system.db')
            print(f"🔄 แทนที่ฐานข้อมูลเดิมด้วยฐานข้อมูลสำหรับ Heroku")
            
            print(f"\n🚀 ตอนนี้คุณสามารถ:")
            print(f"  1. อัพโหลดไฟล์ daex_system.db ขึ้น GitHub")
            print(f"  2. Deploy ไปยัง Heroku")
            print(f"  3. ทุกเมนูควรทำงานได้ปกติ")
            
        else:
            print(f"⚠️  ไฟล์ยังมีขนาดใหญ่เกิน 25MB")
            print(f"💡 ลองลดจำนวนข้อมูลลงอีก")
        
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def verify_database():
    """ตรวจสอบฐานข้อมูลที่สร้าง"""
    print("\n🔍 ตรวจสอบฐานข้อมูลที่สร้าง")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('daex_system.db')
        cursor = conn.cursor()
        
        # ตรวจสอบตารางหลัก
        test_tables = [
            ('users', 'ผู้ใช้ระบบ'),
            ('employees', 'พนักงาน'),
            ('piece_rates', 'อัตราเงินเดือน'),
            ('permissions', 'สิทธิ์การเข้าถึง'),
            ('vehicles', 'ยานพาหนะ'),
            ('vehicle_daily_usage', 'การใช้งานยานพาหนะ'),
            ('vehicle_fuel_usage', 'การใช้เชื้อเพลิง'),
            ('vehicle_maintenance', 'การบำรุงรักษา'),
        ]
        
        print("📋 ตรวจสอบตารางหลัก:")
        total_rows = 0
        for table_name, description in test_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                total_rows += count
                print(f"  ✅ {description}: {count:,} รายการ")
            except Exception as e:
                print(f"  ❌ {description}: ไม่สามารถเข้าถึงได้ - {e}")
        
        print(f"\n📈 จำนวนแถวรวมในตารางหลัก: {total_rows:,} แถว")
        
        # ตรวจสอบขนาดไฟล์
        file_size = os.path.getsize('daex_system.db')
        file_size_mb = file_size / (1024 * 1024)
        print(f"📁 ขนาดไฟล์: {file_size_mb:.2f} MB")
        
        if file_size_mb <= 25:
            print(f"✅ ไฟล์มีขนาดเหมาะสมสำหรับ GitHub และ Heroku")
        else:
            print(f"⚠️  ไฟล์ยังมีขนาดใหญ่เกิน 25MB")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการตรวจสอบ: {e}")
        return False

if __name__ == "__main__":
    print("🚀 แก้ไขฐานข้อมูลสำหรับ Heroku")
    print("=" * 60)
    
    # สร้างฐานข้อมูลสำหรับ Heroku
    if build_heroku_database():
        print("\n" + "=" * 60)
        # ตรวจสอบฐานข้อมูล
        verify_database()
    else:
        print("❌ ไม่สามารถสร้างฐานข้อมูลได้")
    
    print("\n👋 เสร็จสิ้น")

#!/usr/bin/env python3
"""
ปรับปรุงและลดขนาดฐานข้อมูล daex_system.db
โดยใช้ VACUUM และการจัดการข้อมูล
"""

import sqlite3
import os
import shutil
from datetime import datetime

def check_database_size():
    """ตรวจสอบขนาดฐานข้อมูลปัจจุบัน"""
    print("📊 ตรวจสอบขนาดฐานข้อมูลปัจจุบัน")
    print("=" * 50)
    
    if not os.path.exists('daex_system.db'):
        print("❌ ไม่พบไฟล์ daex_system.db")
        return False
    
    # ขนาดไฟล์
    file_size = os.path.getsize('daex_system.db')
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"📁 ไฟล์: daex_system.db")
    print(f"📊 ขนาด: {file_size_mb:.2f} MB")
    
    # เชื่อมต่อฐานข้อมูล
    conn = sqlite3.connect('daex_system.db')
    cursor = conn.cursor()
    
    # ตรวจสอบจำนวนตาราง
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"🏗️  จำนวนตาราง: {len(tables)} ตาราง")
    print("\n📋 รายละเอียดตาราง:")
    
    total_rows = 0
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            total_rows += row_count
            print(f"  📊 {table_name}: {row_count:,} แถว")
        except:
            print(f"  ❌ {table_name}: ไม่สามารถนับได้")
    
    print(f"\n📈 จำนวนแถวรวม: {total_rows:,} แถว")
    
    # ตรวจสอบข้อมูลในตารางที่ใหญ่
    print(f"\n🔍 ตารางที่มีข้อมูลมาก:")
    table_sizes = []
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            if row_count > 1000:  # แสดงเฉพาะตารางที่มีข้อมูลมาก
                table_sizes.append((table_name, row_count))
        except:
            pass
    
    # เรียงลำดับตามจำนวนข้อมูล
    table_sizes.sort(key=lambda x: x[1], reverse=True)
    
    for table_name, row_count in table_sizes[:10]:  # แสดง 10 อันดับแรก
        print(f"  📊 {table_name}: {row_count:,} แถว")
    
    conn.close()
    
    if file_size_mb > 25:
        print(f"\n⚠️  ไฟล์ยังมีขนาดใหญ่เกิน 25MB (GitHub limit)")
        print("💡 ต้องทำการ VACUUM และลดข้อมูลลงอีก")
    else:
        print(f"\n✅ ไฟล์มีขนาดเหมาะสมสำหรับอัปโหลด GitHub")
    
    return True

def optimize_database():
    """ปรับปรุงฐานข้อมูลด้วย VACUUM"""
    print("\n🔧 ปรับปรุงฐานข้อมูลด้วย VACUUM")
    print("=" * 50)
    
    try:
        # สำรองฐานข้อมูล
        backup_file = f'daex_system_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2('daex_system.db', backup_file)
        print(f"📦 สำรองฐานข้อมูลเป็น: {backup_file}")
        
        # เชื่อมต่อฐานข้อมูล
        conn = sqlite3.connect('daex_system.db')
        cursor = conn.cursor()
        
        # ตรวจสอบขนาดก่อน VACUUM
        file_size_before = os.path.getsize('daex_system.db')
        file_size_before_mb = file_size_before / (1024 * 1024)
        print(f"📊 ขนาดก่อน VACUUM: {file_size_before_mb:.2f} MB")
        
        # รัน VACUUM
        print("🔄 กำลังรัน VACUUM...")
        cursor.execute("VACUUM")
        
        # ตรวจสอบขนาดหลัง VACUUM
        file_size_after = os.path.getsize('daex_system.db')
        file_size_after_mb = file_size_after / (1024 * 1024)
        
        # คำนวณการลดขนาด
        reduction = file_size_before - file_size_after
        reduction_mb = reduction / (1024 * 1024)
        reduction_percent = (reduction / file_size_before) * 100
        
        print(f"📊 ขนาดหลัง VACUUM: {file_size_after_mb:.2f} MB")
        print(f"📉 ลดขนาดลง: {reduction_mb:.2f} MB ({reduction_percent:.1f}%)")
        
        conn.close()
        
        if file_size_after_mb <= 25:
            print(f"\n✅ ไฟล์มีขนาดเหมาะสมสำหรับอัปโหลด GitHub แล้ว!")
        else:
            print(f"\n⚠️  ไฟล์ยังมีขนาดใหญ่เกิน 25MB")
            print("💡 ต้องลดข้อมูลลงอีก")
        
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def create_minimal_database():
    """สร้างฐานข้อมูลขนาดเล็กที่สุด"""
    print("\n🔧 สร้างฐานข้อมูลขนาดเล็กที่สุด")
    print("=" * 50)
    
    try:
        # สำรองฐานข้อมูลเดิม
        backup_file = f'daex_system_full_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2('daex_system.db', backup_file)
        print(f"📦 สำรองฐานข้อมูลเดิมเป็น: {backup_file}")
        
        # เชื่อมต่อฐานข้อมูลหลัก
        conn = sqlite3.connect('daex_system.db')
        cursor = conn.cursor()
        
        # สร้างฐานข้อมูลใหม่ขนาดเล็ก
        minimal_db = 'daex_system_minimal.db'
        if os.path.exists(minimal_db):
            os.remove(minimal_db)
        
        minimal_conn = sqlite3.connect(minimal_db)
        minimal_cursor = minimal_conn.cursor()
        
        print("🏗️  สร้างฐานข้อมูลขนาดเล็กที่สุด...")
        
        # ตารางที่จำเป็นที่สุด
        essential_tables = [
            'users',           # ผู้ใช้ระบบ (จำเป็น)
            'employees',       # พนักงาน (จำเป็น)
            'piece_rates',     # อัตราเงินเดือน (จำเป็น)
            'menu_items',      # เมนูระบบ (จำเป็น)
            'permissions',     # สิทธิ์การเข้าถึง (จำเป็น)
        ]
        
        for table_name in essential_tables:
            try:
                # ดึงโครงสร้างตาราง
                cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                create_sql = cursor.fetchone()
                
                if create_sql and create_sql[0]:
                    print(f"  📋 สร้างตาราง: {table_name}")
                    minimal_cursor.execute(create_sql[0])
                    
                    # ดึงข้อมูลตัวอย่าง (จำกัดจำนวนมาก)
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    total_count = cursor.fetchone()[0]
                    
                    if total_count > 0:
                        # จำกัดจำนวนแถวให้เหลือน้อยที่สุด
                        if table_name in ['users']:
                            limit = min(10, total_count)  # ผู้ใช้ 10 คน
                        elif table_name in ['employees']:
                            limit = min(20, total_count)  # พนักงาน 20 คน
                        elif table_name in ['permissions']:
                            limit = min(50, total_count)  # สิทธิ์ 50 รายการ
                        else:
                            limit = min(25, total_count)  # อื่นๆ 25 รายการ
                        
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                        rows = cursor.fetchall()
                        
                        if rows:
                            # ดึงชื่อคอลัมน์
                            cursor.execute(f"PRAGMA table_info({table_name})")
                            columns = [col[1] for col in cursor.fetchall()]
                            
                            # เขียนข้อมูล
                            for row in rows:
                                placeholders = ', '.join(['?' for _ in row])
                                minimal_cursor.execute(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})", row)
                            
                            print(f"    📊 คัดลอกข้อมูล {len(rows)} แถว (จากทั้งหมด {total_count:,} แถว)")
                        else:
                            print(f"    📊 ไม่มีข้อมูล")
                    else:
                        print(f"    📊 ไม่มีข้อมูล")
                
            except Exception as e:
                print(f"    ❌ ไม่สามารถสร้างตาราง {table_name}: {e}")
        
        minimal_conn.commit()
        minimal_conn.close()
        conn.close()
        
        # ตรวจสอบขนาด
        file_size = os.path.getsize(minimal_db)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n✅ สร้างฐานข้อมูลขนาดเล็กที่สุดสำเร็จ!")
        print(f"📁 ไฟล์: {minimal_db}")
        print(f"📊 ขนาด: {file_size_mb:.2f} MB")
        
        if file_size_mb <= 25:
            print(f"✅ ไฟล์มีขนาดเหมาะสมสำหรับอัปโหลด GitHub")
            
            # แทนที่ฐานข้อมูลเดิม
            os.remove('daex_system.db')
            os.rename(minimal_db, 'daex_system.db')
            print(f"🔄 แทนที่ฐานข้อมูลเดิมด้วยฐานข้อมูลขนาดเล็กที่สุด")
            
        else:
            print(f"⚠️  ไฟล์ยังมีขนาดใหญ่เกิน 25MB")
            print(f"💡 ลองลดจำนวนข้อมูลลงอีก")
        
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def main():
    """ฟังก์ชันหลัก"""
    print("🚀 ปรับปรุงฐานข้อมูลสำหรับ GitHub")
    print("=" * 60)
    
    while True:
        print("\nเลือกการดำเนินการ:")
        print("1. ตรวจสอบขนาดฐานข้อมูลปัจจุบัน")
        print("2. ปรับปรุงฐานข้อมูลด้วย VACUUM")
        print("3. สร้างฐานข้อมูลขนาดเล็กที่สุด")
        print("4. ออกจากโปรแกรม")
        
        try:
            choice = input("\n👉 กรุณาเลือก (1-4): ").strip()
            
            if choice == "1":
                check_database_size()
            elif choice == "2":
                optimize_database()
            elif choice == "3":
                create_minimal_database()
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

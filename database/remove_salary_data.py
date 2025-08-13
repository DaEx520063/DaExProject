#!/usr/bin/env python3
"""
ลบเฉพาะข้อมูลเงินเดือนประจำเดือนที่มีจำนวนมาก
โดยเก็บข้อมูลอื่นๆ ไว้ทั้งหมด
"""

import sqlite3
import os
import shutil
from datetime import datetime

def check_salary_tables():
    """ตรวจสอบตารางที่เกี่ยวข้องกับเงินเดือน"""
    print("💰 ตรวจสอบตารางที่เกี่ยวข้องกับเงินเดือน")
    print("=" * 50)
    
    if not os.path.exists('daex_system.db'):
        print("❌ ไม่พบไฟล์ daex_system.db")
        return False
    
    conn = sqlite3.connect('daex_system.db')
    cursor = conn.cursor()
    
    # หาตารางที่เกี่ยวข้องกับเงินเดือน
    salary_related_tables = []
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = cursor.fetchall()
    
    for table in all_tables:
        table_name = table[0].lower()
        if any(keyword in table_name for keyword in ['salary', 'monthly', 'payment', 'unmatched']):
            salary_related_tables.append(table[0])
    
    print(f"🔍 พบตารางที่เกี่ยวข้องกับเงินเดือน {len(salary_related_tables)} ตาราง:")
    
    total_salary_rows = 0
    for table_name in salary_related_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            total_salary_rows += row_count
            print(f"  📊 {table_name}: {row_count:,} แถว")
        except Exception as e:
            print(f"  ❌ {table_name}: ไม่สามารถนับได้ - {e}")
    
    print(f"\n📈 จำนวนแถวรวมในตารางเงินเดือน: {total_salary_rows:,} แถว")
    
    # ตรวจสอบขนาดไฟล์
    file_size = os.path.getsize('daex_system.db')
    file_size_mb = file_size / (1024 * 1024)
    print(f"📁 ขนาดไฟล์ปัจจุบัน: {file_size_mb:.2f} MB")
    
    conn.close()
    return salary_related_tables

def remove_salary_data():
    """ลบข้อมูลในตารางเงินเดือนทั้งหมด"""
    print("\n🗑️  ลบข้อมูลในตารางเงินเดือน")
    print("=" * 50)
    
    try:
        # สำรองฐานข้อมูล
        backup_file = f'daex_system_before_salary_removal_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2('daex_system.db', backup_file)
        print(f"📦 สำรองฐานข้อมูลเป็น: {backup_file}")
        
        # ตรวจสอบขนาดก่อนลบ
        file_size_before = os.path.getsize('daex_system.db')
        file_size_before_mb = file_size_before / (1024 * 1024)
        print(f"📊 ขนาดก่อนลบ: {file_size_before_mb:.2f} MB")
        
        conn = sqlite3.connect('daex_system.db')
        cursor = conn.cursor()
        
        # ตารางที่เกี่ยวข้องกับเงินเดือน
        salary_tables = [
            'monthly_salary_data',           # ข้อมูลเงินเดือนประจำเดือน
            'monthly_salary_calculation',    # การคำนวณเงินเดือน
            'unmatched_salary_records',      # บันทึกเงินเดือนที่ไม่ตรงกัน
            'salary_uploads',                # อัปโหลดข้อมูลเงินเดือน
            'salary_confirmation',           # การยืนยันเงินเดือน
            'salary_payment_confirmations',  # การยืนยันการจ่ายเงินเดือน
            'payment_confirmations',         # การยืนยันการจ่ายเงิน
            'employee_salary_records',       # บันทึกเงินเดือนพนักงาน
        ]
        
        total_deleted_rows = 0
        
        for table_name in salary_tables:
            try:
                # ตรวจสอบว่าตารางมีอยู่หรือไม่
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                if cursor.fetchone():
                    # นับจำนวนแถวก่อนลบ
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    
                    if row_count > 0:
                        print(f"  🗑️  ลบข้อมูลในตาราง: {table_name}")
                        print(f"    📊 จำนวนแถวที่จะลบ: {row_count:,} แถว")
                        
                        # ลบข้อมูลทั้งหมดในตาราง
                        cursor.execute(f"DELETE FROM {table_name}")
                        deleted_rows = cursor.rowcount
                        total_deleted_rows += deleted_rows
                        
                        print(f"    ✅ ลบสำเร็จ: {deleted_rows:,} แถว")
                    else:
                        print(f"  📊 ตาราง {table_name}: ไม่มีข้อมูล")
                else:
                    print(f"  ❌ ตาราง {table_name}: ไม่มีอยู่")
                    
            except Exception as e:
                print(f"  ❌ ไม่สามารถลบข้อมูลในตาราง {table_name}: {e}")
        
        # ลบข้อมูลในตารางอื่นๆ ที่อาจเกี่ยวข้อง
        other_salary_tables = [
            'salaries',           # ข้อมูลเงินเดือนทั่วไป
            'salary_rates',       # อัตราเงินเดือน
        ]
        
        for table_name in other_salary_tables:
            try:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                if cursor.fetchone():
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    
                    if row_count > 100:  # ลบเฉพาะถ้ามีข้อมูลมาก
                        print(f"  🗑️  ลบข้อมูลส่วนเกินในตาราง: {table_name}")
                        print(f"    📊 จำนวนแถวทั้งหมด: {row_count:,} แถว")
                        
                        # เก็บเฉพาะ 100 แถวแรก
                        cursor.execute(f"DELETE FROM {table_name} WHERE rowid > 100")
                        deleted_rows = cursor.rowcount
                        total_deleted_rows += deleted_rows
                        
                        print(f"    ✅ ลบส่วนเกินสำเร็จ: {deleted_rows:,} แถว")
                        print(f"    📊 เหลือข้อมูล: 100 แถว")
                        
            except Exception as e:
                print(f"  ❌ ไม่สามารถลบข้อมูลในตาราง {table_name}: {e}")
        
        conn.commit()
        conn.close()
        
        # รัน VACUUM เพื่อลดขนาดไฟล์
        print("\n🔄 กำลังรัน VACUUM เพื่อลดขนาดไฟล์...")
        conn = sqlite3.connect('daex_system.db')
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        conn.close()
        
        # ตรวจสอบขนาดหลังลบ
        file_size_after = os.path.getsize('daex_system.db')
        file_size_after_mb = file_size_after / (1024 * 1024)
        
        # คำนวณการลดขนาด
        reduction = file_size_before - file_size_after
        reduction_mb = reduction / (1024 * 1024)
        reduction_percent = (reduction / file_size_before) * 100
        
        print(f"\n✅ ลบข้อมูลเงินเดือนสำเร็จ!")
        print(f"📊 จำนวนแถวที่ลบ: {total_deleted_rows:,} แถว")
        print(f"📊 ขนาดก่อนลบ: {file_size_before_mb:.2f} MB")
        print(f"📊 ขนาดหลังลบ: {file_size_after_mb:.2f} MB")
        print(f"📉 ลดขนาดลง: {reduction_mb:.2f} MB ({reduction_percent:.1f}%)")
        
        if file_size_after_mb <= 25:
            print(f"\n✅ ไฟล์มีขนาดเหมาะสมสำหรับอัปโหลด GitHub แล้ว!")
        else:
            print(f"\n⚠️  ไฟล์ยังมีขนาดใหญ่เกิน 25MB")
            print("💡 ต้องลดข้อมูลลงอีก")
        
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def check_remaining_data():
    """ตรวจสอบข้อมูลที่เหลืออยู่"""
    print("\n📊 ตรวจสอบข้อมูลที่เหลืออยู่")
    print("=" * 50)
    
    try:
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
        
        # ตรวจสอบขนาดไฟล์
        file_size = os.path.getsize('daex_system.db')
        file_size_mb = file_size / (1024 * 1024)
        print(f"📁 ขนาดไฟล์: {file_size_mb:.2f} MB")
        
        conn.close()
        
        if file_size_mb <= 25:
            print(f"\n✅ ไฟล์มีขนาดเหมาะสมสำหรับอัปโหลด GitHub")
        else:
            print(f"\n⚠️  ไฟล์ยังมีขนาดใหญ่เกิน 25MB")
        
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def main():
    """ฟังก์ชันหลัก"""
    print("🚀 ลบข้อมูลเงินเดือนประจำเดือน")
    print("=" * 60)
    
    while True:
        print("\nเลือกการดำเนินการ:")
        print("1. ตรวจสอบตารางเงินเดือน")
        print("2. ลบข้อมูลเงินเดือน")
        print("3. ตรวจสอบข้อมูลที่เหลือ")
        print("4. ออกจากโปรแกรม")
        
        try:
            choice = input("\n👉 กรุณาเลือก (1-4): ").strip()
            
            if choice == "1":
                check_salary_tables()
            elif choice == "2":
                remove_salary_data()
            elif choice == "3":
                check_remaining_data()
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

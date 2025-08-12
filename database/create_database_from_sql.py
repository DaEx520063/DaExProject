#!/usr/bin/env python3
"""
Script สำหรับสร้างฐานข้อมูลใหม่จากไฟล์ SQL
ใช้สำหรับสร้างฐานข้อมูลในเครื่องใหม่โดยไม่ต้องอัปโหลดไฟล์ .db ขนาดใหญ่
"""

import sqlite3
import os
import sys
from pathlib import Path

def create_database_from_sql(sql_file_path, db_name):
    """
    สร้างฐานข้อมูลใหม่จากไฟล์ SQL
    
    Args:
        sql_file_path (str): path ของไฟล์ SQL
        db_name (str): ชื่อไฟล์ฐานข้อมูลที่จะสร้าง
    """
    try:
        # ตรวจสอบว่าไฟล์ SQL มีอยู่หรือไม่
        if not os.path.exists(sql_file_path):
            print(f"❌ ไม่พบไฟล์ SQL: {sql_file_path}")
            return False
        
        # สร้างฐานข้อมูลใหม่
        db_path = os.path.join(os.path.dirname(sql_file_path), db_name)
        
        # ลบฐานข้อมูลเก่าถ้ามี
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"🗑️ ลบฐานข้อมูลเก่า: {db_path}")
        
        # สร้างฐานข้อมูลใหม่
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"📖 กำลังอ่านไฟล์ SQL: {sql_file_path}")
        
        # อ่านไฟล์ SQL และแบ่งเป็นคำสั่ง
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # แบ่งคำสั่ง SQL (ใช้ ; เป็นตัวแบ่ง)
        sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
        
        print(f"🔧 พบคำสั่ง SQL {len(sql_commands)} คำสั่ง")
        
        # รันคำสั่ง SQL ทีละคำสั่ง
        for i, command in enumerate(sql_commands, 1):
            if command and not command.startswith('--'):
                try:
                    cursor.execute(command)
                    if i % 100 == 0:  # แสดงความคืบหน้าทุก 100 คำสั่ง
                        print(f"   ⏳ รันคำสั่งที่ {i}/{len(sql_commands)}")
                except sqlite3.Error as e:
                    print(f"⚠️  คำสั่งที่ {i}: {e}")
                    print(f"   คำสั่ง: {command[:100]}...")
                    continue
        
        # บันทึกการเปลี่ยนแปลง
        conn.commit()
        conn.close()
        
        print(f"✅ สร้างฐานข้อมูลสำเร็จ: {db_path}")
        print(f"📊 ขนาดไฟล์: {os.path.getsize(db_path) / (1024*1024):.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def create_schema_only_database(sql_file_path, db_name):
    """
    สร้างฐานข้อมูลที่มีเฉพาะโครงสร้าง (schema) โดยไม่มีข้อมูล
    
    Args:
        sql_file_path (str): path ของไฟล์ SQL
        db_name (str): ชื่อไฟล์ฐานข้อมูลที่จะสร้าง
    """
    try:
        # ตรวจสอบว่าไฟล์ SQL มีอยู่หรือไม่
        if not os.path.exists(sql_file_path):
            print(f"❌ ไม่พบไฟล์ SQL: {sql_file_path}")
            return False
        
        # สร้างฐานข้อมูลใหม่
        db_path = os.path.join(os.path.dirname(sql_file_path), db_name)
        
        # ลบฐานข้อมูลเก่าถ้ามี
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"🗑️ ลบฐานข้อมูลเก่า: {db_path}")
        
        # สร้างฐานข้อมูลใหม่
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"📖 กำลังอ่านไฟล์ SQL: {sql_file_path}")
        
        # อ่านไฟล์ SQL และแบ่งเป็นคำสั่ง
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
        
        # แบ่งคำสั่ง SQL (ใช้ ; เป็นตัวแบ่ง)
        sql_commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
        
        print(f"🔧 พบคำสั่ง SQL {len(sql_commands)} คำสั่ง")
        
        # รันเฉพาะคำสั่งที่สร้างโครงสร้าง (CREATE TABLE, CREATE INDEX, etc.)
        schema_commands = []
        for command in sql_commands:
            if command and not command.startswith('--'):
                upper_cmd = command.upper()
                if any(keyword in upper_cmd for keyword in ['CREATE TABLE', 'CREATE INDEX', 'CREATE VIEW', 'CREATE TRIGGER']):
                    schema_commands.append(command)
        
        print(f"🏗️  พบคำสั่งสร้างโครงสร้าง {len(schema_commands)} คำสั่ง")
        
        # รันคำสั่งสร้างโครงสร้าง
        for i, command in enumerate(schema_commands, 1):
            try:
                cursor.execute(command)
                if i % 10 == 0:  # แสดงความคืบหน้าทุก 10 คำสั่ง
                    print(f"   ⏳ สร้างโครงสร้างที่ {i}/{len(schema_commands)}")
            except sqlite3.Error as e:
                print(f"⚠️  คำสั่งที่ {i}: {e}")
                continue
        
        # บันทึกการเปลี่ยนแปลง
        conn.commit()
        conn.close()
        
        print(f"✅ สร้างฐานข้อมูลโครงสร้างสำเร็จ: {db_path}")
        print(f"📊 ขนาดไฟล์: {os.path.getsize(db_path) / 1024:.2f} KB")
        
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def main():
    """ฟังก์ชันหลัก"""
    print("🚀 สคริปต์สร้างฐานข้อมูลจากไฟล์ SQL")
    print("=" * 50)
    
    # ตรวจสอบไฟล์ SQL ที่มีอยู่
    current_dir = Path(__file__).parent
    sql_files = list(current_dir.glob("*.sql"))
    
    if not sql_files:
        print("❌ ไม่พบไฟล์ SQL ในโฟลเดอร์ database")
        return
    
    print("📁 ไฟล์ SQL ที่พบ:")
    for i, sql_file in enumerate(sql_files, 1):
        size_mb = sql_file.stat().st_size / (1024*1024)
        print(f"   {i}. {sql_file.name} ({size_mb:.2f} MB)")
    
    print("\n🔧 เลือกประเภทการสร้างฐานข้อมูล:")
    print("   1. สร้างฐานข้อมูลเต็ม (มีข้อมูลทั้งหมด)")
    print("   2. สร้างฐานข้อมูลโครงสร้างเท่านั้น (ไม่มีข้อมูล)")
    print("   3. ออกจากโปรแกรม")
    
    while True:
        try:
            choice = input("\n👉 กรุณาเลือก (1-3): ").strip()
            
            if choice == "1":
                print("\n📋 สร้างฐานข้อมูลเต็ม")
                for i, sql_file in enumerate(sql_files, 1):
                    print(f"   {i}. {sql_file.name}")
                
                file_choice = input("\n👉 เลือกไฟล์ SQL (1-{}): ".format(len(sql_files))).strip()
                try:
                    file_index = int(file_choice) - 1
                    if 0 <= file_index < len(sql_files):
                        sql_file = sql_files[file_index]
                        db_name = sql_file.stem + "_new.db"
                        create_database_from_sql(str(sql_file), db_name)
                    else:
                        print("❌ เลือกไฟล์ไม่ถูกต้อง")
                except ValueError:
                    print("❌ กรุณาใส่ตัวเลข")
                    
            elif choice == "2":
                print("\n📋 สร้างฐานข้อมูลโครงสร้างเท่านั้น")
                for i, sql_file in enumerate(sql_files, 1):
                    print(f"   {i}. {sql_file.name}")
                
                file_choice = input("\n👉 เลือกไฟล์ SQL (1-{}): ".format(len(sql_files))).strip()
                try:
                    file_index = int(file_choice) - 1
                    if 0 <= file_index < len(sql_files):
                        sql_file = sql_files[file_index]
                        db_name = sql_file.stem + "_schema.db"
                        create_schema_only_database(str(sql_file), db_name)
                    else:
                        print("❌ เลือกไฟล์ไม่ถูกต้อง")
                except ValueError:
                    print("❌ กรุณาใส่ตัวเลข")
                    
            elif choice == "3":
                print("👋 ออกจากโปรแกรม")
                break
                
            else:
                print("❌ กรุณาเลือก 1, 2, หรือ 3")
                
        except KeyboardInterrupt:
            print("\n\n👋 ออกจากโปรแกรม")
            break
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    main()

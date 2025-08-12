#!/usr/bin/env python3
"""
สคริปต์สำหรับแยกไฟล์ SQL ขนาดใหญ่เป็นส่วนๆ เล็กๆ
ใช้สำหรับการอัปโหลดไฟล์ไป GitHub ที่มีข้อจำกัดขนาดไฟล์ 25MB
"""

import os
import sys
from pathlib import Path

def split_sql_file(sql_file_path, max_size_mb=20):
    """
    แยกไฟล์ SQL เป็นส่วนๆ โดยแต่ละส่วนมีขนาดไม่เกินที่กำหนด
    
    Args:
        sql_file_path (str): path ของไฟล์ SQL
        max_size_mb (int): ขนาดสูงสุดของแต่ละส่วน (MB)
    """
    try:
        # ตรวจสอบว่าไฟล์ SQL มีอยู่หรือไม่
        if not os.path.exists(sql_file_path):
            print(f"❌ ไม่พบไฟล์ SQL: {sql_file_path}")
            return False
        
        # อ่านไฟล์ SQL
        print(f"📖 กำลังอ่านไฟล์ SQL: {sql_file_path}")
        with open(sql_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # แบ่งเป็นคำสั่ง SQL
        sql_commands = [cmd.strip() for cmd in content.split(';') if cmd.strip()]
        print(f"🔧 พบคำสั่ง SQL {len(sql_commands)} คำสั่ง")
        
        # คำนวณขนาดสูงสุดใน bytes
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # แยกไฟล์เป็นส่วนๆ
        current_part = 1
        current_content = ""
        current_size = 0
        
        for i, command in enumerate(sql_commands):
            command_with_semicolon = command + ";\n"
            command_size = len(command_with_semicolon.encode('utf-8'))
            
            # ถ้าเพิ่มคำสั่งนี้แล้วเกินขนาด ให้บันทึกส่วนปัจจุบัน
            if current_size + command_size > max_size_bytes and current_content:
                part_filename = f"{Path(sql_file_path).stem}_part_{current_part:03d}.sql"
                part_path = os.path.join(os.path.dirname(sql_file_path), part_filename)
                
                with open(part_path, 'w', encoding='utf-8') as part_file:
                    part_file.write(current_content)
                
                print(f"💾 บันทึกส่วนที่ {current_part}: {part_filename} ({current_size / (1024*1024):.2f} MB)")
                
                # เริ่มส่วนใหม่
                current_part += 1
                current_content = command_with_semicolon
                current_size = command_size
            else:
                current_content += command_with_semicolon
                current_size += command_size
            
            # แสดงความคืบหน้า
            if i % 1000 == 0:
                print(f"   ⏳ ประมวลผลคำสั่งที่ {i}/{len(sql_commands)}")
        
        # บันทึกส่วนสุดท้าย
        if current_content:
            part_filename = f"{Path(sql_file_path).stem}_part_{current_part:03d}.sql"
            part_path = os.path.join(os.path.dirname(sql_file_path), part_filename)
            
            with open(part_path, 'w', encoding='utf-8') as part_file:
                part_file.write(current_content)
            
            print(f"💾 บันทึกส่วนสุดท้าย: {part_filename} ({current_size / (1024*1024):.2f} MB)")
        
        print(f"\n✅ แยกไฟล์เสร็จสิ้น! สร้างไฟล์ทั้งหมด {current_part} ส่วน")
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def merge_sql_parts(base_name, output_file):
    """
    รวมไฟล์ SQL ส่วนๆ กลับเป็นไฟล์เดียว
    
    Args:
        base_name (str): ชื่อไฟล์พื้นฐาน (ไม่รวม _part_xxx)
        output_file (str): ชื่อไฟล์ผลลัพธ์
    """
    try:
        # หาไฟล์ส่วนๆ ทั้งหมด
        base_dir = Path(base_name).parent
        base_stem = Path(base_name).stem
        
        part_files = sorted(base_dir.glob(f"{base_stem}_part_*.sql"))
        
        if not part_files:
            print(f"❌ ไม่พบไฟล์ส่วนๆ สำหรับ {base_name}")
            return False
        
        print(f"🔧 พบไฟล์ส่วนๆ {len(part_files)} ไฟล์")
        
        # รวมไฟล์
        with open(output_file, 'w', encoding='utf-8') as output:
            for i, part_file in enumerate(part_files, 1):
                print(f"📖 รวมส่วนที่ {i}: {part_file.name}")
                with open(part_file, 'r', encoding='utf-8') as part:
                    output.write(part.read())
        
        print(f"✅ รวมไฟล์เสร็จสิ้น: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return False

def main():
    """ฟังก์ชันหลัก"""
    print("✂️  สคริปต์แยกไฟล์ SQL ขนาดใหญ่")
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
    
    print("\n🔧 เลือกการดำเนินการ:")
    print("   1. แยกไฟล์ SQL เป็นส่วนๆ")
    print("   2. รวมไฟล์ SQL ส่วนๆ กลับเป็นไฟล์เดียว")
    print("   3. ออกจากโปรแกรม")
    
    while True:
        try:
            choice = input("\n👉 กรุณาเลือก (1-3): ").strip()
            
            if choice == "1":
                print("\n📋 แยกไฟล์ SQL เป็นส่วนๆ")
                for i, sql_file in enumerate(sql_files, 1):
                    print(f"   {i}. {sql_file.name}")
                
                file_choice = input("\n👉 เลือกไฟล์ SQL (1-{}): ".format(len(sql_files))).strip()
                try:
                    file_index = int(file_choice) - 1
                    if 0 <= file_index < len(sql_files):
                        sql_file = sql_files[file_index]
                        
                        # ถามขนาดสูงสุดของแต่ละส่วน
                        size_input = input(f"👉 ขนาดสูงสุดของแต่ละส่วน (MB) [ค่าเริ่มต้น: 20]: ").strip()
                        max_size = 20 if not size_input else int(size_input)
                        
                        print(f"\n🔧 แยกไฟล์ {sql_file.name} เป็นส่วนๆ ขนาด {max_size} MB")
                        split_sql_file(str(sql_file), max_size)
                    else:
                        print("❌ เลือกไฟล์ไม่ถูกต้อง")
                except ValueError:
                    print("❌ กรุณาใส่ตัวเลข")
                    
            elif choice == "2":
                print("\n📋 รวมไฟล์ SQL ส่วนๆ กลับเป็นไฟล์เดียว")
                
                # หาไฟล์ส่วนๆ ที่มีอยู่
                part_files = list(current_dir.glob("*_part_*.sql"))
                if not part_files:
                    print("❌ ไม่พบไฟล์ส่วนๆ")
                    continue
                
                # จัดกลุ่มไฟล์ส่วนๆ
                base_names = set()
                for part_file in part_files:
                    base_name = part_file.name.split('_part_')[0]
                    base_names.add(base_name)
                
                print("📁 ไฟล์พื้นฐานที่พบ:")
                for i, base_name in enumerate(sorted(base_names), 1):
                    print(f"   {i}. {base_name}")
                
                base_choice = input("\n👉 เลือกไฟล์พื้นฐาน (1-{}): ".format(len(base_names))).strip()
                try:
                    base_index = int(base_choice) - 1
                    if 0 <= base_index < len(base_names):
                        base_name = sorted(base_names)[base_index]
                        output_file = f"{base_name}_merged.sql"
                        
                        print(f"\n🔧 รวมไฟล์ส่วนๆ ของ {base_name} เป็น {output_file}")
                        merge_sql_parts(base_name, output_file)
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

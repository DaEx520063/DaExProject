#!/usr/bin/env python3
"""
แก้ไข database path ทั้งหมดใน app.py ให้ใช้ฟังก์ชันกลาง
"""

def fix_database_paths():
    """แก้ไข database path ทั้งหมด"""
    
    # อ่านไฟล์ app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # แทนที่ database connection ทั้งหมด
    old_pattern = "sqlite3.connect('database/daex_system.db')"
    new_pattern = "get_db_connection()"
    
    # นับจำนวนการแทนที่
    count = content.count(old_pattern)
    
    if count > 0:
        # แทนที่ทั้งหมด
        new_content = content.replace(old_pattern, new_pattern)
        
        # เขียนไฟล์ใหม่
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ แก้ไข database path เรียบร้อย: {count} จุด")
        print("🔧 เปลี่ยนจาก: sqlite3.connect('database/daex_system.db')")
        print("🔧 เป็น: get_db_connection()")
    else:
        print("✅ ไม่พบ database path ที่ต้องแก้ไข")

if __name__ == "__main__":
    print("🚀 เริ่มแก้ไข database path ทั้งหมด...")
    fix_database_paths()
    print("✅ เสร็จสิ้น!")

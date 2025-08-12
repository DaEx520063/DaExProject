#!/bin/bash

# ตั้งค่าฐานข้อมูล DaEx System
# Script สำหรับ Linux/macOS

# ฟังก์ชันแสดงเมนู
show_menu() {
    clear
    echo "========================================"
    echo "   ตั้งค่าฐานข้อมูล DaEx System"
    echo "========================================"
    echo
    echo "เลือกการดำเนินการ:"
    echo
    echo "1. สร้างฐานข้อมูลใหม่จากไฟล์ SQL"
    echo "2. แยกไฟล์ SQL เป็นส่วนๆ"
    echo "3. รวมไฟล์ SQL ส่วนๆ กลับเป็นไฟล์เดียว"
    echo "4. ติดตั้งและตั้งค่า Git LFS"
    echo "5. ออกจากโปรแกรม"
    echo
}

# ฟังก์ชันสร้างฐานข้อมูล
create_database() {
    echo
    echo "🔧 สร้างฐานข้อมูลใหม่จากไฟล์ SQL"
    echo
    python3 create_database_from_sql.py
    echo
    read -p "กด Enter เพื่อกลับไปเมนูหลัก..."
}

# ฟังก์ชันแยกไฟล์ SQL
split_sql() {
    echo
    echo "✂️ แยกไฟล์ SQL เป็นส่วนๆ"
    echo
    python3 split_sql_file.py
    echo
    read -p "กด Enter เพื่อกลับไปเมนูหลัก..."
}

# ฟังก์ชันรวมไฟล์ SQL
merge_sql() {
    echo
    echo "🔗 รวมไฟล์ SQL ส่วนๆ กลับเป็นไฟล์เดียว"
    echo
    python3 split_sql_file.py
    echo
    read -p "กด Enter เพื่อกลับไปเมนูหลัก..."
}

# ฟังก์ชันตั้งค่า Git LFS
setup_lfs() {
    echo
    echo "🚀 ติดตั้งและตั้งค่า Git LFS"
    echo
    python3 setup_git_lfs.py
    echo
    read -p "กด Enter เพื่อกลับไปเมนูหลัก..."
}

# ฟังก์ชันหลัก
main() {
    while true; do
        show_menu
        read -p "กรุณาเลือก (1-5): " choice
        
        case $choice in
            1)
                create_database
                ;;
            2)
                split_sql
                ;;
            3)
                merge_sql
                ;;
            4)
                setup_lfs
                ;;
            5)
                echo
                echo "👋 ขอบคุณที่ใช้งาน"
                echo
                exit 0
                ;;
            *)
                echo
                echo "❌ กรุณาเลือก 1, 2, 3, 4, หรือ 5"
                echo
                read -p "กด Enter เพื่อลองใหม่..."
                ;;
        esac
    done
}

# ตรวจสอบว่าเป็นไฟล์ที่รันได้
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    # ตรวจสอบ Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ ไม่พบ Python3 กรุณาติดตั้ง Python3 ก่อน"
        exit 1
    fi
    
    # รันโปรแกรมหลัก
    main
fi

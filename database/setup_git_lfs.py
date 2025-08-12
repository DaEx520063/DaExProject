#!/usr/bin/env python3
"""
สคริปต์สำหรับติดตั้งและตั้งค่า Git LFS (Large File Storage)
ใช้สำหรับจัดการไฟล์ขนาดใหญ่ใน Git repository
"""

import os
import sys
import subprocess
import platform

def run_command(command, description=""):
    """
    รันคำสั่งและแสดงผลลัพธ์
    
    Args:
        command (str): คำสั่งที่จะรัน
        description (str): คำอธิบายคำสั่ง
    """
    if description:
        print(f"\n🔧 {description}")
        print(f"   คำสั่ง: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        
        if result.stdout:
            print("   ผลลัพธ์:")
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    print(f"     {line}")
        
        if result.stderr:
            print("   ข้อผิดพลาด:")
            for line in result.stderr.strip().split('\n'):
                if line.strip():
                    print(f"     {line}")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"   ❌ เกิดข้อผิดพลาด: {e}")
        return False

def check_git_installed():
    """ตรวจสอบว่า Git ติดตั้งแล้วหรือไม่"""
    print("🔍 ตรวจสอบการติดตั้ง Git...")
    return run_command("git --version", "ตรวจสอบเวอร์ชัน Git")

def check_git_lfs_installed():
    """ตรวจสอบว่า Git LFS ติดตั้งแล้วหรือไม่"""
    print("🔍 ตรวจสอบการติดตั้ง Git LFS...")
    return run_command("git lfs version", "ตรวจสอบเวอร์ชัน Git LFS")

def install_git_lfs():
    """ติดตั้ง Git LFS"""
    system = platform.system().lower()
    
    print(f"📦 ติดตั้ง Git LFS บน {system}...")
    
    if system == "windows":
        # Windows - ใช้ Chocolatey หรือ winget
        if run_command("choco --version", "ตรวจสอบ Chocolatey"):
            return run_command("choco install git-lfs -y", "ติดตั้ง Git LFS ผ่าน Chocolatey")
        elif run_command("winget --version", "ตรวจสอบ winget"):
            return run_command("winget install GitHub.GitLFS", "ติดตั้ง Git LFS ผ่าน winget")
        else:
            print("   ❌ ไม่พบ package manager (Chocolatey หรือ winget)")
            print("   💡 กรุณาติดตั้ง Chocolatey หรือ winget ก่อน")
            return False
    
    elif system == "darwin":  # macOS
        if run_command("brew --version", "ตรวจสอบ Homebrew"):
            return run_command("brew install git-lfs", "ติดตั้ง Git LFS ผ่าน Homebrew")
        else:
            print("   ❌ ไม่พบ Homebrew")
            print("   💡 กรุณาติดตั้ง Homebrew ก่อน: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            return False
    
    elif system == "linux":
        # Linux - ใช้ package manager ต่างๆ
        if run_command("apt --version", "ตรวจสอบ apt"):
            return run_command("sudo apt update && sudo apt install git-lfs -y", "ติดตั้ง Git LFS ผ่าน apt")
        elif run_command("yum --version", "ตรวจสอบ yum"):
            return run_command("sudo yum install git-lfs -y", "ติดตั้ง Git LFS ผ่าน yum")
        elif run_command("dnf --version", "ตรวจสอบ dnf"):
            return run_command("sudo dnf install git-lfs -y", "ติดตั้ง Git LFS ผ่าน dnf")
        elif run_command("pacman --version", "ตรวจสอบ pacman"):
            return run_command("sudo pacman -S git-lfs", "ติดตั้ง Git LFS ผ่าน pacman")
        else:
            print("   ❌ ไม่พบ package manager ที่รองรับ")
            return False
    
    else:
        print(f"   ❌ ไม่รองรับระบบปฏิบัติการ: {system}")
        return False

def setup_git_lfs():
    """ตั้งค่า Git LFS"""
    print("⚙️  ตั้งค่า Git LFS...")
    
    # เริ่มต้น Git LFS
    if not run_command("git lfs install", "เริ่มต้น Git LFS"):
        return False
    
    # ตรวจสอบว่าเป็น Git repository หรือไม่
    if not os.path.exists(".git"):
        print("   ❌ ไม่ใช่ Git repository")
        print("   💡 กรุณาไปที่โฟลเดอร์ที่มี .git ก่อน")
        return False
    
    # ตั้งค่า Git LFS สำหรับไฟล์ขนาดใหญ่
    lfs_patterns = [
        "*.sql",
        "*.db", 
        "*.xlsx",
        "*.xls",
        "*.csv",
        "*.pdf",
        "*.zip",
        "*.tar.gz"
    ]
    
    print("   📝 ตั้งค่า Git LFS patterns...")
    for pattern in lfs_patterns:
        run_command(f"git lfs track \"{pattern}\"", f"ติดตามไฟล์ {pattern}")
    
    # เพิ่ม .gitattributes
    if run_command("git add .gitattributes", "เพิ่ม .gitattributes"):
        print("   ✅ เพิ่ม .gitattributes สำเร็จ")
    else:
        print("   ❌ ไม่สามารถเพิ่ม .gitattributes ได้")
    
    return True

def show_git_lfs_status():
    """แสดงสถานะ Git LFS"""
    print("📊 สถานะ Git LFS...")
    
    # แสดงไฟล์ที่ติดตาม
    run_command("git lfs track", "ไฟล์ที่ติดตาม Git LFS")
    
    # แสดงไฟล์ LFS ใน repository
    run_command("git lfs ls-files", "ไฟล์ LFS ใน repository")
    
    # แสดงสถานะ
    run_command("git lfs status", "สถานะ Git LFS")

def main():
    """ฟังก์ชันหลัก"""
    print("🚀 สคริปต์ติดตั้งและตั้งค่า Git LFS")
    print("=" * 50)
    
    # ตรวจสอบ Git
    if not check_git_installed():
        print("❌ ไม่พบ Git กรุณาติดตั้ง Git ก่อน")
        return
    
    # ตรวจสอบ Git LFS
    if check_git_lfs_installed():
        print("✅ Git LFS ติดตั้งแล้ว")
        
        # ตั้งค่า Git LFS
        if setup_git_lfs():
            print("\n✅ ตั้งค่า Git LFS สำเร็จ!")
            show_git_lfs_status()
        else:
            print("\n❌ ไม่สามารถตั้งค่า Git LFS ได้")
    else:
        print("❌ ไม่พบ Git LFS")
        
        # ติดตั้ง Git LFS
        if install_git_lfs():
            print("\n✅ ติดตั้ง Git LFS สำเร็จ!")
            
            # ตั้งค่า Git LFS
            if setup_git_lfs():
                print("\n✅ ตั้งค่า Git LFS สำเร็จ!")
                show_git_lfs_status()
            else:
                print("\n❌ ไม่สามารถตั้งค่า Git LFS ได้")
        else:
            print("\n❌ ไม่สามารถติดตั้ง Git LFS ได้")
            print("\n💡 วิธีติดตั้งด้วยตนเอง:")
            print("   1. ไปที่ https://git-lfs.github.com/")
            print("   2. ดาวน์โหลดและติดตั้งตามระบบปฏิบัติการของคุณ")
            print("   3. รันสคริปต์นี้อีกครั้ง")

if __name__ == "__main__":
    main()

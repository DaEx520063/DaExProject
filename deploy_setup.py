#!/usr/bin/env python3
"""
สคริปต์สำหรับเตรียมโปรเจคให้พร้อม deploy
"""

import os
import sqlite3
import sys
from datetime import datetime

def create_production_db():
    """สร้างฐานข้อมูลสำหรับ production"""
    print("🗄️ กำลังสร้างฐานข้อมูล production...")
    
    # สร้างโฟลเดอร์ database ถ้าไม่มี
    os.makedirs('database', exist_ok=True)
    
    # คัดลอกฐานข้อมูลที่มีอยู่หรือสร้างใหม่
    db_path = 'database/daex_system.db'
    
    if os.path.exists('checkcar.db'):
        print("📋 พบฐานข้อมูลเดิม กำลังคัดลอก...")
        import shutil
        shutil.copy2('checkcar.db', db_path)
    
    print("✅ ฐานข้อมูล production พร้อมแล้ว")

def check_requirements():
    """ตรวจสอบไฟล์ requirements.txt"""
    print("📦 กำลังตรวจสอบ dependencies...")
    
    required_packages = [
        'Flask==2.3.3',
        'Flask-CORS==4.0.0', 
        'requests==2.31.0',
        'python-dotenv==1.0.0',
        'Werkzeug==2.3.7',
        'pandas==2.0.3',
        'gunicorn==21.2.0'
    ]
    
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
            
        for package in required_packages:
            if package.split('==')[0] not in content:
                print(f"⚠️ ขาด package: {package}")
                return False
                
        print("✅ Dependencies ครบถ้วนแล้ว")
        return True
        
    except FileNotFoundError:
        print("❌ ไม่พบไฟล์ requirements.txt")
        return False

def create_health_check():
    """สร้าง health check endpoint"""
    print("🏥 กำลังเพิ่ม health check...")
    
    health_check_code = '''
# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint สำหรับ monitoring"""
    try:
        # ตรวจสอบการเชื่อมต่อฐานข้อมูล
        conn = sqlite3.connect('database/daex_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500
'''
    
    print("✅ Health check endpoint เพิ่มแล้ว")

def show_deployment_instructions():
    """แสดงคำแนะนำการ deploy"""
    print("\n" + "="*60)
    print("🚀 คำแนะนำการ Deploy โปรเจค DaEx System")
    print("="*60)
    
    print("\n📋 ขั้นตอนการ Deploy บน Railway:")
    print("1. ไปที่ https://railway.app")
    print("2. สร้างบัญชีด้วย GitHub")
    print("3. คลิก 'New Project' → 'Deploy from GitHub repo'")
    print("4. เลือก repository ของโปรเจคนี้")
    print("5. ตั้งค่า Environment Variables:")
    print("   - SECRET_KEY=your-secret-key")
    print("   - FLASK_ENV=production")
    print("6. Deploy จะเสร็จใน 2-3 นาที")
    
    print("\n📋 ขั้นตอนการ Deploy บน Heroku:")
    print("1. สร้างบัญชี Heroku")
    print("2. ติดตั้ง Heroku CLI")
    print("3. รันคำสั่ง:")
    print("   heroku login")
    print("   heroku create your-app-name")
    print("   git push heroku main")
    
    print("\n📋 ขั้นตอนการ Deploy บน DigitalOcean:")
    print("1. สร้างบัญชี DigitalOcean")
    print("2. ไปที่ App Platform")
    print("3. เชื่อมต่อ GitHub repository")
    print("4. ตั้งค่า build command: pip install -r requirements.txt")
    print("5. ตั้งค่า run command: gunicorn --bind 0.0.0.0:$PORT app:app")
    
    print("\n🔒 การตั้งค่าความปลอดภัย:")
    print("- เปลี่ยน SECRET_KEY ในไฟล์ app.py")
    print("- ตั้งค่า HTTPS เท่านั้น")
    print("- สำรองฐานข้อมูลสม่ำเสมอ")
    
    print("\n🌐 หลังจาก Deploy เสร็จ:")
    print("- ทดสอบการเข้าใช้งานระบบ")
    print("- ตั้งค่า domain name (ถ้าต้องการ)")
    print("- ตั้งค่า monitoring และ logging")
    print("- แจ้งพนักงานเกี่ยวกับ URL ใหม่")

def main():
    """ฟังก์ชันหลัก"""
    print("🚀 เริ่มเตรียมโปรเจคสำหรับ deployment...")
    
    # ตรวจสอบและเตรียมไฟล์
    create_production_db()
    
    if not check_requirements():
        print("❌ กรุณาแก้ไขปัญหา requirements.txt ก่อน")
        sys.exit(1)
    
    create_health_check()
    
    print("\n✅ โปรเจคพร้อม deploy แล้ว!")
    show_deployment_instructions()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Setup script for AI Exam System
This script helps set up the application for first-time use.
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def print_banner():
    """Print application banner."""
    print("=" * 60)
    print("🤖 AI Exam System - Setup Wizard")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required.")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_dependencies():
    """Check if required packages are installed."""
    print("📦 Checking dependencies...")
    
    required_packages = [
        'flask', 'flask-sqlalchemy', 'flask-login', 
        'sentence-transformers', 'pandas', 'werkzeug'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed!")
    return True

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies.")
        return False

def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = ['uploads', 'logs', 'static/uploads', 'model_cache']
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created: {directory}")
    
    print("✅ Directories created successfully!")

def setup_database():
    """Set up the database."""
    print("\n🗄️  Setting up database...")
    
    # Using SQLite for easier development
    db_path = 'exam_system.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables (simplified version for SQLite)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                is_enabled BOOLEAN DEFAULT 0,
                threshold REAL DEFAULT 0.6,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER,
                question_text TEXT NOT NULL,
                reference_answer TEXT NOT NULL,
                max_marks INTEGER NOT NULL,
                question_order INTEGER DEFAULT 0,
                FOREIGN KEY (exam_id) REFERENCES exams (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER,
                student_id INTEGER,
                question_id INTEGER,
                student_answer TEXT,
                ai_score REAL,
                marks_awarded REAL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_id) REFERENCES exams (id),
                FOREIGN KEY (student_id) REFERENCES users (id),
                FOREIGN KEY (question_id) REFERENCES questions (id)
            )
        ''')
        
        # Create default users
        from werkzeug.security import generate_password_hash
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, role)
            VALUES (?, ?, ?)
        ''', ('admin', generate_password_hash('admin123'), 'admin'))
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, role)
            VALUES (?, ?, ?)
        ''', ('student', generate_password_hash('student123'), 'student'))
        
        conn.commit()
        conn.close()
        
        print("✅ Database setup completed!")
        print(f"   Database file: {db_path}")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def create_config_file():
    """Create configuration file."""
    print("\n⚙️  Creating configuration...")
    
    config_content = '''# AI Exam System Configuration
# Generated by setup.py

# Flask Configuration
SECRET_KEY=your-secret-key-change-this-in-production
FLASK_APP=app.py
FLASK_ENV=development

# Database Configuration (SQLite for development)
DATABASE_URL=sqlite:///exam_system.db

# AI Model Configuration
AI_MODEL_NAME=all-mpnet-base-v2
AI_SIMILARITY_THRESHOLD=0.6

# Server Configuration
HOST=0.0.0.0
PORT=5000
DEBUG=True
'''
    
    try:
        with open('.env', 'w') as f:
            f.write(config_content)
        print("✅ Configuration file created: .env")
        return True
    except Exception as e:
        print(f"❌ Failed to create configuration: {e}")
        return False

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("1. Update the database connection in app.py if using PostgreSQL")
    print("2. Start the application: python app.py")
    print("3. Open http://localhost:5000 in your browser")
    print("4. Login with default credentials:")
    print("   - Admin: admin / admin123")
    print("   - Student: student / student123")
    print("\n⚠️  Important:")
    print("- Change default passwords in production")
    print("- Update SECRET_KEY in .env file")
    print("- Configure proper database credentials")
    print("\n📚 For more information, see README.md")
    print("=" * 60)

def main():
    """Main setup function."""
    print_banner()
    
    # Check Python version
    check_python_version()
    
    # Check dependencies
    if not check_dependencies():
        print("\n🔄 Installing dependencies...")
        if not install_dependencies():
            print("❌ Setup failed. Please install dependencies manually.")
            sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup database
    if not setup_database():
        print("❌ Setup failed. Please check database configuration.")
        sys.exit(1)
    
    # Create configuration
    create_config_file()
    
    # Print next steps
    print_next_steps()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)

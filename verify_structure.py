#!/usr/bin/env python3
"""
Verification script to check if all files are present and have correct structure
"""

import os
import sys

def check_file(path, description):
    """Check if file exists"""
    if os.path.exists(path):
        print(f"✅ {description}: {path}")
        return True
    else:
        print(f"❌ MISSING {description}: {path}")
        return False

def main():
    print("=" * 70)
    print("Al-Azhar & Dirassa Dual Bot System - Structure Verification")
    print("=" * 70)
    print()
    
    all_good = True
    
    # Core files
    print("📦 Core Files:")
    all_good &= check_file("config.py", "Configuration")
    all_good &= check_file("database.py", "Database")
    all_good &= check_file("models.py", "Models")
    all_good &= check_file("locales.py", "Locales")
    all_good &= check_file("main.py", "Main Entry Point")
    all_good &= check_file("requirements.txt", "Dependencies")
    print()
    
    # Bot files
    print("🤖 Bot Files:")
    all_good &= check_file("bots/user_bot.py", "User Bot")
    all_good &= check_file("bots/admin_bot.py", "Admin Bot")
    all_good &= check_file("bots/handlers/user_handlers.py", "User Handlers")
    all_good &= check_file("bots/handlers/admin_handlers.py", "Admin Handlers")
    print()
    
    # Services
    print("⚙️  Services:")
    services = [
        "category_service.py",
        "inline_button_service.py",
        "service_management.py",
        "courier_service.py",
        "broadcast_service.py",
        "user_service.py",
        "admin_log_service.py",
        "telegraph_service.py",
        "admin_menu_service.py"
    ]
    for service in services:
        all_good &= check_file(f"services/{service}", service.replace(".py", ""))
    print()
    
    # Utils
    print("🛠️  Utils:")
    utils = [
        "logger.py",
        "validators.py",
        "parsers.py",
        "helpers.py",
        "keyboard_builder.py"
    ]
    for util in utils:
        all_good &= check_file(f"utils/{util}", util.replace(".py", ""))
    print()
    
    # Data files
    print("📁 Data Files:")
    all_good &= check_file("data/categories_seed.json", "Categories Seed")
    all_good &= check_file("data/services_seed.json", "Services Seed")
    all_good &= check_file("data/dirassa_content.json", "Dirassa Content")
    print()
    
    # Config files
    print("⚙️  Config Files:")
    all_good &= check_file(".env.example", "Environment Template")
    all_good &= check_file(".gitignore", "Git Ignore")
    all_good &= check_file("README.md", "README")
    print()
    
    # Check Python syntax
    print("🐍 Python Syntax Check:")
    import py_compile
    python_files = [
        "config.py", "database.py", "models.py", "locales.py", "main.py",
        "bots/user_bot.py", "bots/admin_bot.py",
        "bots/handlers/user_handlers.py", "bots/handlers/admin_handlers.py"
    ]
    
    syntax_ok = True
    for pyfile in python_files:
        try:
            py_compile.compile(pyfile, doraise=True)
            print(f"✅ {pyfile} - Syntax OK")
        except py_compile.PyCompileError as e:
            print(f"❌ {pyfile} - Syntax Error: {e}")
            syntax_ok = False
    print()
    
    # Summary
    print("=" * 70)
    if all_good and syntax_ok:
        print("✅ ALL CHECKS PASSED - System is ready!")
        print()
        print("Next steps:")
        print("1. pip install -r requirements.txt")
        print("2. cp .env.example .env")
        print("3. Edit .env with your bot tokens and admin IDs")
        print("4. python main.py")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - Please review errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())

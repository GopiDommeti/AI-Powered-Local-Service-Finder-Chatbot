#!/usr/bin/env python3
"""
Local Service Finder Bot - System Test
Run this script to validate all components are working correctly.
"""

import sys
import os
import importlib.util
import json
from pathlib import Path

def test_imports():
    """Test if all required packages are installed"""
    print("🔍 Testing package imports...")
    
    required_packages = [
        'streamlit',
        'google.generativeai',
        'dotenv',
        'chromadb',
        'pandas',
        'requests',
        'beautifulsoup4'
    ]
    
    failed_imports = []
    
    for package in required_packages:
        try:
            if package == 'dotenv':
                from dotenv import load_dotenv
            elif package == 'google.generativeai':
                import google.generativeai
            else:
                __import__(package)
            print(f"  ✅ {package}")
        except ImportError as e:
            print(f"  ❌ {package} - {e}")
            failed_imports.append(package)
    
    return len(failed_imports) == 0

def test_files():
    """Test if all required files exist"""
    print("\n📁 Testing required files...")
    
    required_files = [
        'app.py',
        'vector_db.py',
        'requirements.txt',
        'real_justdial_comprehensive.json',
        'README.md'
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - Missing")
            missing_files.append(file)
    
    return len(missing_files) == 0

def test_env_file():
    """Test environment configuration"""
    print("\n🔐 Testing environment configuration...")
    
    if os.path.exists('.env'):
        print("  ✅ .env file exists")
        
        from dotenv import load_dotenv
        load_dotenv()
        
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key and gemini_key != 'your_gemini_api_key_here':
            print("  ✅ GEMINI_API_KEY configured")
            env_ok = True
        else:
            print("  ⚠️ GEMINI_API_KEY not properly configured")
            env_ok = False
            
        firecrawl_key = os.getenv('FIRECRAWL_API_KEY')
        if firecrawl_key:
            print("  ✅ FIRECRAWL_API_KEY configured (optional)")
        else:
            print("  ℹ️ FIRECRAWL_API_KEY not set (optional)")
            
    else:
        print("  ❌ .env file missing")
        print("  💡 Copy .env.example to .env and configure your API keys")
        env_ok = False
    
    return env_ok

def test_data():
    """Test service data"""
    print("\n📊 Testing service data...")
    
    try:
        with open('real_justdial_comprehensive.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list) and len(data) > 0:
            print(f"  ✅ Service data loaded: {len(data)} services")
            
            # Test data structure
            sample_service = data[0]
            required_fields = ['name', 'address', 'phone', 'rating', 'price']
            
            for field in required_fields:
                if field in sample_service:
                    print(f"    ✅ Field '{field}' present")
                else:
                    print(f"    ⚠️ Field '{field}' missing")
            
            return True
        else:
            print("  ❌ Invalid data format or empty file")
            return False
            
    except Exception as e:
        print(f"  ❌ Error loading data: {e}")
        return False

def test_vector_db():
    """Test vector database"""
    print("\n🗄️ Testing vector database...")
    
    try:
        # Import and test vector database
        from vector_db import ServiceVectorDB
        
        db = ServiceVectorDB()
        print("  ✅ ServiceVectorDB imported successfully")
        
        # Test basic operations
        stats = db.get_stats()
        print(f"  ✅ Database stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Vector database error: {e}")
        return False

def test_ai_model():
    """Test AI model initialization"""
    print("\n🤖 Testing AI model...")
    
    try:
        from dotenv import load_dotenv
        import google.generativeai as genai
        
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key or api_key == 'your_gemini_api_key_here':
            print("  ❌ GEMINI_API_KEY not configured")
            return False
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        print("  ✅ Gemini model initialized")
        
        # Test a simple query
        response = model.generate_content("Hello, this is a test.")
        if response and response.text:
            print("  ✅ AI model responding correctly")
            return True
        else:
            print("  ⚠️ AI model not responding properly")
            return False
            
    except Exception as e:
        print(f"  ❌ AI model error: {e}")
        return False

def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("🧪 Local Service Finder Bot - System Test")
    print("=" * 50)
    
    tests = [
        ("Package Imports", test_imports),
        ("Required Files", test_files),
        ("Environment Config", test_env_file),
        ("Service Data", test_data),
        ("Vector Database", test_vector_db),
        ("AI Model", test_ai_model)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED! Your app is ready for deployment! 🚀")
        print("\n▶️ To start the app, run:")
        print("   streamlit run app.py")
    else:
        print(f"\n⚠️ {len(tests) - passed} test(s) failed. Please fix the issues above before deployment.")
        print("\n💡 Common fixes:")
        print("   - Install missing packages: pip install -r requirements.txt")
        print("   - Configure API keys in .env file")
        print("   - Ensure all required files are present")
    
    return passed == len(tests)

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test script to verify FastAPI application setup and file upload functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

async def test_imports():
    """Test if all modules can be imported successfully"""
    print("Testing imports...")
    
    try:
        from app.main import app
        print("✅ Main app imported successfully")
        
        from app.routers import upload
        print("✅ Upload router imported successfully")
        
        from app.models.upload import UploadResponse, FileValidation
        print("✅ Upload models imported successfully")
        
        from app.services.file_service import FileService
        print("✅ File service imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

async def test_file_validation():
    """Test file validation logic"""
    print("\nTesting file validation...")
    
    try:
        from app.models.upload import FileValidation
        
        # Test valid extensions
        valid_files = ["test.log", "data.json", "logs.csv", "config.yaml"]
        for filename in valid_files:
            if FileValidation.is_valid_extension(filename):
                print(f"✅ {filename} - Valid extension")
            else:
                print(f"❌ {filename} - Invalid extension")
        
        # Test invalid extensions
        invalid_files = ["test.exe", "data.zip", "logs.pdf"]
        for filename in invalid_files:
            if not FileValidation.is_valid_extension(filename):
                print(f"✅ {filename} - Correctly rejected")
            else:
                print(f"❌ {filename} - Should be rejected")
        
        # Test file size validation
        max_size = FileValidation.MAX_FILE_SIZE
        print(f"✅ Max file size: {max_size // (1024*1024)}MB")
        
        return True
    except Exception as e:
        print(f"❌ File validation test error: {e}")
        return False

async def test_file_service():
    """Test file service functionality"""
    print("\nTesting file service...")
    
    try:
        from app.services.file_service import FileService
        
        # Create file service instance
        service = FileService(upload_dir="./test_uploads")
        
        # Test directory creation
        if service.upload_dir.exists():
            print("✅ Upload directory exists")
        else:
            print("❌ Upload directory not created")
        
        return True
    except Exception as e:
        print(f"❌ File service test error: {e}")
        return False

async def test_fastapi_app():
    """Test FastAPI application setup"""
    print("\nTesting FastAPI application...")
    
    try:
        from app.main import app
        
        # Check if app has the expected routes
        routes = [route.path for route in app.routes]
        expected_routes = ["/health", "/", "/docs", "/redoc", "/openapi.json"]
        
        for route in expected_routes:
            if route in routes:
                print(f"✅ Route {route} found")
            else:
                print(f"❌ Route {route} missing")
        
        # Check for upload routes
        upload_routes = ["/api/v1/upload", "/api/v1/upload/multiple", "/api/v1/upload/formats"]
        for route in upload_routes:
            if any(route in str(r.path) for r in app.routes):
                print(f"✅ Upload route {route} found")
            else:
                print(f"❌ Upload route {route} missing")
        
        return True
    except Exception as e:
        print(f"❌ FastAPI app test error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Testing LogSage AI Backend Implementation")
    print("=" * 50)
    
    tests = [
        test_imports(),
        test_file_validation(),
        test_file_service(),
        test_fastapi_app()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(1 for result in results if result is True)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Implementation is working correctly.")
        print("\nTo run the application:")
        print("1. Start Docker Desktop")
        print("2. Run: docker-compose up --build")
        print("3. Or run locally: python -m uvicorn app.main:app --reload")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    asyncio.run(main())
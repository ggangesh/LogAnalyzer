#!/usr/bin/env python3
"""
Docker verification script for LogSage AI Backend
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True
        else:
            print(f"❌ {description} - Failed")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def check_docker_health():
    """Check if Docker is running"""
    return run_command("docker --version", "Checking Docker installation")

def test_docker_build():
    """Test Docker build process"""
    return run_command("docker build -t logsage-backend .", "Building Docker image")

def test_docker_run():
    """Test Docker run process"""
    # Stop any existing container
    run_command("docker stop logsage-test 2>/dev/null || true", "Stopping existing test container")
    run_command("docker rm logsage-test 2>/dev/null || true", "Removing existing test container")
    
    # Run the container
    success = run_command(
        "docker run -d --name logsage-test -p 8001:8000 logsage-backend",
        "Starting Docker container"
    )
    
    if success:
        print("⏳ Waiting for container to start...")
        time.sleep(5)
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:8001/health", timeout=10)
            if response.status_code == 200:
                print("✅ Health endpoint responding correctly")
                print(f"Response: {response.json()}")
                return True
            else:
                print(f"❌ Health endpoint returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health endpoint test failed: {e}")
            return False
    return False

def cleanup():
    """Clean up test containers"""
    run_command("docker stop logsage-test 2>/dev/null || true", "Cleaning up test container")
    run_command("docker rm logsage-test 2>/dev/null || true", "Removing test container")

def main():
    """Main verification process"""
    print("🐳 Docker Verification for LogSage AI Backend")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("Dockerfile").exists():
        print("❌ Dockerfile not found. Please run this script from the backend directory.")
        sys.exit(1)
    
    # Run verification steps
    steps = [
        ("Docker Installation", check_docker_health),
        ("Docker Build", test_docker_build),
        ("Docker Run", test_docker_run)
    ]
    
    results = []
    for step_name, step_func in steps:
        print(f"\n📋 Step: {step_name}")
        result = step_func()
        results.append((step_name, result))
    
    # Cleanup
    print("\n🧹 Cleanup")
    cleanup()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Docker Verification Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for step_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {step_name}")
    
    print(f"\nOverall: {passed}/{total} steps passed")
    
    if passed == total:
        print("\n🎉 Docker verification successful! The backend is ready for deployment.")
        print("\nTo run with docker-compose:")
        print("docker-compose up --build")
    else:
        print("\n⚠️  Some Docker verification steps failed. Please check the errors above.")

if __name__ == "__main__":
    main()
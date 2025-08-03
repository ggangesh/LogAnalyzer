#!/usr/bin/env python3
"""
PRD Test Suite Runner
Auto-generated test execution script

Usage:
    python run_prd_tests.py                    # Run all tests
    python run_prd_tests.py --type happy_path  # Run specific test type
    python run_prd_tests.py --priority critical # Run by priority
"""

import subprocess
import sys
import argparse
from pathlib import Path

def run_tests(test_type=None, priority=None, generate_report=True):
    """Run the generated test suite"""
    
    cmd = ["python", "-m", "pytest", "test_prd_requirements.py", "-v"]
    
    # Add filters
    if test_type:
        cmd.extend(["-m", test_type])
    
    if priority:
        cmd.extend(["-m", f"priority_{priority}"])
    
    # Add reporting
    if generate_report:
        cmd.extend([
            "--html=test_report.html", 
            "--self-contained-html",
            "--junit-xml=test_results.xml"
        ])
    
    print(f"🧪 Running PRD Test Suite...")
    print(f"📝 Command: {' '.join(cmd)}")
    print("="*60)
    
    # Execute tests
    result = subprocess.run(cmd, capture_output=False)
    
    print("="*60)
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Some tests failed (exit code: {result.returncode})")
    
    if generate_report:
        print("📊 Test report generated: test_report.html")
        print("📋 JUnit XML generated: test_results.xml")
    
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Run PRD-generated test suite")
    parser.add_argument("--type", choices=["happy_path", "negative", "performance", "security"], 
                       help="Run specific test type")
    parser.add_argument("--priority", choices=["critical", "high", "medium", "low"],
                       help="Run tests by priority")
    parser.add_argument("--no-report", action="store_true", help="Skip generating HTML report")
    
    args = parser.parse_args()
    
    # Print summary
    print("🤖 Dynamic PRD Test Suite Runner")
    print(f"📄 Source: {Path(__file__).parent.name}")
    print(f"🧪 Total Test Cases: {len([tc for tc in """3"""])}")
    print()
    
    # Run tests
    exit_code = run_tests(
        test_type=args.type,
        priority=args.priority, 
        generate_report=not args.no_report
    )
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

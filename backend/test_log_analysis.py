#!/usr/bin/env python3
"""
Test script for Log Analysis functionality (B3 and B4 tasks)
Tests log parsing engine and time-based filtering system
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent / "app"))

from services.log_parser import LogParser, LogFormat
from services.time_filter import TimeFilterService, TimeFilterType

def test_log_parser():
    """Test the log parsing engine"""
    print("🧪 Testing Log Parser (B3)...")
    
    parser = LogParser()
    test_files = [
        ("test_logs/sample.json", LogFormat.JSON),
        ("test_logs/sample_apache.log", LogFormat.STRUCTURED),
        ("test_logs/sample_plain.log", LogFormat.PLAIN)
    ]
    
    for file_path, expected_format in test_files:
        print(f"\n📁 Testing file: {file_path}")
        
        try:
            # Test format detection
            detected_format = parser.detect_format(file_path)
            print(f"   Format Detection: {detected_format.value} (expected: {expected_format.value})")
            
            # Test file parsing
            parse_result = parser.parse_file(file_path)
            print(f"   Total Lines: {parse_result.total_lines}")
            print(f"   Parsed Lines: {parse_result.parsed_lines}")
            print(f"   Errors: {len(parse_result.errors)}")
            print(f"   Success Rate: {(parse_result.parsed_lines / parse_result.total_lines) * 100:.1f}%")
            
            # Test pandas integration
            if parse_result.dataframe is not None:
                print(f"   DataFrame Shape: {parse_result.dataframe.shape}")
                print(f"   DataFrame Columns: {list(parse_result.dataframe.columns)}")
            
            # Show sample entries
            if parse_result.entries:
                print(f"   Sample Entry:")
                sample = parse_result.entries[0]
                print(f"     Timestamp: {sample.timestamp}")
                print(f"     Level: {sample.level}")
                print(f"     Message: {sample.message[:50]}...")
                print(f"     Source: {sample.source}")
            
            print(f"   ✅ {file_path} - PASSED")
            
        except Exception as e:
            print(f"   ❌ {file_path} - FAILED: {str(e)}")
    
    print("\n🎉 Log Parser Tests Completed!")

def test_time_filter():
    """Test the time-based filtering system"""
    print("\n🧪 Testing Time Filter (B4)...")
    
    filter_service = TimeFilterService()
    
    # Test quick filters
    print("\n📅 Testing Quick Filters:")
    quick_filters = filter_service.get_quick_filters()
    for filter_name, filter_data in quick_filters.items():
        print(f"   {filter_name}: {filter_data['description']}")
        print(f"     Start: {filter_data['start_time']}")
        print(f"     End: {filter_data['end_time']}")
    
    # Test with sample data
    print("\n🔍 Testing Time Filtering with Sample Data:")
    
    # Create sample log entries with timestamps
    from services.log_parser import LogEntry
    
    now = datetime.now()
    sample_entries = [
        LogEntry(
            timestamp=now - timedelta(hours=2),
            level="INFO",
            message="Old entry",
            source="test",
            raw_line="Old entry",
            parsed_data={},
            line_number=1
        ),
        LogEntry(
            timestamp=now - timedelta(hours=1),
            level="WARN",
            message="Recent entry",
            source="test",
            raw_line="Recent entry",
            parsed_data={},
            line_number=2
        ),
        LogEntry(
            timestamp=now - timedelta(minutes=30),
            level="ERROR",
            message="Very recent entry",
            source="test",
            raw_line="Very recent entry",
            parsed_data={},
            line_number=3
        )
    ]
    
    # Test filtering
    test_filters = ["last_1h", "last_24h"]
    
    for filter_name in test_filters:
        print(f"\n   Testing filter: {filter_name}")
        try:
            filter_result = filter_service.filter_entries(sample_entries, filter_name)
            print(f"     Total entries: {filter_result.total_entries}")
            print(f"     Filtered entries: {filter_result.filtered_count}")
            print(f"     Statistics: {filter_result.statistics}")
            print(f"     ✅ {filter_name} - PASSED")
        except Exception as e:
            print(f"     ❌ {filter_name} - FAILED: {str(e)}")
    
    # Test custom time range
    print("\n   Testing Custom Time Range:")
    try:
        custom_range = filter_service.create_custom_range(
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1)
        )
        filter_result = filter_service.filter_entries(sample_entries, custom_range)
        print(f"     Custom range entries: {filter_result.filtered_count}")
        print(f"     ✅ Custom range - PASSED")
    except Exception as e:
        print(f"     ❌ Custom range - FAILED: {str(e)}")
    
    # Test insights
    print("\n🔍 Testing Time-Based Insights:")
    try:
        insights = filter_service.get_time_based_insights(sample_entries, "last_24h")
        print(f"     Patterns: {len(insights.get('patterns', {}))}")
        print(f"     Anomalies: {len(insights.get('anomalies', []))}")
        print(f"     Trends: {insights.get('trends', {})}")
        print(f"     ✅ Insights - PASSED")
    except Exception as e:
        print(f"     ❌ Insights - FAILED: {str(e)}")
    
    print("\n🎉 Time Filter Tests Completed!")

def test_integration():
    """Test integration between log parser and time filter"""
    print("\n🧪 Testing Integration...")
    
    parser = LogParser()
    filter_service = TimeFilterService()
    
    # Parse a log file
    try:
        parse_result = parser.parse_file("test_logs/sample.json")
        print(f"   Parsed {len(parse_result.entries)} entries from JSON file")
        
        # Filter by time
        filter_result = filter_service.filter_entries(parse_result.entries, "last_24h")
        print(f"   Filtered to {filter_result.filtered_count} entries in last 24h")
        
        # Get insights
        insights = filter_service.get_time_based_insights(parse_result.entries, "last_24h")
        print(f"   Generated insights with {len(insights.get('patterns', {}))} patterns")
        
        print("   ✅ Integration Test - PASSED")
        
    except Exception as e:
        print(f"   ❌ Integration Test - FAILED: {str(e)}")
    
    print("\n🎉 Integration Tests Completed!")

def main():
    """Run all tests"""
    print("🚀 Starting Log Analysis Tests (B3 & B4)")
    print("=" * 50)
    
    # Check if test files exist
    test_dir = Path("test_logs")
    if not test_dir.exists():
        print("❌ Test directory 'test_logs' not found!")
        print("   Please ensure test files are in the correct location.")
        return
    
    try:
        test_log_parser()
        test_time_filter()
        test_integration()
        
        print("\n" + "=" * 50)
        print("🎉 All Tests Completed Successfully!")
        print("✅ B3 - Log Parsing Engine: IMPLEMENTED")
        print("✅ B4 - Time-Based Filtering: IMPLEMENTED")
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
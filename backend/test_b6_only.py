"""
Simple B6 test to debug anomaly detection issues
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.models.database import LogEntry, LogLevel
from app.services.anomaly_detection import anomaly_service

async def test_b6():
    try:
        print("🧪 Testing B6: Anomaly Detection...")
        
        # Create unique file ID
        unique_file_id = f"test_b6_file_{uuid.uuid4().hex[:8]}"
        print(f"Using file_id: {unique_file_id}")
        
        # Create test log entries
        current_time = datetime.utcnow()
        test_entries = []
        
        # Normal entries
        for i in range(5):
            entry = LogEntry(
                file_id=unique_file_id,
                timestamp=current_time - timedelta(hours=i),
                level=LogLevel.INFO,
                message=f"Normal message {i}",
                source="test_service",
                raw_line=f"[INFO] Normal message {i}",
                line_number=i + 1
            )
            test_entries.append(entry)
        
        # Error entries
        for i in range(3):
            entry = LogEntry(
                file_id=unique_file_id,
                timestamp=current_time - timedelta(minutes=i*5),
                level=LogLevel.ERROR,
                message=f"Error message {i}",
                source="error_service",
                raw_line=f"[ERROR] Error message {i}",
                line_number=10 + i
            )
            test_entries.append(entry)
        
        print(f"Created {len(test_entries)} test entries")
        
        # Run anomaly detection
        anomalies = await anomaly_service.detect_anomalies(unique_file_id, test_entries)
        print(f"✅ Detected {len(anomalies)} anomalies")
        
        # Test summary
        summary = await anomaly_service.get_anomaly_summary(unique_file_id)
        print(f"✅ Summary: {summary['total_anomalies']} total anomalies")
        
        return True
        
    except Exception as e:
        print(f"❌ B6 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_b6())
    if result:
        print("🎉 B6 test PASSED!")
    else:
        print("❌ B6 test FAILED!")
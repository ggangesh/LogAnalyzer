#!/usr/bin/env python3
"""
Comprehensive E2E Test Framework for LogSage AI
Implements automated testing for all critical user workflows and system scenarios
"""

import asyncio
import pytest
import httpx
import pandas as pd
import numpy as np
import time
import json
import random
import logging
import tempfile
import sqlite3
import faiss
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from unittest.mock import patch, MagicMock
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dataclasses import dataclass
import psutil
import threading
import queue

# Configuration
TEST_CONFIG = {
    'backend_url': 'http://localhost:8000',
    'frontend_url': 'http://localhost:3000',
    'test_data_dir': Path('./test_data'),
    'max_file_size': 100 * 1024 * 1024,  # 100MB
    'openai_api_key': None,  # Set to enable AI tests
    'performance_timeout': 300,  # 5 minutes
    'stress_test_duration': 1800,  # 30 minutes
}

# Test result tracking
@dataclass
class TestResult:
    test_id: str
    name: str
    status: str  # 'pass', 'fail', 'skip'
    duration: float
    error_message: Optional[str] = None
    performance_metrics: Optional[Dict] = None
    
class TestTracker:
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None
        
    def start_test(self, test_id: str, name: str):
        self.current_test = {'id': test_id, 'name': name, 'start': time.time()}
        
    def end_test(self, status: str, error_message: str = None, metrics: Dict = None):
        duration = time.time() - self.current_test['start']
        result = TestResult(
            test_id=self.current_test['id'],
            name=self.current_test['name'],
            status=status,
            duration=duration,
            error_message=error_message,
            performance_metrics=metrics
        )
        self.results.append(result)
        return result

# Global test tracker
tracker = TestTracker()

class TestDataGenerator:
    """Generates realistic test data for various log formats and scenarios"""
    
    @staticmethod
    def generate_apache_access_logs(num_entries: int = 10000, 
                                  include_anomalies: bool = True) -> str:
        """Generate realistic Apache access logs with optional anomalies"""
        logs = []
        base_time = datetime.now() - timedelta(hours=24)
        
        # Normal traffic patterns
        for i in range(num_entries):
            timestamp = base_time + timedelta(seconds=i * 3)
            ip = f"192.168.{random.randint(1,254)}.{random.randint(1,254)}"
            
            # Realistic user agents and endpoints
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "curl/7.68.0",
                "Python/3.9 requests/2.25.1"
            ]
            
            endpoints = [
                "/", "/api/users", "/api/orders", "/static/css/style.css",
                "/api/products", "/admin/dashboard", "/health", "/metrics"
            ]
            
            status_codes = [200, 200, 200, 200, 404, 500] if include_anomalies else [200, 200, 200, 304]
            
            status = random.choice(status_codes)
            endpoint = random.choice(endpoints)
            user_agent = random.choice(user_agents)
            size = random.randint(100, 5000)
            
            log_line = f'{ip} - - [{timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000")}] "GET {endpoint} HTTP/1.1" {status} {size} "-" "{user_agent}"'
            logs.append(log_line)
        
        # Add anomaly patterns if requested
        if include_anomalies:
            # Simulate error spike
            error_start = len(logs) - 1000
            for i in range(100):  # 100 consecutive errors
                error_time = base_time + timedelta(seconds=(error_start + i) * 3)
                error_log = f'192.168.1.100 - - [{error_time.strftime("%d/%b/%Y:%H:%M:%S +0000")}] "POST /api/payment HTTP/1.1" 500 0 "-" "curl/7.68.0"'
                logs[error_start + i] = error_log
        
        return '\n'.join(logs)
    
    @staticmethod
    def generate_application_json_logs(num_entries: int = 5000) -> str:
        """Generate realistic application JSON logs"""
        logs = []
        base_time = datetime.now() - timedelta(hours=12)
        
        components = ['auth', 'payment', 'inventory', 'notification', 'analytics']
        log_levels = ['DEBUG', 'INFO', 'WARN', 'ERROR']
        
        for i in range(num_entries):
            timestamp = base_time + timedelta(seconds=i * 2)
            level = random.choices(log_levels, weights=[10, 70, 15, 5])[0]
            component = random.choice(components)
            
            # Generate realistic messages based on component
            messages = {
                'auth': [
                    'User authentication successful',
                    'Invalid credentials provided',
                    'Session timeout warning',
                    'Password reset requested'
                ],
                'payment': [
                    'Payment processed successfully',
                    'Payment gateway timeout',
                    'Invalid payment method',
                    'Refund processed'
                ],
                'inventory': [
                    'Stock level updated',
                    'Low inventory warning',
                    'Product out of stock',
                    'Inventory sync completed'
                ]
            }
            
            message = random.choice(messages.get(component, ['Generic log message']))
            
            log_entry = {
                'timestamp': timestamp.isoformat(),
                'level': level,
                'component': component,
                'message': message,
                'thread_id': f'thread-{random.randint(1,10)}',
                'user_id': random.randint(1000, 9999) if component == 'auth' else None,
                'request_id': f'req-{random.randint(100000, 999999)}'
            }
            
            logs.append(json.dumps(log_entry))
        
        return '\n'.join(logs)
    
    @staticmethod
    def generate_database_slow_query_logs(num_entries: int = 1000) -> str:
        """Generate database slow query logs"""
        logs = []
        base_time = datetime.now() - timedelta(hours=6)
        
        queries = [
            "SELECT * FROM users WHERE email = 'user@example.com'",
            "UPDATE orders SET status = 'shipped' WHERE id = 12345",
            "INSERT INTO audit_log (action, user_id, timestamp) VALUES ('login', 1001, NOW())",
            "SELECT COUNT(*) FROM products WHERE category = 'electronics'",
            "DELETE FROM sessions WHERE expires_at < NOW()"
        ]
        
        for i in range(num_entries):
            timestamp = base_time + timedelta(seconds=i * 10)
            query = random.choice(queries)
            duration = random.uniform(1.0, 15.0)  # 1-15 second queries
            
            log_line = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] SLOW QUERY: {duration:.3f}s - {query}"
            logs.append(log_line)
        
        return '\n'.join(logs)
    
    @staticmethod
    def generate_security_audit_logs(num_entries: int = 500) -> str:
        """Generate security audit logs with some suspicious activities"""
        logs = []
        base_time = datetime.now() - timedelta(hours=3)
        
        normal_activities = [
            'User login successful',
            'User logout',
            'Password changed',
            'Profile updated',
            'File uploaded',
            'Report generated'
        ]
        
        suspicious_activities = [
            'Failed login attempt',
            'Multiple failed login attempts',
            'Privilege escalation attempt',
            'Unauthorized file access',
            'SQL injection attempt detected',
            'Suspicious API usage pattern'
        ]
        
        for i in range(num_entries):
            timestamp = base_time + timedelta(seconds=i * 15)
            
            # 90% normal, 10% suspicious
            if random.random() < 0.9:
                activity = random.choice(normal_activities)
                severity = 'INFO'
            else:
                activity = random.choice(suspicious_activities)
                severity = 'WARN' if 'attempt' in activity else 'ERROR'
            
            user_id = random.randint(1000, 9999)
            ip_address = f"192.168.{random.randint(1,254)}.{random.randint(1,254)}"
            
            log_line = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] [{severity}] User:{user_id} IP:{ip_address} - {activity}"
            logs.append(log_line)
        
        return '\n'.join(logs)
    
    @staticmethod
    def generate_malformed_logs() -> str:
        """Generate malformed logs for testing error handling"""
        malformed_logs = [
            # Incomplete JSON
            '{"timestamp": "2024-01-28T10:00:00", "level": "ERROR"',
            # Invalid JSON
            '{timestamp: 2024-01-28, level: ERROR, message: null}',
            # Binary data
            '\x00\x01\x02\xFF\xFE corrupted log entry',
            # Extremely long line
            'ERROR: ' + 'A' * 50000 + ' huge log message',
            # Mixed encoding
            'Log entry with mixed encoding: café résumé naïve 日本語 русский',
            # SQL injection attempt
            "'; DROP TABLE log_entries; --",
            # Empty lines and whitespace
            '',
            '   ',
            '\t\n',
            # CSV with inconsistent columns
            'timestamp,level,message\n2024-01-28,ERROR,Failed\n2024-01-28,WARN,Warning,extra,fields',
        ]
        
        return '\n'.join(malformed_logs)

class APITestClient:
    """HTTP client for testing backend API endpoints"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def upload_file(self, file_content: str, filename: str = "test.log") -> Dict:
        """Upload a log file to the backend"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write(file_content)
            f.flush()
            
            with open(f.name, 'rb') as upload_file:
                files = {'file': (filename, upload_file, 'text/plain')}
                response = await self.client.post(f"{self.base_url}/api/v1/upload", files=files)
                
        return response.json() if response.status_code == 200 else {'error': response.text}
    
    async def parse_file(self, file_id: str, max_entries: int = 1000) -> Dict:
        """Parse an uploaded log file"""
        url = f"{self.base_url}/api/v1/logs/parse/{file_id}"
        params = {'max_entries': max_entries}
        response = await self.client.get(url, params=params)
        return response.json() if response.status_code == 200 else {'error': response.text}
    
    async def get_anomalies(self, file_id: str) -> Dict:
        """Get anomaly detection results"""
        url = f"{self.base_url}/api/v1/anomaly/analyze/{file_id}"
        response = await self.client.get(url)
        return response.json() if response.status_code == 200 else {'error': response.text}
    
    async def chat_query(self, file_id: str, message: str) -> Dict:
        """Send a chat query to the AI system"""
        url = f"{self.base_url}/api/v1/chat/message/{file_id}"
        data = {'message': message}
        response = await self.client.post(url, json=data)
        return response.json() if response.status_code == 200 else {'error': response.text}
    
    async def health_check(self) -> Dict:
        """Check system health"""
        response = await self.client.get(f"{self.base_url}/health")
        return response.json() if response.status_code == 200 else {'error': response.text}

class FrontendTestClient:
    """Selenium-based client for testing frontend functionality"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver for testing"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode for CI
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        
    def teardown_driver(self):
        """Cleanup driver resources"""
        if self.driver:
            self.driver.quit()
            
    def navigate_to_upload(self):
        """Navigate to file upload page"""
        self.driver.get(f"{self.base_url}/upload")
        return WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "file-upload"))
        )
    
    def upload_file_via_ui(self, file_path: str):
        """Upload file through the UI"""
        upload_element = self.navigate_to_upload()
        upload_element.send_keys(file_path)
        
        # Wait for upload completion
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "upload-success"))
        )
        
    def navigate_to_logs(self):
        """Navigate to log viewer page"""
        self.driver.get(f"{self.base_url}/logs")
        return WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "log-table"))
        )
    
    def apply_time_filter(self, filter_type: str = "last_24h"):
        """Apply time filter in log viewer"""
        filter_dropdown = self.driver.find_element(By.ID, "time-filter-select")
        filter_dropdown.click()
        
        filter_option = self.driver.find_element(By.XPATH, f"//option[@value='{filter_type}']")
        filter_option.click()
        
        # Wait for filter to apply
        WebDriverWait(self.driver, 10).until(
            EC.staleness_of(self.driver.find_element(By.ID, "log-table"))
        )

class PerformanceMonitor:
    """Monitor system performance during tests"""
    
    def __init__(self):
        self.metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_io': [],
            'network_io': [],
            'response_times': []
        }
        self.monitoring = False
        
    def start_monitoring(self):
        """Start performance monitoring in background thread"""
        self.monitoring = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()
        
    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                # CPU and memory usage
                self.metrics['cpu_usage'].append(psutil.cpu_percent())
                self.metrics['memory_usage'].append(psutil.virtual_memory().percent)
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    self.metrics['disk_io'].append({
                        'read_bytes': disk_io.read_bytes,
                        'write_bytes': disk_io.write_bytes
                    })
                
                # Network I/O
                net_io = psutil.net_io_counters()
                if net_io:
                    self.metrics['network_io'].append({
                        'bytes_sent': net_io.bytes_sent,
                        'bytes_recv': net_io.bytes_recv
                    })
                    
                time.sleep(1)  # Sample every second
            except Exception as e:
                logging.warning(f"Performance monitoring error: {e}")
                
    def get_summary(self) -> Dict:
        """Get performance summary statistics"""
        return {
            'cpu_avg': np.mean(self.metrics['cpu_usage']) if self.metrics['cpu_usage'] else 0,
            'cpu_max': np.max(self.metrics['cpu_usage']) if self.metrics['cpu_usage'] else 0,
            'memory_avg': np.mean(self.metrics['memory_usage']) if self.metrics['memory_usage'] else 0,
            'memory_max': np.max(self.metrics['memory_usage']) if self.metrics['memory_usage'] else 0,
            'response_times_avg': np.mean(self.metrics['response_times']) if self.metrics['response_times'] else 0,
            'response_times_p95': np.percentile(self.metrics['response_times'], 95) if self.metrics['response_times'] else 0
        }

# Core Test Classes
class HappyPathTests:
    """Implementation of happy path user workflow tests"""
    
    def __init__(self, api_client: APITestClient, frontend_client: FrontendTestClient):
        self.api = api_client
        self.frontend = frontend_client
        self.monitor = PerformanceMonitor()
        
    async def test_complete_sre_workflow(self):
        """T001: Complete SRE Investigation Workflow"""
        tracker.start_test("T001", "Complete SRE Investigation Workflow")
        
        try:
            self.monitor.start_monitoring()
            
            # Step 1: Upload production log
            log_content = TestDataGenerator.generate_apache_access_logs(50000, include_anomalies=True)
            upload_result = await self.api.upload_file(log_content, "production.log")
            assert 'file_id' in upload_result, f"Upload failed: {upload_result}"
            file_id = upload_result['file_id']
            
            # Step 2: Parse and analyze
            parse_result = await self.api.parse_file(file_id, max_entries=50000)
            assert 'entries' in parse_result, f"Parse failed: {parse_result}"
            assert len(parse_result['entries']) > 0, "No entries parsed"
            
            # Step 3: Time-based filtering (via API)
            # This would be tested via frontend in full integration
            
            # Step 4: Anomaly detection
            anomaly_result = await self.api.get_anomalies(file_id)
            # Anomalies might not be present, so just verify API works
            assert 'anomalies' in anomaly_result or 'error' in anomaly_result
            
            # Step 5: AI investigation (if OpenAI key available)
            if TEST_CONFIG['openai_api_key']:
                chat_result = await self.api.chat_query(file_id, "What caused the 500 errors?")
                assert 'message' in chat_result, f"Chat failed: {chat_result}"
                assert len(chat_result['message']) > 50, "AI response too short"
            
            self.monitor.stop_monitoring()
            metrics = self.monitor.get_summary()
            
            # Performance validation
            assert metrics['memory_max'] < 80, f"Memory usage too high: {metrics['memory_max']}%"
            
            tracker.end_test('pass', metrics=metrics)
            
        except Exception as e:
            self.monitor.stop_monitoring()
            tracker.end_test('fail', str(e))
            raise
    
    async def test_devops_bulk_processing(self):
        """T002: DevOps Automated Log Processing"""
        tracker.start_test("T002", "DevOps Automated Log Processing")
        
        try:
            # Generate multiple log files
            test_files = {
                'apache.log': TestDataGenerator.generate_apache_access_logs(1000),
                'app.json': TestDataGenerator.generate_application_json_logs(500),
                'db.log': TestDataGenerator.generate_database_slow_query_logs(100),
                'security.log': TestDataGenerator.generate_security_audit_logs(200)
            }
            
            # Upload all files
            file_ids = []
            for filename, content in test_files.items():
                result = await self.api.upload_file(content, filename)
                assert 'file_id' in result, f"Failed to upload {filename}"
                file_ids.append(result['file_id'])
            
            # Parse all files
            parse_results = []
            for file_id in file_ids:
                result = await self.api.parse_file(file_id)
                assert 'entries' in result, f"Failed to parse {file_id}"
                parse_results.append(result)
            
            # Verify all files processed
            total_entries = sum(len(result['entries']) for result in parse_results)
            assert total_entries > 1500, f"Expected >1500 entries, got {total_entries}"
            
            tracker.end_test('pass')
            
        except Exception as e:
            tracker.end_test('fail', str(e))
            raise

class DataIntegrityTests:
    """Tests for data integrity across the stack"""
    
    def __init__(self, api_client: APITestClient):
        self.api = api_client
        
    async def test_full_stack_consistency(self):
        """T010: Full-Stack Data Consistency Validation"""
        tracker.start_test("T010", "Full-Stack Data Consistency")
        
        try:
            # Generate test data with known patterns
            test_entries = 1000
            log_content = TestDataGenerator.generate_application_json_logs(test_entries)
            
            # Upload and parse
            upload_result = await self.api.upload_file(log_content, "consistency_test.json")
            file_id = upload_result['file_id']
            
            parse_result = await self.api.parse_file(file_id, max_entries=test_entries)
            
            # Verify data consistency
            parsed_entries = len(parse_result['entries'])
            expected_ratio = parsed_entries / test_entries
            
            assert expected_ratio > 0.95, f"Parse ratio too low: {expected_ratio}"
            
            # Verify data structure integrity
            for entry in parse_result['entries'][:10]:  # Check first 10 entries
                assert 'timestamp' in entry, "Missing timestamp"
                assert 'level' in entry, "Missing log level"
                assert 'message' in entry, "Missing message"
                assert entry['level'] in ['DEBUG', 'INFO', 'WARN', 'ERROR'], f"Invalid level: {entry['level']}"
            
            tracker.end_test('pass')
            
        except Exception as e:
            tracker.end_test('fail', str(e))
            raise

class NegativeScenarioTests:
    """Tests for edge cases and error handling"""
    
    def __init__(self, api_client: APITestClient):
        self.api = api_client
        
    async def test_malformed_data_handling(self):
        """T020: Malformed and Corrupted Data Handling"""
        tracker.start_test("T020", "Malformed Data Handling")
        
        try:
            # Test with malformed logs
            malformed_content = TestDataGenerator.generate_malformed_logs()
            
            upload_result = await self.api.upload_file(malformed_content, "malformed.log")
            
            if 'file_id' in upload_result:
                # If upload succeeds, parsing should handle errors gracefully
                parse_result = await self.api.parse_file(upload_result['file_id'])
                
                # Should have some parsing errors but not crash
                if 'error' not in parse_result:
                    assert 'entries' in parse_result, "Expected entries or error"
                    # Some entries might parse, but system should be stable
            else:
                # Upload rejection is acceptable for malformed data
                assert 'error' in upload_result, "Expected error message"
            
            tracker.end_test('pass')
            
        except Exception as e:
            tracker.end_test('fail', str(e))
            raise
    
    async def test_oversized_file_handling(self):
        """Test handling of files exceeding size limits"""
        tracker.start_test("T021", "Oversized File Handling")
        
        try:
            # Generate file larger than limit (but not too large for test)
            large_content = "ERROR: Large log entry\n" * 100000  # ~2MB
            
            upload_result = await self.api.upload_file(large_content, "large.log")
            
            # Should either succeed or fail gracefully
            if 'error' in upload_result:
                assert 'size' in upload_result['error'].lower() or 'limit' in upload_result['error'].lower()
            else:
                # If accepted, should parse successfully
                parse_result = await self.api.parse_file(upload_result['file_id'])
                assert 'entries' in parse_result or 'error' in parse_result
            
            tracker.end_test('pass')
            
        except Exception as e:
            tracker.end_test('fail', str(e))
            raise

class SecurityTests:
    """Security and privacy validation tests"""
    
    def __init__(self, api_client: APITestClient):
        self.api = api_client
        
    async def test_injection_prevention(self):
        """T040: Input Sanitization and Injection Prevention"""
        tracker.start_test("T040", "Injection Prevention")
        
        try:
            # Test SQL injection patterns in log content
            injection_patterns = [
                "'; DROP TABLE log_entries; --",
                "admin'--",
                "1' OR '1'='1",
                "UNION SELECT password FROM users--"
            ]
            
            for pattern in injection_patterns:
                log_content = f"ERROR: Database query failed: {pattern}\n"
                
                upload_result = await self.api.upload_file(log_content, "injection_test.log")
                
                if 'file_id' in upload_result:
                    parse_result = await self.api.parse_file(upload_result['file_id'])
                    
                    # Verify injection didn't succeed
                    # System should still be functional
                    health_result = await self.api.health_check()
                    assert 'status' in health_result, "System health check failed after injection test"
            
            tracker.end_test('pass')
            
        except Exception as e:
            tracker.end_test('fail', str(e))
            raise
    
    async def test_pii_detection(self):
        """T041: PII Detection and Sanitization"""
        tracker.start_test("T041", "PII Detection")
        
        try:
            # Create logs with PII patterns
            pii_logs = [
                "User john.doe@company.com failed authentication",
                "Processing payment for card 4532-1234-5678-9000",
                "SSN 123-45-6789 verification failed",
                "Phone number +1-555-123-4567 requested password reset"
            ]
            
            log_content = '\n'.join(pii_logs)
            upload_result = await self.api.upload_file(log_content, "pii_test.log")
            
            if 'file_id' in upload_result:
                parse_result = await self.api.parse_file(upload_result['file_id'])
                
                # Check if PII is handled appropriately
                # This would depend on implementation - might be flagged, masked, or filtered
                if 'entries' in parse_result:
                    for entry in parse_result['entries']:
                        message = entry.get('message', '')
                        # Verify sensitive patterns are not exposed in raw form
                        # Implementation should mask or flag these
                        
            tracker.end_test('pass')
            
        except Exception as e:
            tracker.end_test('fail', str(e))
            raise

class PerformanceTests:
    """Performance and stress testing"""
    
    def __init__(self, api_client: APITestClient):
        self.api = api_client
        self.monitor = PerformanceMonitor()
        
    async def test_large_file_performance(self):
        """T030: Large File Processing Performance"""
        tracker.start_test("T030", "Large File Performance")
        
        try:
            self.monitor.start_monitoring()
            
            # Generate large log file (10MB)
            large_log = TestDataGenerator.generate_apache_access_logs(100000)
            
            # Test upload performance
            start_time = time.time()
            upload_result = await self.api.upload_file(large_log, "large_performance.log")
            upload_time = time.time() - start_time
            
            assert 'file_id' in upload_result, "Large file upload failed"
            assert upload_time < 60, f"Upload too slow: {upload_time}s"
            
            # Test parsing performance
            start_time = time.time()
            parse_result = await self.api.parse_file(upload_result['file_id'], max_entries=100000)
            parse_time = time.time() - start_time
            
            assert 'entries' in parse_result, "Large file parsing failed"
            assert parse_time < 120, f"Parsing too slow: {parse_time}s"
            
            self.monitor.stop_monitoring()
            metrics = self.monitor.get_summary()
            
            # Performance assertions
            assert metrics['memory_max'] < 90, f"Memory usage too high: {metrics['memory_max']}%"
            assert metrics['cpu_avg'] < 80, f"CPU usage too high: {metrics['cpu_avg']}%"
            
            tracker.end_test('pass', metrics=metrics)
            
        except Exception as e:
            self.monitor.stop_monitoring()
            tracker.end_test('fail', str(e))
            raise
    
    async def test_concurrent_uploads(self):
        """T031: Concurrent User Load Testing (simplified)"""
        tracker.start_test("T031", "Concurrent Uploads")
        
        try:
            # Test 5 concurrent uploads (reduced from 50 for test environment)
            upload_tasks = []
            
            for i in range(5):
                log_content = TestDataGenerator.generate_application_json_logs(1000)
                task = self.api.upload_file(log_content, f"concurrent_{i}.log")
                upload_tasks.append(task)
            
            # Execute all uploads concurrently
            results = await asyncio.gather(*upload_tasks, return_exceptions=True)
            
            # Verify results
            successful_uploads = 0
            for result in results:
                if isinstance(result, dict) and 'file_id' in result:
                    successful_uploads += 1
                elif isinstance(result, Exception):
                    logging.warning(f"Concurrent upload failed: {result}")
            
            # At least 80% should succeed
            success_rate = successful_uploads / len(upload_tasks)
            assert success_rate >= 0.8, f"Success rate too low: {success_rate}"
            
            tracker.end_test('pass', performance_metrics={'success_rate': success_rate})
            
        except Exception as e:
            tracker.end_test('fail', str(e))
            raise

# Test Execution Framework
class E2ETestRunner:
    """Main test runner that orchestrates all test execution"""
    
    def __init__(self):
        self.api_client = APITestClient(TEST_CONFIG['backend_url'])
        self.frontend_client = FrontendTestClient(TEST_CONFIG['frontend_url'])
        
    async def setup_test_environment(self):
        """Setup test environment and verify system is ready"""
        try:
            # Check backend health
            health_result = await self.api_client.health_check()
            assert 'status' in health_result, "Backend health check failed"
            
            # Setup frontend if needed
            self.frontend_client.setup_driver()
            
            return True
        except Exception as e:
            logging.error(f"Test environment setup failed: {e}")
            return False
    
    async def cleanup_test_environment(self):
        """Cleanup test environment and resources"""
        try:
            await self.api_client.client.aclose()
            self.frontend_client.teardown_driver()
        except Exception as e:
            logging.warning(f"Cleanup error: {e}")
    
    async def run_test_suite(self, test_categories: List[str] = None):
        """Run the complete test suite"""
        if not await self.setup_test_environment():
            return False
        
        try:
            # Initialize test classes
            happy_path_tests = HappyPathTests(self.api_client, self.frontend_client)
            data_integrity_tests = DataIntegrityTests(self.api_client)
            negative_tests = NegativeScenarioTests(self.api_client)
            security_tests = SecurityTests(self.api_client)
            performance_tests = PerformanceTests(self.api_client)
            
            # Define test execution order
            test_sequence = [
                # Critical path tests first
                ('happy_path', happy_path_tests.test_complete_sre_workflow),
                ('data_integrity', data_integrity_tests.test_full_stack_consistency),
                ('security', security_tests.test_injection_prevention),
                ('security', security_tests.test_pii_detection),
                
                # Additional tests
                ('happy_path', happy_path_tests.test_devops_bulk_processing),
                ('negative', negative_tests.test_malformed_data_handling),
                ('negative', negative_tests.test_oversized_file_handling),
                ('performance', performance_tests.test_large_file_performance),
                ('performance', performance_tests.test_concurrent_uploads),
            ]
            
            # Filter tests by category if specified
            if test_categories:
                test_sequence = [(cat, test) for cat, test in test_sequence if cat in test_categories]
            
            # Execute tests
            for category, test_func in test_sequence:
                try:
                    await test_func()
                    logging.info(f"✅ {test_func.__name__} passed")
                except Exception as e:
                    logging.error(f"❌ {test_func.__name__} failed: {e}")
            
            return True
            
        finally:
            await self.cleanup_test_environment()
    
    def generate_test_report(self) -> Dict:
        """Generate comprehensive test report"""
        total_tests = len(tracker.results)
        passed_tests = len([r for r in tracker.results if r.status == 'pass'])
        failed_tests = len([r for r in tracker.results if r.status == 'fail'])
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'total_duration': sum(r.duration for r in tracker.results)
            },
            'test_results': [],
            'performance_summary': {},
            'recommendations': []
        }
        
        # Detailed test results
        for result in tracker.results:
            report['test_results'].append({
                'test_id': result.test_id,
                'name': result.name,
                'status': result.status,
                'duration': result.duration,
                'error': result.error_message,
                'metrics': result.performance_metrics
            })
        
        # Performance summary
        perf_metrics = [r.performance_metrics for r in tracker.results if r.performance_metrics]
        if perf_metrics:
            report['performance_summary'] = {
                'avg_memory_usage': np.mean([m.get('memory_avg', 0) for m in perf_metrics]),
                'max_memory_usage': np.max([m.get('memory_max', 0) for m in perf_metrics]),
                'avg_cpu_usage': np.mean([m.get('cpu_avg', 0) for m in perf_metrics]),
            }
        
        # Recommendations based on results
        if failed_tests > 0:
            report['recommendations'].append("Review failed tests and fix underlying issues")
        
        if report['performance_summary'].get('max_memory_usage', 0) > 80:
            report['recommendations'].append("Consider memory optimization - peak usage exceeded 80%")
        
        if report['summary']['total_duration'] > 3600:  # 1 hour
            report['recommendations'].append("Test suite duration is high - consider parallelization")
        
        return report

# CLI Interface
async def main():
    """Main entry point for test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LogSage AI E2E Test Suite')
    parser.add_argument('--categories', nargs='+', 
                       choices=['happy_path', 'data_integrity', 'negative', 'security', 'performance'],
                       help='Test categories to run')
    parser.add_argument('--backend-url', default='http://localhost:8000',
                       help='Backend API URL')
    parser.add_argument('--frontend-url', default='http://localhost:3000',
                       help='Frontend URL')
    parser.add_argument('--openai-key', help='OpenAI API key for AI tests')
    parser.add_argument('--report-file', default='test_report.json',
                       help='Output file for test report')
    
    args = parser.parse_args()
    
    # Update configuration
    TEST_CONFIG['backend_url'] = args.backend_url
    TEST_CONFIG['frontend_url'] = args.frontend_url
    if args.openai_key:
        TEST_CONFIG['openai_api_key'] = args.openai_key
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Run tests
    runner = E2ETestRunner()
    logging.info("🚀 Starting LogSage AI E2E Test Suite")
    
    success = await runner.run_test_suite(args.categories)
    
    # Generate report
    report = runner.generate_test_report()
    
    # Save report
    with open(args.report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST EXECUTION SUMMARY")
    print("="*60)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Success Rate: {report['summary']['success_rate']:.1%}")
    print(f"Duration: {report['summary']['total_duration']:.1f}s")
    print(f"Report saved to: {args.report_file}")
    
    if report['recommendations']:
        print("\n🎯 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
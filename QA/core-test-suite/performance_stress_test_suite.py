#!/usr/bin/env python3
"""
Performance and Stress Test Suite for LogSage AI
Focuses on high-performance testing, realistic production scenarios, and boundary conditions
"""

import asyncio
import aiohttp
import time
import psutil
import threading
import queue
import random
import json
import tempfile
import sqlite3
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
import logging
import gc
import resource

# Performance test configuration
PERF_CONFIG = {
    'backend_url': 'http://localhost:8000',
    'max_concurrent_users': 100,
    'stress_test_duration': 1800,  # 30 minutes
    'load_ramp_up_time': 300,     # 5 minutes
    'large_file_size_mb': 500,    # 500MB files
    'memory_limit_gb': 16,        # 16GB memory limit
    'cpu_threshold': 85,          # 85% CPU threshold
    'response_time_p95_ms': 5000, # 5 second 95th percentile
    'throughput_target': 1000,    # Requests per minute
}

@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    test_name: str
    start_time: datetime
    end_time: datetime
    duration: float
    
    # Response time metrics
    response_times: List[float] = field(default_factory=list)
    avg_response_time: float = 0.0
    p50_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    max_response_time: float = 0.0
    
    # Throughput metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    requests_per_second: float = 0.0
    
    # System metrics
    peak_cpu_usage: float = 0.0
    avg_cpu_usage: float = 0.0
    peak_memory_usage: float = 0.0
    avg_memory_usage: float = 0.0
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    
    # Error metrics
    errors: List[str] = field(default_factory=list)
    timeout_count: int = 0
    connection_errors: int = 0
    
    def calculate_derived_metrics(self):
        """Calculate derived metrics from raw data"""
        if self.response_times:
            self.avg_response_time = statistics.mean(self.response_times)
            self.p50_response_time = np.percentile(self.response_times, 50)
            self.p95_response_time = np.percentile(self.response_times, 95)
            self.p99_response_time = np.percentile(self.response_times, 99)
            self.max_response_time = max(self.response_times)
        
        if self.duration > 0:
            self.requests_per_second = self.total_requests / self.duration
    
    def meets_performance_criteria(self) -> Tuple[bool, List[str]]:
        """Check if metrics meet performance criteria"""
        issues = []
        
        if self.p95_response_time > PERF_CONFIG['response_time_p95_ms']:
            issues.append(f"P95 response time {self.p95_response_time:.1f}ms exceeds {PERF_CONFIG['response_time_p95_ms']}ms")
        
        if self.peak_cpu_usage > PERF_CONFIG['cpu_threshold']:
            issues.append(f"Peak CPU usage {self.peak_cpu_usage:.1f}% exceeds {PERF_CONFIG['cpu_threshold']}%")
        
        error_rate = self.failed_requests / self.total_requests if self.total_requests > 0 else 0
        if error_rate > 0.05:  # 5% error rate threshold
            issues.append(f"Error rate {error_rate:.1%} exceeds 5%")
        
        if self.requests_per_second < (PERF_CONFIG['throughput_target'] / 60) * 0.8:  # 80% of target
            issues.append(f"Throughput {self.requests_per_second:.1f} req/s below target")
        
        return len(issues) == 0, issues

class SystemMonitor:
    """Advanced system monitoring with detailed metrics collection"""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_io': [],
            'network_io': [],
            'open_files': [],
            'thread_count': [],
            'timestamps': []
        }
        self.monitoring_thread = None
        
    def start_monitoring(self, interval: float = 0.5):
        """Start system monitoring with specified interval"""
        self.monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, args=(interval,), daemon=True)
        self.monitoring_thread.start()
        
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
            
    def _monitor_loop(self, interval: float):
        """System monitoring loop"""
        process = psutil.Process()
        
        while self.monitoring:
            try:
                timestamp = time.time()
                
                # CPU and memory metrics
                cpu_percent = psutil.cpu_percent(interval=None)
                memory_info = psutil.virtual_memory()
                process_memory = process.memory_info()
                
                # Disk I/O metrics
                disk_io = psutil.disk_io_counters()
                
                # Network I/O metrics
                network_io = psutil.net_io_counters()
                
                # Process metrics
                open_files = len(process.open_files())
                thread_count = process.num_threads()
                
                # Store metrics
                self.metrics['timestamps'].append(timestamp)
                self.metrics['cpu_usage'].append(cpu_percent)
                self.metrics['memory_usage'].append(memory_info.percent)
                self.metrics['disk_io'].append({
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0
                })
                self.metrics['network_io'].append({
                    'bytes_sent': network_io.bytes_sent if network_io else 0,
                    'bytes_recv': network_io.bytes_recv if network_io else 0
                })
                self.metrics['open_files'].append(open_files)
                self.metrics['thread_count'].append(thread_count)
                
                time.sleep(interval)
                
            except Exception as e:
                logging.warning(f"Monitoring error: {e}")
                
    def get_summary_metrics(self) -> Dict:
        """Get summary of collected metrics"""
        if not self.metrics['cpu_usage']:
            return {}
            
        return {
            'cpu_avg': statistics.mean(self.metrics['cpu_usage']),
            'cpu_max': max(self.metrics['cpu_usage']),
            'memory_avg': statistics.mean(self.metrics['memory_usage']),
            'memory_max': max(self.metrics['memory_usage']),
            'max_open_files': max(self.metrics['open_files']) if self.metrics['open_files'] else 0,
            'max_threads': max(self.metrics['thread_count']) if self.metrics['thread_count'] else 0,
            'monitoring_duration': self.metrics['timestamps'][-1] - self.metrics['timestamps'][0] if len(self.metrics['timestamps']) > 1 else 0
        }

class RealisticDataGenerator:
    """Generate realistic production-like test data"""
    
    @staticmethod
    def generate_production_log_file(size_mb: int, log_type: str = 'mixed') -> str:
        """Generate large production-like log file"""
        target_size = size_mb * 1024 * 1024  # Convert to bytes
        current_size = 0
        lines = []
        
        base_time = datetime.now() - timedelta(hours=24)
        
        # Define realistic log patterns based on type
        patterns = {
            'apache': RealisticDataGenerator._generate_apache_pattern,
            'application': RealisticDataGenerator._generate_app_pattern,
            'database': RealisticDataGenerator._generate_db_pattern,
            'mixed': RealisticDataGenerator._generate_mixed_pattern
        }
        
        pattern_func = patterns.get(log_type, patterns['mixed'])
        
        entry_count = 0
        while current_size < target_size:
            timestamp = base_time + timedelta(seconds=entry_count * random.uniform(0.1, 2.0))
            log_line = pattern_func(timestamp, entry_count)
            lines.append(log_line)
            current_size += len(log_line.encode('utf-8'))
            entry_count += 1
            
            # Periodically check size to avoid excessive memory use
            if entry_count % 10000 == 0:
                current_size = sum(len(line.encode('utf-8')) for line in lines)
        
        return '\n'.join(lines)
    
    @staticmethod
    def _generate_apache_pattern(timestamp: datetime, entry_count: int) -> str:
        """Generate Apache access log pattern"""
        ips = [f"192.168.{random.randint(1,254)}.{random.randint(1,254)}" for _ in range(100)]
        endpoints = [
            "/", "/api/users", "/api/orders", "/static/css/main.css",
            "/api/products", "/admin", "/health", "/metrics", "/api/analytics"
        ]
        
        # Simulate realistic traffic patterns
        if entry_count % 1000 < 50:  # 5% error rate during peak
            status_codes = [500, 502, 503, 504]
        elif entry_count % 100 < 5:  # 5% 4xx errors
            status_codes = [404, 403, 400, 429]
        else:
            status_codes = [200, 200, 200, 304]  # Mostly success
        
        ip = random.choice(ips)
        endpoint = random.choice(endpoints)
        status = random.choice(status_codes)
        size = random.randint(100, 10000)
        
        return f'{ip} - - [{timestamp.strftime("%d/%b/%Y:%H:%M:%S +0000")}] "GET {endpoint} HTTP/1.1" {status} {size} "-" "Mozilla/5.0"'
    
    @staticmethod
    def _generate_app_pattern(timestamp: datetime, entry_count: int) -> str:
        """Generate application log pattern"""
        components = ['auth', 'payment', 'inventory', 'notification', 'analytics', 'user-service', 'order-service']
        levels = ['DEBUG', 'INFO', 'WARN', 'ERROR']
        
        # Realistic error distribution
        if entry_count % 10000 < 10:  # 0.1% ERROR
            level = 'ERROR'
        elif entry_count % 1000 < 20:  # 2% WARN
            level = 'WARN'
        elif entry_count % 100 < 15:  # 15% DEBUG
            level = 'DEBUG'
        else:
            level = 'INFO'
        
        component = random.choice(components)
        thread_id = f"thread-{random.randint(1, 50)}"
        request_id = f"req-{random.randint(100000, 999999)}"
        
        messages = {
            'ERROR': [
                'Database connection timeout after 30s',
                'Payment gateway returned error 503',
                'Memory allocation failed',
                'External API call failed with timeout',
                'Cache miss resulted in database overload'
            ],
            'WARN': [
                'High memory usage detected: 85%',
                'Slow query detected: 2.5s',
                'Rate limit approaching for API key',
                'Disk space running low: 15% remaining',
                'Unusual traffic pattern detected'
            ],
            'INFO': [
                'User session created successfully',
                'Payment processed successfully',
                'Inventory updated for product',
                'Notification sent successfully',
                'Health check passed'
            ],
            'DEBUG': [
                'Processing incoming request',
                'Cache hit for key',
                'Database query executed',
                'Validation completed',
                'Response serialized'
            ]
        }
        
        message = random.choice(messages[level])
        
        return json.dumps({
            'timestamp': timestamp.isoformat(),
            'level': level,
            'component': component,
            'thread': thread_id,
            'request_id': request_id,
            'message': message,
            'execution_time': random.uniform(0.001, 5.0) if level in ['WARN', 'ERROR'] else random.uniform(0.001, 0.1)
        })
    
    @staticmethod
    def _generate_db_pattern(timestamp: datetime, entry_count: int) -> str:
        """Generate database log pattern"""
        query_types = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        tables = ['users', 'orders', 'products', 'payments', 'sessions', 'audit_log']
        
        query_type = random.choice(query_types)
        table = random.choice(tables)
        duration = random.uniform(0.001, 10.0)
        
        # Simulate slow queries
        if entry_count % 1000 < 5:  # 0.5% slow queries
            duration = random.uniform(5.0, 30.0)
            
        query = f"{query_type} FROM {table} WHERE id = {random.randint(1, 1000000)}"
        
        return f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] [DB] Duration: {duration:.3f}s Query: {query}"
    
    @staticmethod
    def _generate_mixed_pattern(timestamp: datetime, entry_count: int) -> str:
        """Generate mixed log patterns"""
        patterns = [
            RealisticDataGenerator._generate_apache_pattern,
            RealisticDataGenerator._generate_app_pattern,
            RealisticDataGenerator._generate_db_pattern
        ]
        
        pattern_func = random.choices(patterns, weights=[50, 40, 10])[0]  # 50% Apache, 40% App, 10% DB
        return pattern_func(timestamp, entry_count)

class LoadTestClient:
    """Advanced HTTP client for load testing"""
    
    def __init__(self, base_url: str, max_connections: int = 100):
        self.base_url = base_url
        self.session = None
        self.max_connections = max_connections
        self.metrics = []
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=self.max_connections, limit_per_host=self.max_connections)
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def upload_file(self, file_content: str, filename: str = "test.log") -> Dict:
        """Upload file with performance tracking"""
        start_time = time.time()
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
                f.write(file_content)
                f.flush()
                
                # Upload file
                with open(f.name, 'rb') as upload_file:
                    data = aiohttp.FormData()
                    data.add_field('file', upload_file, filename=filename, content_type='text/plain')
                    
                    async with self.session.post(f"{self.base_url}/api/v1/upload", data=data) as response:
                        response_time = time.time() - start_time
                        result = await response.json() if response.status == 200 else {'error': await response.text()}
                        
                        self.metrics.append({
                            'operation': 'upload',
                            'response_time': response_time,
                            'status_code': response.status,
                            'file_size': len(file_content)
                        })
                        
                        return result
                        
        except Exception as e:
            response_time = time.time() - start_time
            self.metrics.append({
                'operation': 'upload',
                'response_time': response_time,
                'status_code': 0,
                'error': str(e)
            })
            return {'error': str(e)}
    
    async def parse_file(self, file_id: str, max_entries: int = 10000) -> Dict:
        """Parse file with performance tracking"""
        start_time = time.time()
        
        try:
            url = f"{self.base_url}/api/v1/logs/parse/{file_id}"
            params = {'max_entries': max_entries}
            
            async with self.session.get(url, params=params) as response:
                response_time = time.time() - start_time
                result = await response.json() if response.status == 200 else {'error': await response.text()}
                
                self.metrics.append({
                    'operation': 'parse',
                    'response_time': response_time,
                    'status_code': response.status,
                    'file_id': file_id
                })
                
                return result
                
        except Exception as e:
            response_time = time.time() - start_time
            self.metrics.append({
                'operation': 'parse',
                'response_time': response_time,
                'status_code': 0,
                'error': str(e)
            })
            return {'error': str(e)}

class PerformanceTestSuite:
    """Comprehensive performance testing suite"""
    
    def __init__(self):
        self.monitor = SystemMonitor()
        self.results = {}
        
    async def test_large_file_processing_performance(self):
        """Test processing of very large files (100MB - 1GB)"""
        logging.info("🚀 Starting Large File Processing Performance Test")
        
        test_sizes = [100, 250, 500]  # MB
        
        for size_mb in test_sizes:
            logging.info(f"Testing {size_mb}MB file processing...")
            
            metrics = PerformanceMetrics(
                test_name=f"large_file_{size_mb}mb",
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration=0
            )
            
            self.monitor.start_monitoring()
            
            try:
                # Generate large file
                start_time = time.time()
                file_content = RealisticDataGenerator.generate_production_log_file(size_mb, 'mixed')
                generation_time = time.time() - start_time
                logging.info(f"Generated {size_mb}MB file in {generation_time:.1f}s")
                
                async with LoadTestClient(PERF_CONFIG['backend_url']) as client:
                    # Upload performance test
                    upload_start = time.time()
                    upload_result = await client.upload_file(file_content, f"large_{size_mb}mb.log")
                    upload_time = time.time() - upload_start
                    
                    if 'file_id' in upload_result:
                        file_id = upload_result['file_id']
                        logging.info(f"Upload completed in {upload_time:.1f}s")
                        
                        # Parse performance test
                        parse_start = time.time()
                        parse_result = await client.parse_file(file_id, max_entries=100000)
                        parse_time = time.time() - parse_start
                        
                        if 'entries' in parse_result:
                            logging.info(f"Parse completed in {parse_time:.1f}s, {len(parse_result['entries'])} entries")
                            
                            metrics.response_times = [upload_time, parse_time]
                            metrics.total_requests = 2
                            metrics.successful_requests = 2
                            metrics.failed_requests = 0
                        else:
                            logging.error(f"Parse failed: {parse_result}")
                            metrics.failed_requests = 1
                            metrics.errors.append(f"Parse failed: {parse_result}")
                    else:
                        logging.error(f"Upload failed: {upload_result}")
                        metrics.failed_requests = 1
                        metrics.errors.append(f"Upload failed: {upload_result}")
                
                metrics.end_time = datetime.now()
                metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
                
            except Exception as e:
                logging.error(f"Large file test failed: {e}")
                metrics.errors.append(str(e))
                metrics.failed_requests += 1
            
            finally:
                self.monitor.stop_monitoring()
                
                # Add system metrics
                sys_metrics = self.monitor.get_summary_metrics()
                metrics.peak_cpu_usage = sys_metrics.get('cpu_max', 0)
                metrics.avg_cpu_usage = sys_metrics.get('cpu_avg', 0)
                metrics.peak_memory_usage = sys_metrics.get('memory_max', 0)
                metrics.avg_memory_usage = sys_metrics.get('memory_avg', 0)
                
                metrics.calculate_derived_metrics()
                self.results[f"large_file_{size_mb}mb"] = metrics
                
                # Performance validation
                passes, issues = metrics.meets_performance_criteria()
                if passes:
                    logging.info(f"✅ {size_mb}MB test passed performance criteria")
                else:
                    logging.warning(f"⚠️ {size_mb}MB test performance issues: {issues}")
    
    async def test_concurrent_user_load(self):
        """Test system under concurrent user load"""
        logging.info("🚀 Starting Concurrent User Load Test")
        
        user_counts = [10, 25, 50]  # Concurrent users
        
        for user_count in user_counts:
            logging.info(f"Testing {user_count} concurrent users...")
            
            metrics = PerformanceMetrics(
                test_name=f"concurrent_users_{user_count}",
                start_time=datetime.now(),
                end_time=datetime.now(),
                duration=0
            )
            
            self.monitor.start_monitoring()
            
            try:
                # Generate test files for each user
                test_files = []
                for i in range(user_count):
                    file_content = RealisticDataGenerator.generate_production_log_file(10, 'mixed')  # 10MB each
                    test_files.append((f"user_{i}_test.log", file_content))
                
                async with LoadTestClient(PERF_CONFIG['backend_url'], max_connections=user_count) as client:
                    # Create concurrent upload tasks
                    upload_tasks = []
                    for filename, content in test_files:
                        task = client.upload_file(content, filename)
                        upload_tasks.append(task)
                    
                    # Execute all uploads concurrently
                    start_time = time.time()
                    results = await asyncio.gather(*upload_tasks, return_exceptions=True)
                    total_time = time.time() - start_time
                    
                    # Analyze results
                    successful_uploads = 0
                    failed_uploads = 0
                    file_ids = []
                    
                    for result in results:
                        if isinstance(result, dict) and 'file_id' in result:
                            successful_uploads += 1
                            file_ids.append(result['file_id'])
                        else:
                            failed_uploads += 1
                            if isinstance(result, Exception):
                                metrics.errors.append(str(result))
                    
                    logging.info(f"Uploads: {successful_uploads} successful, {failed_uploads} failed in {total_time:.1f}s")
                    
                    # Test concurrent parsing
                    if file_ids:
                        parse_tasks = []
                        for file_id in file_ids[:min(10, len(file_ids))]:  # Parse up to 10 files
                            task = client.parse_file(file_id, max_entries=5000)
                            parse_tasks.append(task)
                        
                        parse_start = time.time()
                        parse_results = await asyncio.gather(*parse_tasks, return_exceptions=True)
                        parse_time = time.time() - parse_start
                        
                        successful_parses = sum(1 for r in parse_results if isinstance(r, dict) and 'entries' in r)
                        failed_parses = len(parse_results) - successful_parses
                        
                        logging.info(f"Parses: {successful_parses} successful, {failed_parses} failed in {parse_time:.1f}s")
                    
                    # Collect metrics from client
                    response_times = [m['response_time'] for m in client.metrics if 'response_time' in m]
                    metrics.response_times = response_times
                    metrics.total_requests = len(results) + len(parse_tasks) if 'parse_tasks' in locals() else len(results)
                    metrics.successful_requests = successful_uploads + (successful_parses if 'successful_parses' in locals() else 0)
                    metrics.failed_requests = failed_uploads + (failed_parses if 'failed_parses' in locals() else 0)
                
                metrics.end_time = datetime.now()
                metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
                
            except Exception as e:
                logging.error(f"Concurrent load test failed: {e}")
                metrics.errors.append(str(e))
            
            finally:
                self.monitor.stop_monitoring()
                
                # Add system metrics
                sys_metrics = self.monitor.get_summary_metrics()
                metrics.peak_cpu_usage = sys_metrics.get('cpu_max', 0)
                metrics.avg_cpu_usage = sys_metrics.get('cpu_avg', 0)
                metrics.peak_memory_usage = sys_metrics.get('memory_max', 0)
                metrics.avg_memory_usage = sys_metrics.get('memory_avg', 0)
                
                metrics.calculate_derived_metrics()
                self.results[f"concurrent_users_{user_count}"] = metrics
                
                # Performance validation
                success_rate = metrics.successful_requests / metrics.total_requests if metrics.total_requests > 0 else 0
                if success_rate >= 0.95:  # 95% success rate
                    logging.info(f"✅ {user_count} concurrent users test passed")
                else:
                    logging.warning(f"⚠️ {user_count} concurrent users test: {success_rate:.1%} success rate")
    
    async def test_memory_pressure_scenarios(self):
        """Test system behavior under memory pressure"""
        logging.info("🚀 Starting Memory Pressure Test")
        
        metrics = PerformanceMetrics(
            test_name="memory_pressure",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0
        )
        
        self.monitor.start_monitoring()
        
        try:
            # Monitor initial memory state
            initial_memory = psutil.virtual_memory().percent
            logging.info(f"Initial memory usage: {initial_memory:.1f}%")
            
            async with LoadTestClient(PERF_CONFIG['backend_url']) as client:
                # Upload multiple large files to create memory pressure
                large_files = []
                for i in range(5):  # 5 x 100MB = 500MB of data
                    logging.info(f"Generating large file {i+1}/5...")
                    file_content = RealisticDataGenerator.generate_production_log_file(100, 'mixed')
                    large_files.append((f"memory_pressure_{i}.log", file_content))
                
                # Upload files sequentially to build up memory pressure
                file_ids = []
                upload_times = []
                
                for filename, content in large_files:
                    current_memory = psutil.virtual_memory().percent
                    logging.info(f"Uploading {filename}, current memory: {current_memory:.1f}%")
                    
                    start_time = time.time()
                    result = await client.upload_file(content, filename)
                    upload_time = time.time() - start_time
                    upload_times.append(upload_time)
                    
                    if 'file_id' in result:
                        file_ids.append(result['file_id'])
                        logging.info(f"Upload successful in {upload_time:.1f}s")
                    else:
                        logging.error(f"Upload failed: {result}")
                        metrics.errors.append(f"Upload failed: {result}")
                    
                    # Force garbage collection to test memory management
                    gc.collect()
                
                # Test parsing under memory pressure
                if file_ids:
                    for i, file_id in enumerate(file_ids):
                        current_memory = psutil.virtual_memory().percent
                        logging.info(f"Parsing file {i+1}/{len(file_ids)}, memory: {current_memory:.1f}%")
                        
                        start_time = time.time()
                        result = await client.parse_file(file_id, max_entries=50000)
                        parse_time = time.time() - start_time
                        
                        if 'entries' in result:
                            logging.info(f"Parse successful in {parse_time:.1f}s, {len(result['entries'])} entries")
                            metrics.successful_requests += 1
                        else:
                            logging.error(f"Parse failed: {result}")
                            metrics.failed_requests += 1
                            metrics.errors.append(f"Parse failed: {result}")
                
                metrics.response_times = upload_times
                metrics.total_requests = len(large_files) + len(file_ids)
                
            final_memory = psutil.virtual_memory().percent
            logging.info(f"Final memory usage: {final_memory:.1f}%")
            
            metrics.end_time = datetime.now()
            metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
            
        except Exception as e:
            logging.error(f"Memory pressure test failed: {e}")
            metrics.errors.append(str(e))
            
        finally:
            self.monitor.stop_monitoring()
            
            # Add system metrics
            sys_metrics = self.monitor.get_summary_metrics()
            metrics.peak_cpu_usage = sys_metrics.get('cpu_max', 0)
            metrics.avg_cpu_usage = sys_metrics.get('cpu_avg', 0)
            metrics.peak_memory_usage = sys_metrics.get('memory_max', 0)
            metrics.avg_memory_usage = sys_metrics.get('memory_avg', 0)
            
            metrics.calculate_derived_metrics()
            self.results["memory_pressure"] = metrics
            
            # Memory usage validation
            if metrics.peak_memory_usage < 95:  # Stay under 95% memory
                logging.info("✅ Memory pressure test passed")
            else:
                logging.warning(f"⚠️ Memory pressure test: peaked at {metrics.peak_memory_usage:.1f}%")
    
    async def test_sustained_load_endurance(self):
        """Test system endurance under sustained load"""
        logging.info("🚀 Starting Sustained Load Endurance Test (10 minutes)")
        
        metrics = PerformanceMetrics(
            test_name="sustained_load_10min",
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0
        )
        
        self.monitor.start_monitoring()
        test_duration = 600  # 10 minutes for testing (reduce from 30 minutes)
        
        try:
            async with LoadTestClient(PERF_CONFIG['backend_url']) as client:
                start_time = time.time()
                end_time = start_time + test_duration
                
                request_count = 0
                successful_requests = 0
                failed_requests = 0
                response_times = []
                
                while time.time() < end_time:
                    try:
                        # Generate small log file for sustained testing
                        file_content = RealisticDataGenerator.generate_production_log_file(5, 'mixed')  # 5MB files
                        
                        # Upload and parse cycle
                        cycle_start = time.time()
                        
                        upload_result = await client.upload_file(file_content, f"sustained_{request_count}.log")
                        if 'file_id' in upload_result:
                            parse_result = await client.parse_file(upload_result['file_id'], max_entries=10000)
                            
                            if 'entries' in parse_result:
                                successful_requests += 1
                            else:
                                failed_requests += 1
                        else:
                            failed_requests += 1
                        
                        cycle_time = time.time() - cycle_start
                        response_times.append(cycle_time)
                        request_count += 1
                        
                        # Log progress every 50 requests
                        if request_count % 50 == 0:
                            elapsed = time.time() - start_time
                            current_memory = psutil.virtual_memory().percent
                            logging.info(f"Sustained test: {request_count} requests, {elapsed/60:.1f}min elapsed, memory: {current_memory:.1f}%")
                        
                        # Brief pause to prevent overwhelming the system
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        failed_requests += 1
                        metrics.errors.append(str(e))
                        logging.warning(f"Request failed: {e}")
                
                actual_duration = time.time() - start_time
                logging.info(f"Sustained load test completed: {request_count} requests in {actual_duration/60:.1f} minutes")
                
                metrics.response_times = response_times
                metrics.total_requests = request_count
                metrics.successful_requests = successful_requests
                metrics.failed_requests = failed_requests
                
            metrics.end_time = datetime.now()
            metrics.duration = actual_duration
            
        except Exception as e:
            logging.error(f"Sustained load test failed: {e}")
            metrics.errors.append(str(e))
            
        finally:
            self.monitor.stop_monitoring()
            
            # Add system metrics
            sys_metrics = self.monitor.get_summary_metrics()
            metrics.peak_cpu_usage = sys_metrics.get('cpu_max', 0)
            metrics.avg_cpu_usage = sys_metrics.get('cpu_avg', 0)
            metrics.peak_memory_usage = sys_metrics.get('memory_max', 0)
            metrics.avg_memory_usage = sys_metrics.get('memory_avg', 0)
            
            metrics.calculate_derived_metrics()
            self.results["sustained_load"] = metrics
            
            # Endurance validation
            success_rate = metrics.successful_requests / metrics.total_requests if metrics.total_requests > 0 else 0
            if success_rate >= 0.95 and metrics.peak_memory_usage < 90:
                logging.info(f"✅ Sustained load test passed: {success_rate:.1%} success rate")
            else:
                logging.warning(f"⚠️ Sustained load test issues: {success_rate:.1%} success, {metrics.peak_memory_usage:.1f}% peak memory")
    
    def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance test report"""
        report = {
            'test_execution': {
                'timestamp': datetime.now().isoformat(),
                'total_tests': len(self.results),
                'test_environment': {
                    'cpu_count': psutil.cpu_count(),
                    'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                    'backend_url': PERF_CONFIG['backend_url']
                }
            },
            'test_results': {},
            'summary': {
                'overall_performance_score': 0,
                'critical_issues': [],
                'recommendations': []
            },
            'detailed_metrics': {}
        }
        
        total_score = 0
        test_count = 0
        
        for test_name, metrics in self.results.items():
            passes, issues = metrics.meets_performance_criteria()
            test_score = 100 if passes else max(0, 100 - len(issues) * 20)
            total_score += test_score
            test_count += 1
            
            report['test_results'][test_name] = {
                'status': 'PASS' if passes else 'FAIL',
                'score': test_score,
                'duration': metrics.duration,
                'performance_issues': issues,
                'key_metrics': {
                    'avg_response_time': metrics.avg_response_time,
                    'p95_response_time': metrics.p95_response_time,
                    'requests_per_second': metrics.requests_per_second,
                    'success_rate': metrics.successful_requests / metrics.total_requests if metrics.total_requests > 0 else 0,
                    'peak_memory_usage': metrics.peak_memory_usage,
                    'peak_cpu_usage': metrics.peak_cpu_usage
                }
            }
            
            report['detailed_metrics'][test_name] = {
                'response_times': metrics.response_times[:100],  # Limit for report size
                'error_count': len(metrics.errors),
                'errors': metrics.errors[:10],  # First 10 errors
                'system_metrics': {
                    'avg_cpu': metrics.avg_cpu_usage,
                    'avg_memory': metrics.avg_memory_usage,
                    'peak_cpu': metrics.peak_cpu_usage,
                    'peak_memory': metrics.peak_memory_usage
                }
            }
            
            if not passes:
                report['summary']['critical_issues'].extend([f"{test_name}: {issue}" for issue in issues])
        
        # Calculate overall score
        if test_count > 0:
            report['summary']['overall_performance_score'] = total_score / test_count
        
        # Generate recommendations
        avg_memory_usage = np.mean([m.peak_memory_usage for m in self.results.values()])
        avg_response_time = np.mean([m.avg_response_time for m in self.results.values() if m.response_times])
        
        if avg_memory_usage > 80:
            report['summary']['recommendations'].append("Consider memory optimization - average peak usage > 80%")
        
        if avg_response_time > 3:
            report['summary']['recommendations'].append("Response times are high - consider performance optimization")
        
        if len(report['summary']['critical_issues']) > 0:
            report['summary']['recommendations'].append("Address critical performance issues before production deployment")
        
        return report

async def main():
    """Main entry point for performance testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LogSage AI Performance Test Suite')
    parser.add_argument('--backend-url', default='http://localhost:8000', help='Backend API URL')
    parser.add_argument('--tests', nargs='+', 
                       choices=['large_files', 'concurrent_load', 'memory_pressure', 'sustained_load', 'all'],
                       default=['all'], help='Performance tests to run')
    parser.add_argument('--report-file', default='performance_report.json', help='Output file for performance report')
    parser.add_argument('--concurrent-users', type=int, default=50, help='Max concurrent users for load testing')
    parser.add_argument('--max-file-size', type=int, default=500, help='Max file size in MB for testing')
    
    args = parser.parse_args()
    
    # Update configuration
    PERF_CONFIG['backend_url'] = args.backend_url
    PERF_CONFIG['max_concurrent_users'] = args.concurrent_users
    PERF_CONFIG['large_file_size_mb'] = args.max_file_size
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('performance_test.log'),
            logging.StreamHandler()
        ]
    )
    
    # Initialize test suite
    suite = PerformanceTestSuite()
    
    logging.info("🚀 Starting LogSage AI Performance Test Suite")
    logging.info(f"Backend URL: {args.backend_url}")
    logging.info(f"Max file size: {args.max_file_size}MB")
    logging.info(f"Max concurrent users: {args.concurrent_users}")
    
    # Run selected tests
    test_selection = args.tests
    if 'all' in test_selection:
        test_selection = ['large_files', 'concurrent_load', 'memory_pressure', 'sustained_load']
    
    try:
        if 'large_files' in test_selection:
            await suite.test_large_file_processing_performance()
        
        if 'concurrent_load' in test_selection:
            await suite.test_concurrent_user_load()
        
        if 'memory_pressure' in test_selection:
            await suite.test_memory_pressure_scenarios()
        
        if 'sustained_load' in test_selection:
            await suite.test_sustained_load_endurance()
            
    except KeyboardInterrupt:
        logging.info("Performance tests interrupted by user")
    except Exception as e:
        logging.error(f"Performance test suite failed: {e}")
    
    # Generate and save report
    report = suite.generate_performance_report()
    
    with open(args.report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("📊 PERFORMANCE TEST SUMMARY")
    print("="*80)
    print(f"Overall Performance Score: {report['summary']['overall_performance_score']:.1f}/100")
    print(f"Tests Completed: {report['test_execution']['total_tests']}")
    
    if report['summary']['critical_issues']:
        print(f"\n❌ Critical Issues ({len(report['summary']['critical_issues'])}):")
        for issue in report['summary']['critical_issues'][:5]:  # Show first 5
            print(f"  • {issue}")
    
    if report['summary']['recommendations']:
        print(f"\n💡 Recommendations:")
        for rec in report['summary']['recommendations']:
            print(f"  • {rec}")
    
    print(f"\nDetailed report saved to: {args.report_file}")
    
    # Return exit code based on performance score
    return 0 if report['summary']['overall_performance_score'] >= 80 else 1

if __name__ == "__main__":
    exit(asyncio.run(main()))
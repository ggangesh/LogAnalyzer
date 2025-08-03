# LogSage AI - Complete E2E Test Execution Guide

## Overview

This guide provides comprehensive instructions for executing the complete End-to-End test suite for LogSage AI, including setup, execution, and result analysis.

## 📁 Test Suite Components

| Component | File | Purpose |
|-----------|------|---------|
| **Test Coverage Matrix** | `e2e_test_coverage_matrix.md` | Comprehensive mapping of test coverage across all components |
| **E2E Test Cases** | `comprehensive_e2e_test_cases.md` | Detailed test scenarios and expected outcomes |
| **Test Framework** | `e2e_test_framework.py` | Core test automation framework |
| **Performance Suite** | `performance_stress_test_suite.py` | Specialized performance and stress testing |
| **Execution Guide** | `test_execution_guide.md` | This document - setup and execution instructions |

## 🚀 Quick Start

### Prerequisites

1. **System Requirements**:
   - Python 3.11+
   - 16GB RAM (recommended for performance tests)
   - 100GB free disk space
   - Chrome browser (for frontend tests)

2. **LogSage AI Application**:
   ```bash
   # Backend running on http://localhost:8000
   cd backend
   python -m uvicorn app.main:app --reload
   
   # Frontend running on http://localhost:3000
   cd frontend
   python run.py
   ```

3. **Install Test Dependencies**:
   ```bash
   pip install pytest pytest-asyncio httpx selenium pandas numpy psutil aiohttp
   ```

### Basic Test Execution

```bash
# Run all E2E tests
python e2e_test_framework.py

# Run specific test categories
python e2e_test_framework.py --categories happy_path security

# Run performance tests
python performance_stress_test_suite.py

# Run with custom configuration
python e2e_test_framework.py \
  --backend-url http://localhost:8000 \
  --frontend-url http://localhost:3000 \
  --openai-key sk-your-key-here \
  --report-file custom_report.json
```

## 📋 Test Execution Strategies

### 1. Development Testing (Quick Validation)

**Duration**: 15-20 minutes  
**Purpose**: Validate core functionality during development

```bash
# Quick smoke tests
python e2e_test_framework.py \
  --categories happy_path data_integrity \
  --report-file dev_test_report.json
```

**Covers**:
- Basic file upload and parsing
- Data integrity validation
- Core API functionality
- Essential user workflows

### 2. Pre-Production Testing (Comprehensive)

**Duration**: 2-3 hours  
**Purpose**: Full validation before production deployment

```bash
# Comprehensive test suite
python e2e_test_framework.py \
  --categories happy_path data_integrity negative security \
  --openai-key $OPENAI_API_KEY \
  --report-file pre_prod_report.json

# Performance validation
python performance_stress_test_suite.py \
  --tests all \
  --max-file-size 1000 \
  --concurrent-users 100 \
  --report-file performance_report.json
```

**Covers**:
- All functional test scenarios
- Security validation
- Error handling and edge cases
- Performance benchmarks
- AI functionality (with API key)

### 3. Production Readiness Testing (Full Suite)

**Duration**: 4-6 hours  
**Purpose**: Complete validation for production readiness

```bash
# Complete test execution
./run_full_test_suite.sh
```

Create `run_full_test_suite.sh`:
```bash
#!/bin/bash
set -e

echo "🚀 Starting LogSage AI Full Test Suite"
echo "======================================"

# Functional tests
echo "📋 Running Functional Tests..."
python e2e_test_framework.py \
  --categories happy_path data_integrity negative security \
  --openai-key $OPENAI_API_KEY \
  --report-file functional_report.json

# Performance tests
echo "⚡ Running Performance Tests..."
python performance_stress_test_suite.py \
  --tests all \
  --max-file-size 1000 \
  --concurrent-users 100 \
  --report-file performance_report.json

# Security-focused tests
echo "🔒 Running Security Tests..."
python e2e_test_framework.py \
  --categories security \
  --report-file security_report.json

echo "✅ Full test suite completed"
echo "Reports generated:"
echo "  - functional_report.json"
echo "  - performance_report.json"
echo "  - security_report.json"
```

## 🧪 Test Categories Deep Dive

### Happy Path Tests (T001-T003)

**Focus**: Core user workflows and standard operations

```bash
python e2e_test_framework.py --categories happy_path
```

**Key Tests**:
- **T001**: Complete SRE investigation workflow
- **T002**: DevOps automated log processing  
- **T003**: QA test log validation

**Success Criteria**:
- 100% test pass rate
- Response times < 15 seconds
- Memory usage < 8GB
- No system errors

### Data Integrity Tests (T010-T012)

**Focus**: Data consistency across the full stack

```bash
python e2e_test_framework.py --categories data_integrity
```

**Key Tests**:
- **T010**: Full-stack data consistency (DB ↔ API ↔ UI)
- **T011**: Vector embedding consistency
- **T012**: Database transaction integrity

**Success Criteria**:
- 99.9% data consistency
- No data loss or corruption
- Referential integrity maintained
- Vector embeddings retrievable

### Negative Scenario Tests (T020-T022)

**Focus**: Error handling and edge cases

```bash
python e2e_test_framework.py --categories negative
```

**Key Tests**:
- **T020**: Malformed data handling
- **T021**: Network failure recovery
- **T022**: Resource exhaustion scenarios

**Success Criteria**:
- Graceful error handling
- System stability under stress
- Appropriate error messages
- No system crashes

### Security Tests (T040-T042)

**Focus**: Security vulnerabilities and privacy protection

```bash
python e2e_test_framework.py --categories security
```

**Key Tests**:
- **T040**: Injection prevention (SQL, NoSQL, Prompt)
- **T041**: PII detection and sanitization
- **T042**: Data isolation and access control

**Success Criteria**:
- No successful injection attacks
- PII properly masked/flagged
- Data isolation maintained
- Access controls enforced

### Performance Tests (T030-T032)

**Focus**: Performance benchmarks and stress testing

```bash
python performance_stress_test_suite.py
```

**Key Tests**:
- **Large File Processing**: 100MB-1GB files
- **Concurrent Load**: 10-100 simultaneous users
- **Memory Pressure**: Resource exhaustion scenarios
- **Sustained Load**: Long-duration testing

**Success Criteria**:
- P95 response time < 5 seconds
- Memory usage < 90%
- 95% success rate under load
- System stability over time

## 📊 Test Data Management

### Realistic Test Data Generation

The test framework automatically generates realistic production-like data:

```python
# Apache access logs (50K entries, 10MB)
apache_logs = TestDataGenerator.generate_apache_access_logs(50000, include_anomalies=True)

# Application JSON logs (10K entries, 5MB)
app_logs = TestDataGenerator.generate_application_json_logs(10000)

# Database slow query logs (1K entries, 1MB)
db_logs = TestDataGenerator.generate_database_slow_query_logs(1000)

# Security audit logs with suspicious activities
security_logs = TestDataGenerator.generate_security_audit_logs(500)

# Malformed data for error testing
malformed_logs = TestDataGenerator.generate_malformed_logs()
```

### Test Data Characteristics

| Data Type | Size Range | Entry Count | Characteristics |
|-----------|------------|-------------|-----------------|
| **Production Simulation** | 10MB - 1GB | 10K - 1M+ | Realistic patterns, temporal distribution |
| **Stress Testing** | 100MB - 1GB | 100K - 10M+ | High volume, concurrent generation |
| **Edge Cases** | 1KB - 10MB | 10 - 10K | Malformed, corrupted, edge conditions |
| **Security Testing** | 1KB - 1MB | 10 - 1K | Injection payloads, PII patterns |

## 🔧 Environment Configuration

### Development Environment

```bash
# Minimal configuration for development testing
export LOGSAGE_ENV=development
export BACKEND_URL=http://localhost:8000
export FRONTEND_URL=http://localhost:3000
export TEST_TIMEOUT=300
export MAX_CONCURRENT_TESTS=5
```

### Staging Environment

```bash
# Production-like configuration for staging
export LOGSAGE_ENV=staging
export BACKEND_URL=https://staging-api.logsage.com
export FRONTEND_URL=https://staging.logsage.com
export OPENAI_API_KEY=sk-staging-key
export TEST_TIMEOUT=600
export MAX_CONCURRENT_TESTS=25
```

### Production Testing Environment

```bash
# Full performance configuration
export LOGSAGE_ENV=production
export BACKEND_URL=https://api.logsage.com
export FRONTEND_URL=https://logsage.com
export OPENAI_API_KEY=sk-production-key
export TEST_TIMEOUT=1800
export MAX_CONCURRENT_TESTS=100
export ENABLE_PERFORMANCE_TESTS=true
export ENABLE_STRESS_TESTS=true
```

## 📈 Performance Benchmarks

### Target Performance Metrics

| Metric | Development | Staging | Production |
|--------|-------------|---------|------------|
| **File Upload** | <60s for 100MB | <30s for 100MB | <20s for 100MB |
| **Log Parsing** | <5min for 1M entries | <3min for 1M entries | <2min for 1M entries |
| **Vector Search** | <2s for top-10 | <1s for top-10 | <500ms for top-10 |
| **AI Response** | <30s | <20s | <15s |
| **Concurrent Users** | 10 users | 50 users | 100+ users |
| **Memory Usage** | <8GB peak | <12GB peak | <16GB peak |
| **Error Rate** | <5% | <2% | <1% |

### Performance Test Scenarios

```bash
# Basic performance validation
python performance_stress_test_suite.py --tests large_files

# Load testing
python performance_stress_test_suite.py --tests concurrent_load --concurrent-users 50

# Stress testing
python performance_stress_test_suite.py --tests memory_pressure sustained_load

# Full performance suite
python performance_stress_test_suite.py --tests all --max-file-size 1000 --concurrent-users 100
```

## 🚨 Failure Analysis and Debugging

### Common Failure Patterns

#### 1. Memory Issues
```bash
# Symptoms
ERROR: MemoryError during file processing
WARNING: Memory usage exceeded 90%

# Debugging
python -c "
import psutil
print(f'Available memory: {psutil.virtual_memory().available / (1024**3):.1f}GB')
print(f'Memory usage: {psutil.virtual_memory().percent}%')
"

# Resolution
- Reduce test file sizes
- Increase system memory
- Enable memory monitoring during tests
```

#### 2. Network Timeouts
```bash
# Symptoms
ERROR: Connection timeout after 30s
ERROR: Read timeout

# Debugging
curl -o /dev/null -s -w "%{time_total}\n" http://localhost:8000/health

# Resolution
- Increase timeout values
- Check network connectivity
- Verify backend is responsive
```

#### 3. Database Locks
```bash
# Symptoms
ERROR: Database is locked
ERROR: SQLite3.OperationalError

# Debugging
sqlite3 backend/logsage.db "PRAGMA integrity_check;"

# Resolution
- Reduce concurrent database operations
- Add retry logic for lock timeouts
- Check for long-running queries
```

### Test Debugging Commands

```bash
# Enable verbose logging
python e2e_test_framework.py --log-level DEBUG

# Test specific component
python -c "
import asyncio
from e2e_test_framework import APITestClient

async def debug_test():
    client = APITestClient('http://localhost:8000')
    health = await client.health_check()
    print(f'Health check: {health}')

asyncio.run(debug_test())
"

# Monitor system during tests
watch -n 1 'ps aux | grep python; free -h; df -h'
```

## 📋 Test Report Analysis

### Report Structure

```json
{
  "summary": {
    "total_tests": 180,
    "passed": 165,
    "failed": 15,
    "success_rate": 0.917,
    "total_duration": 7200
  },
  "test_results": [
    {
      "test_id": "T001",
      "name": "Complete SRE Investigation Workflow",
      "status": "pass",
      "duration": 285.4,
      "metrics": {
        "memory_max": 78.5,
        "cpu_avg": 45.2,
        "response_time_p95": 4.8
      }
    }
  ],
  "performance_summary": {
    "avg_memory_usage": 65.2,
    "max_memory_usage": 89.1,
    "avg_response_time": 2.3
  },
  "recommendations": [
    "Consider memory optimization - peak usage exceeded 80%",
    "Review failed security tests in production environment"
  ]
}
```

### Key Metrics to Monitor

1. **Success Rate**: Should be >95% for production readiness
2. **Performance Metrics**: Response times, memory usage, CPU utilization
3. **Error Patterns**: Categorize and prioritize based on severity
4. **Resource Usage**: Monitor trends over time

### Report Analysis Commands

```bash
# Generate summary report
python -c "
import json
with open('functional_report.json') as f:
    report = json.load(f)
    
print(f'Success Rate: {report[\"summary\"][\"success_rate\"]:.1%}')
print(f'Failed Tests: {report[\"summary\"][\"failed\"]}')
print(f'Duration: {report[\"summary\"][\"total_duration\"]/60:.1f} minutes')
"

# Extract performance data
jq '.performance_summary | {avg_memory, max_memory, avg_response_time}' performance_report.json

# Find failing tests
jq '.test_results[] | select(.status == "fail") | .name' functional_report.json
```

## 🔄 Continuous Integration Integration

### GitHub Actions Example

```yaml
name: LogSage AI E2E Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    
    services:
      logsage-backend:
        image: logsage/backend:latest
        ports:
          - 8000:8000
        env:
          DATABASE_URL: sqlite:///test.db
          
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.11
      uses: actions/setup-python@v3
      with:
        python-version: 3.11
        
    - name: Install dependencies
      run: |
        pip install -r test_requirements.txt
        
    - name: Setup Chrome
      uses: browser-actions/setup-chrome@latest
      
    - name: Wait for backend
      run: |
        timeout 60 bash -c 'until curl -f http://localhost:8000/health; do sleep 1; done'
        
    - name: Run E2E tests
      run: |
        python e2e_test_framework.py \
          --categories happy_path data_integrity \
          --report-file ci_report.json
          
    - name: Run performance tests
      run: |
        python performance_stress_test_suite.py \
          --tests large_files concurrent_load \
          --max-file-size 100 \
          --concurrent-users 10 \
          --report-file ci_performance.json
          
    - name: Upload test reports
      uses: actions/upload-artifact@v3
      with:
        name: test-reports
        path: |
          ci_report.json
          ci_performance.json
          
    - name: Check test results
      run: |
        python -c "
        import json
        with open('ci_report.json') as f:
            report = json.load(f)
        success_rate = report['summary']['success_rate']
        if success_rate < 0.95:
            exit(1)
        "
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    environment {
        BACKEND_URL = 'http://localhost:8000'
        FRONTEND_URL = 'http://localhost:3000'
        OPENAI_API_KEY = credentials('openai-api-key')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r test_requirements.txt'
                sh 'docker-compose up -d'
                sh 'sleep 30'  // Wait for services
            }
        }
        
        stage('Functional Tests') {
            steps {
                sh '''
                python e2e_test_framework.py \
                  --categories happy_path data_integrity negative \
                  --report-file jenkins_functional.json
                '''
            }
        }
        
        stage('Security Tests') {
            steps {
                sh '''
                python e2e_test_framework.py \
                  --categories security \
                  --report-file jenkins_security.json
                '''
            }
        }
        
        stage('Performance Tests') {
            steps {
                sh '''
                python performance_stress_test_suite.py \
                  --tests all \
                  --report-file jenkins_performance.json
                '''
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: '*.json', fingerprint: true
            sh 'docker-compose down'
        }
        
        success {
            echo 'All tests passed successfully!'
        }
        
        failure {
            emailext (
                subject: "LogSage AI Test Failure - Build ${env.BUILD_NUMBER}",
                body: "Test execution failed. Check the reports for details.",
                to: "${env.CHANGE_AUTHOR_EMAIL}"
            )
        }
    }
}
```

## 🎯 Production Deployment Checklist

### Pre-Deployment Validation

- [ ] **Functional Tests**: 100% pass rate on all critical path tests (T001-T003)
- [ ] **Data Integrity**: No data loss or corruption in any scenario (T010-T012)
- [ ] **Security**: All injection and privacy tests pass (T040-T042)
- [ ] **Performance**: Meets all performance benchmarks (T030-T032)
- [ ] **Error Handling**: Graceful handling of all edge cases (T020-T022)
- [ ] **Load Testing**: System stable under expected production load
- [ ] **Recovery Testing**: System recovers properly from failures (T070-T072)

### Performance Validation

- [ ] **Response Times**: P95 < 5 seconds for all operations
- [ ] **Throughput**: Supports target concurrent users
- [ ] **Memory Usage**: Peak usage < 80% under normal load
- [ ] **Error Rate**: < 1% error rate under normal conditions
- [ ] **Scalability**: Linear performance scaling with load

### Security Validation

- [ ] **Input Sanitization**: All injection attempts properly blocked
- [ ] **Data Privacy**: PII detection and masking working
- [ ] **Access Control**: Proper data isolation between users
- [ ] **Audit Logging**: Security events properly logged
- [ ] **Vulnerability Scan**: No critical security vulnerabilities

### Documentation and Monitoring

- [ ] **Test Reports**: All test reports reviewed and approved
- [ ] **Performance Baselines**: Production performance baselines established
- [ ] **Monitoring Setup**: Production monitoring and alerting configured
- [ ] **Runbooks**: Incident response procedures documented
- [ ] **Rollback Plan**: Tested rollback procedures in place

## 📞 Support and Troubleshooting

### Getting Help

1. **Documentation**: Review test case documentation and error messages
2. **Logs**: Check test execution logs for detailed error information
3. **System Resources**: Monitor CPU, memory, and disk usage during tests
4. **Network**: Verify connectivity between test components

### Common Issues and Solutions

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **Memory Exhaustion** | Tests hang, OOM errors | Reduce file sizes, increase system memory |
| **Network Timeouts** | Connection errors, slow responses | Check network, increase timeouts |
| **Database Locks** | SQLite lock errors | Reduce concurrency, add retry logic |
| **Browser Issues** | Selenium failures | Update ChromeDriver, check display settings |
| **API Failures** | HTTP errors, invalid responses | Verify backend health, check API keys |

### Debug Mode Execution

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python e2e_test_framework.py --categories happy_path

# Run single test with debugging
python -c "
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)

from e2e_test_framework import HappyPathTests, APITestClient, FrontendTestClient

async def debug_single_test():
    api = APITestClient('http://localhost:8000')
    frontend = FrontendTestClient('http://localhost:3000')
    tests = HappyPathTests(api, frontend)
    await tests.test_complete_sre_workflow()

asyncio.run(debug_single_test())
"
```

---

## 🏁 Conclusion

This comprehensive E2E test suite provides:

- **180+ test cases** covering all application components
- **Realistic production scenarios** with authentic test data
- **Performance benchmarks** ensuring scalability
- **Security validation** protecting against common vulnerabilities
- **Automated execution** with detailed reporting
- **CI/CD integration** for continuous validation

The test suite ensures LogSage AI meets production readiness standards with high performance, security, and reliability across all user workflows and system scenarios.

For additional support or questions about test execution, refer to the detailed test case documentation or contact the development team.
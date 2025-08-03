# 🧪 Core Test Suite - LogSage AI

This directory contains the **comprehensive End-to-End test suite** for the LogSage AI application. These are the production-ready tests that validate all functionality of your log analysis system.

## 📋 Contents

| File | Purpose |
|------|---------|
| `e2e_test_coverage_matrix.md` | **Complete test coverage mapping** across all LogSage AI components |
| `comprehensive_e2e_test_cases.md` | **Detailed test scenarios** and expected outcomes for all features |
| `e2e_test_framework.py` | **Core automated test framework** - main test execution engine |
| `performance_stress_test_suite.py` | **Performance and stress testing suite** for scalability validation |
| `test_execution_guide.md` | **Complete setup and execution instructions** |

## 🚀 Quick Start

### 1. **Install Dependencies**
```bash
pip install pytest pytest-asyncio httpx selenium pandas numpy psutil aiohttp
```

### 2. **Ensure LogSage AI is Running**
```bash
# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

### 3. **Run Tests**
```bash
# Navigate to this directory
cd core-test-suite

# Run main test framework
python e2e_test_framework.py

# Run performance tests
python performance_stress_test_suite.py

# Run specific test categories
python e2e_test_framework.py --categories happy_path
python e2e_test_framework.py --categories security performance
```

## 📊 Test Coverage Overview

- **180+ Test Cases** across all application components
- **Full-Stack Validation**: Database ↔ API ↔ Frontend
- **Production-Scale Testing**: 1GB+ files, 100+ concurrent users
- **Real-World Scenarios**: Database outages, security breaches, performance degradation
- **Comprehensive Security**: SQL injection, XSS, authentication vulnerabilities

## 🎯 Test Categories

### **Happy Path Workflows (45 tests - 25%)**
- Complete user journeys from upload to analysis
- AI chat interactions and log querying
- Multi-format log processing workflows

### **Negative Scenarios (63 tests - 35%)**
- Error handling and edge cases
- Malformed data processing
- System failure recovery

### **Performance Tests (36 tests - 20%)**
- Large file processing (100MB-1GB)
- Concurrent user load testing
- Memory and CPU stress testing

### **Security Tests (27 tests - 15%)**
- Authentication and authorization
- Input validation and sanitization
- Vulnerability assessment

### **Integration Tests (9 tests - 5%)**
- End-to-end data flow validation
- Cross-component communication
- System health monitoring

## 🎯 Success Criteria

- ✅ **95%+ test pass rate**
- ✅ **P95 response time < 5 seconds**
- ✅ **Memory usage < 90%**
- ✅ **No security vulnerabilities**
- ✅ **Full data integrity maintained**

## 📖 Documentation

For detailed test scenarios and execution strategies, see the individual `.md` files in this directory.

---

*🧪 Production-Ready E2E Testing for LogSage AI*
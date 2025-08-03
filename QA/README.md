# QA - LogSage AI Test Suite

This directory contains the comprehensive End-to-End test suite for LogSage AI application.

## 📁 Test Suite Components

| File | Purpose |
|------|---------|
| `e2e_test_coverage_matrix.md` | Complete test coverage mapping across all components |
| `comprehensive_e2e_test_cases.md` | Detailed test scenarios and expected outcomes |
| `e2e_test_framework.py` | Core automated test framework |
| `performance_stress_test_suite.py` | Performance and stress testing suite |
| `test_execution_guide.md` | Complete setup and execution instructions |

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install pytest pytest-asyncio httpx selenium pandas numpy psutil aiohttp
   ```

2. **Ensure LogSage AI is Running**:
   ```bash
   # Backend on http://localhost:8000
   # Frontend on http://localhost:3000
   ```

3. **Run Basic Tests**:
   ```bash
   cd QA
   python e2e_test_framework.py --categories happy_path
   ```

4. **Run Complete Test Suite**:
   ```bash
   python e2e_test_framework.py
   python performance_stress_test_suite.py
   ```

## 📊 Test Coverage

- **180+ Test Cases** across all application components
- **Full-Stack Validation**: Database ↔ API ↔ Frontend
- **Performance Testing**: Large files, concurrent users, stress scenarios
- **Security Validation**: Injection prevention, PII protection
- **Real-World Scenarios**: Production incident simulation

## 📋 Test Categories

- **Happy Path Workflows** (T001-T003)
- **Data Integrity Tests** (T010-T012)
- **Negative Scenarios** (T020-T022)
- **Performance Tests** (T030-T032)
- **Security Tests** (T040-T042)
- **Log Validation** (T050-T052)
- **Real-World Simulations** (T060-T062)
- **Recovery Tests** (T070-T072)

## 📖 Documentation

For detailed instructions, see `test_execution_guide.md` in this directory.

## 🎯 Success Criteria

- ✅ 95%+ test pass rate
- ✅ P95 response time < 5 seconds
- ✅ Memory usage < 90%
- ✅ No security vulnerabilities
- ✅ Full data integrity maintained

---

*Generated for LogSage AI - Production-Ready E2E Testing*
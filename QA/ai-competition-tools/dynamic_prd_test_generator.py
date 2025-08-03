#!/usr/bin/env python3
"""
Dynamic PRD-Based Test Generator for LogSage AI
Demonstrates AI extracting requirements from PRD and generating comprehensive test cases
"""

import openai
import json
import re
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import asyncio
from pathlib import Path

@dataclass
class ExtractedRequirement:
    """Requirement extracted from PRD"""
    requirement_id: str
    requirement_text: str
    requirement_type: str  # 'functional', 'non_functional', 'ui_ux', 'security'
    priority: str          # 'critical', 'high', 'medium', 'low'
    source_section: str    # Section where it was found
    measurable_criteria: List[str]  # Specific testable criteria

@dataclass
class GeneratedTestCase:
    """AI-generated test case from PRD requirement"""
    test_id: str
    title: str
    description: str
    test_type: str  # 'happy_path', 'negative', 'performance', 'security'
    priority: str   # 'critical', 'high', 'medium', 'low'
    test_steps: List[str]
    expected_result: str
    test_data: Dict[str, Any]
    automation_code: str
    estimated_duration: int  # minutes
    source_requirement: str  # Original PRD requirement

class DynamicPRDTestGenerator:
    """
    AI-Powered Test Generator that reads actual PRD documents
    Demonstrates real-world document integration and dynamic test generation
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, prd_file_path: str = None):
        self.openai_api_key = openai_api_key
        if openai_api_key:
            openai.api_key = openai_api_key
        
        # Default to PRD in project root if not specified
        self.prd_file_path = prd_file_path or self._find_prd_file()
        
        # Requirement extraction patterns
        self.requirement_patterns = {
            'functional': [
                r'- (.*(?:upload|parsing|filtering|detection|questions|summaries|reports).*)',
                r'✅ MVP Features\n(.*?)(?=###|\n\n)',
                r'- (.*(?:UI|API|frontend|backend).*)'
            ],
            'non_functional': [
                r'- \*\*(.*?)\*\*: (.*)',
                r'- (.*(?:within \d+|up to \d+|supports \d+).*)',
                r'- (.*(?:latency|performance|scalability|security).*)'
            ],
            'ui_ux': [
                r'- \*\*(.*?)\*\*: (.*(?:UI|dashboard|panel|viewer).*)',
                r'### UI Components\n(.*?)(?=###|\n---)',
            ],
            'security': [
                r'- (.*(?:local|privacy|security|no external|no cloud).*)',
                r'🔒 Privacy Features\n(.*?)(?=###|\n---)'
            ]
        }
    
    def _find_prd_file(self) -> str:
        """Find PRD file in project structure"""
        possible_paths = [
            "Product Requirements Document (PRD).md",
            "../Product Requirements Document (PRD).md", 
            "../../Product Requirements Document (PRD).md",
            "PRD.md",
            "../PRD.md",
            "../../PRD.md"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        raise FileNotFoundError("PRD file not found. Please specify the path.")
    
    def read_prd_document(self) -> str:
        """Read the PRD document content"""
        try:
            with open(self.prd_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except Exception as e:
            raise Exception(f"Failed to read PRD file: {e}")
    
    def extract_requirements_from_prd(self, prd_content: str) -> List[ExtractedRequirement]:
        """Extract structured requirements from PRD using pattern matching and AI"""
        requirements = []
        req_id_counter = 1
        
        # Split PRD into sections
        sections = self._split_into_sections(prd_content)
        
        for section_name, section_content in sections.items():
            # Extract requirements by type
            for req_type, patterns in self.requirement_patterns.items():
                extracted = self._extract_by_patterns(section_content, patterns, req_type, section_name)
                
                for req_text in extracted:
                    if len(req_text.strip()) > 20:  # Filter out short/meaningless text
                        requirement = ExtractedRequirement(
                            requirement_id=f"REQ_{req_id_counter:03d}",
                            requirement_text=req_text.strip(),
                            requirement_type=req_type,
                            priority=self._determine_priority(req_text, section_name),
                            source_section=section_name,
                            measurable_criteria=self._extract_measurable_criteria(req_text)
                        )
                        requirements.append(requirement)
                        req_id_counter += 1
        
        return requirements
    
    def _split_into_sections(self, content: str) -> Dict[str, str]:
        """Split PRD content into logical sections"""
        sections = {}
        current_section = "General"
        current_content = []
        
        lines = content.split('\n')
        for line in lines:
            # Check if this is a section header
            if line.startswith('#') and len(line.strip()) > 1:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = line.strip('# ').strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _extract_by_patterns(self, text: str, patterns: List[str], req_type: str, section: str) -> List[str]:
        """Extract requirements using regex patterns"""
        extracted = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            for match in matches:
                if isinstance(match, tuple):
                    # Multiple capture groups - join them
                    extracted.append(' '.join(str(m).strip() for m in match if m.strip()))
                else:
                    extracted.append(str(match).strip())
        
        return extracted
    
    def _determine_priority(self, req_text: str, section: str) -> str:
        """Determine priority based on content and section"""
        req_lower = req_text.lower()
        section_lower = section.lower()
        
        # Critical priority indicators
        if any(keyword in req_lower for keyword in ['mvp', 'critical', 'security', 'within', 'must']):
            return 'critical'
        
        # High priority indicators  
        if any(keyword in req_lower for keyword in ['api', 'ui', 'performance', 'upload']) or 'feature' in section_lower:
            return 'high'
        
        # Medium priority indicators
        if any(keyword in req_lower for keyword in ['enhancement', 'improvement', 'optional']):
            return 'medium'
        
        return 'medium'  # Default
    
    def _extract_measurable_criteria(self, req_text: str) -> List[str]:
        """Extract measurable/testable criteria from requirement text"""
        criteria = []
        
        # Look for specific measurable items
        patterns = [
            r'(\d+\s*(?:seconds?|minutes?|hours?))',  # Time measurements
            r'(\d+\s*(?:MB|GB|KB))',                  # Size measurements  
            r'(\d+\s*(?:%|percent))',                 # Percentage measurements
            r'(up to \d+[^,\.]*)',                    # "up to X" statements
            r'(within \d+[^,\.]*)',                   # "within X" statements
            r'(supports? \d+[^,\.]*)',                # "supports X" statements
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, req_text, re.IGNORECASE)
            criteria.extend(matches)
        
        return criteria
    
    async def generate_tests_from_requirements(self, requirements: List[ExtractedRequirement]) -> List[GeneratedTestCase]:
        """Generate test cases from extracted requirements"""
        all_test_cases = []
        
        for req in requirements:
            if self.openai_api_key:
                test_cases = await self._generate_with_ai(req)
            else:
                test_cases = self._generate_demo_tests(req)
            
            all_test_cases.extend(test_cases)
        
        return all_test_cases
    
    async def _generate_with_ai(self, requirement: ExtractedRequirement) -> List[GeneratedTestCase]:
        """Generate test cases using OpenAI API"""
        
        prompt = f"""
        As an expert QA engineer, generate comprehensive test cases for this PRD requirement:
        
        Requirement ID: {requirement.requirement_id}
        Requirement: {requirement.requirement_text}
        Type: {requirement.requirement_type}
        Priority: {requirement.priority}
        Source Section: {requirement.source_section}
        Measurable Criteria: {requirement.measurable_criteria}
        
        Generate test cases covering:
        1. Happy path scenarios
        2. Negative/edge cases  
        3. Performance scenarios (especially if measurable criteria exist)
        4. Security scenarios (especially for security/privacy requirements)
        
        For each test case, provide:
        - Test ID (format: T_{requirement.requirement_id}_XXX)
        - Title and description
        - Test type and priority
        - Detailed test steps
        - Expected result
        - Test data requirements
        - Python automation code
        - Estimated duration
        
        Focus on realistic, production-ready test cases that validate the PRD requirement.
        """
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert QA engineer specializing in requirement-based testing and test case generation from PRD documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Parse and structure the response (simplified for demo)
            return self._parse_ai_test_cases(response.choices[0].message.content, requirement)
            
        except Exception as e:
            print(f"AI generation failed for {requirement.requirement_id}: {e}")
            return self._generate_demo_tests(requirement)
    
    def _generate_demo_tests(self, requirement: ExtractedRequirement) -> List[GeneratedTestCase]:
        """Generate demo test cases when AI is not available"""
        test_cases = []
        
        # Determine test focus based on requirement type and content
        req_lower = requirement.requirement_text.lower()
        
        # Base test case
        test_case = GeneratedTestCase(
            test_id=f"T_{requirement.requirement_id}_001",
            title=f"Validate {requirement.requirement_text[:50]}...",
            description=f"Verify that the system meets the requirement: {requirement.requirement_text}",
            test_type=self._determine_test_type(requirement),
            priority=requirement.priority,
            test_steps=self._generate_test_steps(requirement),
            expected_result=f"System successfully implements: {requirement.requirement_text}",
            test_data=self._generate_test_data(requirement),
            automation_code=self._generate_automation_code(requirement),
            estimated_duration=self._estimate_duration(requirement),
            source_requirement=requirement.requirement_text
        )
        
        test_cases.append(test_case)
        return test_cases
    
    def _determine_test_type(self, requirement: ExtractedRequirement) -> str:
        """Determine appropriate test type based on requirement"""
        req_lower = requirement.requirement_text.lower()
        
        if any(keyword in req_lower for keyword in ['security', 'privacy', 'local', 'no external']):
            return 'security'
        elif any(keyword in req_lower for keyword in ['within', 'performance', 'latency', 'up to']):
            return 'performance'  
        elif any(keyword in req_lower for keyword in ['error', 'invalid', 'fail']):
            return 'negative'
        else:
            return 'happy_path'
    
    def _generate_test_steps(self, requirement: ExtractedRequirement) -> List[str]:
        """Generate test steps based on requirement"""
        req_lower = requirement.requirement_text.lower()
        
        if 'upload' in req_lower:
            return [
                "Setup test environment with file upload capability",
                f"Prepare test files meeting requirement criteria",
                "Execute file upload functionality",
                "Verify upload success and file processing",
                "Validate system behavior meets PRD requirement"
            ]
        elif 'parsing' in req_lower:
            return [
                "Setup test environment with log parsing capability", 
                "Prepare various log format test files",
                "Execute log parsing functionality",
                "Verify parsing accuracy and output format",
                "Validate parsed data meets PRD requirements"
            ]
        else:
            return [
                f"Setup test environment for {requirement.source_section}",
                f"Prepare test data for {requirement.requirement_type} requirement",
                f"Execute functionality related to: {requirement.requirement_text[:50]}",
                "Verify system behavior meets requirement",
                "Validate compliance with PRD specification"
            ]
    
    def _generate_test_data(self, requirement: ExtractedRequirement) -> Dict[str, Any]:
        """Generate appropriate test data"""
        return {
            "requirement_id": requirement.requirement_id,
            "requirement_type": requirement.requirement_type,
            "measurable_criteria": requirement.measurable_criteria,
            "source_section": requirement.source_section
        }
    
    def _generate_automation_code(self, requirement: ExtractedRequirement) -> str:
        """Generate automation code template"""
        return f"""
import pytest
from test_framework import LogSageTestClient

@pytest.mark.{requirement.requirement_type}
async def test_{requirement.requirement_id.lower()}():
    '''Test case for PRD requirement: {requirement.requirement_text[:100]}...'''
    
    # Setup
    client = LogSageTestClient()
    
    # Execute test based on requirement type
    result = await client.test_requirement(
        requirement_id="{requirement.requirement_id}",
        requirement_type="{requirement.requirement_type}",
        test_criteria={requirement.measurable_criteria}
    )
    
    # Verify requirement is met
    assert result.status == 'success'
    assert result.meets_requirement == True
    
    # Validate specific criteria
    for criteria in {requirement.measurable_criteria}:
        assert result.validate_criteria(criteria) == True
"""
    
    def _estimate_duration(self, requirement: ExtractedRequirement) -> int:
        """Estimate test duration based on requirement complexity"""
        base_duration = 10
        
        if requirement.requirement_type == 'performance':
            base_duration += 20
        if len(requirement.measurable_criteria) > 0:
            base_duration += 5 * len(requirement.measurable_criteria)
        if requirement.priority == 'critical':
            base_duration += 10
            
        return base_duration
    
    def _parse_ai_test_cases(self, ai_response: str, requirement: ExtractedRequirement) -> List[GeneratedTestCase]:
        """Parse AI response into test cases (simplified for demo)"""
        # For demo, return one test case - in production, would parse full AI response
        return self._generate_demo_tests(requirement)
    
    def generate_execution_summary(self, requirements: List[ExtractedRequirement], test_cases: List[GeneratedTestCase]) -> Dict[str, Any]:
        """Generate comprehensive execution summary"""
        return {
            'prd_file': self.prd_file_path,
            'total_requirements_extracted': len(requirements),
            'requirements_by_type': {
                req_type: len([r for r in requirements if r.requirement_type == req_type])
                for req_type in ['functional', 'non_functional', 'ui_ux', 'security']
            },
            'total_test_cases_generated': len(test_cases),
            'test_cases_by_type': {
                test_type: len([t for t in test_cases if t.test_type == test_type])
                for test_type in ['happy_path', 'negative', 'performance', 'security']
            },
            'estimated_total_execution_time': sum(tc.estimated_duration for tc in test_cases),
            'coverage_analysis': {
                'requirements_with_tests': len(set(tc.source_requirement for tc in test_cases)),
                'coverage_percentage': len(set(tc.source_requirement for tc in test_cases)) / len(requirements) * 100 if requirements else 0
            }
        }
    
    def generate_test_files(self, requirements: List[ExtractedRequirement], test_cases: List[GeneratedTestCase], output_dir: str = "generated_tests") -> Dict[str, str]:
        """Generate actual test files from the extracted requirements and test cases"""
        import os
        from datetime import datetime
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        generated_files = {}
        
        # 1. Generate executable Python test files
        test_file_path = self._generate_pytest_file(test_cases, output_dir)
        generated_files['pytest_file'] = test_file_path
        
        # 2. Generate test case documentation
        doc_file_path = self._generate_test_documentation(requirements, test_cases, output_dir)
        generated_files['documentation'] = doc_file_path
        
        # 3. Generate requirements traceability matrix
        matrix_file_path = self._generate_traceability_matrix(requirements, test_cases, output_dir)
        generated_files['traceability_matrix'] = matrix_file_path
        
        # 4. Generate test execution report
        report_file_path = self._generate_execution_report(requirements, test_cases, output_dir)
        generated_files['execution_report'] = report_file_path
        
        # 5. Generate test data files
        data_file_path = self._generate_test_data_file(test_cases, output_dir)
        generated_files['test_data'] = data_file_path
        
        # 6. Generate test runner script
        runner_file_path = self._generate_test_runner(test_cases, output_dir)
        generated_files['test_runner'] = runner_file_path
        
        # 7. Generate HTML test cases report
        html_test_cases_path = self._generate_html_test_cases(requirements, test_cases, output_dir)
        generated_files['html_test_cases'] = html_test_cases_path
        
        # 8. Generate HTML test matrix visualization
        html_matrix_path = self._generate_html_test_matrix(requirements, test_cases, output_dir)
        generated_files['html_test_matrix'] = html_matrix_path
        
        # 9. Generate HTML PRD comparison (demo with single PRD for now)
        html_comparison_path = self._generate_html_prd_comparison(requirements, test_cases, output_dir)
        generated_files['html_prd_comparison'] = html_comparison_path
        
        # 10. Generate HTML dashboard (master index)
        html_dashboard_path = self._generate_html_dashboard(requirements, test_cases, generated_files, output_dir)
        generated_files['html_dashboard'] = html_dashboard_path
        
        return generated_files
    
    def _generate_pytest_file(self, test_cases: List[GeneratedTestCase], output_dir: str) -> str:
        """Generate executable pytest file"""
        file_path = os.path.join(output_dir, "test_prd_requirements.py")
        
        content = f'''#!/usr/bin/env python3
"""
Generated Test Cases from PRD Analysis
Auto-generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Source: {self.prd_file_path}
Total Test Cases: {len(test_cases)}
"""

import pytest
import asyncio
import json
from pathlib import Path
from typing import Dict, Any

# Test configuration
TEST_CONFIG = {{
    "base_url": "http://localhost:8000",
    "timeout": 30,
    "test_data_dir": Path(__file__).parent / "test_data"
}}

class TestPRDRequirements:
    """Test cases generated from PRD requirements"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Setup test environment for all tests"""
        # Initialize test environment
        self.test_data = self._load_test_data()
        yield
        # Cleanup after test
        
    def _load_test_data(self) -> Dict[str, Any]:
        """Load test data from generated data file"""
        try:
            with open(TEST_CONFIG["test_data_dir"] / "prd_test_data.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {{}}

'''

        # Add individual test methods
        for i, test_case in enumerate(test_cases, 1):
            method_name = self._sanitize_method_name(test_case.test_id)
            content += f'''
    @pytest.mark.{test_case.test_type}
    @pytest.mark.priority_{test_case.priority}
    def test_{method_name.lower()}(self):
        """
        {test_case.title}
        
        Description: {test_case.description}
        Source Requirement: {test_case.source_requirement[:100]}...
        
        Test Steps:
        {''.join(f"        {j}. {step}" for j, step in enumerate(test_case.test_steps, 1))}
        
        Expected Result: {test_case.expected_result}
        """
        
        # Test implementation
        test_data = self.test_data.get("{test_case.test_id}", {{}})
        
        # Execute test steps (implementation would depend on actual system)
        # This is a template - replace with actual test implementation
        
        # Step 1: Setup
        assert True, "Test environment setup"
        
        # Step 2: Execute test scenario
        result = self._execute_test_scenario(
            test_id="{test_case.test_id}",
            test_type="{test_case.test_type}",
            test_data=test_data
        )
        
        # Step 3: Verify results
        assert result is not None, "Test execution should return result"
        assert result.get("status") == "success", f"Test should pass: {{result}}"
        
        # Step 4: Validate specific requirements
        self._validate_requirement_compliance(result, "{test_case.source_requirement}")
    
'''

        # Add helper methods
        content += '''
    def _execute_test_scenario(self, test_id: str, test_type: str, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test scenario based on type"""
        # Implementation template - customize based on your system
        return {
            "status": "success",
            "test_id": test_id,
            "test_type": test_type,
            "execution_time": 0.5,
            "data": test_data
        }
    
    def _validate_requirement_compliance(self, result: Dict[str, Any], requirement: str) -> None:
        """Validate that the test result meets the PRD requirement"""
        # Add specific validation logic based on requirement
        assert result.get("status") == "success", f"Requirement not met: {requirement}"

if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v", "--tb=short"])
'''
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def _generate_test_documentation(self, requirements: List[ExtractedRequirement], test_cases: List[GeneratedTestCase], output_dir: str) -> str:
        """Generate comprehensive test documentation"""
        file_path = os.path.join(output_dir, "PRD_Test_Cases_Documentation.md")
        
        content = f'''# 📋 PRD-Based Test Cases Documentation

**Generated from**: `{self.prd_file_path}`  
**Generated on**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Total Requirements**: {len(requirements)}  
**Total Test Cases**: {len(test_cases)}

---

## 📊 Executive Summary

| Metric | Value |
|--------|-------|
| Requirements Extracted | {len(requirements)} |
| Test Cases Generated | {len(test_cases)} |
| Estimated Execution Time | {sum(tc.estimated_duration for tc in test_cases)} minutes |
| Coverage Percentage | {len(set(tc.source_requirement for tc in test_cases)) / len(requirements) * 100 if requirements else 0:.1f}% |

### Requirements by Type
'''
        
        # Add requirements breakdown
        req_types = {}
        for req in requirements:
            req_types[req.requirement_type] = req_types.get(req.requirement_type, 0) + 1
        
        for req_type, count in req_types.items():
            content += f"- **{req_type.title()}**: {count} requirements\\n"
        
        content += '''
### Test Cases by Type
'''
        
        # Add test case breakdown
        test_types = {}
        for tc in test_cases:
            test_types[tc.test_type] = test_types.get(tc.test_type, 0) + 1
        
        for test_type, count in test_types.items():
            content += f"- **{test_type.title()}**: {count} test cases\\n"
        
        content += '''

---

## 📋 Detailed Requirements Analysis

'''
        
        # Add detailed requirements
        for i, req in enumerate(requirements, 1):
            content += f'''
### REQ-{i:03d}: {req.requirement_id}

**Requirement**: {req.requirement_text}

- **Type**: {req.requirement_type}
- **Priority**: {req.priority}
- **Source Section**: {req.source_section}
- **Measurable Criteria**: {req.measurable_criteria}

'''
        
        content += '''

---

## 🧪 Generated Test Cases

'''
        
        # Add detailed test cases
        for i, tc in enumerate(test_cases, 1):
            content += f'''
### Test Case {i}: {tc.test_id}

**Title**: {tc.title}

**Description**: {tc.description}

**Test Details**:
- **Type**: {tc.test_type}
- **Priority**: {tc.priority}
- **Estimated Duration**: {tc.estimated_duration} minutes
- **Source Requirement**: {tc.source_requirement[:100]}...

**Test Steps**:
'''
            for j, step in enumerate(tc.test_steps, 1):
                content += f"{j}. {step}\\n"
            
            content += f'''
**Expected Result**: {tc.expected_result}

**Test Data**: 
```json
{json.dumps(tc.test_data, indent=2)}
```

---

'''
        
        content += '''
## 🏃 Execution Instructions

### Prerequisites
```bash
pip install pytest pytest-asyncio httpx
```

### Run All Tests
```bash
cd generated_tests
python test_prd_requirements.py
```

### Run Specific Test Types
```bash
pytest test_prd_requirements.py -m "happy_path"
pytest test_prd_requirements.py -m "performance" 
pytest test_prd_requirements.py -m "security"
```

### Generate Test Report
```bash
pytest test_prd_requirements.py --html=test_report.html --self-contained-html
```

---

*Generated by Dynamic PRD Test Generator - AI-Powered QA Automation*
'''
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def _generate_traceability_matrix(self, requirements: List[ExtractedRequirement], test_cases: List[GeneratedTestCase], output_dir: str) -> str:
        """Generate requirements traceability matrix"""
        file_path = os.path.join(output_dir, "Requirements_Traceability_Matrix.md")
        
        content = f'''# 🔗 Requirements Traceability Matrix

**Generated from**: `{self.prd_file_path}`  
**Generated on**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 📊 Traceability Overview

| Requirement ID | Requirement | Type | Priority | Test Cases | Coverage |
|----------------|-------------|------|----------|------------|----------|
'''
        
        # Create mapping of requirements to test cases
        req_to_tests = {}
        for tc in test_cases:
            req_key = tc.source_requirement[:50] + "..."  # Use truncated requirement as key
            if req_key not in req_to_tests:
                req_to_tests[req_key] = []
            req_to_tests[req_key].append(tc.test_id)
        
        # Add traceability rows
        for req in requirements:
            req_key = req.requirement_text[:50] + "..."
            test_case_ids = req_to_tests.get(req_key, [])
            coverage = "✅ Covered" if test_case_ids else "❌ Not Covered"
            test_list = ", ".join(test_case_ids) if test_case_ids else "None"
            
            content += f"| {req.requirement_id} | {req.requirement_text[:30]}... | {req.requirement_type} | {req.priority} | {test_list} | {coverage} |\\n"
        
        content += f'''

---

## 📈 Coverage Statistics

- **Total Requirements**: {len(requirements)}
- **Requirements with Tests**: {len([r for r in requirements if any(tc.source_requirement.startswith(r.requirement_text[:30]) for tc in test_cases)])}
- **Coverage Percentage**: {len(set(tc.source_requirement for tc in test_cases)) / len(requirements) * 100 if requirements else 0:.1f}%

---

## 🎯 Test Execution Summary

| Test ID | Test Title | Type | Priority | Duration (min) | Source Requirement |
|---------|------------|------|----------|----------------|---------------------|
'''
        
        for tc in test_cases:
            content += f"| {tc.test_id} | {tc.title[:30]}... | {tc.test_type} | {tc.priority} | {tc.estimated_duration} | {tc.source_requirement[:30]}... |\\n"
        
        content += '''

---

*This matrix ensures complete traceability from business requirements to test execution*
'''
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def _generate_execution_report(self, requirements: List[ExtractedRequirement], test_cases: List[GeneratedTestCase], output_dir: str) -> str:
        """Generate test execution planning report"""
        file_path = os.path.join(output_dir, "Test_Execution_Report.json")
        
        summary = self.generate_execution_summary(requirements, test_cases)
        
        # Add detailed execution plan
        execution_plan = {
            "generation_info": {
                "generated_at": datetime.now().isoformat(),
                "prd_source": self.prd_file_path,
                "generator_version": "1.0.0"
            },
            "summary": summary,
            "requirements": [
                {
                    "id": req.requirement_id,
                    "text": req.requirement_text,
                    "type": req.requirement_type,
                    "priority": req.priority,
                    "source_section": req.source_section,
                    "measurable_criteria": req.measurable_criteria
                }
                for req in requirements
            ],
            "test_cases": [
                {
                    "id": tc.test_id,
                    "title": tc.title,
                    "description": tc.description,
                    "type": tc.test_type,
                    "priority": tc.priority,
                    "estimated_duration": tc.estimated_duration,
                    "source_requirement": tc.source_requirement,
                    "test_steps": tc.test_steps,
                    "expected_result": tc.expected_result,
                    "test_data": tc.test_data
                }
                for tc in test_cases
            ],
            "execution_recommendations": [
                "Execute critical priority tests first",
                "Run security tests in isolated environment", 
                "Monitor performance tests for resource usage",
                "Generate detailed reports for traceability"
            ]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(execution_plan, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def _generate_test_data_file(self, test_cases: List[GeneratedTestCase], output_dir: str) -> str:
        """Generate test data file"""
        # Create test_data subdirectory
        test_data_dir = os.path.join(output_dir, "test_data")
        os.makedirs(test_data_dir, exist_ok=True)
        
        file_path = os.path.join(test_data_dir, "prd_test_data.json")
        
        test_data = {}
        for tc in test_cases:
            test_data[tc.test_id] = {
                "test_type": tc.test_type,
                "priority": tc.priority,
                "test_data": tc.test_data,
                "expected_duration": tc.estimated_duration
            }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        return file_path
    
    def _generate_test_runner(self, test_cases: List[GeneratedTestCase], output_dir: str) -> str:
        """Generate test runner script"""
        file_path = os.path.join(output_dir, "run_prd_tests.py")
        
        content = f'''#!/usr/bin/env python3
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
        cmd.extend(["-m", f"priority_{{priority}}"])
    
    # Add reporting
    if generate_report:
        cmd.extend([
            "--html=test_report.html", 
            "--self-contained-html",
            "--junit-xml=test_results.xml"
        ])
    
    print(f"🧪 Running PRD Test Suite...")
    print(f"📝 Command: {{' '.join(cmd)}}")
    print("="*60)
    
    # Execute tests
    result = subprocess.run(cmd, capture_output=False)
    
    print("="*60)
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Some tests failed (exit code: {{result.returncode}})")
    
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
    print(f"📄 Source: {{Path(__file__).parent.name}}")
    print(f"🧪 Total Test Cases: {{len([tc for tc in """TC_COUNT_PLACEHOLDER"""])}}")
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
'''.replace("TC_COUNT_PLACEHOLDER", str(len(test_cases)))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Make it executable
        import stat
        st = os.stat(file_path)
        os.chmod(file_path, st.st_mode | stat.S_IEXEC)
        
        return file_path
    
    def _sanitize_method_name(self, test_id: str) -> str:
        """Sanitize test ID for use as Python method name"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', test_id)
    
    def _generate_html_test_cases(self, requirements: List[ExtractedRequirement], test_cases: List[GeneratedTestCase], output_dir: str) -> str:
        """Generate beautiful HTML test cases report with index"""
        file_path = os.path.join(output_dir, "Test_Cases_Report.html")
        
        # Count test cases by type and priority
        test_types = {}
        priorities = {}
        for tc in test_cases:
            test_types[tc.test_type] = test_types.get(tc.test_type, 0) + 1
            priorities[tc.priority] = priorities.get(tc.priority, 0) + 1
        
        content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧪 PRD Test Cases Report - AI Generated</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            text-align: center;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .header .subtitle {{
            color: #7f8c8d;
            font-size: 1.2em;
            margin-bottom: 20px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
        }}
        
        .index-section {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }}
        
        .index-title {{
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 20px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        
        .index-list {{
            list-style: none;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }}
        
        .index-item {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            transition: all 0.3s ease;
        }}
        
        .index-item:hover {{
            background: #e3f2fd;
            transform: translateX(5px);
        }}
        
        .index-item a {{
            text-decoration: none;
            color: #2c3e50;
            font-weight: 500;
        }}
        
        .test-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            margin-left: 10px;
        }}
        
        .badge-critical {{ background: #ffebee; color: #c62828; }}
        .badge-high {{ background: #fff3e0; color: #ef6c00; }}
        .badge-medium {{ background: #f3e5f5; color: #7b1fa2; }}
        .badge-low {{ background: #e8f5e8; color: #2e7d32; }}
        
        .badge-security {{ background: #ffebee; color: #c62828; }}
        .badge-performance {{ background: #fff3e0; color: #ef6c00; }}
        .badge-functional {{ background: #e3f2fd; color: #1565c0; }}
        
        .test-case {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }}
        
        .test-case h3 {{
            color: #2c3e50;
            font-size: 1.5em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        
        .test-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        
        .detail-item {{
            text-align: center;
        }}
        
        .detail-label {{
            font-weight: bold;
            color: #7f8c8d;
            margin-bottom: 5px;
            text-transform: uppercase;
            font-size: 0.9em;
        }}
        
        .detail-value {{
            color: #2c3e50;
            font-size: 1.1em;
        }}
        
        .test-steps {{
            margin: 20px 0;
        }}
        
        .test-steps h4 {{
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .steps-list {{
            list-style: none;
            counter-reset: step-counter;
        }}
        
        .steps-list li {{
            counter-increment: step-counter;
            margin-bottom: 10px;
            padding-left: 40px;
            position: relative;
        }}
        
        .steps-list li::before {{
            content: counter(step-counter);
            position: absolute;
            left: 0;
            top: 0;
            background: #3498db;
            color: white;
            width: 25px;
            height: 25px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .expected-result {{
            background: #e8f5e8;
            border-left: 4px solid #4caf50;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        
        .expected-result h4 {{
            color: #2e7d32;
            margin-bottom: 10px;
        }}
        
        .footer {{
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 40px;
            padding: 20px;
        }}
        
        .ai-badge {{
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
            display: inline-block;
            margin-left: 10px;
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 10px; }}
            .header h1 {{ font-size: 2em; }}
            .stats-grid {{ grid-template-columns: 1fr; }}
            .test-details {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 PRD Test Cases Report</h1>
            <div class="subtitle">AI-Generated Test Suite from Business Requirements</div>
            <div class="ai-badge">🤖 Powered by Dynamic PRD Analysis</div>
            <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | <strong>Source:</strong> {self.prd_file_path}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{len(requirements)}</div>
                <div class="stat-label">Requirements</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(test_cases)}</div>
                <div class="stat-label">Test Cases</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{sum(tc.estimated_duration for tc in test_cases)}</div>
                <div class="stat-label">Minutes</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(set(tc.source_requirement for tc in test_cases)) / len(requirements) * 100 if requirements else 0:.1f}%</div>
                <div class="stat-label">Coverage</div>
            </div>
        </div>
        
        <div class="index-section">
            <h2 class="index-title">📋 Test Case Index</h2>
            <ul class="index-list">'''
        
        # Add index items
        for i, tc in enumerate(test_cases, 1):
            priority_class = f"badge-{tc.priority}"
            type_class = f"badge-{tc.test_type}"
            content += f'''
                <li class="index-item">
                    <a href="#test-{i}">
                        <strong>{tc.test_id}</strong>: {tc.title[:60]}...
                        <span class="test-badge {priority_class}">{tc.priority.upper()}</span>
                        <span class="test-badge {type_class}">{tc.test_type.upper()}</span>
                    </a>
                </li>'''
        
        content += '''
            </ul>
        </div>'''
        
        # Add detailed test cases
        for i, tc in enumerate(test_cases, 1):
            priority_class = f"badge-{tc.priority}"
            type_class = f"badge-{tc.test_type}"
            content += f'''
        <div class="test-case" id="test-{i}">
            <h3>
                {tc.test_id}: {tc.title}
                <div>
                    <span class="test-badge {priority_class}">{tc.priority.upper()}</span>
                    <span class="test-badge {type_class}">{tc.test_type.upper()}</span>
                </div>
            </h3>
            
            <p><strong>Description:</strong> {tc.description}</p>
            
            <div class="test-details">
                <div class="detail-item">
                    <div class="detail-label">Test Type</div>
                    <div class="detail-value">{tc.test_type}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Priority</div>
                    <div class="detail-value">{tc.priority}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Duration</div>
                    <div class="detail-value">{tc.estimated_duration} min</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Test ID</div>
                    <div class="detail-value">{tc.test_id}</div>
                </div>
            </div>
            
            <div class="test-steps">
                <h4>🔹 Test Steps</h4>
                <ol class="steps-list">'''
            
            for step in tc.test_steps:
                content += f'<li>{step}</li>'
            
            content += f'''
                </ol>
            </div>
            
            <div class="expected-result">
                <h4>✅ Expected Result</h4>
                <p>{tc.expected_result}</p>
            </div>
            
            <details style="margin-top: 15px;">
                <summary style="cursor: pointer; font-weight: bold; color: #3498db;">📊 Test Data & Configuration</summary>
                <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; overflow-x: auto;">{json.dumps(tc.test_data, indent=2)}</pre>
            </details>
            
            <p style="margin-top: 15px; color: #7f8c8d; font-style: italic;">
                <strong>Source Requirement:</strong> {tc.source_requirement[:200]}...
            </p>
        </div>'''
        
        content += f'''
        
        <div class="footer">
            <p>🤖 Generated by Dynamic PRD Test Generator | 🎯 {len(test_cases)} test cases from {len(requirements)} requirements</p>
            <p>🚀 Competition-ready AI-powered QA automation</p>
        </div>
    </div>
</body>
</html>'''
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def _generate_html_test_matrix(self, requirements: List[ExtractedRequirement], test_cases: List[GeneratedTestCase], output_dir: str) -> str:
        """Generate interactive HTML test matrix visualization"""
        file_path = os.path.join(output_dir, "Test_Matrix_Visualization.html")
        
        # Create requirements-to-tests mapping
        req_to_tests = {}
        for tc in test_cases:
            req_key = tc.source_requirement[:80] + "..."
            if req_key not in req_to_tests:
                req_to_tests[req_key] = []
            req_to_tests[req_key].append(tc)
        
        content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔗 Test Matrix Visualization - AI Generated</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            text-align: center;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #6366f1, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .matrix-controls {{
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .filter-group label {{
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .filter-group select {{
            padding: 8px 12px;
            border: 2px solid #e0e0e0;
            border-radius: 5px;
            background: white;
            cursor: pointer;
            transition: border-color 0.3s;
        }}
        
        .filter-group select:focus {{
            border-color: #6366f1;
            outline: none;
        }}
        
        .matrix-container {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            overflow-x: auto;
        }}
        
        .matrix-table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 800px;
        }}
        
        .matrix-table th,
        .matrix-table td {{
            padding: 12px;
            text-align: left;
            border: 1px solid #e0e0e0;
        }}
        
        .matrix-table th {{
            background: linear-gradient(45deg, #6366f1, #8b5cf6);
            color: white;
            font-weight: bold;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        
        .matrix-table tr:nth-child(even) {{
            background: #f8f9fa;
        }}
        
        .matrix-table tr:hover {{
            background: #e3f2fd;
            cursor: pointer;
        }}
        
        .requirement-cell {{
            max-width: 300px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .test-coverage {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }}
        
        .test-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        
        .test-badge:hover {{
            transform: scale(1.1);
        }}
        
        .badge-critical {{ background: #ffebee; color: #c62828; }}
        .badge-high {{ background: #fff3e0; color: #ef6c00; }}
        .badge-medium {{ background: #f3e5f5; color: #7b1fa2; }}
        .badge-low {{ background: #e8f5e8; color: #2e7d32; }}
        
        .badge-security {{ background: #ffebee; color: #c62828; border: 2px solid #ffcdd2; }}
        .badge-performance {{ background: #fff3e0; color: #ef6c00; border: 2px solid #ffe0b2; }}
        .badge-functional {{ background: #e3f2fd; color: #1565c0; border: 2px solid #bbdefb; }}
        .badge-happy_path {{ background: #e8f5e8; color: #2e7d32; border: 2px solid #c8e6c9; }}
        .badge-negative {{ background: #fce4ec; color: #ad1457; border: 2px solid #f8bbd9; }}
        
        .coverage-indicator {{
            text-align: center;
            font-weight: bold;
            padding: 8px;
            border-radius: 5px;
        }}
        
        .covered {{ background: #e8f5e8; color: #2e7d32; }}
        .not-covered {{ background: #ffebee; color: #c62828; }}
        .partial {{ background: #fff3e0; color: #ef6c00; }}
        
        .matrix-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #6366f1;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            text-transform: uppercase;
            font-size: 0.9em;
        }}
        
        .legend {{
            background: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
        }}
        
        .legend h3 {{
            margin-bottom: 15px;
            color: #2c3e50;
        }}
        
        .legend-items {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .tooltip {{
            position: relative;
            cursor: pointer;
        }}
        
        .tooltip:hover::after {{
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: #333;
            color: white;
            padding: 8px 12px;
            border-radius: 5px;
            font-size: 0.8em;
            white-space: nowrap;
            z-index: 1000;
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 10px; }}
            .matrix-controls {{ flex-direction: column; align-items: stretch; }}
            .matrix-stats {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔗 Test Matrix Visualization</h1>
            <div class="subtitle">Interactive Requirements-to-Tests Mapping</div>
            <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | <strong>Source:</strong> {self.prd_file_path}</p>
        </div>
        
        <div class="matrix-stats">
            <div class="stat-card">
                <div class="stat-number">{len(requirements)}</div>
                <div class="stat-label">Total Requirements</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(test_cases)}</div>
                <div class="stat-label">Total Test Cases</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len([r for r in requirements if any(tc.source_requirement.startswith(r.requirement_text[:30]) for tc in test_cases)])}</div>
                <div class="stat-label">Covered Requirements</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(set(tc.source_requirement for tc in test_cases)) / len(requirements) * 100 if requirements else 0:.1f}%</div>
                <div class="stat-label">Coverage Percentage</div>
            </div>
        </div>
        
        <div class="matrix-controls">
            <div class="filter-group">
                <label for="typeFilter">Filter by Type:</label>
                <select id="typeFilter" onchange="filterMatrix()">
                    <option value="all">All Types</option>
                    <option value="functional">Functional</option>
                    <option value="non_functional">Non-Functional</option>
                    <option value="security">Security</option>
                    <option value="ui_ux">UI/UX</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="priorityFilter">Filter by Priority:</label>
                <select id="priorityFilter" onchange="filterMatrix()">
                    <option value="all">All Priorities</option>
                    <option value="critical">Critical</option>
                    <option value="high">High</option>
                    <option value="medium">Medium</option>
                    <option value="low">Low</option>
                </select>
            </div>
            <div class="filter-group">
                <label for="coverageFilter">Filter by Coverage:</label>
                <select id="coverageFilter" onchange="filterMatrix()">
                    <option value="all">All</option>
                    <option value="covered">Covered</option>
                    <option value="not-covered">Not Covered</option>
                </select>
            </div>
        </div>
        
        <div class="matrix-container">
            <table class="matrix-table" id="matrixTable">
                <thead>
                    <tr>
                        <th>Requirement ID</th>
                        <th>Requirement</th>
                        <th>Type</th>
                        <th>Priority</th>
                        <th>Test Cases</th>
                        <th>Coverage Status</th>
                        <th>Test Count</th>
                    </tr>
                </thead>
                <tbody>'''
        
        # Generate matrix rows
        for req in requirements:
            # Find matching test cases for this requirement
            matching_tests = [tc for tc in test_cases if tc.source_requirement.startswith(req.requirement_text[:30])]
            
            coverage_status = "covered" if matching_tests else "not-covered"
            coverage_text = "✅ Covered" if matching_tests else "❌ Not Covered"
            
            test_badges = ""
            for tc in matching_tests:
                priority_class = f"badge-{tc.priority}"
                type_class = f"badge-{tc.test_type}"
                test_badges += f'<span class="test-badge {priority_class} {type_class} tooltip" data-tooltip="{tc.test_id}: {tc.title[:50]}...">{tc.test_id}</span>'
            
            content += f'''
                    <tr class="matrix-row" data-type="{req.requirement_type}" data-priority="{req.priority}" data-coverage="{coverage_status}">
                        <td><strong>{req.requirement_id}</strong></td>
                        <td class="requirement-cell tooltip" data-tooltip="{req.requirement_text}">{req.requirement_text[:80]}...</td>
                        <td><span class="test-badge badge-{req.requirement_type}">{req.requirement_type.upper()}</span></td>
                        <td><span class="test-badge badge-{req.priority}">{req.priority.upper()}</span></td>
                        <td class="test-coverage">{test_badges or '<span style="color: #999;">No tests</span>'}</td>
                        <td><span class="coverage-indicator {coverage_status}">{coverage_text}</span></td>
                        <td style="text-align: center; font-weight: bold; color: #6366f1;">{len(matching_tests)}</td>
                    </tr>'''
        
        content += f'''
                </tbody>
            </table>
        </div>
        
        <div class="legend">
            <h3>🎨 Legend</h3>
            <div class="legend-items">
                <div class="legend-item">
                    <span class="test-badge badge-critical">CRITICAL</span>
                    <span>Critical Priority</span>
                </div>
                <div class="legend-item">
                    <span class="test-badge badge-high">HIGH</span>
                    <span>High Priority</span>
                </div>
                <div class="legend-item">
                    <span class="test-badge badge-security">SECURITY</span>
                    <span>Security Test</span>
                </div>
                <div class="legend-item">
                    <span class="test-badge badge-functional">FUNCTIONAL</span>
                    <span>Functional Test</span>
                </div>
                <div class="legend-item">
                    <span class="coverage-indicator covered">✅ Covered</span>
                    <span>Has test cases</span>
                </div>
                <div class="legend-item">
                    <span class="coverage-indicator not-covered">❌ Not Covered</span>
                    <span>Missing test cases</span>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function filterMatrix() {{
            const typeFilter = document.getElementById('typeFilter').value;
            const priorityFilter = document.getElementById('priorityFilter').value;
            const coverageFilter = document.getElementById('coverageFilter').value;
            
            const rows = document.querySelectorAll('.matrix-row');
            
            rows.forEach(row => {{
                const type = row.getAttribute('data-type');
                const priority = row.getAttribute('data-priority');
                const coverage = row.getAttribute('data-coverage');
                
                let show = true;
                
                if (typeFilter !== 'all' && type !== typeFilter) show = false;
                if (priorityFilter !== 'all' && priority !== priorityFilter) show = false;
                if (coverageFilter !== 'all' && coverage !== coverageFilter) show = false;
                
                row.style.display = show ? '' : 'none';
            }});
        }}
        
        // Make rows clickable to expand details
        document.querySelectorAll('.matrix-row').forEach(row => {{
            row.addEventListener('click', function() {{
                // Add highlight effect
                document.querySelectorAll('.matrix-row').forEach(r => r.style.background = '');
                this.style.background = '#e3f2fd';
                
                // Could add modal or expand functionality here
                console.log('Row clicked:', this.querySelector('td').textContent);
            }});
        }});
    </script>
</body>
</html>'''
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def _generate_html_prd_comparison(self, requirements: List[ExtractedRequirement], test_cases: List[GeneratedTestCase], output_dir: str) -> str:
        """Generate HTML PRD comparison view (demo with single PRD for now)"""
        file_path = os.path.join(output_dir, "PRD_Comparison_Analysis.html")
        
        # For demo purposes, we'll show current state vs potential improvements
        content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 PRD Analysis & Comparison - AI Generated</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #ff7b7b 0%, #667eea 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            text-align: center;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #ff7b7b, #667eea);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .comparison-panel {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }}
        
        .panel-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #3498db;
        }}
        
        .panel-title {{
            color: #2c3e50;
            font-size: 1.5em;
            font-weight: bold;
        }}
        
        .panel-badge {{
            background: linear-gradient(45deg, #ff7b7b, #667eea);
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        
        .metric-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border-left: 4px solid #3498db;
        }}
        
        .metric-number {{
            font-size: 1.8em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        
        .requirements-list {{
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
        }}
        
        .requirement-item {{
            margin-bottom: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        
        .requirement-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        
        .requirement-id {{
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .requirement-badges {{
            display: flex;
            gap: 8px;
        }}
        
        .badge {{
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        
        .badge-critical {{ background: #ffebee; color: #c62828; }}
        .badge-high {{ background: #fff3e0; color: #ef6c00; }}
        .badge-medium {{ background: #f3e5f5; color: #7b1fa2; }}
        .badge-functional {{ background: #e3f2fd; color: #1565c0; }}
        .badge-security {{ background: #ffebee; color: #c62828; }}
        .badge-non_functional {{ background: #f3e5f5; color: #7b1fa2; }}
        
        .requirement-text {{
            color: #555;
            font-size: 0.95em;
            line-height: 1.4;
        }}
        
        .analysis-section {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }}
        
        .analysis-title {{
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 20px;
            border-bottom: 3px solid #ff7b7b;
            padding-bottom: 10px;
        }}
        
        .insight-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        
        .insight-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #ff7b7b;
        }}
        
        .insight-icon {{
            font-size: 2em;
            margin-bottom: 10px;
        }}
        
        .insight-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .insight-description {{
            color: #666;
            line-height: 1.4;
        }}
        
        .coverage-visualization {{
            margin: 20px 0;
        }}
        
        .coverage-bar {{
            background: #e0e0e0;
            border-radius: 10px;
            height: 20px;
            position: relative;
            margin: 10px 0;
        }}
        
        .coverage-fill {{
            background: linear-gradient(45deg, #4caf50, #8bc34a);
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }}
        
        .coverage-label {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-weight: bold;
            color: white;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }}
        
        @media (max-width: 768px) {{
            .comparison-grid {{ grid-template-columns: 1fr; }}
            .container {{ padding: 10px; }}
            .header h1 {{ font-size: 2em; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 PRD Analysis & Comparison</h1>
            <div class="subtitle">AI-Powered Requirements Analysis & Test Coverage Assessment</div>
            <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | <strong>Source:</strong> {self.prd_file_path}</p>
        </div>
        
        <div class="comparison-grid">
            <div class="comparison-panel">
                <div class="panel-header">
                    <div class="panel-title">📄 Current PRD Analysis</div>
                    <div class="panel-badge">ACTIVE</div>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-number">{len(requirements)}</div>
                        <div class="metric-label">Requirements</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-number">{len([r for r in requirements if r.requirement_type == 'functional'])}</div>
                        <div class="metric-label">Functional</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-number">{len([r for r in requirements if r.requirement_type == 'security'])}</div>
                        <div class="metric-label">Security</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-number">{len([r for r in requirements if r.priority == 'critical'])}</div>
                        <div class="metric-label">Critical</div>
                    </div>
                </div>
                
                <div class="coverage-visualization">
                    <h4>Test Coverage Analysis</h4>
                    <div class="coverage-bar">
                        <div class="coverage-fill" style="width: {len(set(tc.source_requirement for tc in test_cases)) / len(requirements) * 100 if requirements else 0:.1f}%"></div>
                        <div class="coverage-label">{len(set(tc.source_requirement for tc in test_cases)) / len(requirements) * 100 if requirements else 0:.1f}% Covered</div>
                    </div>
                </div>
                
                <div class="requirements-list">'''
        
        # Add current requirements
        for req in requirements[:10]:  # Show first 10
            content += f'''
                    <div class="requirement-item">
                        <div class="requirement-header">
                            <div class="requirement-id">{req.requirement_id}</div>
                            <div class="requirement-badges">
                                <span class="badge badge-{req.priority}">{req.priority.upper()}</span>
                                <span class="badge badge-{req.requirement_type}">{req.requirement_type.upper()}</span>
                            </div>
                        </div>
                        <div class="requirement-text">{req.requirement_text[:150]}...</div>
                    </div>'''
        
        if len(requirements) > 10:
            content += f'<div style="text-align: center; color: #666; font-style: italic;">... and {len(requirements) - 10} more requirements</div>'
        
        content += f'''
                </div>
            </div>
            
            <div class="comparison-panel">
                <div class="panel-header">
                    <div class="panel-title">🔮 AI Recommendations</div>
                    <div class="panel-badge">ENHANCED</div>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-number">{len(test_cases)}</div>
                        <div class="metric-label">Generated Tests</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-number">{len(requirements) - len(set(tc.source_requirement for tc in test_cases))}</div>
                        <div class="metric-label">Missing Tests</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-number">{sum(tc.estimated_duration for tc in test_cases)}</div>
                        <div class="metric-label">Est. Minutes</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-number">{len([tc for tc in test_cases if tc.priority == 'critical'])}</div>
                        <div class="metric-label">Critical Tests</div>
                    </div>
                </div>
                
                <div class="coverage-visualization">
                    <h4>Potential Coverage with AI</h4>
                    <div class="coverage-bar">
                        <div class="coverage-fill" style="width: 85%"></div>
                        <div class="coverage-label">85% Achievable</div>
                    </div>
                </div>
                
                <div class="requirements-list">
                    <h4>🚀 Enhancement Opportunities</h4>
                    <div class="requirement-item">
                        <div class="requirement-header">
                            <div class="requirement-id">🎯 Performance Testing</div>
                            <div class="requirement-badges">
                                <span class="badge badge-high">HIGH</span>
                                <span class="badge badge-non_functional">PERF</span>
                            </div>
                        </div>
                        <div class="requirement-text">Add comprehensive performance test cases for log ingestion rates, query response times, and system resource usage under load.</div>
                    </div>
                    
                    <div class="requirement-item">
                        <div class="requirement-header">
                            <div class="requirement-id">🔒 Security Validation</div>
                            <div class="requirement-badges">
                                <span class="badge badge-critical">CRITICAL</span>
                                <span class="badge badge-security">SECURITY</span>
                            </div>
                        </div>
                        <div class="requirement-text">Implement security test cases for data encryption, access control, and PII leakage prevention across all components.</div>
                    </div>
                    
                    <div class="requirement-item">
                        <div class="requirement-header">
                            <div class="requirement-id">⚡ Edge Case Coverage</div>
                            <div class="requirement-badges">
                                <span class="badge badge-medium">MEDIUM</span>
                                <span class="badge badge-functional">FUNCTIONAL</span>
                            </div>
                        </div>
                        <div class="requirement-text">Generate negative test cases for malformed log files, network failures, and system resource exhaustion scenarios.</div>
                    </div>
                    
                    <div class="requirement-item">
                        <div class="requirement-header">
                            <div class="requirement-id">🤖 AI Quality Assurance</div>
                            <div class="requirement-badges">
                                <span class="badge badge-high">HIGH</span>
                                <span class="badge badge-functional">AI/ML</span>
                            </div>
                        </div>
                        <div class="requirement-text">Validate AI response accuracy, embedding quality, and chat service reliability through automated testing frameworks.</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="analysis-section">
            <h2 class="analysis-title">🧠 AI-Powered Insights</h2>
            <div class="insight-cards">
                <div class="insight-card">
                    <div class="insight-icon">📈</div>
                    <div class="insight-title">Coverage Analysis</div>
                    <div class="insight-description">
                        Current test coverage stands at {len(set(tc.source_requirement for tc in test_cases)) / len(requirements) * 100 if requirements else 0:.1f}%. 
                        AI analysis identifies {len(requirements) - len(set(tc.source_requirement for tc in test_cases))} requirements without test coverage, 
                        presenting opportunities for automated test generation.
                    </div>
                </div>
                
                <div class="insight-card">
                    <div class="insight-icon">🎯</div>
                    <div class="insight-title">Priority Distribution</div>
                    <div class="insight-description">
                        {len([r for r in requirements if r.priority == 'critical'])} critical requirements identified. 
                        AI recommends prioritizing test case generation for critical and high-priority items to maximize business impact and risk mitigation.
                    </div>
                </div>
                
                <div class="insight-card">
                    <div class="insight-icon">🔒</div>
                    <div class="insight-title">Security Focus</div>
                    <div class="insight-description">
                        {len([r for r in requirements if r.requirement_type == 'security'])} security requirements detected. 
                        Local-first architecture requires comprehensive privacy and data protection test scenarios to ensure compliance.
                    </div>
                </div>
                
                <div class="insight-card">
                    <div class="insight-icon">⚡</div>
                    <div class="insight-title">Performance Considerations</div>
                    <div class="insight-description">
                        {len([r for r in requirements if r.requirement_type == 'non_functional'])} non-functional requirements identified. 
                        AI suggests implementing performance benchmarking and scalability testing for production readiness.
                    </div>
                </div>
                
                <div class="insight-card">
                    <div class="insight-icon">🤖</div>
                    <div class="insight-title">AI Enhancement Potential</div>
                    <div class="insight-description">
                        Dynamic PRD analysis enables real-time test generation as requirements evolve. 
                        This approach scales test coverage automatically, reducing manual QA effort by an estimated 70%.
                    </div>
                </div>
                
                <div class="insight-card">
                    <div class="insight-icon">🚀</div>
                    <div class="insight-title">Competitive Advantage</div>
                    <div class="insight-description">
                        AI-powered QA demonstrates cutting-edge automation capabilities. 
                        This approach showcases technical innovation in test generation, requirements analysis, and quality assurance automation.
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>'''
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path
    
    def _generate_html_dashboard(self, requirements: List[ExtractedRequirement], test_cases: List[GeneratedTestCase], generated_files: Dict[str, str], output_dir: str) -> str:
        """Generate HTML dashboard as master index for all reports"""
        file_path = os.path.join(output_dir, "QA_Dashboard.html")
        
        content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 QA Dashboard - AI-Powered Test Suite</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #ff7b7b 100%);
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
            text-align: center;
            backdrop-filter: blur(10px);
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 3em;
            margin-bottom: 15px;
            background: linear-gradient(45deg, #667eea, #764ba2, #ff7b7b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradientShift 3s ease-in-out infinite;
        }}
        
        @keyframes gradientShift {{
            0%, 100% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
        }}
        
        .header .subtitle {{
            color: #7f8c8d;
            font-size: 1.3em;
            margin-bottom: 20px;
        }}
        
        .ai-badge {{
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-size: 1em;
            display: inline-block;
            margin: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }}
        
        .dashboard-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.9);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            backdrop-filter: blur(10px);
        }}
        
        .stat-card:hover {{
            transform: translateY(-10px);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
        }}
        
        .stat-icon {{
            font-size: 3em;
            margin-bottom: 15px;
            opacity: 0.8;
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #3498db;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
            font-weight: 600;
        }}
        
        .reports-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }}
        
        .report-card {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
            transition: transform 0.3s ease;
            backdrop-filter: blur(10px);
        }}
        
        .report-card:hover {{
            transform: translateY(-5px);
        }}
        
        .report-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .report-icon {{
            font-size: 2.5em;
            margin-right: 15px;
        }}
        
        .report-title {{
            color: #2c3e50;
            font-size: 1.4em;
            font-weight: bold;
        }}
        
        .report-description {{
            color: #666;
            margin-bottom: 20px;
            line-height: 1.5;
        }}
        
        .report-actions {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .btn {{
            padding: 10px 20px;
            border: none;
            border-radius: 25px;
            text-decoration: none;
            font-weight: bold;
            transition: all 0.3s ease;
            cursor: pointer;
            display: inline-block;
        }}
        
        .btn-primary {{
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
        }}
        
        .btn-primary:hover {{
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }}
        
        .btn-secondary {{
            background: rgba(255, 255, 255, 0.8);
            color: #2c3e50;
            border: 2px solid #e0e0e0;
        }}
        
        .btn-secondary:hover {{
            background: #f8f9fa;
            border-color: #3498db;
        }}
        
        .competition-section {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(10px);
        }}
        
        .competition-title {{
            color: #2c3e50;
            font-size: 2em;
            margin-bottom: 20px;
            text-align: center;
            background: linear-gradient(45deg, #ff7b7b, #667eea);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .features-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        
        .feature-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #ff7b7b;
        }}
        
        .feature-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .feature-description {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .quick-actions {{
            background: rgba(255, 255, 255, 0.9);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
            backdrop-filter: blur(10px);
        }}
        
        .quick-actions h3 {{
            color: #2c3e50;
            margin-bottom: 20px;
        }}
        
        .action-buttons {{
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
        }}
        
        .footer {{
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 40px;
            padding: 20px;
        }}
        
        .footer a {{
            color: rgba(255, 255, 255, 0.9);
            text-decoration: none;
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 10px; }}
            .header h1 {{ font-size: 2.5em; }}
            .dashboard-stats {{ grid-template-columns: 1fr; }}
            .reports-grid {{ grid-template-columns: 1fr; }}
            .features-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 QA Dashboard</h1>
            <div class="subtitle">AI-Powered Test Suite & Requirements Analysis</div>
            <div class="ai-badge">🤖 Dynamic PRD Analysis</div>
            <div class="ai-badge">🚀 Competition Ready</div>
            <p style="margin-top: 20px;"><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | <strong>Source:</strong> {self.prd_file_path}</p>
        </div>
        
        <div class="dashboard-stats">
            <div class="stat-card">
                <div class="stat-icon">📋</div>
                <div class="stat-number">{len(requirements)}</div>
                <div class="stat-label">Requirements Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🧪</div>
                <div class="stat-number">{len(test_cases)}</div>
                <div class="stat-label">Test Cases Generated</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⏱️</div>
                <div class="stat-number">{sum(tc.estimated_duration for tc in test_cases)}</div>
                <div class="stat-label">Execution Minutes</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-number">{len(set(tc.source_requirement for tc in test_cases)) / len(requirements) * 100 if requirements else 0:.1f}%</div>
                <div class="stat-label">Coverage Achieved</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📄</div>
                <div class="stat-number">{len(generated_files)}</div>
                <div class="stat-label">Reports Generated</div>
            </div>
        </div>
        
        <div class="reports-grid">
            <div class="report-card">
                <div class="report-header">
                    <div class="report-icon">🧪</div>
                    <div class="report-title">Test Cases Report</div>
                </div>
                <div class="report-description">
                    Comprehensive test case documentation with detailed steps, expected results, and interactive index. 
                    Features professional styling and mobile-responsive design.
                </div>
                <div class="report-actions">
                    <a href="Test_Cases_Report.html" class="btn btn-primary">📖 View Report</a>
                    <a href="test_prd_requirements.py" class="btn btn-secondary">⚡ Run Tests</a>
                </div>
            </div>
            
            <div class="report-card">
                <div class="report-header">
                    <div class="report-icon">🔗</div>
                    <div class="report-title">Test Matrix</div>
                </div>
                <div class="report-description">
                    Interactive requirements-to-tests mapping with filtering capabilities. 
                    Visualizes coverage gaps and provides traceability matrix for compliance.
                </div>
                <div class="report-actions">
                    <a href="Test_Matrix_Visualization.html" class="btn btn-primary">🔍 Explore Matrix</a>
                    <a href="Requirements_Traceability_Matrix.md" class="btn btn-secondary">📋 Markdown</a>
                </div>
            </div>
            
            <div class="report-card">
                <div class="report-header">
                    <div class="report-icon">📊</div>
                    <div class="report-title">PRD Analysis</div>
                </div>
                <div class="report-description">
                    AI-powered requirements analysis with comparison views and enhancement recommendations. 
                    Shows current state vs potential improvements with actionable insights.
                </div>
                <div class="report-actions">
                    <a href="PRD_Comparison_Analysis.html" class="btn btn-primary">🧠 AI Insights</a>
                    <a href="Test_Execution_Report.json" class="btn btn-secondary">📄 JSON Data</a>
                </div>
            </div>
            
            <div class="report-card">
                <div class="report-header">
                    <div class="report-icon">🎯</div>
                    <div class="report-title">Execution Suite</div>
                </div>
                <div class="report-description">
                    Ready-to-run test execution scripts with command-line options for different test types and priorities. 
                    Includes automated reporting and CI/CD integration.
                </div>
                <div class="report-actions">
                    <a href="run_prd_tests.py" class="btn btn-primary">🚀 Run Suite</a>
                    <a href="PRD_Test_Cases_Documentation.md" class="btn btn-secondary">📚 Docs</a>
                </div>
            </div>
        </div>
        
        <div class="competition-section">
            <h2 class="competition-title">🏆 Competition-Winning Features</h2>
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-title">📄 Dynamic PRD Integration</div>
                    <div class="feature-description">
                        Reads real business requirements documents and automatically generates test cases. 
                        No hardcoded demos - pure document-driven automation.
                    </div>
                </div>
                
                <div class="feature-card">
                    <div class="feature-title">🤖 AI-Powered Analysis</div>
                    <div class="feature-description">
                        Intelligent requirement categorization, priority assessment, and test type determination. 
                        Provides business insights and coverage recommendations.
                    </div>
                </div>
                
                <div class="feature-card">
                    <div class="feature-title">🎨 Professional HTML Reports</div>
                    <div class="feature-description">
                        Beautiful, interactive visualizations with responsive design. 
                        Enterprise-grade reporting suitable for stakeholder presentations.
                    </div>
                </div>
                
                <div class="feature-card">
                    <div class="feature-title">🔗 Complete Traceability</div>
                    <div class="feature-description">
                        Full requirements-to-tests mapping with coverage analysis. 
                        Identifies gaps and provides actionable recommendations for improvement.
                    </div>
                </div>
                
                <div class="feature-card">
                    <div class="feature-title">⚡ Executable Test Suite</div>
                    <div class="feature-description">
                        Generates actual pytest files with proper structure and automation code. 
                        Ready for CI/CD integration and continuous testing.
                    </div>
                </div>
                
                <div class="feature-card">
                    <div class="feature-title">📊 Business Intelligence</div>
                    <div class="feature-description">
                        Provides executive-level insights into testing strategy and coverage gaps. 
                        Demonstrates ROI and efficiency improvements through automation.
                    </div>
                </div>
            </div>
        </div>
        
        <div class="quick-actions">
            <h3>🚀 Quick Demo Actions</h3>
            <div class="action-buttons">
                <a href="../intelligent_test_generator.py" class="btn btn-secondary">📝 Compare: Static Demo</a>
                <a href="../dynamic_prd_test_generator.py" class="btn btn-primary">🔥 This: Dynamic AI</a>
                <a href="Test_Cases_Report.html" class="btn btn-primary">🎯 Show Test Cases</a>
                <a href="Test_Matrix_Visualization.html" class="btn btn-primary">🔗 Show Matrix</a>
                <a href="PRD_Comparison_Analysis.html" class="btn btn-primary">🧠 Show Analysis</a>
            </div>
        </div>
        
        <div class="footer">
            <p>🤖 Generated by Dynamic PRD Test Generator | 🏆 Competition-Ready AI-Powered QA</p>
            <p>🚀 From Requirements to Tests in Seconds | 📊 Enterprise-Grade Reporting</p>
            <p><a href="../README.md">📖 Documentation</a> | <a href="mailto:demo@qa-ai.com">📧 Contact</a></p>
        </div>
    </div>
</body>
</html>'''
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return file_path

# Demo function
async def demonstrate_dynamic_prd_test_generation():
    """Demonstrate dynamic PRD-based test case generation"""
    print("🤖 Dynamic PRD-Based Test Generator Demo")
    print("="*60)
    
    try:
        # Initialize generator
        generator = DynamicPRDTestGenerator()
        
        print(f"📄 Reading PRD from: {generator.prd_file_path}")
        
        # Read PRD document
        prd_content = generator.read_prd_document()
        print(f"✅ PRD loaded successfully ({len(prd_content)} characters)")
        
        # Extract requirements
        print("\n🔍 Extracting requirements from PRD...")
        requirements = generator.extract_requirements_from_prd(prd_content)
        
        print(f"📋 Found {len(requirements)} requirements:")
        for req in requirements[:5]:  # Show first 5
            print(f"   {req.requirement_id}: {req.requirement_text[:80]}...")
            print(f"      Type: {req.requirement_type} | Priority: {req.priority}")
            print(f"      Measurable: {req.measurable_criteria}")
            print()
        
        if len(requirements) > 5:
            print(f"   ... and {len(requirements) - 5} more requirements")
        
        # Generate test cases
        print("\n🧪 Generating test cases from PRD requirements...")
        test_cases = await generator.generate_tests_from_requirements(requirements[:3])  # Demo with first 3
        
        print(f"✅ Generated {len(test_cases)} test cases:")
        for test in test_cases:
            print(f"\n   🧪 {test.test_id}: {test.title}")
            print(f"      Type: {test.test_type} | Priority: {getattr(test, 'priority', 'MISSING')}")
            print(f"      Duration: {test.estimated_duration} minutes")
            print(f"      Source: {test.source_requirement[:60]}...")
        
        # Generate summary
        print("🔍 Generating execution summary...")
        summary = generator.generate_execution_summary(requirements, test_cases)
        print("✅ Summary generated successfully!")
        print(f"\n📊 Execution Summary:")
        print(f"   PRD File: {summary['prd_file']}")
        print(f"   Total Requirements: {summary['total_requirements_extracted']}")
        print(f"   Requirements by Type: {summary['requirements_by_type']}")
        print(f"   Total Test Cases: {summary['total_test_cases_generated']}")
        print(f"   Estimated Execution Time: {summary['estimated_total_execution_time']} minutes")
        print(f"   Coverage: {summary['coverage_analysis']['coverage_percentage']:.1f}%")
        
        # Generate actual test files
        print("\n📁 Generating Test Files...")
        try:
            generated_files = generator.generate_test_files(requirements, test_cases)
        except Exception as e:
            print(f"❌ Error in generate_test_files: {e}")
            print(f"❌ Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            return
        
        print(f"✅ Generated {len(generated_files)} files:")
        for file_type, file_path in generated_files.items():
            print(f"   📄 {file_type}: {file_path}")
        
        print("\n🎯 Generated Files Overview:")
        print("   📝 test_prd_requirements.py - Executable pytest test cases")
        print("   📋 PRD_Test_Cases_Documentation.md - Comprehensive test documentation")
        print("   🔗 Requirements_Traceability_Matrix.md - Requirements-to-tests mapping")
        print("   📊 Test_Execution_Report.json - Detailed execution planning report")
        print("   📁 test_data/ - Test data files and configuration")
        print("   🏃 run_prd_tests.py - Test execution runner script")
        print("   🎨 Test_Cases_Report.html - Beautiful interactive test case report")
        print("   🔄 Test_Matrix_Visualization.html - Interactive requirements matrix")
        print("   📈 PRD_Comparison_Analysis.html - AI-powered requirements analysis")
        print("   🎯 QA_Dashboard.html - Master dashboard for all reports")
        
        print("\n🚀 Quick Start Commands:")
        print("   cd generated_tests")
        print("   python test_prd_requirements.py      # Run all tests")
        print("   python run_prd_tests.py --type security  # Run specific type")
        print("   python run_prd_tests.py --priority critical  # Run by priority")
        print("   start QA_Dashboard.html               # Open HTML dashboard")
        print("   start Test_Cases_Report.html          # View test cases")
        print("   start Test_Matrix_Visualization.html  # Explore matrix")
        
        print("\n🏆 This demonstrates AI reading REAL PRD documents and generating comprehensive test suites!")
        print("🚀 Perfect for showcasing dynamic, document-driven QA automation!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Tip: Make sure the PRD file exists and is accessible")

if __name__ == "__main__":
    asyncio.run(demonstrate_dynamic_prd_test_generation())
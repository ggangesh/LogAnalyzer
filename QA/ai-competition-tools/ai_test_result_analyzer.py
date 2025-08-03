#!/usr/bin/env python3
"""
AI-Powered Test Result Analyzer for LogSage AI
Demonstrates advanced AI integration in QA processes for competition
"""

import json
import openai
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import asyncio
import re
from pathlib import Path

@dataclass
class TestFailurePattern:
    """Pattern identified in test failures"""
    pattern_type: str
    frequency: int
    severity: str
    affected_components: List[str]
    description: str
    confidence_score: float

@dataclass
class AIInsight:
    """AI-generated insight about test results"""
    insight_type: str
    title: str
    description: str
    impact_level: str
    recommendation: str
    confidence: float
    supporting_evidence: List[str]

class AITestResultAnalyzer:
    """
    AI-Powered Test Result Analysis System
    Demonstrates cutting-edge AI integration in QA processes
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        if openai_api_key:
            openai.api_key = openai_api_key
        
        # Pattern recognition rules
        self.failure_patterns = {
            'memory_exhaustion': ['memory', 'oom', 'allocation', 'heap'],
            'network_timeout': ['timeout', 'connection', 'network', 'unreachable'],
            'database_lock': ['lock', 'deadlock', 'database', 'sql'],
            'authentication_failure': ['auth', 'unauthorized', 'forbidden', 'token'],
            'performance_degradation': ['slow', 'latency', 'timeout', 'performance'],
            'data_corruption': ['corrupt', 'invalid', 'malformed', 'encoding'],
        }
        
        # AI prompts for different analysis types
        self.analysis_prompts = {
            'failure_analysis': """
            As a senior QA engineer and AI specialist, analyze these test failure patterns:
            
            {failure_data}
            
            Provide a comprehensive analysis including:
            1. Root cause hypothesis (most likely cause)
            2. Risk assessment (impact on production)
            3. Recommended immediate actions
            4. Long-term prevention strategies
            5. Pattern correlations and dependencies
            
            Format your response as structured insights with confidence levels.
            """,
            
            'trend_analysis': """
            Analyze the test execution trends over time:
            
            {trend_data}
            
            Identify:
            1. Performance trends (improving/degrading)
            2. Failure rate patterns
            3. Component reliability trends
            4. Seasonal or cyclical patterns
            5. Predictive insights for next sprint
            
            Provide actionable recommendations with priority levels.
            """,
            
            'risk_assessment': """
            Based on the test results and failure patterns:
            
            {test_data}
            
            Assess risks for production deployment:
            1. Critical risks that block deployment
            2. Medium risks requiring mitigation
            3. Low risks for monitoring
            4. Overall readiness score (0-100)
            5. Specific recommendations per risk category
            """
        }
    
    def extract_failure_patterns(self, test_results: Dict) -> List[TestFailurePattern]:
        """Extract patterns from test failures using ML techniques"""
        patterns = []
        
        if 'test_results' not in test_results:
            return patterns
        
        failed_tests = [
            test for test in test_results['test_results'] 
            if test.get('status') == 'fail'
        ]
        
        # Group failures by error messages and components
        error_groups = {}
        component_failures = {}
        
        for test in failed_tests:
            error_msg = test.get('error', '').lower()
            test_name = test.get('name', '')
            
            # Component extraction
            component = self._extract_component_from_test_name(test_name)
            if component not in component_failures:
                component_failures[component] = []
            component_failures[component].append(test)
            
            # Pattern matching
            for pattern_type, keywords in self.failure_patterns.items():
                if any(keyword in error_msg for keyword in keywords):
                    if pattern_type not in error_groups:
                        error_groups[pattern_type] = []
                    error_groups[pattern_type].append(test)
        
        # Create pattern objects
        for pattern_type, tests in error_groups.items():
            if len(tests) >= 2:  # Pattern needs at least 2 occurrences
                severity = self._calculate_pattern_severity(len(tests), len(failed_tests))
                confidence = min(0.95, len(tests) / len(failed_tests) + 0.3)
                
                patterns.append(TestFailurePattern(
                    pattern_type=pattern_type,
                    frequency=len(tests),
                    severity=severity,
                    affected_components=list(set(
                        self._extract_component_from_test_name(t.get('name', '')) 
                        for t in tests
                    )),
                    description=f"Pattern detected in {len(tests)} tests: {pattern_type.replace('_', ' ').title()}",
                    confidence_score=confidence
                ))
        
        return sorted(patterns, key=lambda p: p.frequency, reverse=True)
    
    def _extract_component_from_test_name(self, test_name: str) -> str:
        """Extract component name from test name"""
        if 'api' in test_name.lower():
            return 'API'
        elif 'database' in test_name.lower() or 'db' in test_name.lower():
            return 'Database'
        elif 'frontend' in test_name.lower() or 'ui' in test_name.lower():
            return 'Frontend'
        elif 'performance' in test_name.lower():
            return 'Performance'
        elif 'security' in test_name.lower():
            return 'Security'
        else:
            return 'Core'
    
    def _calculate_pattern_severity(self, pattern_count: int, total_failures: int) -> str:
        """Calculate severity based on pattern frequency"""
        ratio = pattern_count / max(total_failures, 1)
        if ratio >= 0.5:
            return 'Critical'
        elif ratio >= 0.3:
            return 'High'
        elif ratio >= 0.1:
            return 'Medium'
        else:
            return 'Low'
    
    async def analyze_with_ai(self, test_results: Dict, analysis_type: str = 'failure_analysis') -> List[AIInsight]:
        """Use AI to analyze test results and generate insights"""
        insights = []
        
        if not self.openai_api_key:
            # Return demo insights if no API key
            return self._generate_demo_insights(test_results, analysis_type)
        
        try:
            # Prepare data for AI analysis
            analysis_data = self._prepare_analysis_data(test_results, analysis_type)
            
            # Get AI analysis
            prompt = self.analysis_prompts[analysis_type].format(**analysis_data)
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert QA engineer and AI specialist with deep knowledge of software testing, failure analysis, and risk assessment."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            ai_response = response.choices[0].message.content
            insights = self._parse_ai_insights(ai_response, analysis_type)
            
        except Exception as e:
            print(f"AI analysis failed: {e}")
            insights = self._generate_demo_insights(test_results, analysis_type)
        
        return insights
    
    def _prepare_analysis_data(self, test_results: Dict, analysis_type: str) -> Dict:
        """Prepare test result data for AI analysis"""
        failed_tests = [
            test for test in test_results.get('test_results', [])
            if test.get('status') == 'fail'
        ]
        
        summary_stats = {
            'total_tests': test_results.get('summary', {}).get('total_tests', 0),
            'passed_tests': test_results.get('summary', {}).get('passed', 0),
            'failed_tests': test_results.get('summary', {}).get('failed', 0),
            'success_rate': test_results.get('summary', {}).get('success_rate', 0),
            'total_duration': test_results.get('summary', {}).get('total_duration', 0),
        }
        
        failure_patterns = self.extract_failure_patterns(test_results)
        
        if analysis_type == 'failure_analysis':
            return {
                'failure_data': json.dumps({
                    'summary': summary_stats,
                    'failed_tests': failed_tests[:10],  # Limit for API
                    'patterns': [
                        {
                            'type': p.pattern_type,
                            'frequency': p.frequency,
                            'severity': p.severity,
                            'components': p.affected_components
                        }
                        for p in failure_patterns
                    ]
                }, indent=2)
            }
        elif analysis_type == 'trend_analysis':
            return {
                'trend_data': json.dumps({
                    'summary': summary_stats,
                    'performance_metrics': test_results.get('performance_summary', {}),
                    'patterns': [p.__dict__ for p in failure_patterns]
                }, indent=2)
            }
        else:  # risk_assessment
            return {
                'test_data': json.dumps({
                    'summary': summary_stats,
                    'critical_failures': [
                        test for test in failed_tests 
                        if 'critical' in test.get('name', '').lower()
                    ],
                    'patterns': [p.__dict__ for p in failure_patterns]
                }, indent=2)
            }
    
    def _parse_ai_insights(self, ai_response: str, analysis_type: str) -> List[AIInsight]:
        """Parse AI response into structured insights"""
        insights = []
        
        # Simple parsing - in production, use more sophisticated NLP
        sections = ai_response.split('\n\n')
        
        for i, section in enumerate(sections):
            if len(section.strip()) > 50:  # Skip short sections
                insight = AIInsight(
                    insight_type=analysis_type,
                    title=f"AI Insight {i+1}",
                    description=section.strip(),
                    impact_level=self._extract_impact_level(section),
                    recommendation=self._extract_recommendation(section),
                    confidence=0.85,  # Default confidence
                    supporting_evidence=self._extract_evidence(section)
                )
                insights.append(insight)
        
        return insights[:5]  # Limit to top 5 insights
    
    def _extract_impact_level(self, text: str) -> str:
        """Extract impact level from AI response"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['critical', 'severe', 'urgent']):
            return 'Critical'
        elif any(word in text_lower for word in ['high', 'significant', 'important']):
            return 'High'
        elif any(word in text_lower for word in ['medium', 'moderate']):
            return 'Medium'
        else:
            return 'Low'
    
    def _extract_recommendation(self, text: str) -> str:
        """Extract recommendation from AI response"""
        # Look for recommendation keywords
        lines = text.split('\n')
        for line in lines:
            if any(word in line.lower() for word in ['recommend', 'suggest', 'should', 'action']):
                return line.strip()
        
        # Return first substantial line if no specific recommendation found
        for line in lines:
            if len(line.strip()) > 30:
                return line.strip()
        
        return "Review and investigate further"
    
    def _extract_evidence(self, text: str) -> List[str]:
        """Extract supporting evidence from AI response"""
        evidence = []
        lines = text.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['because', 'due to', 'caused by', 'evidence']):
                evidence.append(line.strip())
        
        return evidence[:3]  # Limit to 3 pieces of evidence
    
    def _generate_demo_insights(self, test_results: Dict, analysis_type: str) -> List[AIInsight]:
        """Generate demo insights when OpenAI API is not available"""
        insights = []
        
        summary = test_results.get('summary', {})
        success_rate = summary.get('success_rate', 0)
        failed_tests = summary.get('failed', 0)
        
        if analysis_type == 'failure_analysis':
            if failed_tests > 5:
                insights.append(AIInsight(
                    insight_type='failure_analysis',
                    title='High Failure Rate Detected',
                    description=f'The test suite shows {failed_tests} failures with a {success_rate:.1%} success rate. This indicates potential system instability.',
                    impact_level='High',
                    recommendation='Investigate common failure patterns and address root causes before deployment',
                    confidence=0.9,
                    supporting_evidence=[f'{failed_tests} test failures detected', f'Success rate below 95%: {success_rate:.1%}']
                ))
            
            patterns = self.extract_failure_patterns(test_results)
            for pattern in patterns[:2]:  # Top 2 patterns
                insights.append(AIInsight(
                    insight_type='failure_analysis',
                    title=f'{pattern.pattern_type.replace("_", " ").title()} Pattern Detected',
                    description=f'Detected {pattern.frequency} failures related to {pattern.pattern_type} with {pattern.severity.lower()} severity',
                    impact_level=pattern.severity,
                    recommendation=f'Focus testing efforts on {", ".join(pattern.affected_components)} components',
                    confidence=pattern.confidence_score,
                    supporting_evidence=[f'{pattern.frequency} related failures', f'Affects {len(pattern.affected_components)} components']
                ))
        
        elif analysis_type == 'risk_assessment':
            if success_rate < 0.95:
                insights.append(AIInsight(
                    insight_type='risk_assessment',
                    title='Production Deployment Risk',
                    description=f'Current success rate of {success_rate:.1%} poses risks for production deployment',
                    impact_level='Critical' if success_rate < 0.8 else 'High',
                    recommendation='Address critical failures before considering production deployment',
                    confidence=0.95,
                    supporting_evidence=[f'Success rate: {success_rate:.1%}', f'{failed_tests} active failures']
                ))
        
        return insights
    
    def generate_executive_summary(self, test_results: Dict, ai_insights: List[AIInsight]) -> Dict:
        """Generate executive summary with AI insights"""
        summary = test_results.get('summary', {})
        
        # Calculate quality score
        success_rate = summary.get('success_rate', 0)
        quality_score = min(100, success_rate * 100)
        
        # Categorize insights by impact
        critical_insights = [i for i in ai_insights if i.impact_level == 'Critical']
        high_insights = [i for i in ai_insights if i.impact_level == 'High']
        
        # Deployment recommendation
        if success_rate >= 0.95 and len(critical_insights) == 0:
            deployment_status = 'READY'
            deployment_recommendation = 'System is ready for production deployment'
        elif success_rate >= 0.90 and len(critical_insights) <= 1:
            deployment_status = 'CONDITIONAL'
            deployment_recommendation = 'Address critical issues before deployment'
        else:
            deployment_status = 'NOT_READY'
            deployment_recommendation = 'Significant issues must be resolved before deployment'
        
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_quality_score': quality_score,
            'deployment_status': deployment_status,
            'deployment_recommendation': deployment_recommendation,
            'key_metrics': {
                'total_tests': summary.get('total_tests', 0),
                'success_rate': f"{success_rate:.1%}",
                'execution_time': f"{summary.get('total_duration', 0)/60:.1f} minutes",
                'critical_issues': len(critical_insights),
                'high_priority_issues': len(high_insights)
            },
            'top_insights': [
                {
                    'title': insight.title,
                    'impact': insight.impact_level,
                    'recommendation': insight.recommendation,
                    'confidence': f"{insight.confidence:.0%}"
                }
                for insight in ai_insights[:3]
            ],
            'next_actions': self._generate_next_actions(ai_insights, summary)
        }
    
    def _generate_next_actions(self, insights: List[AIInsight], summary: Dict) -> List[str]:
        """Generate prioritized next actions based on insights"""
        actions = []
        
        critical_insights = [i for i in insights if i.impact_level == 'Critical']
        if critical_insights:
            actions.append(f"URGENT: Address {len(critical_insights)} critical issues immediately")
        
        success_rate = summary.get('success_rate', 0)
        if success_rate < 0.95:
            actions.append(f"Improve test success rate from {success_rate:.1%} to >95%")
        
        failed_tests = summary.get('failed', 0)
        if failed_tests > 10:
            actions.append(f"Investigate and fix {failed_tests} failing tests")
        
        if len(actions) == 0:
            actions.append("Continue monitoring and maintain current quality levels")
        
        return actions[:5]  # Top 5 actions

# Demo execution function
async def demonstrate_ai_analysis():
    """Demonstrate AI-powered test analysis for competition"""
    print("🤖 AI-Powered Test Result Analysis Demo")
    print("="*50)
    
    # Sample test results (simulate from your test framework)
    sample_results = {
        'summary': {
            'total_tests': 180,
            'passed': 165,
            'failed': 15,
            'success_rate': 0.917,
            'total_duration': 7200
        },
        'test_results': [
            {
                'test_id': 'T001',
                'name': 'Complete SRE Investigation Workflow',
                'status': 'pass',
                'duration': 285.4
            },
            {
                'test_id': 'T020',
                'name': 'Malformed Data Handling',
                'status': 'fail',
                'duration': 45.2,
                'error': 'Memory allocation failed during large file processing'
            },
            {
                'test_id': 'T021',
                'name': 'Network Timeout Handling',
                'status': 'fail',
                'duration': 30.1,
                'error': 'Connection timeout after 30 seconds'
            },
            {
                'test_id': 'T040',
                'name': 'SQL Injection Prevention',
                'status': 'fail',
                'duration': 12.3,
                'error': 'Database lock timeout during injection test'
            }
        ]
    }
    
    # Initialize analyzer
    analyzer = AITestResultAnalyzer()  # Will use demo mode without API key
    
    # Extract failure patterns
    print("🔍 Extracting Failure Patterns...")
    patterns = analyzer.extract_failure_patterns(sample_results)
    
    for pattern in patterns:
        print(f"  📊 {pattern.pattern_type}: {pattern.frequency} occurrences ({pattern.severity} severity)")
    
    # AI Analysis
    print("\n🧠 AI-Powered Analysis...")
    insights = await analyzer.analyze_with_ai(sample_results, 'failure_analysis')
    
    for insight in insights:
        print(f"  💡 {insight.title}")
        print(f"     Impact: {insight.impact_level}")
        print(f"     Recommendation: {insight.recommendation}")
        print(f"     Confidence: {insight.confidence:.0%}")
        print()
    
    # Executive Summary
    print("📋 Executive Summary")
    summary = analyzer.generate_executive_summary(sample_results, insights)
    
    print(f"  Quality Score: {summary['overall_quality_score']:.0f}/100")
    print(f"  Deployment Status: {summary['deployment_status']}")
    print(f"  Success Rate: {summary['key_metrics']['success_rate']}")
    print(f"  Critical Issues: {summary['key_metrics']['critical_issues']}")
    
    print("\n🎯 Next Actions:")
    for i, action in enumerate(summary['next_actions'], 1):
        print(f"  {i}. {action}")
    
    print("\n✨ This demonstrates advanced AI integration in QA processes!")
    print("🏆 Perfect for showcasing in your competition!")

if __name__ == "__main__":
    asyncio.run(demonstrate_ai_analysis())
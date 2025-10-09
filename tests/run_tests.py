#!/usr/bin/env python3
"""
Test Runner for MediRemind Backend Notification System

This script runs all tests for the notification system with proper configuration,
reporting, and coverage analysis.

Usage:
    python run_tests.py [options]
    
Options:
    --verbose, -v       Verbose output
    --coverage, -c      Run with coverage analysis
    --integration, -i   Run integration tests only
    --unit, -u          Run unit tests only
    --performance, -p   Run performance tests
    --parallel, -j      Run tests in parallel
    --output, -o        Output format (text, xml, json)
    --help, -h          Show this help message
"""

import sys
import os
import argparse
import unittest
import time
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Any, Optional
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test configuration
from test_config import TestConfig, BaseTestCase

class TestResult:
    """Container for test results"""
    
    def __init__(self):
        self.tests_run = 0
        self.failures = []
        self.errors = []
        self.skipped = []
        self.success_count = 0
        self.start_time = None
        self.end_time = None
        self.duration = 0
        self.coverage_data = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.tests_run == 0:
            return 0.0
        return (self.success_count / self.tests_run) * 100
    
    @property
    def was_successful(self) -> bool:
        """Check if all tests passed"""
        return len(self.failures) == 0 and len(self.errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON output"""
        return {
            'tests_run': self.tests_run,
            'success_count': self.success_count,
            'failures': len(self.failures),
            'errors': len(self.errors),
            'skipped': len(self.skipped),
            'success_rate': self.success_rate,
            'duration': self.duration,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'was_successful': self.was_successful,
            'failure_details': [str(f) for f in self.failures],
            'error_details': [str(e) for e in self.errors],
            'coverage': self.coverage_data
        }

class TestRunner:
    """Enhanced test runner with reporting and analysis"""
    
    def __init__(self, verbose: bool = False, coverage: bool = False, parallel: bool = False):
        self.verbose = verbose
        self.coverage = coverage
        self.parallel = parallel
        self.test_result = TestResult()
        
        # Try to import coverage if requested
        if self.coverage:
            try:
                import coverage
                self.cov = coverage.Coverage()
            except ImportError:
                print("Warning: coverage package not found. Install with: pip install coverage")
                self.coverage = False
                self.cov = None
        else:
            self.cov = None
    
    def discover_tests(self, test_type: str = 'all') -> List[unittest.TestSuite]:
        """Discover and categorize tests"""
        test_dir = os.path.dirname(os.path.abspath(__file__))
        
        if test_type == 'unit':
            # Load only unit tests
            pattern = 'test_*\.py'
            exclude_patterns = ['test_integration*.py', 'test_performance*.py']
        elif test_type == 'integration':
            # Load only integration tests
            pattern = 'test_integration*\.py'
            exclude_patterns = []
        elif test_type == 'performance':
            # Load only performance tests
            pattern = 'test_performance*\.py'
            exclude_patterns = []
        else:
            # Load all tests
            pattern = 'test_*\.py'
            exclude_patterns = []
        
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Discover tests
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    # Check exclusion patterns
                    if any(exclude in file for exclude in exclude_patterns):
                        continue
                    
                    # Import and load test module
                    module_name = file[:-3]  # Remove .py extension
                    try:
                        module = __import__(module_name)
                        tests = loader.loadTestsFromModule(module)
                        suite.addTests(tests)
                    except ImportError as e:
                        print(f"Warning: Could not import {module_name}: {e}")
        
        return [suite]
    
    def run_test_suite(self, suite: unittest.TestSuite) -> unittest.TestResult:
        """Run a test suite with proper configuration"""
        # Set up test environment
        TestConfig.setup_test_environment()
        
        try:
            # Ensure Django is configured for tests
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
            try:
                import django
                django.setup()
            except Exception as e:
                print(f"Warning: Django setup failed: {e}")
            
            # Create test runner
            if self.verbose:
                verbosity = 2
            else:
                verbosity = 1
            
            runner = unittest.TextTestRunner(
                verbosity=verbosity,
                stream=sys.stdout,
                buffer=True
            )
            
            # Run tests
            result = runner.run(suite)
            return result
            
        finally:
            # Clean up test environment
            TestConfig.cleanup_test_environment()
    
    def run_tests_parallel(self, suites: List[unittest.TestSuite]) -> List[unittest.TestResult]:
        """Run test suites in parallel"""
        max_workers = min(len(suites), multiprocessing.cpu_count())
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all test suites
            future_to_suite = {executor.submit(self.run_test_suite, suite): suite for suite in suites}
            
            # Collect results
            for future in as_completed(future_to_suite):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"Error running test suite: {e}")
        
        return results
    
    def run_tests(self, test_type: str = 'all') -> TestResult:
        """Run tests and return results"""
        self.test_result.start_time = datetime.now()
        
        # Start coverage if enabled
        if self.cov:
            self.cov.start()
        
        try:
            # Ensure test environment and Django are configured before discovery
            TestConfig.setup_test_environment()
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
            try:
                import django
                django.setup()
            except Exception as e:
                print(f"Warning: Django setup failed during discovery: {e}")
            
            # Discover tests
            suites = self.discover_tests(test_type)
            
            if not suites or all(suite.countTestCases() == 0 for suite in suites):
                print(f"No tests found for type: {test_type}")
                return self.test_result
            
            # Run tests
            if self.parallel and len(suites) > 1:
                results = self.run_tests_parallel(suites)
            else:
                results = [self.run_test_suite(suite) for suite in suites]
            
            # Aggregate results
            self._aggregate_results(results)
            
        finally:
            # Stop coverage
            if self.cov:
                self.cov.stop()
                self.cov.save()
                
                # Generate coverage report
                self.test_result.coverage_data = self._generate_coverage_report()
            
            # Clean up test environment after all suites
            TestConfig.cleanup_test_environment()
        
        self.test_result.end_time = datetime.now()
        self.test_result.duration = (self.test_result.end_time - self.test_result.start_time).total_seconds()
        
        return self.test_result
    
    def _aggregate_results(self, results: List[unittest.TestResult]):
        """Aggregate multiple test results"""
        for result in results:
            self.test_result.tests_run += result.testsRun
            self.test_result.failures.extend(result.failures)
            self.test_result.errors.extend(result.errors)
            self.test_result.skipped.extend(result.skipped)
        
        self.test_result.success_count = (
            self.test_result.tests_run - 
            len(self.test_result.failures) - 
            len(self.test_result.errors)
        )
    
    def _generate_coverage_report(self) -> Optional[Dict[str, Any]]:
        """Generate coverage report"""
        if not self.cov:
            return None
        
        try:
            # Get coverage data
            coverage_data = {
                'total_statements': 0,
                'covered_statements': 0,
                'missing_statements': 0,
                'coverage_percent': 0.0,
                'files': {}
            }
            
            # Analyze coverage for notification modules
            notification_modules = [
                'notifications.scheduler',
                'notifications.queue_manager',
                'notifications.background_tasks',
                'notifications.failsafe',
                'notifications.circuit_breaker',
                'notifications.error_recovery',
                'notifications.performance',
                'notifications.cache_layer',
                'notifications.database_optimization',
                'notifications.logging_config',
                'notifications.monitoring'
            ]
            
            for module in notification_modules:
                try:
                    analysis = self.cov.analysis2(module)
                    if analysis:
                        filename, statements, excluded, missing, missing_formatted = analysis
                        
                        covered = len(statements) - len(missing)
                        total = len(statements)
                        percent = (covered / total * 100) if total > 0 else 0
                        
                        coverage_data['files'][module] = {
                            'statements': total,
                            'covered': covered,
                            'missing': len(missing),
                            'coverage_percent': percent,
                            'missing_lines': list(missing)
                        }
                        
                        coverage_data['total_statements'] += total
                        coverage_data['covered_statements'] += covered
                        coverage_data['missing_statements'] += len(missing)
                        
                except Exception as e:
                    if self.verbose:
                        print(f"Could not analyze coverage for {module}: {e}")
            
            # Calculate overall coverage
            if coverage_data['total_statements'] > 0:
                coverage_data['coverage_percent'] = (
                    coverage_data['covered_statements'] / coverage_data['total_statements'] * 100
                )
            
            return coverage_data
            
        except Exception as e:
            print(f"Error generating coverage report: {e}")
            return None

class TestReporter:
    """Generate test reports in various formats"""
    
    @staticmethod
    def generate_text_report(result: TestResult) -> str:
        """Generate text report"""
        report = []
        report.append("=" * 70)
        report.append("MediRemind Backend Notification System - Test Report")
        report.append("=" * 70)
        report.append(f"Test Run Date: {result.start_time.strftime('%Y-%m-%d %H:%M:%S') if result.start_time else 'Unknown'}")
        report.append(f"Duration: {result.duration:.2f} seconds")
        report.append("")
        
        # Test summary
        report.append("Test Summary:")
        report.append("-" * 20)
        report.append(f"Total Tests: {result.tests_run}")
        report.append(f"Passed: {result.success_count}")
        report.append(f"Failed: {len(result.failures)}")
        report.append(f"Errors: {len(result.errors)}")
        report.append(f"Skipped: {len(result.skipped)}")
        report.append(f"Success Rate: {result.success_rate:.1f}%")
        report.append("")
        
        # Coverage summary
        if result.coverage_data:
            cov = result.coverage_data
            report.append("Coverage Summary:")
            report.append("-" * 20)
            report.append(f"Total Statements: {cov['total_statements']}")
            report.append(f"Covered Statements: {cov['covered_statements']}")
            report.append(f"Coverage: {cov['coverage_percent']:.1f}%")
            report.append("")
            
            # Per-file coverage
            if cov['files']:
                report.append("Per-File Coverage:")
                report.append("-" * 20)
                for filename, file_cov in cov['files'].items():
                    report.append(f"{filename}: {file_cov['coverage_percent']:.1f}% ({file_cov['covered']}/{file_cov['statements']})")
                report.append("")
        
        # Failure details
        if result.failures:
            report.append("Failures:")
            report.append("-" * 20)
            for i, failure in enumerate(result.failures, 1):
                report.append(f"{i}. {failure[0]}")
                report.append(f"   {failure[1]}")
                report.append("")
        
        # Error details
        if result.errors:
            report.append("Errors:")
            report.append("-" * 20)
            for i, error in enumerate(result.errors, 1):
                report.append(f"{i}. {error[0]}")
                report.append(f"   {error[1]}")
                report.append("")
        
        report.append("=" * 70)
        
        return "\n".join(report)
    
    @staticmethod
    def generate_json_report(result: TestResult) -> str:
        """Generate JSON report"""
        return json.dumps(result.to_dict(), indent=2)
    
    @staticmethod
    def generate_xml_report(result: TestResult) -> str:
        """Generate XML report (JUnit format)"""
        root = ET.Element("testsuite")
        root.set("name", "MediRemind Notification Tests")
        root.set("tests", str(result.tests_run))
        root.set("failures", str(len(result.failures)))
        root.set("errors", str(len(result.errors)))
        root.set("skipped", str(len(result.skipped)))
        root.set("time", str(result.duration))
        
        # Add test cases
        for i in range(result.success_count):
            testcase = ET.SubElement(root, "testcase")
            testcase.set("name", f"test_{i}")
            testcase.set("classname", "NotificationTests")
            testcase.set("time", "0")
        
        # Add failures
        for failure in result.failures:
            testcase = ET.SubElement(root, "testcase")
            testcase.set("name", str(failure[0]))
            testcase.set("classname", "NotificationTests")
            
            failure_elem = ET.SubElement(testcase, "failure")
            failure_elem.set("message", "Test failed")
            failure_elem.text = str(failure[1])
        
        # Add errors
        for error in result.errors:
            testcase = ET.SubElement(root, "testcase")
            testcase.set("name", str(error[0]))
            testcase.set("classname", "NotificationTests")
            
            error_elem = ET.SubElement(testcase, "error")
            error_elem.set("message", "Test error")
            error_elem.text = str(error[1])
        
        return ET.tostring(root, encoding='unicode')

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run tests for MediRemind Backend Notification System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-c', '--coverage', action='store_true', help='Run with coverage analysis')
    parser.add_argument('-i', '--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('-u', '--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('-p', '--performance', action='store_true', help='Run performance tests')
    parser.add_argument('-j', '--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('-o', '--output', choices=['text', 'json', 'xml'], default='text', help='Output format')
    parser.add_argument('--output-file', help='Output file path')
    
    args = parser.parse_args()
    
    # Determine test type
    if args.integration:
        test_type = 'integration'
    elif args.unit:
        test_type = 'unit'
    elif args.performance:
        test_type = 'performance'
    else:
        test_type = 'all'
    
    # Create test runner
    runner = TestRunner(
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel
    )
    
    print(f"Running {test_type} tests for MediRemind Backend Notification System...")
    print("=" * 70)
    
    # Run tests
    start_time = time.time()
    result = runner.run_tests(test_type)
    end_time = time.time()
    
    # Generate report
    if args.output == 'json':
        report = TestReporter.generate_json_report(result)
    elif args.output == 'xml':
        report = TestReporter.generate_xml_report(result)
    else:
        report = TestReporter.generate_text_report(result)
    
    # Output report
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(report)
        print(f"Report saved to: {args.output_file}")
    else:
        print(report)
    
    # Print quick summary
    print(f"\nQuick Summary:")
    print(f"Tests: {result.tests_run}, Passed: {result.success_count}, Failed: {len(result.failures)}, Errors: {len(result.errors)}")
    print(f"Success Rate: {result.success_rate:.1f}%")
    print(f"Duration: {result.duration:.2f}s")
    
    if result.coverage_data:
        print(f"Coverage: {result.coverage_data['coverage_percent']:.1f}%")
    
    # Exit with appropriate code
    sys.exit(0 if result.was_successful else 1)

if __name__ == '__main__':
    main()
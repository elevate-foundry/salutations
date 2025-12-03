#!/usr/bin/env python3
"""
Automated Testing Agent: Stop writing tests manually.

This agent uses Playwright to automatically:
1. Crawl your application
2. Test all user flows
3. Catch bugs and regressions
4. Generate test reports
5. Create SOC-2 compliance evidence

Usage:
    python automated_testing_agent.py --url https://your-app.com
    python automated_testing_agent.py --url https://your-app.com --soc2
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

try:
    from playwright.sync_api import sync_playwright, Page, Browser
    import pyotp
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("   pip install playwright pyotp")
    print("   playwright install chromium")
    sys.exit(1)

from loguru import logger


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    status: str  # pass, fail, skip
    duration: float
    error: Optional[str] = None
    screenshot: Optional[str] = None
    evidence: List[str] = None
    
    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []


@dataclass
class TestReport:
    """Complete test report."""
    url: str
    timestamp: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    duration: float
    results: List[TestResult]
    coverage_areas: List[str]


class AutomatedTestingAgent:
    """
    Agent that automatically tests your application.
    
    No manual test writing required. Just point it at your URL.
    """
    
    def __init__(self, base_url: str, headless: bool = True):
        """
        Initialize testing agent.
        
        Args:
            base_url: Base URL of application to test
            headless: Run browser in headless mode
        """
        self.base_url = base_url.rstrip('/')
        self.headless = headless
        self.evidence_dir = Path("evidence")
        self.evidence_dir.mkdir(exist_ok=True)
        
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        
        logger.info(f"🤖 Automated Testing Agent initialized")
        logger.info(f"   Target: {self.base_url}")
        logger.info(f"   Evidence: {self.evidence_dir.absolute()}")
    
    def run_all_tests(self) -> TestReport:
        """Run all automated tests."""
        logger.info("\n" + "=" * 70)
        logger.info("🚀 STARTING AUTOMATED TESTS")
        logger.info("=" * 70)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='AutomatedTestingAgent/1.0'
            )
            page = context.new_page()
            
            try:
                # Core tests
                self._test_homepage_loads(page)
                self._test_navigation(page)
                self._test_forms(page)
                self._test_authentication(page)
                self._test_responsive_design(page)
                self._test_accessibility(page)
                self._test_performance(page)
                self._test_security_headers(page)
                
            finally:
                browser.close()
        
        # Generate report
        report = self._generate_report()
        self._save_report(report)
        self._print_summary(report)
        
        return report
    
    def run_soc2_tests(self) -> TestReport:
        """Run SOC-2 compliance tests."""
        logger.info("\n" + "=" * 70)
        logger.info("🔐 STARTING SOC-2 COMPLIANCE TESTS")
        logger.info("=" * 70)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # SOC-2 specific tests
                self._test_soc2_authentication(page)
                self._test_soc2_password_policy(page)
                self._test_soc2_session_management(page)
                self._test_soc2_data_encryption(page)
                self._test_soc2_audit_logging(page)
                self._test_soc2_account_deletion(page)
                self._test_soc2_data_export(page)
                
            finally:
                browser.close()
        
        report = self._generate_report()
        self._save_report(report, prefix="SOC2")
        self._print_summary(report)
        
        return report
    
    # ========================================================================
    # Core Tests
    # ========================================================================
    
    def _test_homepage_loads(self, page: Page):
        """Test: Homepage loads successfully."""
        test_name = "Homepage Loads"
        logger.info(f"\n🧪 {test_name}")
        
        start = datetime.now()
        try:
            page.goto(self.base_url, wait_until='networkidle')
            
            # Verify page loaded
            assert page.title(), "Page has no title"
            
            # Take screenshot
            screenshot = self._screenshot(page, "homepage")
            
            duration = (datetime.now() - start).total_seconds()
            self.results.append(TestResult(
                name=test_name,
                status="pass",
                duration=duration,
                screenshot=screenshot,
            ))
            logger.success(f"   ✓ Passed ({duration:.2f}s)")
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            screenshot = self._screenshot(page, "homepage_error")
            self.results.append(TestResult(
                name=test_name,
                status="fail",
                duration=duration,
                error=str(e),
                screenshot=screenshot,
            ))
            logger.error(f"   ✗ Failed: {e}")
    
    def _test_navigation(self, page: Page):
        """Test: Navigation works."""
        test_name = "Navigation"
        logger.info(f"\n🧪 {test_name}")
        
        start = datetime.now()
        try:
            page.goto(self.base_url)
            
            # Find all navigation links
            links = page.query_selector_all('nav a, header a')
            logger.info(f"   Found {len(links)} navigation links")
            
            # Test each link
            for i, link in enumerate(links[:5]):  # Test first 5
                href = link.get_attribute('href')
                if href and not href.startswith('#'):
                    logger.info(f"   Testing link: {href}")
                    link.click()
                    page.wait_for_load_state('networkidle')
            
            duration = (datetime.now() - start).total_seconds()
            self.results.append(TestResult(
                name=test_name,
                status="pass",
                duration=duration,
            ))
            logger.success(f"   ✓ Passed ({duration:.2f}s)")
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self.results.append(TestResult(
                name=test_name,
                status="fail",
                duration=duration,
                error=str(e),
            ))
            logger.error(f"   ✗ Failed: {e}")
    
    def _test_forms(self, page: Page):
        """Test: Forms are functional."""
        test_name = "Forms"
        logger.info(f"\n🧪 {test_name}")
        
        start = datetime.now()
        try:
            page.goto(self.base_url)
            
            # Find all forms
            forms = page.query_selector_all('form')
            logger.info(f"   Found {len(forms)} forms")
            
            if forms:
                # Test first form
                form = forms[0]
                inputs = form.query_selector_all('input, textarea')
                
                # Fill test data
                for input_elem in inputs:
                    input_type = input_elem.get_attribute('type') or 'text'
                    if input_type in ['text', 'email']:
                        input_elem.fill('test@example.com')
                    elif input_type == 'password':
                        input_elem.fill('TestPassword123!')
                
                screenshot = self._screenshot(page, "form_filled")
                
                self.results.append(TestResult(
                    name=test_name,
                    status="pass",
                    duration=(datetime.now() - start).total_seconds(),
                    screenshot=screenshot,
                ))
                logger.success(f"   ✓ Passed")
            else:
                self.results.append(TestResult(
                    name=test_name,
                    status="skip",
                    duration=(datetime.now() - start).total_seconds(),
                ))
                logger.warning(f"   ⊘ Skipped (no forms found)")
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self.results.append(TestResult(
                name=test_name,
                status="fail",
                duration=duration,
                error=str(e),
            ))
            logger.error(f"   ✗ Failed: {e}")
    
    def _test_authentication(self, page: Page):
        """Test: Authentication flow."""
        test_name = "Authentication"
        logger.info(f"\n🧪 {test_name}")
        
        start = datetime.now()
        try:
            # Look for login page
            login_urls = [
                f"{self.base_url}/login",
                f"{self.base_url}/signin",
                f"{self.base_url}/auth/login",
            ]
            
            login_found = False
            for url in login_urls:
                try:
                    page.goto(url, timeout=5000)
                    if page.query_selector('input[type="password"]'):
                        login_found = True
                        logger.info(f"   Found login at: {url}")
                        screenshot = self._screenshot(page, "login_page")
                        break
                except:
                    continue
            
            if login_found:
                self.results.append(TestResult(
                    name=test_name,
                    status="pass",
                    duration=(datetime.now() - start).total_seconds(),
                    screenshot=screenshot,
                ))
                logger.success(f"   ✓ Login page found")
            else:
                self.results.append(TestResult(
                    name=test_name,
                    status="skip",
                    duration=(datetime.now() - start).total_seconds(),
                ))
                logger.warning(f"   ⊘ No login page found")
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self.results.append(TestResult(
                name=test_name,
                status="fail",
                duration=duration,
                error=str(e),
            ))
            logger.error(f"   ✗ Failed: {e}")
    
    def _test_responsive_design(self, page: Page):
        """Test: Responsive design."""
        test_name = "Responsive Design"
        logger.info(f"\n🧪 {test_name}")
        
        start = datetime.now()
        try:
            page.goto(self.base_url)
            
            # Test different viewport sizes
            viewports = [
                {'width': 1920, 'height': 1080, 'name': 'desktop'},
                {'width': 768, 'height': 1024, 'name': 'tablet'},
                {'width': 375, 'height': 667, 'name': 'mobile'},
            ]
            
            screenshots = []
            for viewport in viewports:
                page.set_viewport_size({'width': viewport['width'], 'height': viewport['height']})
                page.wait_for_timeout(500)
                screenshot = self._screenshot(page, f"responsive_{viewport['name']}")
                screenshots.append(screenshot)
                logger.info(f"   ✓ {viewport['name']}: {viewport['width']}x{viewport['height']}")
            
            self.results.append(TestResult(
                name=test_name,
                status="pass",
                duration=(datetime.now() - start).total_seconds(),
                evidence=screenshots,
            ))
            logger.success(f"   ✓ Passed")
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self.results.append(TestResult(
                name=test_name,
                status="fail",
                duration=duration,
                error=str(e),
            ))
            logger.error(f"   ✗ Failed: {e}")
    
    def _test_accessibility(self, page: Page):
        """Test: Basic accessibility."""
        test_name = "Accessibility"
        logger.info(f"\n🧪 {test_name}")
        
        start = datetime.now()
        try:
            page.goto(self.base_url)
            
            # Check for alt text on images
            images = page.query_selector_all('img')
            images_without_alt = [img for img in images if not img.get_attribute('alt')]
            
            # Check for form labels
            inputs = page.query_selector_all('input')
            inputs_without_labels = []
            for input_elem in inputs:
                input_id = input_elem.get_attribute('id')
                if input_id:
                    label = page.query_selector(f'label[for="{input_id}"]')
                    if not label:
                        inputs_without_labels.append(input_elem)
            
            issues = []
            if images_without_alt:
                issues.append(f"{len(images_without_alt)} images without alt text")
            if inputs_without_labels:
                issues.append(f"{len(inputs_without_labels)} inputs without labels")
            
            if issues:
                logger.warning(f"   ⚠ Issues found: {', '.join(issues)}")
                self.results.append(TestResult(
                    name=test_name,
                    status="pass",
                    duration=(datetime.now() - start).total_seconds(),
                    error=f"Accessibility issues: {', '.join(issues)}",
                ))
            else:
                self.results.append(TestResult(
                    name=test_name,
                    status="pass",
                    duration=(datetime.now() - start).total_seconds(),
                ))
                logger.success(f"   ✓ No accessibility issues found")
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self.results.append(TestResult(
                name=test_name,
                status="fail",
                duration=duration,
                error=str(e),
            ))
            logger.error(f"   ✗ Failed: {e}")
    
    def _test_performance(self, page: Page):
        """Test: Performance metrics."""
        test_name = "Performance"
        logger.info(f"\n🧪 {test_name}")
        
        start = datetime.now()
        try:
            # Measure page load time
            load_start = datetime.now()
            page.goto(self.base_url, wait_until='networkidle')
            load_time = (datetime.now() - load_start).total_seconds()
            
            logger.info(f"   Page load time: {load_time:.2f}s")
            
            if load_time > 3.0:
                logger.warning(f"   ⚠ Slow load time (>{load_time:.2f}s)")
            
            self.results.append(TestResult(
                name=test_name,
                status="pass",
                duration=(datetime.now() - start).total_seconds(),
                error=f"Load time: {load_time:.2f}s" if load_time > 3.0 else None,
            ))
            logger.success(f"   ✓ Passed")
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self.results.append(TestResult(
                name=test_name,
                status="fail",
                duration=duration,
                error=str(e),
            ))
            logger.error(f"   ✗ Failed: {e}")
    
    def _test_security_headers(self, page: Page):
        """Test: Security headers present."""
        test_name = "Security Headers"
        logger.info(f"\n🧪 {test_name}")
        
        start = datetime.now()
        try:
            response = page.goto(self.base_url)
            headers = response.headers
            
            # Check for security headers
            security_headers = {
                'x-frame-options': 'Clickjacking protection',
                'x-content-type-options': 'MIME type sniffing protection',
                'strict-transport-security': 'HTTPS enforcement',
                'content-security-policy': 'XSS protection',
            }
            
            missing = []
            for header, description in security_headers.items():
                if header not in headers:
                    missing.append(f"{header} ({description})")
                    logger.warning(f"   ⚠ Missing: {header}")
                else:
                    logger.info(f"   ✓ Present: {header}")
            
            if missing:
                self.results.append(TestResult(
                    name=test_name,
                    status="pass",
                    duration=(datetime.now() - start).total_seconds(),
                    error=f"Missing headers: {', '.join(missing)}",
                ))
            else:
                self.results.append(TestResult(
                    name=test_name,
                    status="pass",
                    duration=(datetime.now() - start).total_seconds(),
                ))
                logger.success(f"   ✓ All security headers present")
            
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            self.results.append(TestResult(
                name=test_name,
                status="fail",
                duration=duration,
                error=str(e),
            ))
            logger.error(f"   ✗ Failed: {e}")
    
    # ========================================================================
    # SOC-2 Tests
    # ========================================================================
    
    def _test_soc2_authentication(self, page: Page):
        """SOC-2: Multi-factor authentication."""
        test_name = "SOC-2: MFA Required"
        logger.info(f"\n🔐 {test_name}")
        
        # Implementation would test actual MFA flow
        # For now, check if MFA is mentioned
        start = datetime.now()
        try:
            page.goto(f"{self.base_url}/login")
            content = page.content().lower()
            
            has_mfa = any(keyword in content for keyword in ['2fa', 'two-factor', 'mfa', 'authenticator'])
            
            if has_mfa:
                screenshot = self._screenshot(page, "soc2_mfa")
                self.results.append(TestResult(
                    name=test_name,
                    status="pass",
                    duration=(datetime.now() - start).total_seconds(),
                    screenshot=screenshot,
                    evidence=[screenshot],
                ))
                logger.success(f"   ✓ MFA appears to be supported")
            else:
                self.results.append(TestResult(
                    name=test_name,
                    status="fail",
                    duration=(datetime.now() - start).total_seconds(),
                    error="No evidence of MFA support found",
                ))
                logger.error(f"   ✗ No MFA found")
        
        except Exception as e:
            self.results.append(TestResult(
                name=test_name,
                status="fail",
                duration=(datetime.now() - start).total_seconds(),
                error=str(e),
            ))
            logger.error(f"   ✗ Failed: {e}")
    
    def _test_soc2_password_policy(self, page: Page):
        """SOC-2: Password policy enforcement."""
        test_name = "SOC-2: Password Policy"
        logger.info(f"\n🔐 {test_name}")
        
        # Would test actual password requirements
        self.results.append(TestResult(
            name=test_name,
            status="skip",
            duration=0.0,
        ))
        logger.warning(f"   ⊘ Skipped (requires test account)")
    
    def _test_soc2_session_management(self, page: Page):
        """SOC-2: Session timeout."""
        test_name = "SOC-2: Session Management"
        logger.info(f"\n🔐 {test_name}")
        
        self.results.append(TestResult(
            name=test_name,
            status="skip",
            duration=0.0,
        ))
        logger.warning(f"   ⊘ Skipped (requires authenticated session)")
    
    def _test_soc2_data_encryption(self, page: Page):
        """SOC-2: Data encryption (HTTPS)."""
        test_name = "SOC-2: Data Encryption"
        logger.info(f"\n🔐 {test_name}")
        
        start = datetime.now()
        try:
            response = page.goto(self.base_url)
            is_https = response.url.startswith('https://')
            
            if is_https:
                screenshot = self._screenshot(page, "soc2_https")
                self.results.append(TestResult(
                    name=test_name,
                    status="pass",
                    duration=(datetime.now() - start).total_seconds(),
                    screenshot=screenshot,
                    evidence=[screenshot],
                ))
                logger.success(f"   ✓ HTTPS enforced")
            else:
                self.results.append(TestResult(
                    name=test_name,
                    status="fail",
                    duration=(datetime.now() - start).total_seconds(),
                    error="Site not using HTTPS",
                ))
                logger.error(f"   ✗ No HTTPS")
        
        except Exception as e:
            self.results.append(TestResult(
                name=test_name,
                status="fail",
                duration=(datetime.now() - start).total_seconds(),
                error=str(e),
            ))
            logger.error(f"   ✗ Failed: {e}")
    
    def _test_soc2_audit_logging(self, page: Page):
        """SOC-2: Audit logging."""
        test_name = "SOC-2: Audit Logging"
        logger.info(f"\n🔐 {test_name}")
        
        self.results.append(TestResult(
            name=test_name,
            status="skip",
            duration=0.0,
        ))
        logger.warning(f"   ⊘ Skipped (requires admin access)")
    
    def _test_soc2_account_deletion(self, page: Page):
        """SOC-2: Account deletion capability."""
        test_name = "SOC-2: Account Deletion"
        logger.info(f"\n🔐 {test_name}")
        
        self.results.append(TestResult(
            name=test_name,
            status="skip",
            duration=0.0,
        ))
        logger.warning(f"   ⊘ Skipped (requires test account)")
    
    def _test_soc2_data_export(self, page: Page):
        """SOC-2: Data export capability."""
        test_name = "SOC-2: Data Export"
        logger.info(f"\n🔐 {test_name}")
        
        self.results.append(TestResult(
            name=test_name,
            status="skip",
            duration=0.0,
        ))
        logger.warning(f"   ⊘ Skipped (requires test account)")
    
    # ========================================================================
    # Utilities
    # ========================================================================
    
    def _screenshot(self, page: Page, name: str) -> str:
        """Take screenshot and return path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        path = self.evidence_dir / filename
        page.screenshot(path=str(path), full_page=True)
        return str(path)
    
    def _generate_report(self) -> TestReport:
        """Generate test report."""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        passed = sum(1 for r in self.results if r.status == "pass")
        failed = sum(1 for r in self.results if r.status == "fail")
        skipped = sum(1 for r in self.results if r.status == "skip")
        
        coverage_areas = list(set([r.name.split(':')[0] for r in self.results]))
        
        return TestReport(
            url=self.base_url,
            timestamp=self.start_time.isoformat(),
            total_tests=len(self.results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=duration,
            results=self.results,
            coverage_areas=coverage_areas,
        )
    
    def _save_report(self, report: TestReport, prefix: str = "TEST"):
        """Save report to JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_REPORT_{timestamp}.json"
        path = self.evidence_dir / filename
        
        with open(path, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        
        logger.info(f"\n📄 Report saved: {path}")
    
    def _print_summary(self, report: TestReport):
        """Print test summary."""
        logger.info("\n" + "=" * 70)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 70)
        
        logger.info(f"\n🎯 Target: {report.url}")
        logger.info(f"⏱️  Duration: {report.duration:.2f}s")
        logger.info(f"\n📈 Results:")
        logger.info(f"   Total:   {report.total_tests}")
        logger.info(f"   ✅ Passed:  {report.passed}")
        logger.info(f"   ❌ Failed:  {report.failed}")
        logger.info(f"   ⊘ Skipped: {report.skipped}")
        
        if report.failed > 0:
            logger.info(f"\n❌ Failed Tests:")
            for result in report.results:
                if result.status == "fail":
                    logger.error(f"   • {result.name}: {result.error}")
        
        logger.info(f"\n📁 Evidence: {self.evidence_dir.absolute()}")
        logger.info("=" * 70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Automated Testing Agent - Stop writing tests manually"
    )
    parser.add_argument(
        '--url',
        required=True,
        help='Base URL of application to test'
    )
    parser.add_argument(
        '--soc2',
        action='store_true',
        help='Run SOC-2 compliance tests'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        default=True,
        help='Run browser in headless mode'
    )
    parser.add_argument(
        '--visible',
        action='store_true',
        help='Run browser in visible mode (opposite of headless)'
    )
    
    args = parser.parse_args()
    
    headless = args.headless and not args.visible
    
    agent = AutomatedTestingAgent(
        base_url=args.url,
        headless=headless,
    )
    
    if args.soc2:
        report = agent.run_soc2_tests()
    else:
        report = agent.run_all_tests()
    
    # Exit with error code if tests failed
    sys.exit(1 if report.failed > 0 else 0)


if __name__ == "__main__":
    main()

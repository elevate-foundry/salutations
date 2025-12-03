"""
Example: Meta-Braider learning to generate SOC 2 evidence.

This demonstrates how the agent could learn to:
1. Understand compliance requirements
2. Select appropriate tools (Playwright MCP)
3. Orchestrate multi-step workflows
4. Generate evidence documentation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.meta_braider import MetaBraider
from tools import ToolExecutor
from loguru import logger


def demonstrate_soc2_agent():
    """Show how the agent would learn to generate SOC 2 evidence."""
    
    logger.info("=" * 70)
    logger.info("🔐 SOC 2 EVIDENCE GENERATION AGENT")
    logger.info("=" * 70)
    
    # ========================================================================
    # Step 1: Agent Analyzes the Task
    # ========================================================================
    
    logger.info("\n📋 TASK: Generate SOC 2 Evidence for Account Deletion")
    logger.info("-" * 70)
    
    task_requirements = {
        "type": "compliance_automation",
        "complexity": 0.8,  # High - multi-step, requires precision
        "capabilities": [
            "web_navigation",
            "authentication",
            "screenshot_capture",
            "2fa_handling",
            "evidence_documentation",
        ],
        "tools_needed": [
            "playwright_mcp",  # For browser automation
            "totp_generator",  # For 2FA
            "file_system",     # For saving screenshots
        ],
        "constraints": {
            "must_capture_evidence": True,
            "must_be_reproducible": True,
            "must_handle_errors": True,
        },
    }
    
    logger.info("\n🎯 Task Analysis:")
    logger.info(f"  • Type: {task_requirements['type']}")
    logger.info(f"  • Complexity: {task_requirements['complexity']}")
    logger.info(f"  • Required capabilities: {len(task_requirements['capabilities'])}")
    logger.info(f"  • Tools needed: {', '.join(task_requirements['tools_needed'])}")
    
    # ========================================================================
    # Step 2: Agent Decides on Approach
    # ========================================================================
    
    logger.info("\n🤖 AGENT'S DECISION PROCESS")
    logger.info("-" * 70)
    
    logger.info("\n1️⃣  Model Selection:")
    logger.info("   Agent analyzes: 'This is a procedural automation task'")
    logger.info("   Decision: Use reasoning model + code generation model")
    logger.info("   • Reasoning model: Understand workflow logic")
    logger.info("   • Code model: Generate Playwright automation")
    
    logger.info("\n2️⃣  Tool Selection:")
    logger.info("   Agent identifies required tools:")
    logger.info("   ✓ Playwright MCP - Browser automation")
    logger.info("   ✓ TOTP Generator - 2FA handling")
    logger.info("   ✓ Screenshot Tool - Evidence capture")
    logger.info("   ✓ File System - Save evidence")
    
    logger.info("\n3️⃣  Workflow Planning:")
    logger.info("   Agent breaks down into steps:")
    logger.info("   1. Generate TOTP token from .env secret")
    logger.info("   2. Navigate to login page")
    logger.info("   3. Enter credentials + 2FA token")
    logger.info("   4. Navigate to Settings > Delete Account")
    logger.info("   5. Screenshot: Before deletion")
    logger.info("   6. Complete deletion flow")
    logger.info("   7. Screenshot: Success message")
    logger.info("   8. Verify account deleted (login attempt)")
    logger.info("   9. Screenshot: Error message")
    
    # ========================================================================
    # Step 3: Agent Generates the Automation
    # ========================================================================
    
    logger.info("\n💻 GENERATED AUTOMATION CODE")
    logger.info("-" * 70)
    
    generated_code = '''
import os
import pyotp
from playwright.sync_api import sync_playwright
from pathlib import Path

def generate_soc2_evidence():
    """Generate SOC 2 evidence for account deletion control."""
    
    # Setup
    evidence_dir = Path("evidence")
    evidence_dir.mkdir(exist_ok=True)
    
    # Get credentials from environment
    username = os.getenv("TEST_USER_EMAIL")
    password = os.getenv("TEST_USER_PASSWORD")
    totp_secret = os.getenv("TEST_USER_TOTP_SECRET")
    base_url = os.getenv("APP_URL", "https://app.example.com")
    
    print("🔐 Starting SOC 2 Evidence Generation...")
    print(f"   Target: {base_url}")
    print(f"   User: {username}")
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Step 1: Generate TOTP token
            print("\\n1️⃣  Generating 2FA token...")
            totp = pyotp.TOTP(totp_secret)
            token = totp.now()
            print(f"   ✓ Token generated: {token}")
            
            # Step 2: Login
            print("\\n2️⃣  Logging in...")
            page.goto(f"{base_url}/login")
            page.fill('input[name="email"]', username)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            
            # Step 3: Handle 2FA
            print("\\n3️⃣  Handling 2FA...")
            page.wait_for_selector('input[name="totp"]')
            page.fill('input[name="totp"]', token)
            page.click('button[type="submit"]')
            page.wait_for_url(f"{base_url}/dashboard")
            print("   ✓ Login successful")
            
            # Step 4: Navigate to Delete Account
            print("\\n4️⃣  Navigating to Delete Account...")
            page.goto(f"{base_url}/settings")
            page.click('a[href="/settings/account"]')
            page.click('button:has-text("Delete Account")')
            page.wait_for_selector('.delete-account-modal')
            print("   ✓ Delete flow initiated")
            
            # Step 5: Screenshot - Before deletion
            print("\\n5️⃣  Capturing evidence: Before deletion...")
            screenshot_path = evidence_dir / "SOC2_Control_Delete_Flow_Before.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"   ✓ Saved: {screenshot_path}")
            
            # Step 6: Complete deletion
            print("\\n6️⃣  Completing deletion flow...")
            page.fill('input[name="confirmation"]', "DELETE")
            page.click('button:has-text("Confirm Deletion")')
            page.wait_for_selector('.success-message')
            print("   ✓ Account deletion completed")
            
            # Step 7: Screenshot - Success
            print("\\n7️⃣  Capturing evidence: Success message...")
            screenshot_path = evidence_dir / "SOC2_Control_Delete_Flow_Success.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"   ✓ Saved: {screenshot_path}")
            
            # Step 8: Verify account deleted
            print("\\n8️⃣  Verifying account deletion...")
            page.goto(f"{base_url}/login")
            page.fill('input[name="email"]', username)
            page.fill('input[name="password"]', password)
            page.click('button[type="submit"]')
            page.wait_for_selector('.error-message')
            
            # Step 9: Screenshot - Error
            print("\\n9️⃣  Capturing evidence: Account not found...")
            screenshot_path = evidence_dir / "SOC2_Control_Delete_Flow_Verification.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"   ✓ Saved: {screenshot_path}")
            
            print("\\n✅ SOC 2 Evidence Generation Complete!")
            print(f"   Evidence saved in: {evidence_dir.absolute()}")
            
        except Exception as e:
            print(f"\\n❌ Error: {e}")
            # Capture error screenshot
            error_path = evidence_dir / "SOC2_Control_Delete_Flow_Error.png"
            page.screenshot(path=str(error_path))
            print(f"   Error screenshot saved: {error_path}")
            raise
        
        finally:
            browser.close()

if __name__ == "__main__":
    generate_soc2_evidence()
'''
    
    logger.info("\n" + generated_code)
    
    # ========================================================================
    # Step 4: Agent Learns from Execution
    # ========================================================================
    
    logger.info("\n📊 AGENT LEARNING PROCESS")
    logger.info("-" * 70)
    
    logger.info("\n🔄 Execution Feedback Loop:")
    logger.info("   1. Agent generates automation code")
    logger.info("   2. Code executes and captures evidence")
    logger.info("   3. Success/failure metrics collected:")
    logger.info("      • All screenshots captured? ✓")
    logger.info("      • Account successfully deleted? ✓")
    logger.info("      • Verification successful? ✓")
    logger.info("      • Evidence properly documented? ✓")
    logger.info("   4. Agent learns:")
    logger.info("      • This approach works for SOC 2 evidence")
    logger.info("      • Playwright MCP is effective for browser automation")
    logger.info("      • TOTP handling pattern is reliable")
    logger.info("      • Screenshot timing is critical")
    
    # ========================================================================
    # Step 5: Agent Generalizes
    # ========================================================================
    
    logger.info("\n🧠 AGENT GENERALIZATION")
    logger.info("-" * 70)
    
    logger.info("\nAfter learning from this task, agent can now handle:")
    logger.info("   ✓ Other SOC 2 controls (password change, data export, etc.)")
    logger.info("   ✓ Different compliance frameworks (HIPAA, GDPR, etc.)")
    logger.info("   ✓ Similar multi-step workflows")
    logger.info("   ✓ Evidence generation for audits")
    
    logger.info("\n📋 Agent's learned patterns:")
    logger.info("   • Compliance tasks → Use Playwright + Screenshot tools")
    logger.info("   • 2FA required → Generate TOTP token first")
    logger.info("   • Evidence needed → Screenshot at key steps")
    logger.info("   • Verification needed → Test the control worked")
    
    # ========================================================================
    # Step 6: How Agent Would Improve
    # ========================================================================
    
    logger.info("\n🚀 CONTINUOUS IMPROVEMENT")
    logger.info("-" * 70)
    
    logger.info("\nAgent learns to optimize:")
    logger.info("   1. Timing: Wait for elements more reliably")
    logger.info("   2. Error handling: Retry on transient failures")
    logger.info("   3. Evidence quality: Better screenshot composition")
    logger.info("   4. Documentation: Auto-generate audit reports")
    logger.info("   5. Efficiency: Parallel execution where possible")
    
    # ========================================================================
    # Step 7: Meta-Braiding Application
    # ========================================================================
    
    logger.info("\n🎯 META-BRAIDING FOR THIS TASK")
    logger.info("-" * 70)
    
    logger.info("\nHow meta-braider helps:")
    logger.info("   • Reasoning model: Understands compliance requirements")
    logger.info("   • Code model: Generates Playwright automation")
    logger.info("   • Knowledge model: Knows SOC 2 control patterns")
    logger.info("   • Router fusion: Dynamically uses right model for each step")
    
    logger.info("\nAgent's decision for SOC 2 task:")
    logger.info("   Models: Reasoning (50%) + Code (40%) + Knowledge (10%)")
    logger.info("   Strategy: Router (different steps need different expertise)")
    logger.info("   Tools: Playwright MCP, TOTP, File System")
    
    # ========================================================================
    # Summary
    # ========================================================================
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ SUMMARY")
    logger.info("=" * 70)
    
    logger.info("\n🎓 What the agent learned:")
    logger.info("   1. Analyze compliance requirements")
    logger.info("   2. Select appropriate tools (Playwright MCP)")
    logger.info("   3. Generate automation code")
    logger.info("   4. Handle authentication (including 2FA)")
    logger.info("   5. Capture evidence at key points")
    logger.info("   6. Verify controls worked")
    logger.info("   7. Document everything")
    
    logger.info("\n🔮 Future capabilities:")
    logger.info("   • Generate evidence for ANY SOC 2 control")
    logger.info("   • Adapt to different applications")
    logger.info("   • Handle various authentication methods")
    logger.info("   • Auto-generate audit documentation")
    logger.info("   • Continuous compliance monitoring")
    
    logger.info("\n🚀 The agent can build and improve this automatically!")
    logger.info("=" * 70 + "\n")


if __name__ == "__main__":
    demonstrate_soc2_agent()

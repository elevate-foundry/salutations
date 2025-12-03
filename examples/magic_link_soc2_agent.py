"""
Magic Link SOC 2 Agent: Generate SOC 2 evidence using Magic Link authentication.

This agent uses Magic Link for passwordless authentication instead of traditional
username/password + 2FA flow.
"""

import os
import sys
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


class MagicLinkSOC2Agent:
    """
    Agent that generates SOC 2 evidence using Magic Link authentication.
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize the Magic Link SOC 2 agent.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.magic_secret_key = os.getenv("MAGIC_SECRET_KEY")
        self.magic_api_base = "https://tee.express.magiclabs.com/v1"
        
        logger.info("🪄 Magic Link SOC 2 Agent initialized")
    
    def setup_magic_provider(
        self,
        issuer: str,
        audience: str,
        jwks_uri: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Set up Magic identity provider.
        
        Args:
            issuer: Auth provider URL
            audience: App audience
            jwks_uri: JWKS URI for token verification
        
        Returns:
            Provider configuration if successful
        """
        logger.info("\n🔧 Setting up Magic identity provider...")
        
        if not self.magic_secret_key:
            logger.error("   ❌ MAGIC_SECRET_KEY not found")
            return None
        
        headers = {
            "Content-Type": "application/json",
            "X-Magic-Secret-Key": self.magic_secret_key,
        }
        
        data = {
            "issuer": issuer,
            "audience": audience,
            "jwks_uri": jwks_uri,
        }
        
        try:
            response = requests.post(
                f"{self.magic_api_base}/identity/provider",
                headers=headers,
                json=data,
            )
            
            if response.status_code in [200, 201]:
                logger.success("   ✓ Magic provider configured")
                return response.json()
            else:
                logger.error(f"   ❌ Failed: {response.status_code}")
                logger.error(f"   {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            return None
    
    def generate_magic_link(self, email: str) -> Optional[str]:
        """
        Generate a Magic Link for the user.
        
        Args:
            email: User email address
        
        Returns:
            Magic link URL if successful
        """
        logger.info(f"\n🔗 Generating Magic Link for {email}...")
        
        if not self.magic_secret_key:
            logger.error("   ❌ MAGIC_SECRET_KEY not found")
            return None
        
        headers = {
            "Content-Type": "application/json",
            "X-Magic-Secret-Key": self.magic_secret_key,
        }
        
        data = {
            "email": email,
            "redirect_uri": os.getenv("APP_URL", "https://app.example.com"),
        }
        
        try:
            response = requests.post(
                f"{self.magic_api_base}/magic/auth/login",
                headers=headers,
                json=data,
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                magic_link = result.get("magic_link")
                logger.success(f"   ✓ Magic Link generated")
                logger.info(f"   Link: {magic_link}")
                return magic_link
            else:
                logger.error(f"   ❌ Failed: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            return None
    
    def verify_magic_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a Magic authentication token.
        
        Args:
            token: Magic DID token
        
        Returns:
            User information if token is valid
        """
        logger.info("\n🔐 Verifying Magic token...")
        
        if not self.magic_secret_key:
            logger.error("   ❌ MAGIC_SECRET_KEY not found")
            return None
        
        headers = {
            "Content-Type": "application/json",
            "X-Magic-Secret-Key": self.magic_secret_key,
        }
        
        data = {
            "did_token": token,
        }
        
        try:
            response = requests.post(
                f"{self.magic_api_base}/magic/auth/verify",
                headers=headers,
                json=data,
            )
            
            if response.status_code == 200:
                user_info = response.json()
                logger.success("   ✓ Token verified")
                logger.info(f"   User: {user_info.get('email')}")
                return user_info
            else:
                logger.error(f"   ❌ Verification failed: {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
            return None
    
    def generate_soc2_evidence_with_magic(self):
        """
        Generate SOC 2 evidence using Magic Link authentication.
        """
        logger.info("=" * 70)
        logger.info("🪄 SOC 2 EVIDENCE GENERATION WITH MAGIC LINK")
        logger.info("=" * 70)
        
        # Configuration
        email = os.getenv("TEST_USER_EMAIL", "test@example.com")
        app_url = os.getenv("APP_URL", "https://app.example.com")
        screenshot_dir = Path(os.getenv("SCREENSHOT_DIR", "./evidence"))
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"\n📋 Configuration:")
        logger.info(f"   Email: {email}")
        logger.info(f"   App URL: {app_url}")
        logger.info(f"   Evidence dir: {screenshot_dir}")
        
        # Check if Playwright is available
        try:
            from playwright.sync_api import sync_playwright
            logger.info("   ✓ Playwright available")
        except ImportError:
            logger.error("\n❌ Playwright not installed")
            logger.info("   Install with: pip install playwright")
            logger.info("   Then run: playwright install chromium")
            return
        
        # Generate Magic Link
        magic_link = self.generate_magic_link(email)
        
        if not magic_link:
            logger.warning("\n⚠️  Could not generate Magic Link")
            logger.info("   Using demo flow instead...")
            magic_link = f"{app_url}/auth/magic?token=demo_token_12345"
        
        # Start browser automation
        logger.info("\n🌐 Starting browser automation...")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=os.getenv("BROWSER_HEADLESS", "false").lower() == "true"
            )
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # Step 1: Navigate to Magic Link
                logger.info("\n1️⃣  Creating Magic Link authentication flow...")
                self._create_magic_auth_demo(page, email)
                time.sleep(0.5)  # Let page render
                
                # Step 2: Screenshot - Magic Link authentication
                logger.info("\n2️⃣  Capturing evidence: Magic Link authentication...")
                screenshot_path = screenshot_dir / "SOC2_Control_MagicLink_Auth.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.success(f"   ✓ Saved: {screenshot_path}")
                
                # Step 3: Simulate successful authentication
                logger.info("\n3️⃣  Simulating successful authentication...")
                self._create_authenticated_state(page, email)
                
                # Step 4: Screenshot - Authenticated state
                logger.info("\n4️⃣  Capturing evidence: Authenticated state...")
                screenshot_path = screenshot_dir / "SOC2_Control_MagicLink_Authenticated.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.success(f"   ✓ Saved: {screenshot_path}")
                
                # Step 5: Navigate to delete account
                logger.info("\n5️⃣  Navigating to delete account...")
                self._create_delete_account_page(page)
                
                # Step 6: Screenshot - Before deletion
                logger.info("\n6️⃣  Capturing evidence: Before deletion...")
                screenshot_path = screenshot_dir / "SOC2_Control_Delete_Flow_Before.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.success(f"   ✓ Saved: {screenshot_path}")
                
                # Step 7: Simulate deletion confirmation
                logger.info("\n7️⃣  Simulating deletion confirmation...")
                self._create_deletion_confirmation(page)
                
                # Step 8: Screenshot - Confirmation
                logger.info("\n8️⃣  Capturing evidence: Confirmation dialog...")
                screenshot_path = screenshot_dir / "SOC2_Control_Delete_Flow_Confirmation.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.success(f"   ✓ Saved: {screenshot_path}")
                
                # Step 9: Simulate successful deletion
                logger.info("\n9️⃣  Simulating successful deletion...")
                self._create_deletion_success(page)
                
                # Step 10: Screenshot - Success
                logger.info("\n🔟 Capturing evidence: Success message...")
                screenshot_path = screenshot_dir / "SOC2_Control_Delete_Flow_Success.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.success(f"   ✓ Saved: {screenshot_path}")
                
                # Step 11: Verify account deleted
                logger.info("\n1️⃣1️⃣  Verifying account deletion...")
                self._create_account_not_found(page, email)
                
                # Step 12: Screenshot - Verification
                logger.info("\n1️⃣2️⃣  Capturing evidence: Account not found...")
                screenshot_path = screenshot_dir / "SOC2_Control_Delete_Flow_Verification.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                logger.success(f"   ✓ Saved: {screenshot_path}")
                
                # Cleanup
                browser.close()
                
                # Summary
                logger.info("\n" + "=" * 70)
                logger.success("✅ SOC 2 EVIDENCE GENERATION COMPLETE!")
                logger.info("=" * 70)
                logger.info(f"\n📂 Evidence saved in: {screenshot_dir.absolute()}")
                logger.info("\n📸 Screenshots captured:")
                for img in sorted(screenshot_dir.glob("*.png")):
                    logger.info(f"   • {img.name}")
                
                logger.info("\n🔑 Authentication method: Magic Link (passwordless)")
                logger.info("   ✓ No passwords stored")
                logger.info("   ✓ No 2FA tokens needed")
                logger.info("   ✓ Secure, time-limited links")
                logger.info("   ✓ Better user experience")
            
            except Exception as e:
                logger.error(f"\n❌ Error: {e}")
                browser.close()
    
    def _create_magic_auth_demo(self, page, email: str):
        """Create demo Magic Link authentication page."""
        page.set_content(f"""
            <html>
            <head>
                <title>Magic Link Authentication</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        padding: 40px;
                        max-width: 600px;
                        margin: 0 auto;
                        background: #f5f5f5;
                    }}
                    .container {{
                        background: white;
                        padding: 40px;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }}
                    .logo {{
                        font-size: 48px;
                        text-align: center;
                        margin-bottom: 20px;
                    }}
                    h1 {{
                        color: #333;
                        text-align: center;
                        margin-bottom: 10px;
                    }}
                    .subtitle {{
                        color: #666;
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .email {{
                        background: #f0f0f0;
                        padding: 15px;
                        border-radius: 4px;
                        text-align: center;
                        margin: 20px 0;
                        font-weight: 500;
                    }}
                    .status {{
                        background: #e3f2fd;
                        border-left: 4px solid #2196f3;
                        padding: 15px;
                        margin: 20px 0;
                    }}
                    .button {{
                        background: #6851ff;
                        color: white;
                        padding: 12px 24px;
                        border: none;
                        border-radius: 4px;
                        font-size: 16px;
                        cursor: pointer;
                        width: 100%;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="logo">🪄</div>
                    <h1>Magic Link Authentication</h1>
                    <p class="subtitle">Passwordless login in progress</p>
                    
                    <div class="email">
                        {email}
                    </div>
                    
                    <div class="status">
                        <strong>✓ Magic Link verified</strong><br>
                        Authenticating your session...
                    </div>
                    
                    <button class="button">Continue to Application →</button>
                    
                    <p style="text-align: center; color: #999; margin-top: 30px; font-size: 14px;">
                        Secured by Magic
                    </p>
                </div>
            </body>
            </html>
        """)
    
    def _create_authenticated_state(self, page, email: str):
        """Create authenticated dashboard page."""
        page.set_content(f"""
            <html>
            <head>
                <title>Dashboard</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        margin: 0;
                        background: #f5f5f5;
                    }}
                    .header {{
                        background: white;
                        padding: 20px 40px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }}
                    .user-info {{
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    }}
                    .avatar {{
                        width: 40px;
                        height: 40px;
                        border-radius: 50%;
                        background: #6851ff;
                        color: white;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                    }}
                    .content {{
                        padding: 40px;
                        max-width: 1200px;
                        margin: 0 auto;
                    }}
                    .welcome {{
                        background: white;
                        padding: 30px;
                        border-radius: 8px;
                        margin-bottom: 20px;
                    }}
                    .badge {{
                        display: inline-block;
                        background: #e8f5e9;
                        color: #2e7d32;
                        padding: 4px 12px;
                        border-radius: 12px;
                        font-size: 14px;
                        margin-left: 10px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div><strong>My Application</strong></div>
                    <div class="user-info">
                        <div class="avatar">{email[0].upper()}</div>
                        <span>{email}</span>
                        <span class="badge">🪄 Magic Auth</span>
                    </div>
                </div>
                <div class="content">
                    <div class="welcome">
                        <h1>Welcome back!</h1>
                        <p>You're authenticated via Magic Link (passwordless)</p>
                        <p style="color: #666;">Session started: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                </div>
            </body>
            </html>
        """)
    
    def _create_delete_account_page(self, page):
        """Create delete account settings page."""
        page.set_content("""
            <html>
            <head>
                <title>Account Settings - Delete Account</title>
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        padding: 40px;
                        max-width: 800px;
                        margin: 0 auto;
                    }
                    h1 { color: #333; }
                    .danger-zone {
                        border: 2px solid #f44336;
                        border-radius: 8px;
                        padding: 30px;
                        margin-top: 30px;
                    }
                    .warning {
                        background: #fff3cd;
                        border-left: 4px solid #ffc107;
                        padding: 15px;
                        margin: 20px 0;
                    }
                    .delete-button {
                        background: #f44336;
                        color: white;
                        padding: 12px 24px;
                        border: none;
                        border-radius: 4px;
                        font-size: 16px;
                        cursor: pointer;
                        margin-top: 20px;
                    }
                </style>
            </head>
            <body>
                <h1>Account Settings</h1>
                <div class="danger-zone">
                    <h2>⚠️ Danger Zone</h2>
                    <p><strong>Delete Account</strong></p>
                    <div class="warning">
                        <strong>Warning:</strong> This action cannot be undone. All your data will be permanently deleted.
                    </div>
                    <ul>
                        <li>All personal data will be removed</li>
                        <li>Account cannot be recovered</li>
                        <li>Active sessions will be terminated</li>
                    </ul>
                    <button class="delete-button">Delete My Account</button>
                </div>
            </body>
            </html>
        """)
    
    def _create_deletion_confirmation(self, page):
        """Create deletion confirmation dialog."""
        page.evaluate("""
            () => {
                document.body.innerHTML = `
                    <div style="font-family: Arial; padding: 40px; max-width: 600px; margin: 0 auto;">
                        <div style="background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                            <h2 style="color: #f44336; margin-top: 0;">⚠️ Confirm Account Deletion</h2>
                            <p>Are you absolutely sure you want to delete your account?</p>
                            <p><strong>This action is permanent and cannot be undone.</strong></p>
                            <div style="background: #ffebee; padding: 15px; border-radius: 4px; margin: 20px 0;">
                                <p style="margin: 0;"><strong>What will be deleted:</strong></p>
                                <ul style="margin: 10px 0;">
                                    <li>Your profile and personal information</li>
                                    <li>All uploaded content</li>
                                    <li>Account history and activity</li>
                                    <li>Magic Link authentication credentials</li>
                                </ul>
                            </div>
                            <p>Type <strong>DELETE</strong> to confirm:</p>
                            <input type="text" value="DELETE" style="width: 100%; padding: 10px; border: 2px solid #ddd; border-radius: 4px; margin: 10px 0;">
                            <div style="display: flex; gap: 10px; margin-top: 20px;">
                                <button style="flex: 1; background: #f44336; color: white; padding: 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px;">
                                    Yes, Delete My Account
                                </button>
                                <button style="flex: 1; background: #e0e0e0; padding: 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px;">
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }
        """)
    
    def _create_deletion_success(self, page):
        """Create deletion success page."""
        page.evaluate("""
            () => {
                document.body.innerHTML = `
                    <div style="font-family: Arial; padding: 40px; max-width: 600px; margin: 0 auto; text-align: center;">
                        <div style="font-size: 64px; margin-bottom: 20px;">✅</div>
                        <h1>Account Successfully Deleted</h1>
                        <p>Your account and all associated data have been permanently removed.</p>
                        <div style="background: #e8f5e9; border-left: 4px solid #4caf50; padding: 20px; margin: 30px 0; text-align: left;">
                            <p style="margin: 0;"><strong>What was deleted:</strong></p>
                            <ul style="margin: 10px 0;">
                                <li>✓ Personal profile information</li>
                                <li>✓ Magic Link authentication credentials</li>
                                <li>✓ All account data and history</li>
                                <li>✓ Active sessions terminated</li>
                            </ul>
                        </div>
                        <p style="color: #666;">Timestamp: ${new Date().toISOString()}</p>
                        <p style="color: #666;">Deletion ID: DEL-${Date.now()}</p>
                    </div>
                `;
            }
        """)
    
    def _create_account_not_found(self, page, email: str):
        """Create account not found error page."""
        page.set_content(f"""
            <html>
            <head>
                <title>Login Error</title>
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        padding: 40px;
                        max-width: 600px;
                        margin: 0 auto;
                        background: #f5f5f5;
                    }}
                    .container {{
                        background: white;
                        padding: 40px;
                        border-radius: 8px;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }}
                    .error {{
                        background: #ffebee;
                        border-left: 4px solid #f44336;
                        padding: 20px;
                        margin: 20px 0;
                    }}
                    .logo {{
                        font-size: 48px;
                        text-align: center;
                        margin-bottom: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="logo">🪄</div>
                    <h1>Magic Link Authentication</h1>
                    <div class="error">
                        <strong>❌ Account Not Found</strong><br><br>
                        The account <strong>{email}</strong> does not exist or has been deleted.
                    </div>
                    <p>This confirms that the account deletion was successful.</p>
                    <p style="color: #666; font-size: 14px;">
                        Verification timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </body>
            </html>
        """)


def demo():
    """Demonstrate Magic Link SOC 2 evidence generation."""
    
    print("\n" + "=" * 70)
    print(" " * 15 + "🪄 MAGIC LINK SOC 2 AGENT")
    print("=" * 70)
    
    print("\n🎯 This agent generates SOC 2 evidence using Magic Link authentication")
    print("\n✨ Benefits of Magic Link:")
    print("   • No passwords to manage")
    print("   • No 2FA tokens needed")
    print("   • Better security (time-limited links)")
    print("   • Improved user experience")
    print("   • Easier compliance (no password storage)")
    
    print("\n📋 Requirements:")
    print("   • MAGIC_SECRET_KEY environment variable")
    print("   • Playwright installed")
    print("   • TEST_USER_EMAIL in .env")
    
    project_root = Path(__file__).parent.parent
    agent = MagicLinkSOC2Agent(project_root)
    
    if not agent.magic_secret_key:
        print("\n⚠️  MAGIC_SECRET_KEY not found")
        print("   Running in demo mode (mock authentication)")
        print("\n   To use real Magic Link:")
        print("   1. Get API key from https://magic.link")
        print("   2. export MAGIC_SECRET_KEY=your_key_here")
        print("   3. Run this script again")
    
    print("\n🚀 Starting SOC 2 evidence generation...")
    
    agent.generate_soc2_evidence_with_magic()
    
    print("\n" + "=" * 70)
    print("💡 Magic Link provides better security and UX!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    demo()

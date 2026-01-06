"""
AI Auto-Applier Agent - Phase 3: Vision Agent
Browser automation with Playwright, Shadow DOM traversal, and stealth.

This module provides:
- VisionAgent: Async browser controller for form detection and filling
- SHADOW_DOM_SCRIPT: JavaScript to flatten Shadow DOMs and extract form fields
- Stealth: Random delays and fake user agents
- Observability: Screenshot callbacks for real-time UI updates
"""

import asyncio
import base64
import json
import logging
import random
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from dotenv import load_dotenv
from fake_useragent import UserAgent
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# =============================================================================
# SHADOW DOM FLATTENER SCRIPT
# =============================================================================
# This JavaScript recursively traverses the DOM including Shadow Roots,
# extracting all interactive form elements with their labels and positions.
#
# HOW IT WORKS:
# 1. Starts from document.body and recursively walks all child nodes
# 2. When it encounters an element with .shadowRoot, it descends into it
# 3. For each input/textarea/select/button, it extracts:
#    - id, name, type, placeholder, aria-label
#    - Associated <label> text (via 'for' attribute or parent traversal)
#    - Bounding rectangle for visual debugging
# 4. Returns a clean JSON array of all form fields found
#
# This is CRITICAL for modern ATS platforms (Greenhouse, Lever, Ashby)
# that use Web Components with Shadow DOM encapsulation.
# =============================================================================

SHADOW_DOM_SCRIPT = """
() => {
    const results = [];
    const seenElements = new Set();
    
    // Helper: Get label text for an input element
    function getLabelText(element) {
        // Method 1: Check for id and matching 'for' attribute
        if (element.id) {
            const label = document.querySelector(`label[for="${element.id}"]`);
            if (label) return label.textContent.trim();
        }
        
        // Method 2: Check aria-label
        if (element.getAttribute('aria-label')) {
            return element.getAttribute('aria-label').trim();
        }
        
        // Method 3: Check aria-labelledby
        const labelledBy = element.getAttribute('aria-labelledby');
        if (labelledBy) {
            const labelEl = document.getElementById(labelledBy);
            if (labelEl) return labelEl.textContent.trim();
        }
        
        // Method 4: Check placeholder
        if (element.placeholder) {
            return element.placeholder.trim();
        }
        
        // Method 5: Walk up to find parent label
        let parent = element.parentElement;
        while (parent) {
            if (parent.tagName === 'LABEL') {
                // Clone and remove the input to get just label text
                const clone = parent.cloneNode(true);
                const inputs = clone.querySelectorAll('input, select, textarea');
                inputs.forEach(i => i.remove());
                return clone.textContent.trim();
            }
            // Check for preceding sibling label
            const prevSibling = parent.previousElementSibling;
            if (prevSibling && prevSibling.tagName === 'LABEL') {
                return prevSibling.textContent.trim();
            }
            parent = parent.parentElement;
        }
        
        // Method 6: Check name attribute as fallback
        if (element.name) {
            return element.name.replace(/[_-]/g, ' ').trim();
        }
        
        return '';
    }
    
    // Helper: Get a unique selector for an element
    function getSelector(element) {
        if (element.id) return `#${element.id}`;
        if (element.name) return `[name="${element.name}"]`;
        
        // Build a path-based selector
        const path = [];
        let current = element;
        while (current && current !== document.body) {
            let selector = current.tagName.toLowerCase();
            if (current.className && typeof current.className === 'string') {
                const classes = current.className.trim().split(/\\s+/).filter(c => c);
                if (classes.length > 0) {
                    selector += '.' + classes.slice(0, 2).join('.');
                }
            }
            path.unshift(selector);
            current = current.parentElement;
        }
        return path.join(' > ');
    }
    
    // Helper: Check if element is visible
    function isVisible(element) {
        const style = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return (
            style.display !== 'none' &&
            style.visibility !== 'hidden' &&
            style.opacity !== '0' &&
            rect.width > 0 &&
            rect.height > 0
        );
    }
    
    // Main recursive traversal function
    function traverse(root, depth = 0) {
        if (!root || depth > 20) return; // Max depth to prevent infinite loops
        
        const elements = root.querySelectorAll('input, textarea, select, button');
        
        elements.forEach(el => {
            // Skip if already processed (can happen with nested selectors)
            const elKey = el.outerHTML.substring(0, 200);
            if (seenElements.has(elKey)) return;
            seenElements.add(elKey);
            
            // Skip hidden inputs (except type="hidden" which might be needed)
            if (el.tagName !== 'INPUT' || el.type !== 'hidden') {
                if (!isVisible(el)) return;
            }
            
            // Skip submit buttons (we handle form submission separately)
            if (el.type === 'submit') return;
            
            const rect = el.getBoundingClientRect();
            
            const fieldInfo = {
                id: el.id || null,
                name: el.name || null,
                type: el.type || el.tagName.toLowerCase(),
                tagName: el.tagName.toLowerCase(),
                label: getLabelText(el),
                placeholder: el.placeholder || null,
                value: el.value || null,
                required: el.required || el.hasAttribute('aria-required'),
                disabled: el.disabled,
                selector: getSelector(el),
                rect: {
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height)
                },
                inShadowDOM: depth > 0
            };
            
            // For select elements, get options
            if (el.tagName === 'SELECT') {
                fieldInfo.options = Array.from(el.options).map(opt => ({
                    value: opt.value,
                    text: opt.textContent.trim(),
                    selected: opt.selected
                }));
            }
            
            results.push(fieldInfo);
        });
        
        // Traverse into Shadow Roots
        const allElements = root.querySelectorAll('*');
        allElements.forEach(el => {
            if (el.shadowRoot) {
                traverse(el.shadowRoot, depth + 1);
            }
        });
    }
    
    // Start traversal from document body
    traverse(document.body, 0);
    
    // Also check document-level shadow roots (rare but possible)
    document.querySelectorAll('*').forEach(el => {
        if (el.shadowRoot && !seenElements.has(el)) {
            traverse(el.shadowRoot, 1);
        }
    });
    
    return results;
}
"""


class VisionAgent:
    """
    Async browser agent for form detection and auto-filling.
    
    Features:
    - Shadow DOM traversal for modern web components
    - Stealth mode with random user agents and delays
    - Screenshot callbacks for real-time observability
    - Async-first design for Playwright integration
    
    Usage:
        async with VisionAgent() as agent:
            await agent.navigate("https://example.com/apply")
            fields = await agent.scan_page()
            await agent.fill_form({"email": "test@example.com"})
    """
    
    def __init__(
        self,
        headless: bool = False,
        screenshot_callback: Optional[Callable[[str], None]] = None,
        slow_mo: int = 0
    ):
        """
        Initialize the Vision Agent.
        
        Args:
            headless: Run browser in headless mode (False for debugging)
            screenshot_callback: Function to call with base64 screenshot data
            slow_mo: Slow down operations by this many milliseconds
        """
        self.headless = headless
        self.screenshot_callback = screenshot_callback
        self.slow_mo = slow_mo
        
        # Browser instances (initialized in start_session)
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        
        # Stealth configuration
        self._ua = UserAgent()
        self._current_user_agent: Optional[str] = None
        
        # State tracking
        self._is_started = False
        self._last_scan_results: List[Dict[str, Any]] = []
        
        logger.info("VisionAgent initialized (headless=%s)", headless)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    # =========================================================================
    # SESSION MANAGEMENT
    # =========================================================================
    
    async def start_session(self) -> None:
        """
        Launch browser with stealth configuration.
        
        Sets up:
        - Random User-Agent header
        - Viewport size (standard desktop)
        - WebGL/Canvas fingerprinting protections
        """
        if self._is_started:
            logger.warning("Session already started, skipping")
            return
        
        # Generate random user agent
        self._current_user_agent = self._ua.random
        logger.info("Using User-Agent: %s", self._current_user_agent[:60] + "...")
        
        # Launch Playwright
        self._playwright = await async_playwright().start()
        
        # Launch Chromium with stealth settings
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-size=1920,1080",
            ]
        )
        
        # Create context with stealth headers
        self._context = await self._browser.new_context(
            user_agent=self._current_user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="America/New_York",
            # Permissions for clipboard, notifications
            permissions=["clipboard-read", "clipboard-write"],
            # Extra HTTP headers for stealth
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
            }
        )
        
        # Inject stealth scripts to hide automation
        await self._context.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override chrome runtime
            window.chrome = {
                runtime: {}
            };
            
            // Override permissions query
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        # Create new page
        self._page = await self._context.new_page()
        
        self._is_started = True
        logger.info("✓ Browser session started")
    
    async def close(self) -> None:
        """Clean up browser resources."""
        try:
            if self._page:
                try:
                    await self._page.close()
                except Exception:
                    pass  # Page may already be closed
                self._page = None
            
            if self._context:
                try:
                    await self._context.close()
                except Exception:
                    pass  # Context may already be closed
                self._context = None
            
            if self._browser:
                try:
                    await self._browser.close()
                except Exception:
                    pass  # Browser may already be closed
                self._browser = None
            
            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception:
                    pass  # Playwright may already be stopped
                self._playwright = None
            
            self._is_started = False
            logger.info("✓ Browser session closed")
        except Exception as e:
            logger.warning("Error during cleanup: %s", str(e))
    
    # =========================================================================
    # NAVIGATION
    # =========================================================================
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> bool:
        """
        Navigate to a URL and wait for page load.
        
        Args:
            url: The URL to navigate to
            wait_until: Load state to wait for (networkidle, domcontentloaded, load)
        
        Returns:
            True if navigation successful, False otherwise
        """
        if not self._page:
            raise RuntimeError("Session not started. Call start_session() first.")
        
        try:
            # Add random delay for stealth (50-150ms)
            await self._random_delay(50, 150)
            
            logger.info("Navigating to: %s", url)
            response = await self._page.goto(url, wait_until=wait_until, timeout=30000)
            
            if response and response.ok:
                logger.info("✓ Navigation successful (status=%d)", response.status)
                await self.capture_state()  # Auto-capture screenshot
                return True
            else:
                status = response.status if response else "N/A"
                logger.warning("Navigation returned status: %s", status)
                return False
                
        except Exception as e:
            logger.error("Navigation failed: %s", str(e))
            return False
    
    # =========================================================================
    # PAGE SCANNING (Shadow DOM Flattening)
    # =========================================================================
    
    async def scan_page(self) -> List[Dict[str, Any]]:
        """
        Scan the current page for form fields using Shadow DOM flattening.
        
        Executes SHADOW_DOM_SCRIPT to traverse the entire DOM tree,
        including Shadow Roots, and extract all interactive form elements.
        
        Returns:
            List of field dictionaries with id, label, type, selector, etc.
        """
        if not self._page:
            raise RuntimeError("Session not started. Call start_session() first.")
        
        try:
            # Wait for any dynamic content to load
            await self._page.wait_for_load_state("domcontentloaded")
            await self._random_delay(200, 500)  # Wait for JS frameworks
            
            # Execute the Shadow DOM flattener script
            logger.info("Scanning page for form fields...")
            fields = await self._page.evaluate(SHADOW_DOM_SCRIPT)
            
            # Store results for later reference
            self._last_scan_results = fields
            
            # Log summary
            field_types = {}
            for f in fields:
                t = f.get("type", "unknown")
                field_types[t] = field_types.get(t, 0) + 1
            
            logger.info("✓ Found %d form fields: %s", len(fields), field_types)
            
            return fields
            
        except Exception as e:
            logger.error("Page scan failed: %s", str(e))
            return []
    
    async def get_page_html(self, clean: bool = True) -> str:
        """
        Get the current page HTML content.
        
        Args:
            clean: If True, strips scripts, styles, and base64 images
                   to reduce token count for LLM processing.
        
        Returns:
            HTML string (cleaned or raw)
        """
        if not self._page:
            raise RuntimeError("Session not started. Call start_session() first.")
        
        html = await self._page.content()
        
        if clean:
            # Clean HTML for LLM token efficiency
            import re
            # Remove script tags
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            # Remove style tags
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            # Remove SVG elements
            html = re.sub(r'<svg[^>]*>.*?</svg>', '', html, flags=re.DOTALL | re.IGNORECASE)
            # Remove base64 images
            html = re.sub(r'data:image/[^"\']+', 'data:image/REDACTED', html)
            # Remove excessive whitespace
            html = re.sub(r'\s+', ' ', html)
        
        return html
    
    # =========================================================================
    # SCREENSHOT & OBSERVABILITY
    # =========================================================================
    
    async def capture_state(self) -> Optional[str]:
        """
        Capture current page screenshot and trigger callback.
        
        Returns:
            Base64-encoded PNG screenshot string
        """
        if not self._page:
            raise RuntimeError("Session not started. Call start_session() first.")
        
        try:
            # Take full page screenshot
            screenshot_bytes = await self._page.screenshot(full_page=False)
            screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            
            # Trigger callback if registered (for WebSocket streaming to UI)
            if self.screenshot_callback:
                try:
                    self.screenshot_callback(screenshot_b64)
                except Exception as e:
                    logger.warning("Screenshot callback failed: %s", str(e))
            
            logger.debug("Screenshot captured (%d bytes)", len(screenshot_bytes))
            return screenshot_b64
            
        except Exception as e:
            logger.error("Screenshot capture failed: %s", str(e))
            return None
    
    async def save_screenshot(self, path: str = "debug_screenshot.png") -> bool:
        """
        Save current screenshot to disk.
        
        Args:
            path: File path to save the screenshot
        
        Returns:
            True if saved successfully
        """
        if not self._page:
            raise RuntimeError("Session not started. Call start_session() first.")
        
        try:
            await self._page.screenshot(path=path, full_page=False)
            logger.info("✓ Screenshot saved to: %s", path)
            return True
        except Exception as e:
            logger.error("Failed to save screenshot: %s", str(e))
            return False
    
    # =========================================================================
    # FORM FILLING
    # =========================================================================
    
    async def fill_form(self, field_map: Dict[str, str]) -> Dict[str, bool]:
        """
        Fill form fields with provided values.
        
        Args:
            field_map: Dictionary mapping field identifiers to values.
                       Keys can be: field ID, name, or selector from scan_page().
        
        Returns:
            Dictionary of {field_key: success_bool} results
        """
        if not self._page:
            raise RuntimeError("Session not started. Call start_session() first.")
        
        results = {}
        
        for field_key, value in field_map.items():
            try:
                # Determine the selector to use
                selector = self._resolve_selector(field_key)
                
                if not selector:
                    logger.warning("Could not resolve selector for: %s", field_key)
                    results[field_key] = False
                    continue
                
                # Wait for element
                await self._page.wait_for_selector(selector, timeout=5000)
                
                # Get element type
                element = await self._page.query_selector(selector)
                if not element:
                    results[field_key] = False
                    continue
                
                tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                input_type = await element.evaluate("el => el.type || ''")
                
                # Random delay for human-like behavior
                await self._random_delay(100, 300)
                
                # Fill based on element type
                if tag_name == "select":
                    await self._page.select_option(selector, value)
                    logger.info("Selected option '%s' for: %s", value, field_key)
                    
                elif tag_name == "input" and input_type == "checkbox":
                    is_checked = await element.is_checked()
                    should_check = value.lower() in ("true", "yes", "1", "on")
                    if is_checked != should_check:
                        await element.click()
                    logger.info("Set checkbox to %s for: %s", should_check, field_key)
                    
                elif tag_name == "input" and input_type == "radio":
                    await element.click()
                    logger.info("Selected radio for: %s", field_key)
                    
                elif tag_name == "input" and input_type == "file":
                    # File upload
                    await self._page.set_input_files(selector, value)
                    logger.info("Uploaded file for: %s", field_key)
                    
                else:
                    # Text input, textarea, etc.
                    # Clear existing value first
                    await element.click()
                    await self._page.keyboard.press("Control+a")
                    await self._random_delay(50, 100)
                    
                    # Type with human-like delays
                    await element.fill(value)
                    logger.info("Filled '%s' for: %s", value[:30] + "..." if len(value) > 30 else value, field_key)
                
                results[field_key] = True
                
                # Capture state after each field (for observability)
                await self.capture_state()
                
            except Exception as e:
                logger.error("Failed to fill field '%s': %s", field_key, str(e))
                results[field_key] = False
        
        return results
    
    async def click_button(self, selector: str = None, text: str = None) -> bool:
        """
        Click a button by selector or text content.
        
        Args:
            selector: CSS selector for the button
            text: Text content of the button (uses text matching)
        
        Returns:
            True if click successful
        """
        if not self._page:
            raise RuntimeError("Session not started. Call start_session() first.")
        
        try:
            await self._random_delay(200, 400)
            
            if selector:
                await self._page.click(selector)
                logger.info("Clicked button: %s", selector)
            elif text:
                await self._page.click(f"button:has-text('{text}'), input[type='submit'][value='{text}']")
                logger.info("Clicked button with text: %s", text)
            else:
                raise ValueError("Must provide either selector or text")
            
            await self.capture_state()
            return True
            
        except Exception as e:
            logger.error("Click failed: %s", str(e))
            return False
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _resolve_selector(self, field_key: str) -> Optional[str]:
        """
        Resolve a field key to a CSS selector.
        
        Checks:
        1. If it's already a selector (starts with #, ., or [)
        2. If it matches a field ID from last scan
        3. If it matches a field name from last scan
        4. If it matches a field label from last scan
        """
        # Already a selector
        if field_key.startswith(("#", ".", "[")):
            return field_key
        
        # Check last scan results
        for field in self._last_scan_results:
            if field.get("id") == field_key:
                return f"#{field_key}"
            if field.get("name") == field_key:
                return f"[name='{field_key}']"
            if field.get("label", "").lower() == field_key.lower():
                return field.get("selector")
        
        # Fallback: try as ID
        return f"#{field_key}"
    
    async def _random_delay(self, min_ms: int, max_ms: int) -> None:
        """Add random delay for human-like behavior."""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    @property
    def page(self) -> Optional[Page]:
        """Access the underlying Playwright page object."""
        return self._page
    
    @property
    def is_started(self) -> bool:
        """Check if session is active."""
        return self._is_started
    
    @property
    def last_scan_results(self) -> List[Dict[str, Any]]:
        """Get results from the last scan_page() call."""
        return self._last_scan_results


# =============================================================================
# STANDALONE TEST
# =============================================================================

async def _test_agent():
    """Quick test of VisionAgent functionality."""
    print("=" * 60)
    print("VisionAgent Quick Test")
    print("=" * 60)
    
    async with VisionAgent(headless=False) as agent:
        # Navigate to test form
        url = "https://www.w3schools.com/html/html_forms.asp"
        await agent.navigate(url)
        
        # Scan for form fields
        fields = await agent.scan_page()
        print(f"\nFound {len(fields)} form fields:")
        for f in fields[:10]:  # Show first 10
            print(f"  - {f['type']:10} | {f['label'][:30] if f['label'] else 'No label':<30} | {f['selector'][:40]}")
        
        # Save screenshot
        await agent.save_screenshot("debug_screenshot.png")
        print("\n✓ Screenshot saved to debug_screenshot.png")
        
        # Wait for user to see the browser
        print("\nBrowser will close in 5 seconds...")
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(_test_agent())

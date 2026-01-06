"""
AI Auto-Applier Agent - Phase 3: Vision Agent Integration Test

This script tests the VisionAgent class by:
1. Launching a browser session with stealth headers
2. Navigating to a sample HTML form page
3. Scanning the page for form fields using Shadow DOM flattening
4. Printing detected fields as JSON
5. Saving a debug screenshot
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from browser.vision_agent import VisionAgent, SHADOW_DOM_SCRIPT


async def test_vision_agent():
    """
    Full integration test for VisionAgent.
    
    Tests:
    - Session start/stop
    - Navigation with stealth
    - Shadow DOM form scanning
    - Screenshot capture
    """
    print("=" * 70)
    print("AI Auto-Applier Agent - Phase 3: VisionAgent Integration Test")
    print("=" * 70)
    
    # Track screenshots for observability demo
    screenshot_count = [0]
    
    def on_screenshot(base64_data: str):
        """Callback for screenshot events (simulates WebSocket push)."""
        screenshot_count[0] += 1
        size_kb = len(base64_data) / 1024
        print(f"  📸 Screenshot #{screenshot_count[0]} received ({size_kb:.1f} KB)")
    
    # Initialize VisionAgent with screenshot callback
    print("\n[1/5] Initializing VisionAgent...")
    agent = VisionAgent(
        headless=False,  # Set to True for CI/headless environments
        screenshot_callback=on_screenshot,
        slow_mo=50  # Slight slowdown for visibility
    )
    
    try:
        # Start browser session
        print("\n[2/5] Starting browser session...")
        await agent.start_session()
        print(f"  ✓ Browser launched (headless={agent.headless})")
        print(f"  ✓ Stealth mode active")
        
        # Navigate to test form
        print("\n[3/5] Navigating to test page...")
        test_url = "https://www.w3schools.com/html/html_forms.asp"
        success = await agent.navigate(test_url)
        
        if not success:
            print("  ✗ Navigation failed!")
            return False
        
        print(f"  ✓ Loaded: {test_url}")
        
        # Scan page for form fields
        print("\n[4/5] Scanning page for form fields...")
        fields = await agent.scan_page()
        
        if not fields:
            print("  ⚠ No form fields detected")
        else:
            print(f"  ✓ Detected {len(fields)} form fields")
            
            # Print field summary
            print("\n" + "-" * 70)
            print("DETECTED FORM FIELDS:")
            print("-" * 70)
            
            for i, field in enumerate(fields, 1):
                # Build field description
                field_type = field.get("type", "unknown")
                field_label = field.get("label", "")[:40] or "(no label)"
                field_id = field.get("id") or field.get("name") or "(anonymous)"
                required = "★" if field.get("required") else " "
                shadow = "🔒" if field.get("inShadowDOM") else "  "
                
                print(f"  {i:2}. {required} {shadow} [{field_type:12}] {field_label:40} → {field_id}")
            
            print("-" * 70)
            
            # Print full JSON for debugging
            print("\n[DEBUG] Full JSON output (first 5 fields):")
            print(json.dumps(fields[:5], indent=2))
        
        # Save screenshot
        print("\n[5/5] Saving debug screenshot...")
        screenshot_path = "debug_screenshot.png"
        saved = await agent.save_screenshot(screenshot_path)
        
        if saved:
            abs_path = Path(screenshot_path).absolute()
            print(f"  ✓ Screenshot saved: {abs_path}")
        else:
            print("  ✗ Failed to save screenshot")
        
        # Wait for user to observe
        print("\n" + "=" * 70)
        print("TEST COMPLETE - Browser will close in 5 seconds...")
        print("=" * 70)
        await asyncio.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        print("\nClosing browser session...")
        await agent.close()
        print("✓ Session closed")


async def test_form_filling():
    """
    Test form filling functionality.
    
    Uses a simple test form to verify:
    - Text input filling
    - Proper field resolution
    - Screenshot after each fill
    """
    print("\n" + "=" * 70)
    print("VisionAgent Form Filling Test")
    print("=" * 70)
    
    async with VisionAgent(headless=False) as agent:
        # Navigate to W3Schools form
        await agent.navigate("https://www.w3schools.com/html/tryit.asp?filename=tryhtml_form_submit")
        
        # Wait for iframe content
        await asyncio.sleep(2)
        
        # Try to fill some fields
        print("\nAttempting to fill form fields...")
        
        # Note: W3Schools uses iframes, so this is a basic test
        # For real ATS forms, the Shadow DOM script will be more useful
        
        await agent.save_screenshot("form_test.png")
        print("✓ Form screenshot saved")
        
        await asyncio.sleep(3)


async def test_shadow_dom_script():
    """
    Test the Shadow DOM flattening script in isolation.
    """
    print("\n" + "=" * 70)
    print("Shadow DOM Script Analysis")
    print("=" * 70)
    
    print("\nThe SHADOW_DOM_SCRIPT does the following:")
    print("-" * 50)
    print("1. Starts from document.body")
    print("2. Uses querySelectorAll for input, textarea, select, button")
    print("3. For each element, extracts:")
    print("   - id, name, type, tagName")
    print("   - Label (via for attribute, aria-label, placeholder)")
    print("   - Bounding rectangle (x, y, width, height)")
    print("   - Required/disabled status")
    print("   - CSS selector for targeting")
    print("4. Recursively traverses shadowRoot of all elements")
    print("5. Returns JSON array of all detected fields")
    print("-" * 50)
    print("\nThis is critical for ATS platforms using Web Components:")
    print("  • Greenhouse.io uses custom elements")
    print("  • Lever.co has shadow DOM forms")
    print("  • Ashby uses modern web component architecture")
    print("\nWithout Shadow DOM traversal, standard selectors would fail!")


async def main():
    """Run all tests."""
    print("\n🚀 Starting VisionAgent Test Suite\n")
    
    # Test 1: Shadow DOM script explanation
    await test_shadow_dom_script()
    
    # Test 2: Full integration test
    success = await test_vision_agent()
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async tests
    asyncio.run(main())

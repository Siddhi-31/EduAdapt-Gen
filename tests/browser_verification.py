"""End-to-End Browser Workflow Verification for EduAdapt Subtopic Sequential Learning.

Uses Playwright to automate Chrome headless testing:
1. Loads EduAdapt frontend at http://localhost:5173/
2. Navigates to the Learn page.
3. Verifies initial subtopic states (Subtopic 1 ready, Subtopics 2..N locked).
4. Verifies clicking locked subtopics is blocked.
5. Verifies reading completion button unlocks the mandatory mastery gate.
6. Verifies mandatory mastery-check question evaluation.
7. Takes screenshot for visual verification.
"""

import asyncio
import json
import sys
from pathlib import Path

# Ensure UTF-8 output encoding for console prints with emojis on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from playwright.async_api import async_playwright


async def run_browser_verification():
    print("Starting Playwright Browser Verification...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        # Route session generation to mock provider for fast and deterministic test runs
        async def handle_generate_route(route):
            if "/api/session/generate" in route.request.url and route.request.method == "POST":
                try:
                    data = route.request.post_data_json or {}
                    data["provider"] = "mock"
                    await route.continue_(post_data=json.dumps(data))
                except Exception:
                    await route.continue_()
            else:
                await route.continue_()

        await page.route("**/api/session/generate", handle_generate_route)

        # 1. Navigate to Frontend
        print("Navigating to http://localhost:5173/ ...")
        await page.goto("http://localhost:5173/", wait_until="networkidle")
        title = await page.title()
        print(f"Page loaded. Title: {title}")

        # 2. Reset student state to clean baseline for S005 or S001
        print("Resetting baseline via API for S_BROWSER_TEST...")
        await page.evaluate("""async () => {
            await fetch('http://127.0.0.1:8000/api/subtopics/reset', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({student_id: 'S001', topic: 'Pointers'})
            });
        }""")

        # 3. Navigate to Learn tab
        print("Clicking Learn tab...")
        learn_btn = page.locator("button:has-text('Learn')").first
        await learn_btn.click()
        await page.wait_for_timeout(1000)

        # 4. Verify Subtopic Curriculum Sequence header
        seq_header = page.locator("text=Subtopic Curriculum Sequence")
        await seq_header.wait_for(state="visible", timeout=10000)
        print("Subtopic Curriculum Sequence header is visible.")

        # Check progress text: must show '0 of 9 Completed (0%)'
        page_text = await page.content()
        assert "0 of 9 Completed" in page_text, "Failed: Should show 0 of 9 Completed on reset"
        print("Verified: Progress indicates '0 of 9 Completed (0%)' (no fabricated 89% / 100%)")

        # 5. Check subtopic button states
        sub1_btn = page.locator("button:has-text('1. Introduction')").first
        sub2_btn = page.locator("button:has-text('2. Pointer Declaration')").first

        await sub1_btn.wait_for(state="visible")
        await sub2_btn.wait_for(state="visible")

        sub1_text = await sub1_btn.text_content()
        sub2_text = await sub2_btn.text_content()
        print(f"Subtopic 1 status: {sub1_text.strip()}")
        print(f"Subtopic 2 status: {sub2_text.strip()}")

        # Subtopic 2 must show 'Locked' and be disabled
        assert "Locked" in sub2_text, "Failed: Subtopic 2 should have Locked badge"
        is_sub2_disabled = await sub2_btn.is_disabled()
        assert is_sub2_disabled is True, "Failed: Subtopic 2 button should be disabled"
        print("Verified: Subtopic 2 is visually and functionally LOCKED.")

        # 6. Attempt to click locked Subtopic 2 -> should remain locked
        await sub2_btn.click(force=True)
        await page.wait_for_timeout(500)
        assert "0 of 9 Completed" in await page.content()
        print("Verified: Clicking locked Subtopic 2 does not skip or unlock out-of-order.")

        # 7. Wait for Lesson Generation to Complete
        print("Waiting for personalized lesson content (Mistral 7B)...")
        reading_card = page.locator("text=Step 1: Read Learning Content").first
        try:
            await reading_card.wait_for(state="visible", timeout=45000)
            print("Personalized lesson generated and rendered successfully.")
        except Exception:
            # Check if there is a 'Start Learning' button to manually click
            start_btn = page.locator("button:has-text('Start Learning')").first
            if await start_btn.is_visible():
                print("Clicking 'Start Learning'...")
                await start_btn.click()
                await reading_card.wait_for(state="visible", timeout=45000)

        # 8. Check Reading Progress Section
        assert await reading_card.is_visible()
        print("Verified: Reading Requirement section is visible.")
        mark_read_btn = page.locator("button:has-text('Mark Reading Complete')").first
        assert await mark_read_btn.is_visible()

        # Mastery check must show locked indicator
        gate_badge = page.locator("text=Locked: Reading Required").first
        assert await gate_badge.is_visible()
        print("Verified: Mastery check is locked pending reading completion.")

        # Click Mark Reading Complete
        print("Clicking 'Mark Reading Complete ✓'...")
        await mark_read_btn.click()
        await page.wait_for_timeout(1000)

        # Gate is now ready
        gate_ready = page.locator("text=Gate Ready").first
        assert await gate_ready.is_visible()
        print("Verified: Mastery gate unlocked after reading completion verified.")

        # 9. Test Mastery Check Question Submission
        print("Selecting option for Mastery Check...")
        first_opt = page.locator("input[name='understanding-check-option']").first
        await first_opt.click()

        submit_check_btn = page.locator("button:has-text('Submit Mastery Check')").first
        await submit_check_btn.click()
        await page.wait_for_timeout(2000)

        # Verify evaluation card appears
        eval_card = page.locator("text=Mastery Gate Passed").or_(page.locator("text=Misconception Detected"))
        await eval_card.first.wait_for(state="visible", timeout=10000)
        print("Verified: Authoritative mastery evaluation card rendered.")

        # 10. Capture screenshot for audit evidence
        screenshot_path = Path("tests/subtopic_workflow_screenshot.png")
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"Captured full-page screenshot to {screenshot_path}")

        await browser.close()
        print("ALL BROWSER WORKFLOW CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(run_browser_verification())

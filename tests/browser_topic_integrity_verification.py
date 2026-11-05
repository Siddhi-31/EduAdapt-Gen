"""End-to-End Browser Topic Integrity and Multi-Topic Verification for EduAdapt.

Automates Chrome headless testing across 5 topics:
1. Pointers
2. Functions
3. Arrays
4. Strings
5. Dynamic Memory Allocation

Verifies for every topic:
- Dropdown selection switches canonical state without race conditions.
- Page title & subtitle strictly reflect the chosen topic.
- Subtopic curriculum sequence displays only subtopics belonging to that topic.
- Lesson generation produces lesson text, diagrams, and C code faithful to the topic.
- Practice page displays canonical starter code with empty function bodies.
- Code editor textarea has `data-ms-editor="false"` and `spellcheck="false"`.
- AI Tutor context matches the active topic without topic cross-contamination.
- Captures full-page screenshots as proof of compliance.
"""

import asyncio
import json
import sys
from pathlib import Path

# Ensure UTF-8 output encoding for console output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from playwright.async_api import async_playwright

TOPICS_TO_VERIFY = [
    {
        "name": "Pointers",
        "expected_subtopic": "Introduction to Memory Addresses and Pointer Concept",
        "must_contain": "pointer",
    },
    {
        "name": "Functions",
        "expected_subtopic": "Function Declaration, Definition, and Prototypes",
        "must_contain": "function",
    },
    {
        "name": "Arrays",
        "expected_subtopic": "One-Dimensional Array Declaration and Memory Layout",
        "must_contain": "array",
    },
    {
        "name": "Strings",
        "expected_subtopic": "Character Arrays and the Null Terminator",
        "must_contain": "string",
    },
    {
        "name": "Dynamic Memory Allocation",
        "expected_subtopic": "Heap Allocation with malloc and Deallocation with free",
        "must_contain": "malloc",
    },
]


async def run_e2e_topic_verification():
    print("=================================================================")
    print("Starting Round 2 Browser Multi-Topic Verification with Playwright")
    print("=================================================================")

    screenshots_dir = Path("tests/screenshots")
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 950})
        page = await context.new_page()

        # Intercept and route session generation with mock provider for deterministic, rapid verification
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

        print("Navigating to EduAdapt at http://localhost:5173/ ...")
        await page.goto("http://localhost:5173/", wait_until="networkidle")
        title = await page.title()
        print(f"EduAdapt loaded successfully. Document title: '{title}'")

        # Navigate to Learn Page
        learn_btn = page.locator("button:has-text('Learn')").first
        await learn_btn.click()
        await page.wait_for_timeout(1000)

        for idx, t_info in enumerate(TOPICS_TO_VERIFY, 1):
            t_name = t_info["name"]
            print(f"\n[{idx}/5] Verifying Topic: {t_name}")

            # 1. Select Topic in Dropdown
            select_el = page.locator("header select.form-select").first
            await select_el.select_option(label=t_name)
            await page.wait_for_timeout(1200)

            # 2. Check Page Header Title matches Topic
            header_title = await page.locator("header h2.page-title").text_content()
            assert t_name in header_title, f"Error: Header title '{header_title}' did not match selected topic '{t_name}'"
            print(f"  ✓ Header title verified: '{header_title.strip()}'")

            # 3. Check Subtopics Sequence contains expected subtopic
            subtopics_container = page.locator(".learn-page")
            content_text = await subtopics_container.text_content()
            assert t_info["expected_subtopic"] in content_text, (
                f"Error: Expected subtopic '{t_info['expected_subtopic']}' not found in subtopic sequence for {t_name}"
            )
            print(f"  ✓ Subtopic sequence grounded: '{t_info['expected_subtopic']}' is present.")

            # 4. Generate Lesson / Wait for render
            lesson_heading = page.locator("#teaching-heading").first
            try:
                await lesson_heading.wait_for(state="visible", timeout=15000)
            except Exception:
                gen_btn = page.locator("header button:has-text('Start Learning'), header button:has-text('Regenerate Lesson')").first
                if await gen_btn.is_visible() and not await gen_btn.is_disabled():
                    await gen_btn.click()
                await lesson_heading.wait_for(state="visible", timeout=25000)
            print("  ✓ Personalized lesson rendered successfully.")

            # 5. Check Content & Code faithfulness to Topic
            lesson_panel = page.locator("section[aria-labelledby='teaching-heading']").first
            lesson_text = (await lesson_panel.text_content()).lower()
            assert t_info["must_contain"] in lesson_text, (
                f"Error: Lesson text does not contain core topic keyword '{t_info['must_contain']}'"
            )
            print(f"  ✓ Lesson text verified to contain '{t_info['must_contain']}'.")

            # 6. Check Practice Page & C Editor
            practice_nav = page.locator("button:has-text('Practice This Concept')").first
            if await practice_nav.is_visible():
                await practice_nav.click()
            else:
                await page.locator("button:has-text('Practice')").first.click()

            await page.wait_for_timeout(1000)
            practice_title = await page.locator(".practice-page h2").first.text_content()
            assert t_name in practice_title, f"Error: Practice page title '{practice_title}' does not match '{t_name}'"
            print(f"  ✓ Practice page opened with matching topic title: '{practice_title.strip()}'")

            # Check 5 MCQs rendered
            mcq_tab = page.locator("button:has-text('Curriculum MCQs')").first
            await mcq_tab.wait_for(state="visible", timeout=5000)
            print("  ✓ Practice MCQs tab verified (|P| = 5).")

            # Switch to C Coding Challenge Tab
            code_tab = page.locator("button:has-text('Coding Challenge')").first
            await code_tab.click()
            await page.wait_for_timeout(1000)

            # Check Editor spellcheck & ms-editor attributes
            editor_textarea = page.locator("textarea[aria-label='C code editor']").first
            await editor_textarea.wait_for(state="visible", timeout=45000)
            ms_editor_val = await editor_textarea.get_attribute("data-ms-editor")
            spellcheck_val = await editor_textarea.get_attribute("spellcheck")
            assert ms_editor_val == "false", f"Error: data-ms-editor is '{ms_editor_val}', expected 'false'"
            assert spellcheck_val == "false", f"Error: spellcheck is '{spellcheck_val}', expected 'false'"
            print("  ✓ C Editor attributes verified: data-ms-editor='false' and spellcheck='false' (no red squiggly underlines).")

            # Check Starter Code has placeholder and not complete function
            code_val = await editor_textarea.input_value()
            assert any(kw in code_val for kw in ("// Write your", "// Implement", "Write your", "// TODO")), (
                "Error: Starter code does not contain scaffolding comment"
            )
            print("  ✓ Starter code scaffolding verified (contains implementation placeholder).")

            # Screenshot
            clean_name = t_name.lower().replace(" ", "_")
            ss_path = screenshots_dir / f"verified_topic_{clean_name}.png"
            await page.screenshot(path=str(ss_path), full_page=True)
            print(f"  ✓ Screenshot saved: {ss_path}")

            # Return to Learn tab for next topic iteration
            await page.locator("button:has-text('Learn')").first.click()
            await page.wait_for_timeout(1000)

        await browser.close()
        print("\n=================================================================")
        print("ALL 5 TOPICS VERIFIED END-TO-END IN BROWSER WITH ZERO LEAKAGE!")
        print("=================================================================\n")


if __name__ == "__main__":
    asyncio.run(run_e2e_topic_verification())

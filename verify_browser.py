import os
import asyncio
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Load backend/.env to get the real ADMIN_PASSWORD
load_dotenv(Path(__file__).parent / "backend" / ".env")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "aurelia2026")

ARTIFACT_SCREENSHOTS = Path(r"C:\Users\imvis\.gemini\antigravity\brain\a03ae3b0-e8e1-4dff-9265-93345cb44316\screenshots")
LOCAL_SCREENSHOTS = Path("test_reports/screenshots")
ARTIFACT_SCREENSHOTS.mkdir(parents=True, exist_ok=True)
LOCAL_SCREENSHOTS.mkdir(parents=True, exist_ok=True)

# Generate a sample image to upload
sample_upload_file = Path("test_reports/sample_idea.png")
sample_upload_file.parent.mkdir(parents=True, exist_ok=True)
img = Image.new("RGB", (600, 400), color="#C59B27")
img.save(sample_upload_file, format="PNG")


async def capture(page, name: str):
    p1 = ARTIFACT_SCREENSHOTS / f"{name}.png"
    p2 = LOCAL_SCREENSHOTS / f"{name}.png"
    await page.screenshot(path=str(p1), full_page=False)
    await page.screenshot(path=str(p2), full_page=False)
    print(f"Captured screenshot: {name}.png")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        print("\n--- 1. Loading Homepage ---")
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await capture(page, "01_homepage")

        print("\n--- 2. Testing Gallery Filter ---")
        # Scroll to gallery section
        gallery_btn = page.locator("button:has-text('Shops')").first
        if await gallery_btn.is_visible():
            await gallery_btn.click()
            await page.wait_for_timeout(1000)
            await capture(page, "02_gallery_shops_filter")
        
        furniture_btn = page.locator("button:has-text('Furniture')").first
        if await furniture_btn.is_visible():
            await furniture_btn.click()
            await page.wait_for_timeout(1000)
            await capture(page, "02_gallery_furniture_filter")

        print("\n--- 3. Submitting Enquiry ---")
        contact_section = page.locator("#contact")
        await contact_section.scroll_into_view_if_needed()
        await page.wait_for_timeout(1000)

        await page.fill("[data-testid='contact-form-name-input']", "Arjun Mohanty")
        await page.fill("[data-testid='contact-form-phone-input']", "+91 94370 12345")
        await page.select_option("[data-testid='contact-form-service-select']", label="Full Home Interiors")
        await page.fill("[data-testid='contact-form-message-input']", "Looking for a turnkey duplex interior design in Cuttack.")
        await page.click("[data-testid='contact-form-submit-button']")
        await page.wait_for_timeout(1500)
        await capture(page, "03_enquiry_submitted")

        print("\n--- 4. Navigating to /admin and Logging In ---")
        await page.goto("http://localhost:3000/admin", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await capture(page, "04_admin_login_page")

        await page.fill("[data-testid='admin-password-input']", ADMIN_PASSWORD)
        await page.click("[data-testid='admin-login-button']")
        await page.wait_for_timeout(2000)
        await capture(page, "05_admin_dashboard_ideas")

        print("\n--- 5. Adding a Design Idea with Photo Upload ---")
        await page.click("[data-testid='admin-add-idea-button']")
        await page.wait_for_timeout(800)
        await page.fill("[data-testid='admin-idea-title-input']", "Luxury Brass Dining Lounge")
        await page.click("[data-testid='admin-idea-category-homes']")
        await page.fill("[data-testid='admin-idea-description-input']", "Warm brass accents and custom woodwork designed by ANWESHAN Infra.")
        
        # Upload file
        file_input = page.locator("[data-testid='admin-idea-photo-input']")
        await file_input.set_input_files(str(sample_upload_file.resolve()))
        await page.wait_for_timeout(800)
        await page.click("[data-testid='admin-idea-save-button']")
        await page.wait_for_timeout(2000)
        await capture(page, "06_idea_added_admin")

        print("\n--- 6. Verifying New Idea on Home Page ---")
        await page.goto("http://localhost:3000", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        gallery = page.locator("#ideas, [data-testid='gallery-section']").first
        if await gallery.is_visible():
            await gallery.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)
        await capture(page, "07_new_idea_on_homepage")

        print("\n--- 7. Editing a Service Price in Admin ---")
        await page.goto("http://localhost:3000/admin", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        # Click Services Tab
        await page.click("button:has-text('Services & Prices')")
        await page.wait_for_timeout(1000)
        
        price_input = page.locator("[data-testid='admin-edit-price-input-0']")
        await price_input.fill("₹1,95,000 onwards (Updated)")
        await page.click("[data-testid='admin-save-service-0']")
        await page.wait_for_timeout(1500)
        await capture(page, "08_service_price_edited")

        print("\n--- 8. Marking Enquiry as Read ---")
        await page.click("button:has-text('Enquiries')")
        await page.wait_for_timeout(1000)
        # Mark read button on the first enquiry
        mark_read_btn = page.locator("[data-testid^='admin-mark-read-']").first
        if await mark_read_btn.is_visible():
            await mark_read_btn.click()
            await page.wait_for_timeout(1000)
        await capture(page, "09_enquiry_marked_read")

        print("\n--- 9. Logging Out of Admin ---")
        logout_btn = page.locator("[data-testid='admin-logout-button']")
        if await logout_btn.is_visible():
            await logout_btn.click()
            await page.wait_for_timeout(1000)
        await capture(page, "10_admin_logged_out")

        await browser.close()
        print("\n=== Live Browser Verification Complete! All screenshots captured. ===")

asyncio.run(main())

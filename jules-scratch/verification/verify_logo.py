import os
from playwright.sync_api import sync_playwright, Page, expect

def run_verification(page: Page):
    """
    Navigates to the local server and takes a screenshot of the header logo.
    """
    # 1. Navigate to the homepage served by the python server.
    page.goto("http://localhost:8000")

    # 2. Locate the logo.
    # Using get_by_role with the alt text is a reliable way to find the image.
    logo_image = page.get_by_role("img", name="CMS Consultores Logo")

    # 3. Assert that the logo is visible.
    # This ensures the page has loaded enough for the logo to be present.
    expect(logo_image).to_be_visible()

    # 4. Take a screenshot for visual verification.
    # The script is run from the root, so the path is relative to the root.
    screenshot_path = "jules-scratch/verification/logo_verification.png"
    logo_image.screenshot(path=screenshot_path)
    print(f"Screenshot saved to {screenshot_path}")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        run_verification(page)
        browser.close()

if __name__ == "__main__":
    main()

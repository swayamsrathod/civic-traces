"""Fill and submit the demo complaint portal with Playwright.

Start the demo portal first:  python -m http.server 8080 --directory demo_portal
"""
import os

from playwright.sync_api import sync_playwright

PORTAL_URL = os.getenv("PORTAL_URL", "http://localhost:8080/index.html")


def file_on_portal(department, issue_type, location, description, headless=False):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=300)  # slow_mo so judges can watch
        page = browser.new_page()
        page.goto(PORTAL_URL)
        page.select_option("#department", label=department)
        page.fill("#issue", issue_type)
        page.fill("#location", location)
        page.fill("#description", description)
        page.click("#submit")
        ref = page.inner_text("#reference")
        browser.close()
    return ref.strip()

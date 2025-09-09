import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.smbcgroup.com/"

@pytest.fixture(scope="session")
def playwright_context():
    pw = sync_playwright().start()
    yield pw
    pw.stop()

@pytest.fixture(scope="session")
def browser(playwright_context):
    browser = playwright_context.chromium.launch(headless=False)
    yield browser
    browser.close()

@pytest.fixture
def page(browser):
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    yield page
    context.close()

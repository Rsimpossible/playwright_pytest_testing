# conftest.py
"""
Pytest fixtures for Playwright tests (sync API).

Features:
- Use HEADLESS env var to switch headed/headless behavior.
- Safe Chromium args for CI (--no-sandbox, --disable-dev-shm-usage).
- ignore_https_errors=True to avoid cert failures in CI.
- On test failure, save screenshot + HTML to ./test-results/.
"""

import os
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.smbcgroup.com/"

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook wrapper so fixtures can inspect the test outcome later (item.rep_call).
    Must be decorated with hookwrapper=True.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="session")
def playwright_context():
    pw = sync_playwright().start()
    try:
        yield pw
    finally:
        try:
            pw.stop()
        except Exception:
            pass


@pytest.fixture(scope="session")
def browser(playwright_context):
    """
    Launch a single Chromium browser for the session.
    Controlled by HEADLESS env var (default true).
    """
    headless = os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes")
    args = ["--no-sandbox", "--disable-dev-shm-usage"]
    browser = playwright_context.chromium.launch(headless=headless, args=args)
    try:
        yield browser
    finally:
        try:
            browser.close()
        except Exception:
            pass


@pytest.fixture
def page(browser, request):
    """
    Provide a fresh context + page per test.
    Ignores HTTPS errors (helpful for CI), and on failure saves a screenshot + HTML.
    """
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True
    )
    page = context.new_page()
    try:
        yield page
    finally:
        # If the

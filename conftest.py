# conftest.py
"""
Pytest fixtures for Playwright tests (sync API).

Features:
- Use HEADLESS env var to switch headed/headless behavior.
- Launch Chromium with safe CI args (--no-sandbox, --disable-dev-shm-usage).
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
        # ensure we stop Playwright even if teardown raises
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
        # If the test failed, pytest attaches rep_call to the request.node
        rep_call = getattr(request.node, "rep_call", None)
        if rep_call is not None and rep_call.failed:
            results_dir = Path("test-results")
            results_dir.mkdir(parents=True, exist_ok=True)
            # use test node name for filenames
            safe_name = request.node.name.replace("/", "_").replace(" ", "_")
            screenshot_path = results_dir / f"{safe_name}.png"
            html_path = results_dir / f"{safe_name}.html"
            try:
                page.screenshot(path=str(screenshot_path))
            except Exception as e:
                print(f"[teardown] failed to take screenshot: {e}")
            try:
                html = page.content()
                html_path.write_text(html, encoding="utf-8")
            except Exception as e:
                print(f"[teardown] failed to save page html: {e}")
        # cleanup
        try:
            page.close()
        except Exception:
            pass
        try:
            context.close()
        except Exception:
            pass

# conftest.py
"""
Pytest fixtures for Playwright tests (sync + async).

- HEADLESS env var controls headless mode (default true).
- Uses safe Chromium args for CI (--no-sandbox, --disable-dev-shm-usage).
- ignore_https_errors=True to avoid cert failures in CI.
- Saves screenshot + HTML into ./test-results/ on failure (for both sync & async).
"""

import os
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright

BASE_URL = "https://www.smbcgroup.com/"

# --- pytest hook wrapper to attach reports to nodes ---
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


# -------------------- Sync fixtures --------------------
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
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True
    )
    page = context.new_page()
    try:
        yield page
    finally:
        # on failure, save screenshot + HTML
        rep_call = getattr(request.node, "rep_call", None)
        if rep_call is not None and rep_call.failed:
            results_dir = Path("test-results")
            results_dir.mkdir(parents=True, exist_ok=True)
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


# -------------------- Async fixtures --------------------
@pytest.fixture(scope="session")
async def async_playwright_context():
    # Use async context manager for the async playwright
    async with async_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
async def async_browser(async_playwright_context):
    headless = os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes")
    args = ["--no-sandbox", "--disable-dev-shm-usage"]
    browser = await async_playwright_context.chromium.launch(headless=headless, args=args)
    try:
        yield browser
    finally:
        try:
            await browser.close()
        except Exception:
            pass


@pytest.fixture
async def async_page(async_browser, request):
    context = await async_browser.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True
    )
    page = await context.new_page()
    try:
        yield page
    finally:
        # on failure, save screenshot + HTML (async)
        rep_call = getattr(request.node, "rep_call", None)
        if rep_call is not None and rep_call.failed:
            results_dir = Path("test-results")
            results_dir.mkdir(parents=True, exist_ok=True)
            safe_name = request.node.name.replace("/", "_").replace(" ", "_") + "_async"
            screenshot_path = results_dir / f"{safe_name}.png"
            html_path = results_dir / f"{safe_name}.html"
            try:
                await page.screenshot(path=str(screenshot_path))
            except Exception as e:
                print(f"[async teardown] failed to take screenshot: {e}")
            try:
                html = await page.content()
                html_path.write_text(html, encoding="utf-8")
            except Exception as e:
                print(f"[async teardown] failed to save page html: {e}")

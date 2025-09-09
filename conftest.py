# conftest.py
import os
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.smbcgroup.com/"

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Pytest hook wrapper so fixtures can inspect the test outcome later (item.rep_call).
    Must be decorated with hookwrapper=True so pytest executes the generator properly.
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
        pw.stop()


@pytest.fixture(scope="session")
def browser(playwright_context):
    """
    Launch a single browser instance for the session. Use HEADLESS env var
    to control headed/headless behavior (CI should set HEADLESS=true).
    """
    headless = os.getenv("HEADLESS", "true").lower() in ("1", "true", "yes")
    args = ["--no-sandbox", "--disable-dev-shm-usage"]
    browser = playwright_context.chromium.launch(headless=headless, args=args)
    try:
        yield browser
    finally:
        browser.close()


@pytest.fixture
def page(browser, request):
    """
    Create a fresh context+page for each test. Ignore HTTPS errors (useful in CI).
    On failure, save a screenshot and page HTML into ./test-results/.
    """
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True
    )
    page = context.new_page()
    try:
        yield page
    finally:
        # if the test failed, pytest will have attached the call report to request.node
        rep_call = getattr(request.node, "rep_call", None)
        if rep_call is not None and rep_call.failed:
            results_dir = Path("test-results")
            results_dir.mkdir(parents=True, exist_ok=True)
            name = request.node.name
            screenshot_path = results_dir / f"{name}.png"
            html_path = results_dir / f"{name}.html"
            try:
                page.screenshot(path=str(screenshot_path))
            except Exception as e:
                print(f"[teardown] failed to take screenshot: {e}")
            try:
                html = page.content()
                html_path.write_text(html, encoding="utf-8")
            except Exception as e:
                print(f"[teardown] failed to save page html: {e}")
        # ensure cleanup
        try:
            page.close()
        except Exception:
            pass
        try:
            context.close()
        except Exception:
            pass

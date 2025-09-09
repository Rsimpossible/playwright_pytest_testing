import pytest
from playwright.async_api import async_playwright

BASE_URL = "https://www.smbcgroup.com/"

@pytest.mark.asyncio
async def test_async_home_title_and_screenshot():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width":1280, "height":800})
        page = await context.new_page()
        await page.goto(BASE_URL)
        title = await page.title()
        assert "SMBC" in title or "smbc" in title.lower()
        await page.screenshot(path="artifacts/async_smbc_home.png", full_page=True)
        await context.close()
        await browser.close()

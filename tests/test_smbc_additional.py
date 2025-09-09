from pathlib import Path

BASE_URL = "https://www.smbcgroup.com/"

def test_navigation_links(page):
    page.goto(BASE_URL, wait_until="load")
    nav = page.query_selector_all("nav")
    assert nav
    expected_texts = ["About", "Business", "Investor", "Sustainability", "Contact"]
    found_any = any(page.query_selector(f"text=\"{txt}\"") for txt in expected_texts)
    assert found_any

def test_contact_page_form_exists(page):
    page.goto(BASE_URL, wait_until="load")
    contact_link = page.query_selector("text=Contact")
    if contact_link:
        contact_link.click()
        page.wait_for_load_state("load")
    else:
        page.goto(f"{BASE_URL}contact", wait_until="load")
    form = page.query_selector("form")
    assert form is not None
    assert page.query_selector("input, textarea")

def test_footer_links(page):
    page.goto(BASE_URL, wait_until="load")
    footer = page.query_selector("footer")
    assert footer is not None
    links = footer.query_selector_all("a")
    assert len(links) >= 3

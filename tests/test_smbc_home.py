from pathlib import Path

BASE_URL = "https://www.smbcgroup.com/"

def test_home_title_and_nav(page):
    page.goto(BASE_URL, wait_until="load")
    title = page.title()
    assert "SMBC" in title or "smbc" in title.lower()

    header = None
    for sel in ["header", "nav", "#header", ".site-header", "#main-nav"]:
        elems = page.query_selector_all(sel)
        if elems:
            header = elems[0]
            break
    assert header is not None

    out_dir = Path("artifacts")
    out_dir.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out_dir / "smbc_home.png"), full_page=True)

    main = page.query_selector("main")
    assert main is not None

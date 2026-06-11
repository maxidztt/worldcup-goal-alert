from playwright.sync_api import sync_playwright
from datetime import datetime
import json

TOURNAMENT_ID = 16  # FIFA World Cup


def get_json(page, url):
    return page.evaluate(
        """
        async (url) => {
            const r = await fetch(url);
            return await r.json();
        }
        """,
        url
    )


with sync_playwright() as p:
    browser = p.chromium.launch(
        channel="chrome",
        headless=False
    )

    page = browser.new_page()

    page.goto(
        "https://www.sofascore.com",
        wait_until="domcontentloaded"
    )

    today = datetime.utcnow().strftime("%Y-%m-%d")

    url = (
        f"https://www.sofascore.com/api/v1/"
        f"unique-tournament/{TOURNAMENT_ID}/"
        f"scheduled-events/{today}"
    )

    print("Buscando partidos...")
    print(url)

    data = get_json(page, url)

    print(json.dumps(data, indent=2)[:5000])

    browser.close()

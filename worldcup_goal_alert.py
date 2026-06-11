import os
import json
import time
import requests

from datetime import datetime
from playwright.sync_api import sync_playwright

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "8872716038:AAEGKXRM8F87vnp_L7WEpb1IpSuaVlQSRnQ"
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or "7727821551"

TOURNAMENT_ID = 16
CHECK_INTERVAL = 3

SEEN_FILE = "seen_goals.json"


def send_telegram(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=15
        )
    except Exception as e:
        print("Error Telegram:", e)


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()

    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("goals", []))
    except:
        return set()


def save_seen(goals):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"goals": list(goals)},
            f,
            ensure_ascii=False,
            indent=2
        )


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


def get_worldcup_events(page):
    today = datetime.utcnow().strftime("%Y-%m-%d")

    url = (
        f"https://www.sofascore.com/api/v1/"
        f"unique-tournament/{TOURNAMENT_ID}/"
        f"scheduled-events/{today}"
    )

    data = get_json(page, url)

    return data.get("events", [])


def get_incidents(page, event_id):
    url = (
        f"https://www.sofascore.com/api/v1/"
        f"event/{event_id}/incidents"
    )

    data = get_json(page, url)

    return data.get("incidents", [])


def process_goal(seen_goals, event, incident):
    goal_id = incident.get("id")

    if goal_id in seen_goals:
        return

    seen_goals.add(goal_id)

    home = event["homeTeam"]["name"]
    away = event["awayTeam"]["name"]

    minute = incident.get("time", "?")

    home_score = incident.get("homeScore", "?")
    away_score = incident.get("awayScore", "?")

    text = (
        "⚽ GOL EN EL MUNDIAL\n\n"
        f"{home} {home_score}-{away_score} {away}\n\n"
        f"⏱️ {minute}'"
    )

    print(text)
    send_telegram(text)

    save_seen(seen_goals)


def main():

    seen_goals = load_seen()

    with sync_playwright() as p:

        browser = p.chromium.launch(
            channel="chrome",
            headless=True
        )

        page = browser.new_page()

        page.goto(
            "https://www.sofascore.com/football/tournament/world/world-championship/16",
            wait_until="domcontentloaded",
            timeout=30000
        )

        page.wait_for_timeout(5000)

        send_telegram(
            "⚽ Mundial Bot iniciado\n"
            f"Chequeo cada {CHECK_INTERVAL} segundos"
        )

        while True:

            try:

                events = get_worldcup_events(page)

                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"Partidos encontrados: {len(events)}"
                )

                for event in events:

                    event_id = event["id"]

                    incidents = get_incidents(
                        page,
                        event_id
                    )

                    for incident in incidents:

                        if incident.get("incidentType") == "goal":

                            process_goal(
                                seen_goals,
                                event,
                                incident
                            )

                time.sleep(CHECK_INTERVAL)

            except Exception as e:

                print("ERROR:", e)

                time.sleep(10)


if __name__ == "__main__":
    main()

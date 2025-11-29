import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime

PRODUCT_URL = "https://www.microsoft.com/en-us/d/surface-pro-10-for-business-certified-refurbished/8p7h1dg85brj?activetab=pivot:overviewtab"
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
FORCE_NOTIFY = os.environ.get("FORCE_NOTIFY", "false").lower() == "true"

STATUS_FILE = "status.json"


def send_discord_message():
    title = "Surface Pro 10 Refurbished is AVAILABLE!"
    color = 0x00FF00  # Green

    embed = {
        "title": title,
        "url": PRODUCT_URL,
        "description": "A refurbished Microsoft Surface Pro 10 is now available!\n\n@here",
        "color": color,
        "timestamp": datetime.utcnow().isoformat()
    }

    payload = {
        "content": "@here",
        "embeds": [embed]
    }

    if FORCE_NOTIFY:
        print("[TEST MODE] Would send embed:", payload)
    else:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)


def load_last_status():
    try:
        with open(STATUS_FILE, "r") as f:
            return json.load(f).get("available")
    except:
        return None


def save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump({"available": status}, f, indent=2)


def check_api():
    try:
        api_url = "https://www.microsoft.com/msstoreapiprod/api/products/pdp/8p7h1dg85brj"
        r = requests.get(api_url, timeout=10)
        if r.status_code != 200:
            return None

        data = r.json()
        return data.get("availability", {}).get("isAvailable")
    except:
        return None


def check_scrape():
    r = requests.get(PRODUCT_URL, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")

    text = soup.get_text(" ", strip=True).lower()
    if "out of stock" in text or "sold out" in text:
        return False

    for btn in soup.find_all(["button", "a"]):
        if "add to cart" in btn.get_text(strip=True).lower():
            return True

    return None


def main():
    current = check_api()
    if current is None:
        current = check_scrape()

    print(f"Current status: {current}")

    last = load_last_status()
    print(f"Last status: {last}")

    # Manual test mode
    if FORCE_NOTIFY:
        send_discord_message()
        return

    # Only notify when availability switches to True
    if current is True and last != True:
        print("Stock became AVAILABLE — sending alert.")
        send_discord_message()
    else:
        print("No new availability — no alert.")

    save_status(current)


if __name__ == "__main__":
    main()

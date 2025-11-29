import json
import os
import time
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()

URL = "https://www.microsoft.com/en-us/store/configure/surface-pro-10-for-business/8p7h1dg85brj"
STATUS_FILE = "status.json"

def get_current_status():
    """Scrapes the configurator page and returns 5G SKU availability using Selenium."""
    driver = None
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Initialize the driver
        print("Starting Chrome browser...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Load the page
        print(f"Loading page: {URL}")
        driver.get(URL)
        
        # Wait for the page to load
        wait = WebDriverWait(driver, 15)
        
        # Wait for the 5G button to be present
        print("Waiting for 5G button...")
        fiveg_button = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation-test-id="configuratorV3-tile-button-5G-0-1-1"]'))
        )
        
        # Click the 5G button
        print("Clicking 5G button...")
        driver.execute_script("arguments[0].click();", fiveg_button)
        
        # Wait a bit for the SKUs to load after clicking 5G
        time.sleep(3)
        
        all_available_skus = []
        all_out_of_stock_skus = []
        
        # Check both processor options
        processor_buttons = [
            ('configuratorV3-tile-button-IntelCoreUltra5Processor135U-0-0-0', 'Intel Core Ultra 5 (135U)'),
            ('configuratorV3-tile-button-IntelCoreUltra7Processor165U-0-0-1', 'Intel Core Ultra 7 (165U)')
        ]
        
        for processor_selector, processor_name in processor_buttons:
            print(f"Checking {processor_name}...")
            
            # Click the processor button
            try:
                processor_button = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-automation-test-id="{processor_selector}"]'))
                )
                driver.execute_script("arguments[0].click();", processor_button)
                
                # Wait for the page to update after clicking
                time.sleep(3)
            except Exception as e:
                print(f"Could not click {processor_name}: {e}")
                continue
            
            # Wait for specifications section to be present
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation-test-id="configuratorV3-step-index-0-3"]'))
            )
            
            # Get the page source and parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            # Find the specifications (RAM/Storage) container
            specs_ul = soup.find("ul", attrs={"data-automation-test-id": "configuratorV3-step-index-0-3"})
            if not specs_ul:
                print(f"Specifications section not found for {processor_name}.")
                continue

            # Find all SKU tiles (li elements with class "tile" but NOT "d-none")
            all_tiles = specs_ul.find_all("li", class_="tile")
            # Filter: must not have "d-none" (hidden)
            visible_tiles = [tile for tile in all_tiles 
                            if "d-none" not in tile.get("class", [])]
            
            print(f"  Found {len(all_tiles)} total tiles, {len(visible_tiles)} visible")
            
            # Further filter to only include tiles that match the current processor
            # by checking if the button's data-m contains the processor name
            sku_tiles = []
            for tile in visible_tiles:
                button = tile.find("button", class_="tile__button")
                if button and button.has_attr("data-m"):
                    button_data_str = button.get("data-m", "")
                    # Check if this tile is for the currently selected processor
                    if "Ultra 5" in processor_name and "Ultra 5" in button_data_str:
                        sku_tiles.append(tile)
                    elif "Ultra 7" in processor_name and "Ultra 7" in button_data_str:
                        sku_tiles.append(tile)
            
            print(f"  {len(sku_tiles)} tiles match {processor_name}")
            
            if not sku_tiles:
                print(f"  No matching SKU tiles found for {processor_name}.")
                continue

            for tile in sku_tiles:
                # Extract RAM and storage info
                tile_body = tile.find("div", class_="v3tile__tilebody")
                if not tile_body:
                    continue
                
                # Get all <p> tags in the tile body
                p_tags = tile_body.find_all("p")
                
                if len(p_tags) < 2:
                    # Skip tiles that don't have enough info
                    continue
                
                # Handle two different tile structures:
                # 1. Tiles with 3 tags: [Processor Name, RAM, Storage]
                # 2. Tiles with 2 tags: [RAM, Storage]
                if len(p_tags) >= 3:
                    # Structure: Processor, RAM, Storage (skip first tag which is processor)
                    ram = p_tags[1].get_text(strip=True)
                    storage = p_tags[2].get_text(strip=True)
                else:
                    # Structure: RAM, Storage
                    ram = p_tags[0].get_text(strip=True)
                    storage = p_tags[1].get_text(strip=True)
                
                # Validate we have proper RAM and Storage
                if "RAM" not in ram.upper() or "SSD" not in storage.upper():
                    continue
                
                # Extract price from tilefooter
                tilefooter = tile.find("div", class_="v3tile__tilefooter")
                price_elem = tilefooter.find("span") if tilefooter else None
                price = price_elem.get_text(strip=True) if price_elem else "Unknown Price"
                
                # Check if out of stock
                out_of_stock_badge = tile.find("span", class_="badge", string=lambda text: text and "out of stock" in text.lower())
                
                # Check if button is disabled
                button = tile.find("button", class_="tile__button")
                is_disabled = button and button.has_attr("disabled")
                
                sku_info = {
                    "ram": ram,
                    "storage": storage,
                    "price": price,
                    "processor": processor_name,
                    "network": "5G"
                }
                
                if out_of_stock_badge or is_disabled:
                    all_out_of_stock_skus.append(sku_info)
                else:
                    all_available_skus.append(sku_info)
        
        print(f"Found {len(all_available_skus)} available SKUs and {len(all_out_of_stock_skus)} out of stock SKUs")
        
        return {
            "available": all_available_skus,
            "out_of_stock": all_out_of_stock_skus
        }
    
    except Exception as e:
        print(f"Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        # Always close the browser
        if driver:
            print("Closing browser...")
            driver.quit()


def load_last_status():
    if not os.path.exists(STATUS_FILE):
        return None
    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
            return data.get("available_skus", [])
    except:
        return None


def save_status(available_skus):
    with open(STATUS_FILE, "w") as f:
        json.dump({"available_skus": available_skus}, f, indent=2)


def send_discord_alert(available_skus, newly_available_skus):
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("No DISCORD_WEBHOOK_URL set — skipping alert.")
        return

    # Determine network type from SKUs (default to 5G since that's what we're checking)
    network_type = available_skus[0]['network'] if available_skus else "5G"
    
    # Build description with newly available SKUs
    if newly_available_skus:
        description = "**🎉 Newly Available SKUs:**\n"
        for sku in newly_available_skus:
            description += f"\n• **{sku['processor']}** - {sku['ram']} / {sku['storage']} - {sku['price']}"
    else:
        description = "**📦 Available SKUs:**\n"
        for sku in available_skus:
            description += f"\n• **{sku['processor']}** - {sku['ram']} / {sku['storage']} - {sku['price']}"
    
    if not available_skus:
        description = f"All {network_type} configurations are currently out of stock."

    message = {
        "content": f"@here **Surface Pro 10 for Business (Certified Refurbished) {network_type} availability changed!**",
        "embeds": [
            {
                "title": f"Surface Pro 10 for Business (Certified Refurbished) – {network_type}",
                "url": URL,
                "description": description,
                "color": 65280 if available_skus else 16711680,
                "footer": {
                    "text": f"Total available: {len(available_skus)} SKU(s)"
                }
            }
        ]
    }

    try:
        r = requests.post(webhook_url, json=message, timeout=10)
        print("Discord response:", r.status_code, r.text[:200])
    except Exception as e:
        print("Error sending Discord alert:", e)


def main():
    force_notify = os.getenv("FORCE_NOTIFY") == "true"
    last_available_skus = load_last_status() or []
    current_status = get_current_status()

    if current_status is None:
        print("Could not determine current status — no alert.")
        return

    current_available_skus = current_status.get("available", [])
    
    print(f"\nCurrent available SKUs: {len(current_available_skus)}")
    for sku in current_available_skus:
        print(f"  • {sku['processor']} - {sku['ram']} / {sku['storage']} - {sku['price']}")
    
    print(f"\nOut of stock SKUs: {len(current_status.get('out_of_stock', []))}")
    for sku in current_status.get('out_of_stock', []):
        print(f"  • {sku['processor']} - {sku['ram']} / {sku['storage']} - {sku['price']}")

    if force_notify:
        print("\nForce notify enabled — sending test alert.")
        send_discord_alert(current_available_skus, [])
        return

    # Convert SKU lists to sets of identifying strings for comparison
    def sku_to_key(sku):
        return f"{sku['ram']}|{sku['storage']}|{sku['price']}"
    
    last_sku_keys = {sku_to_key(sku) for sku in last_available_skus}
    current_sku_keys = {sku_to_key(sku) for sku in current_available_skus}
    
    # Find newly available SKUs
    newly_available_keys = current_sku_keys - last_sku_keys
    newly_available_skus = [sku for sku in current_available_skus if sku_to_key(sku) in newly_available_keys]
    
    # Check if availability changed
    if current_sku_keys != last_sku_keys:
        print("\n✓ Availability changed — sending alert!")
        if newly_available_skus:
            print(f"  New SKUs available: {len(newly_available_skus)}")
        send_discord_alert(current_available_skus, newly_available_skus)
        save_status(current_available_skus)
    else:
        print("\n✓ No change in availability — no alert.")


if __name__ == "__main__":
    main()

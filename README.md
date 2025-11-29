# Surface Pro 10 Stock Checker

Automated stock monitoring for Microsoft Surface Pro 10 for Business (Certified Refurbished) with 5G connectivity.

## Features

- 🔍 **Automated Monitoring**: Checks stock every 5 minutes via GitHub Actions
- 🔔 **Discord Notifications**: Sends alerts when availability changes
- 🖥️ **Multi-Processor Support**: Tracks both Intel Core Ultra 5 and Ultra 7 SKUs
- 📊 **Detailed Information**: Shows processor, RAM, storage, and pricing for each configuration
- 🤖 **Selenium-Based**: Uses browser automation to interact with Microsoft's configurator page

## What It Monitors

Currently configured to track **Surface Pro 10 for Business (Certified Refurbished)** with:
- 5G connectivity
- Intel Core Ultra 5 (135U) processor
- Intel Core Ultra 7 (165U) processor
- All available RAM/Storage configurations

## Setup

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/ShinyShips/check-surface-stock.git
   cd check-surface-stock
   ```

2. **Install dependencies**
   ```bash
   pip install requests beautifulsoup4 selenium webdriver-manager python-dotenv
   ```

3. **Create a `.env` file** with your Discord webhook URL:
   ```
   DISCORD_WEBHOOK_URL=your_webhook_url_here
   ```

4. **Run the checker**
   ```bash
   python check_stock.py
   ```

### GitHub Actions Setup

The repository includes a workflow that runs automatically every 5 minutes.

1. **Add Discord Webhook Secret**
   - Go to Repository Settings → Secrets and variables → Actions
   - Create a new secret named `DISCORD_WEBHOOK_URL`
   - Paste your Discord webhook URL as the value

2. **Enable GitHub Actions**
   - The workflow will run automatically on schedule
   - You can also trigger it manually from the Actions tab

## How It Works

1. **Launches Chrome** in headless mode using Selenium
2. **Navigates** to the Microsoft Store configurator page
3. **Clicks the 5G option** to filter network types
4. **Cycles through processors** (Ultra 5 and Ultra 7) to check all SKUs
5. **Extracts information** about RAM, storage, price, and availability
6. **Compares** with previous status stored in `status.json`
7. **Sends Discord alert** if availability changes

## Configuration

### Change Product SKU

Edit the `URL` constant in `check_stock.py`:

```python
# Refurbished model
URL = "https://www.microsoft.com/en-us/store/configure/surface-pro-10-for-business/8p7h1dg85brj"

# Non-refurbished model
URL = "https://www.microsoft.com/en-us/store/configure/surface-pro-10-for-business/8v73d6qwrss1"
```

### Change Check Frequency

Edit the cron schedule in `.github/workflows/check-surface.yml`:

```yaml
schedule:
  - cron: "*/5 * * * *"  # Every 5 minutes
  # - cron: "*/15 * * * *"  # Every 15 minutes
  # - cron: "0 * * * *"  # Every hour
```

## Output Example

```
Current available SKUs: 3
  • Intel Core Ultra 5 (135U) - 16GB RAM / 256GB SSD - $1,529.00
  • Intel Core Ultra 7 (165U) - 16GB RAM / 256GB SSD - $1,699.00
  • Intel Core Ultra 7 (165U) - 32GB RAM / 512GB SSD - $2,129.00

Out of stock SKUs: 0

✓ Availability changed — sending alert!
```

## Discord Notifications

When stock becomes available, you'll receive a Discord message with:
- @here mention for immediate attention
- List of newly available SKUs with processor, RAM, storage, and price
- Direct link to the product page
- Total count of available configurations

## Files

- **`check_stock.py`** - Main script that checks stock availability
- **`status.json`** - Stores the last known status (tracked in git)
- **`.github/workflows/check-surface.yml`** - GitHub Actions workflow
- **`.env`** - Local environment variables (not committed)
- **`.gitignore`** - Excludes sensitive files from git

## Limitations

- GitHub Actions scheduled workflows may be delayed during high load
- Private repositories on free plans have limited Actions minutes
- The script depends on Microsoft's page structure (may break if they update their site)

## License

MIT

## Author

ShinyShips

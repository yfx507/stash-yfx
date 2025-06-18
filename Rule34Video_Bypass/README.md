# Rule34Video DDoS-Guard Bypass Scraper

A Stash scraper for Rule34Video that automatically bypasses DDoS-Guard protection using undetected_chromedriver.

## Features

- ✅ **Full Stash GUI Integration** - Works exactly like the original Rule34Video scraper
- ✅ **Automatic DDoS-Guard Bypass** - No manual intervention or cookie management needed
- ✅ **Session Persistence** - Maintains bypass session for efficient scraping
- ✅ **All Scraper Functions** - URL scraping, search, fragment matching
- ✅ **Error Recovery** - Automatically refreshes sessions when needed

## Requirements

- Stash (tested with v0.20+)
- Python 3.8+
- Chrome/Chromium browser
- VPN connection (recommended)

## Installation

### 1. Install Python Dependencies

```bash
pip3 install undetected-chromedriver requests selenium
```

### 2. Download Files

Download all files from this repository:
- `Rule34Video_Bypass.yml` - Stash scraper configuration
- `stash_ddos_proxy.py` - DDoS-Guard bypass proxy server
- `undetected_scraper.py` - Standalone testing script (optional)

### 3. Place Files

- Copy `Rule34Video_Bypass.yml` to your Stash scrapers directory
- Place `stash_ddos_proxy.py` in your scrapers directory or any accessible location

## Usage

### 1. Start the Bypass Proxy

```bash
python3 stash_ddos_proxy.py
```

The proxy will start on `http://localhost:8890` and automatically handle DDoS-Guard challenges.

### 2. Configure Stash

1. In Stash GUI, go to **Settings > Scrapers**
2. Click **Reload Scrapers**
3. Verify "Rule34Video (DDoS-Guard Bypass)" appears in the list

### 3. Scrape Content

Use the scraper exactly like any other Stash scraper:

**Option A: URL Scraping**
1. Edit a scene in Stash
2. Enter a Rule34Video URL in the URL field
3. Click **Scrape** and select "Rule34Video (DDoS-Guard Bypass)"

**Option B: Search**
1. Click **Scrape** without entering a URL
2. Select the bypass scraper
3. Enter search terms

**Option C: Fragment Matching**
- Automatically matches scenes based on filename if it contains the Rule34Video ID

## How It Works

```
Stash GUI Request → Bypass Proxy (localhost:8890) → undetected_chromedriver → Rule34Video → Clean HTML → Stash
```

1. Stash makes requests to the local proxy server
2. The proxy uses undetected_chromedriver to bypass DDoS-Guard automatically
3. Clean HTML is returned to Stash for normal XPath scraping
4. Metadata is extracted and displayed in Stash GUI

## Troubleshooting

**Proxy Won't Start:**
- Check if port 8890 is already in use: `netstat -tlnp | grep 8890`
- Ensure all Python dependencies are installed

**Scraper Not Working:**
- Make sure the proxy is running before using the scraper
- Check proxy logs for error messages
- Verify your internet connection and VPN if using one

**Performance Notes:**
- First request may take 10-20 seconds (initial DDoS-Guard bypass)
- Subsequent requests are much faster (reuses session)
- Session automatically refreshes every 5 minutes

## Files

- **Rule34Video_Bypass.yml** - Stash scraper YAML configuration
- **stash_ddos_proxy.py** - HTTP proxy server with DDoS-Guard bypass
- **undetected_scraper.py** - Standalone testing script (optional)

## License

This project is provided as-is for educational and personal use.

## Disclaimer

This tool is intended for personal use with content you have the right to access. Please respect website terms of service and applicable laws in your jurisdiction.


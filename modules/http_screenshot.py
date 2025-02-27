import os
import sys
import asyncio
from pyppeteer import launch


async def capture_screenshot_async(navigation_url, output_file):
    browser = await launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-extensions',
            '--disable-gpu',
            '--ignore-certificate-errors',
            '--disable-dev-shm-usage'
        ],
        ignoreHTTPSErrors=True
    )
    page = await browser.newPage()

    # Set a custom user agent
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    # Try with networkidle2, then fallback to domcontentloaded if necessary
    try:
        await page.goto(navigation_url, options={"timeout": 60000, "waitUntil": "networkidle2"})
    except Exception as e:
        print(f"[-] Error loading page with networkidle2: {e}")
        try:
            await page.goto(navigation_url, options={"timeout": 60000, "waitUntil": "domcontentloaded"})
        except Exception as e2:
            print(f"[-] Error loading page with domcontentloaded: {e2}")
            await browser.close()
            return

    try:
        await page.screenshot({'path': output_file})
        print(f"[+] Screenshot saved in {output_file}.")
    except Exception as e:
        print(f"[-] Error capturing screenshot: {e}")

    await browser.close()

def capture_http_screenshot(url):
    print("[+] Capturing screenshot of the website...")
    navigation_url = f"http://{url}"
    output_file = f"logs/{url}/http/screenshot.png"

    os.makedirs(f"logs/{url}/http", exist_ok=True)

    asyncio.run(capture_screenshot_async(navigation_url, output_file))

    if os.path.isfile(output_file):
        os.system(f"cp logs/{url}/http/screenshot.png logs/{url}/report/http_screenshot.png")
    else:
        print(f"[-] Screenshot not found at {output_file}, skipping copy.")

    return True

def run_http_screenshot(url):
    capture_http_screenshot(url)

if __name__ == '__main__':
    url = sys.argv[1]
    capture_http_screenshot(url)
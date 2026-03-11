#!/usr/bin/env python3
"""
RAM Tool: Web Browsing Automation
Control a browser via Playwright (headless or visible).
"""

import subprocess
import sys
from typing import Optional


def check_playwright():
    try:
        import playwright
        return True
    except ImportError:
        return False


def install_playwright():
    """Install playwright if not present"""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "playwright", "--break-system-packages"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True, text=True
        )
        return True
    return False


async def open_page(url: str, headless: bool = True) -> dict:
    """Open a web page and return its title and content"""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            page = await browser.new_page()
            await page.goto(url, timeout=15000)
            title = await page.title()
            content = await page.inner_text("body")
            await browser.close()
            return {
                "success": True,
                "url": url,
                "title": title,
                "content": content[:3000],
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def take_screenshot(url: str, output_path: str = "/tmp/screenshot.png") -> dict:
    """Take a screenshot of a webpage"""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=15000)
            await page.screenshot(path=output_path, full_page=True)
            await browser.close()
            return {"success": True, "path": output_path, "url": url}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def search_web(query: str) -> dict:
    """Search DuckDuckGo and return top results"""
    try:
        from playwright.async_api import async_playwright
        url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=15000)
            # Get result titles and URLs
            results = await page.evaluate("""
                () => {
                    const items = document.querySelectorAll('.result__title a');
                    return Array.from(items).slice(0, 10).map(a => ({
                        title: a.innerText,
                        url: a.href
                    }));
                }
            """)
            await browser.close()
            return {"success": True, "query": query, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def fill_form(url: str, fields: dict, submit_selector: Optional[str] = None) -> dict:
    """Open a page and fill in form fields"""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Visible for forms
            page = await browser.new_page()
            await page.goto(url, timeout=15000)

            for selector, value in fields.items():
                await page.fill(selector, value)

            if submit_selector:
                await page.click(submit_selector)
                await page.wait_for_load_state("networkidle", timeout=10000)

            title = await page.title()
            await browser.close()
            return {"success": True, "final_title": title}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import asyncio
    if not check_playwright():
        print("Installing Playwright...")
        install_playwright()

    result = asyncio.run(open_page("https://example.com"))
    print(result.get("title"), "-", result.get("content", "")[:200])

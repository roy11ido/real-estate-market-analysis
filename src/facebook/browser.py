"""Playwright browser setup with anti-detection configuration."""

from __future__ import annotations

import random

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from src.utils.config import get_cookies_dir, load_settings
from src.utils.logger import get_logger

logger = get_logger()

STATE_FILE = "fb_state.json"


async def create_browser_context(headless: bool | None = None) -> tuple[Browser, BrowserContext]:
    """Create a Playwright browser with anti-detection settings.

    Args:
        headless: Override headless setting. None = use config.

    Returns:
        Tuple of (Browser, BrowserContext).
    """
    settings = load_settings()
    browser_config = settings.get("browser", {})

    if headless is None:
        headless = browser_config.get("headless", True)

    state_path = get_cookies_dir() / STATE_FILE

    pw = await async_playwright().start()

    browser = await pw.chromium.launch(
        headless=headless,
        slow_mo=browser_config.get("slow_mo", 50),
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
        ],
    )

    # Use persistent context if state file exists
    context_options = {
        "viewport": {
            "width": browser_config.get("viewport_width", 1280),
            "height": browser_config.get("viewport_height", 800),
        },
        "locale": "he-IL",
        "timezone_id": "Asia/Jerusalem",
        "user_agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
    }

    # Load saved state if available
    if state_path.exists():
        context_options["storage_state"] = str(state_path)
        logger.info("Loaded saved browser state")

    context = await browser.new_context(**context_options)

    # Anti-detection: override navigator.webdriver
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        Object.defineProperty(navigator, 'languages', {
            get: () => ['he', 'he-IL', 'en-US', 'en'],
        });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
    """)

    return browser, context


async def save_browser_state(context: BrowserContext) -> None:
    """Save browser cookies and storage state for next session."""
    state_path = get_cookies_dir() / STATE_FILE
    await context.storage_state(path=str(state_path))
    logger.info("Browser state saved")


async def random_delay(min_seconds: float | None = None, max_seconds: float | None = None) -> None:
    """Wait a random amount of time (human-like behavior)."""
    import asyncio

    settings = load_settings()
    delays = settings.get("delays", {})

    if min_seconds is None:
        min_seconds = delays.get("page_load_wait_min", 3)
    if max_seconds is None:
        max_seconds = delays.get("page_load_wait_max", 7)

    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)


async def human_type(page: Page, selector: str, text: str) -> None:
    """Type text character by character with random delays (human-like).

    Args:
        page: Playwright page instance.
        selector: CSS selector for the input element.
        text: Text to type.
    """
    settings = load_settings()
    delays = settings.get("delays", {})
    min_delay = delays.get("typing_delay_min", 30)
    max_delay = delays.get("typing_delay_max", 100)

    for char in text:
        await page.type(selector, char, delay=random.randint(min_delay, max_delay))

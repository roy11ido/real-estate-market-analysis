"""Facebook session management: login, verification, and health checks."""

from __future__ import annotations

import asyncio

from playwright.async_api import BrowserContext, Page

from src.facebook.browser import (
    create_browser_context,
    random_delay,
    save_browser_state,
)
from src.utils.config import get_cookies_dir
from src.utils.logger import get_logger

logger = get_logger()

STATE_FILE = "fb_state.json"


async def login_interactive() -> None:
    """Open a headed browser for manual Facebook login.

    The user logs in manually, then the session state is saved.
    """
    logger.info("Opening browser for Facebook login...")
    browser, context = await create_browser_context(headless=False)

    try:
        page = await context.new_page()
        await page.goto("https://www.facebook.com/", wait_until="domcontentloaded")

        logger.info(
            "Please log into Facebook in the browser window.\n"
            "After logging in and seeing your feed, press Enter here to save the session."
        )

        # Wait for user to press Enter in the terminal
        await asyncio.get_event_loop().run_in_executor(
            None, lambda: input("\n>>> Press Enter after logging into Facebook... ")
        )

        # Verify login succeeded
        if await _is_logged_in(page):
            await save_browser_state(context)
            logger.info("Facebook session saved successfully!")
        else:
            logger.error("Login verification failed. Please try again.")

    finally:
        await context.close()
        await browser.close()


async def verify_session(context: BrowserContext) -> bool:
    """Check if the saved Facebook session is still valid.

    Args:
        context: Browser context with loaded state.

    Returns:
        True if logged in, False otherwise.
    """
    page = await context.new_page()
    try:
        await page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        await random_delay(2, 4)

        # Check for checkpoint/security pages
        if await _is_checkpoint(page):
            logger.error("Facebook checkpoint detected! Manual intervention required.")
            return False

        logged_in = await _is_logged_in(page)
        if logged_in:
            logger.info("Facebook session is valid")
        else:
            logger.warning("Facebook session expired or invalid")

        return logged_in
    finally:
        await page.close()


async def has_saved_session() -> bool:
    """Check if a saved session file exists."""
    state_path = get_cookies_dir() / STATE_FILE
    return state_path.exists()


async def _is_logged_in(page: Page) -> bool:
    """Check if we're logged into Facebook by looking for common UI elements."""
    try:
        # Look for the profile/menu icon that appears when logged in
        selectors = [
            '[aria-label="Your profile"]',
            '[aria-label="הפרופיל שלך"]',
            '[aria-label="Account"]',
            '[aria-label="חשבון"]',
            'div[role="navigation"]',
            '[data-pagelet="LeftRail"]',
        ]
        for selector in selectors:
            element = await page.query_selector(selector)
            if element:
                return True

        # Also check URL - if we're on a login page, we're not logged in
        url = page.url
        if "login" in url or "checkpoint" in url:
            return False

        # Check if we can find the compose box (feed)
        compose = await page.query_selector('[aria-label="Create a post"]')
        if compose:
            return True
        compose_he = await page.query_selector('[aria-label="יצירת פוסט"]')
        if compose_he:
            return True

        return False
    except Exception:
        return False


async def _is_checkpoint(page: Page) -> bool:
    """Check if Facebook is showing a security checkpoint."""
    url = page.url
    if "checkpoint" in url or "security" in url:
        return True

    # Check for common checkpoint text
    try:
        body_text = await page.inner_text("body")
        checkpoint_phrases = [
            "verify your identity",
            "confirm your identity",
            "security check",
            "אמת את זהותך",
            "בדיקת אבטחה",
        ]
        for phrase in checkpoint_phrases:
            if phrase.lower() in body_text.lower():
                return True
    except Exception:
        pass

    return False

"""Core Facebook group posting logic using Playwright browser automation."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from pathlib import Path

from playwright.async_api import BrowserContext, Page, TimeoutError as PlaywrightTimeout

from src.facebook.browser import random_delay, save_browser_state
from src.utils.config import load_settings
from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class PostResult:
    """Result of posting to a single group."""

    group_name: str
    success: bool
    error: str = ""


@dataclass
class PropertyPostResult:
    """Result of posting a property to all groups."""

    property_address: str
    page_id: str
    group_results: list[PostResult] = field(default_factory=list)

    @property
    def successful_groups(self) -> list[str]:
        return [r.group_name for r in self.group_results if r.success]

    @property
    def failed_groups(self) -> list[str]:
        return [r.group_name for r in self.group_results if not r.success]

    @property
    def success_count(self) -> int:
        return len(self.successful_groups)

    @property
    def total_count(self) -> int:
        return len(self.group_results)


async def post_to_group(
    context: BrowserContext,
    group_url: str,
    group_name: str,
    text: str,
    image_paths: list[Path],
    progress_callback=None,
) -> PostResult:
    """Post content to a single Facebook group.

    Args:
        context: Playwright browser context.
        group_url: Facebook group URL.
        group_name: Group name for logging.
        text: Post text content.
        image_paths: List of local image file paths to upload.
        progress_callback: Optional callback(message: str) for progress updates.

    Returns:
        PostResult with success/failure status.
    """
    page = await context.new_page()

    def _log(msg: str):
        logger.info(msg)
        if progress_callback:
            progress_callback(msg)

    try:
        # 1. Navigate to the group
        _log(f"Navigating to group: {group_name}")
        await page.goto(group_url, wait_until="domcontentloaded", timeout=30000)
        await random_delay(3, 6)

        # Check for errors
        if "not available" in (await page.title()).lower():
            return PostResult(group_name=group_name, success=False, error="Group not available")

        # 2. Find and click the post creation area
        _log(f"Opening post composer in: {group_name}")
        compose_clicked = await _click_compose_box(page)
        if not compose_clicked:
            return PostResult(
                group_name=group_name, success=False, error="Could not find compose box"
            )

        await random_delay(2, 4)

        # 3. Type the post text
        _log(f"Typing post text in: {group_name}")
        await _type_post_text(page, text)
        await random_delay(1, 3)

        # 4. Upload images
        if image_paths:
            _log(f"Uploading {len(image_paths)} images to: {group_name}")
            await _upload_images(page, image_paths)
            await random_delay(2, 4)

        # 5. Click the Post button
        _log(f"Submitting post to: {group_name}")
        posted = await _click_post_button(page)

        if posted:
            await random_delay(3, 5)
            _log(f"Successfully posted to: {group_name}")
            return PostResult(group_name=group_name, success=True)
        else:
            return PostResult(
                group_name=group_name, success=False, error="Could not click Post button"
            )

    except PlaywrightTimeout as e:
        error = f"Timeout: {str(e)[:100]}"
        logger.error(f"Timeout posting to {group_name}: {error}")
        return PostResult(group_name=group_name, success=False, error=error)

    except Exception as e:
        error = f"{type(e).__name__}: {str(e)[:100]}"
        logger.error(f"Error posting to {group_name}: {error}")
        return PostResult(group_name=group_name, success=False, error=error)

    finally:
        await page.close()


async def post_property_to_all_groups(
    context: BrowserContext,
    groups: list[dict],
    text: str,
    image_paths: list[Path],
    property_address: str,
    page_id: str,
    progress_callback=None,
) -> PropertyPostResult:
    """Post a property to all configured Facebook groups.

    Args:
        context: Playwright browser context.
        groups: List of group configs from facebook_groups.yaml.
        text: Post text content.
        image_paths: List of local image file paths.
        property_address: For logging and result tracking.
        page_id: Notion page ID.
        progress_callback: Optional callback(message: str) for progress.

    Returns:
        PropertyPostResult with results per group.
    """
    settings = load_settings()
    delays = settings.get("delays", {})
    limits = settings.get("limits", {})

    result = PropertyPostResult(property_address=property_address, page_id=page_id)

    # Shuffle groups for anti-detection
    shuffled_groups = list(groups)
    random.shuffle(shuffled_groups)

    # Apply ramp-up limits
    max_groups = _get_ramp_up_limit(settings)
    if len(shuffled_groups) > max_groups:
        logger.info(f"Ramp-up limit: posting to {max_groups} groups (out of {len(shuffled_groups)})")
        shuffled_groups = shuffled_groups[:max_groups]

    consecutive_failures = 0

    for i, group in enumerate(shuffled_groups, 1):
        group_name = group["name"]
        group_url = group["url"]
        max_images = group.get("max_images", 4)

        if progress_callback:
            progress_callback(
                f"[{i}/{len(shuffled_groups)}] מפרסם את {property_address} בקבוצה: {group_name}"
            )

        # Limit images per group config
        group_images = image_paths[:max_images]

        # Post to this group
        post_result = await post_to_group(
            context=context,
            group_url=group_url,
            group_name=group_name,
            text=text,
            image_paths=group_images,
            progress_callback=progress_callback,
        )
        result.group_results.append(post_result)

        # Track consecutive failures for cool-down
        if post_result.success:
            consecutive_failures = 0
        else:
            consecutive_failures += 1

        # Cool-down on multiple failures
        if consecutive_failures >= 3:
            logger.warning("3 consecutive failures - cooling down for 5 minutes")
            if progress_callback:
                progress_callback("3 כישלונות ברצף - ממתין 5 דקות...")
            await asyncio.sleep(300)
            consecutive_failures = 0

        # Wait between groups (anti-detection)
        if i < len(shuffled_groups):
            wait_min = delays.get("between_groups_min", 45)
            wait_max = delays.get("between_groups_max", 120)
            wait_time = random.uniform(wait_min, wait_max)
            if progress_callback:
                progress_callback(f"ממתין {int(wait_time)} שניות לפני הקבוצה הבאה...")
            await asyncio.sleep(wait_time)

    # Save browser state after all posts
    await save_browser_state(context)

    return result


# --- Private helper functions ---


async def _click_compose_box(page: Page) -> bool:
    """Find and click the 'Write something...' compose area in a group."""
    # Try multiple selectors (Facebook changes these frequently)
    selectors = [
        # Hebrew UI
        '[aria-label="כתבו משהו..."]',
        '[aria-label="מה חדש אצלך?"]',
        # English UI
        '[aria-label="Write something..."]',
        "[aria-label=\"What's on your mind?\"]",
        # Generic compose selectors
        'div[role="button"] span:has-text("כתבו משהו")',
        'div[role="button"] span:has-text("Write something")',
        # Fallback: look for the create post area
        '[data-pagelet="GroupInlineComposer"]',
    ]

    for selector in selectors:
        try:
            element = await page.wait_for_selector(selector, timeout=5000)
            if element:
                await element.click()
                return True
        except (PlaywrightTimeout, Exception):
            continue

    # Last resort: try to click on any text that looks like the compose area
    try:
        compose = await page.query_selector('div[contenteditable="true"]')
        if compose:
            await compose.click()
            return True
    except Exception:
        pass

    return False


async def _type_post_text(page: Page, text: str) -> None:
    """Type the post text into the compose box character by character."""
    settings = load_settings()
    delays = settings.get("delays", {})
    min_delay = delays.get("typing_delay_min", 30)
    max_delay = delays.get("typing_delay_max", 100)

    # Wait for the compose dialog/editor to appear
    editor_selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"]',
    ]

    editor = None
    for selector in editor_selectors:
        try:
            editor = await page.wait_for_selector(selector, timeout=5000)
            if editor:
                break
        except PlaywrightTimeout:
            continue

    if not editor:
        raise Exception("Could not find text editor")

    await editor.click()
    await asyncio.sleep(0.5)

    # Type text character by character for human-like behavior
    for char in text:
        if char == "\n":
            await page.keyboard.press("Enter")
        else:
            await page.keyboard.type(char, delay=random.randint(min_delay, max_delay))

        # Occasional micro-pause (human behavior)
        if random.random() < 0.05:
            await asyncio.sleep(random.uniform(0.3, 1.0))


async def _upload_images(page: Page, image_paths: list[Path]) -> None:
    """Upload images to the post one at a time."""
    settings = load_settings()
    image_wait = settings.get("delays", {}).get("image_upload_wait", 5)

    # Click the photo/video button to enable image upload
    photo_selectors = [
        '[aria-label="תמונה/סרטון"]',
        '[aria-label="Photo/video"]',
        '[aria-label="Photo/Video"]',
    ]

    photo_btn = None
    for selector in photo_selectors:
        try:
            photo_btn = await page.wait_for_selector(selector, timeout=5000)
            if photo_btn:
                break
        except PlaywrightTimeout:
            continue

    if photo_btn:
        await photo_btn.click()
        await asyncio.sleep(2)

    # Upload images via file input
    for i, img_path in enumerate(image_paths):
        try:
            # Look for file input
            file_input = await page.query_selector('input[type="file"][accept*="image"]')
            if not file_input:
                # Try to find any file input
                file_input = await page.query_selector('input[type="file"]')

            if file_input:
                await file_input.set_input_files(str(img_path))
                logger.debug(f"Uploaded image {i + 1}/{len(image_paths)}")
                # Wait for upload to process
                await asyncio.sleep(image_wait)
            else:
                logger.warning(f"Could not find file input for image {i + 1}")
                break

        except Exception as e:
            logger.warning(f"Failed to upload image {i + 1}: {e}")


async def _click_post_button(page: Page) -> bool:
    """Click the Post/Submit button."""
    post_selectors = [
        # Hebrew
        '[aria-label="פרסום"]',
        '[aria-label="פרסם"]',
        'div[role="button"]:has-text("פרסום")',
        'div[role="button"]:has-text("פרסם")',
        # English
        '[aria-label="Post"]',
        'div[role="button"]:has-text("Post")',
        # Generic submit button
        'form div[role="button"][tabindex="0"]:last-of-type',
    ]

    for selector in post_selectors:
        try:
            btn = await page.wait_for_selector(selector, timeout=5000)
            if btn:
                # Check if button is enabled
                is_disabled = await btn.get_attribute("aria-disabled")
                if is_disabled == "true":
                    logger.warning("Post button is disabled, waiting...")
                    await asyncio.sleep(3)
                    is_disabled = await btn.get_attribute("aria-disabled")
                    if is_disabled == "true":
                        continue

                await btn.click()
                # Wait for post to submit
                await asyncio.sleep(5)
                return True
        except (PlaywrightTimeout, Exception):
            continue

    return False


def _get_ramp_up_limit(settings: dict) -> int:
    """Get the maximum number of groups based on ramp-up schedule."""
    ramp_up = settings.get("ramp_up", {})
    if not ramp_up.get("enabled", False):
        return 999

    from datetime import datetime, date

    start_date_str = ramp_up.get("start_date", "2026-02-15")
    start_date = date.fromisoformat(start_date_str)
    today = date.today()

    days_since_start = (today - start_date).days

    if days_since_start < 7:
        return ramp_up.get("week1_max_groups", 4)
    elif days_since_start < 14:
        return ramp_up.get("week2_max_groups", 8)
    elif days_since_start < 21:
        return ramp_up.get("week3_max_groups", 12)
    else:
        return ramp_up.get("week4_max_groups", 99)

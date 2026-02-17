"""Main orchestration: coordinates Notion data, content generation, and Facebook posting."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from src.content.generator import generate_post
from src.content.image_handler import download_property_images, cleanup_old_cache
from src.facebook.browser import create_browser_context, save_browser_state
from src.facebook.poster import (
    PostResult,
    PropertyPostResult,
    post_property_to_all_groups,
)
from src.facebook.session import verify_session
from src.notion.client import NotionPropertyClient
from src.notion.models import Property
from src.utils.config import load_facebook_groups, load_settings
from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class RunResult:
    """Result of a full posting run."""

    property_results: list[PropertyPostResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def total_properties(self) -> int:
        return len(self.property_results)

    @property
    def total_posts(self) -> int:
        return sum(r.total_count for r in self.property_results)

    @property
    def successful_posts(self) -> int:
        return sum(r.success_count for r in self.property_results)

    @property
    def summary(self) -> str:
        lines = [
            f"סיכום ריצה:",
            f"  נכסים: {self.total_properties}",
            f"  פוסטים: {self.successful_posts}/{self.total_posts} הצליחו",
        ]
        if self.errors:
            lines.append(f"  שגיאות: {len(self.errors)}")
        return "\n".join(lines)


async def run_posting(
    selected_properties: list[Property],
    progress_callback=None,
    dry_run: bool = False,
) -> RunResult:
    """Run the full posting flow for selected properties.

    Args:
        selected_properties: Properties to post (selected by user in GUI).
        progress_callback: Optional callback(message: str) for GUI updates.
        dry_run: If True, generate content but don't actually post.

    Returns:
        RunResult with all results.
    """
    result = RunResult()
    settings = load_settings()
    groups = load_facebook_groups()

    if not groups:
        result.errors.append("No Facebook groups configured. Edit config/facebook_groups.yaml")
        return result

    if not selected_properties:
        result.errors.append("No properties selected for posting.")
        return result

    def _log(msg: str):
        logger.info(msg)
        if progress_callback:
            progress_callback(msg)

    _log(f"Starting posting run: {len(selected_properties)} properties, {len(groups)} groups")

    # Initialize Notion client for status updates
    notion_client = NotionPropertyClient()

    # Download images for all properties first
    _log("Downloading property images...")
    property_images: dict[str, list[Path]] = {}
    for prop in selected_properties:
        if prop.image_urls:
            images = download_property_images(prop.page_id, prop.image_urls)
            property_images[prop.page_id] = images
            _log(f"  {prop.address}: {len(images)} images downloaded")
        else:
            property_images[prop.page_id] = []
            _log(f"  {prop.address}: no images")

    # Generate post content for all properties
    _log("Generating post content...")
    property_posts: dict[str, str] = {}
    for prop in selected_properties:
        post_text = generate_post(prop)
        property_posts[prop.page_id] = post_text
        _log(f"  {prop.address}: post generated ({len(post_text)} chars)")

    if dry_run:
        _log("DRY RUN - not posting to Facebook")
        for prop in selected_properties:
            _log(f"\n--- {prop.address} ---")
            _log(property_posts[prop.page_id])
            _log(f"Images: {len(property_images[prop.page_id])}")
        return result

    # Initialize browser and verify session
    _log("Starting browser...")
    browser, context = await create_browser_context()

    try:
        _log("Verifying Facebook session...")
        if not await verify_session(context):
            result.errors.append(
                "Facebook session expired. Run 'python src/cli.py login' to re-login."
            )
            return result

        _log("Session valid! Starting posting...")

        # Post each property to all groups
        for i, prop in enumerate(selected_properties, 1):
            _log(f"\n=== Property {i}/{len(selected_properties)}: {prop.address} ===")

            prop_result = await post_property_to_all_groups(
                context=context,
                groups=groups,
                text=property_posts[prop.page_id],
                image_paths=property_images[prop.page_id],
                property_address=prop.address,
                page_id=prop.page_id,
                progress_callback=progress_callback,
            )
            result.property_results.append(prop_result)

            # Update Notion status
            if prop_result.successful_groups:
                try:
                    notion_client.mark_as_posted(prop.page_id, prop_result.successful_groups)
                    _log(f"Updated Notion: {prop.address} → posted to {prop_result.success_count} groups")
                except Exception as e:
                    _log(f"Warning: Failed to update Notion for {prop.address}: {e}")

            elif prop_result.failed_groups:
                try:
                    first_error = prop_result.group_results[0].error if prop_result.group_results else "Unknown"
                    notion_client.mark_as_failed(prop.page_id, first_error)
                except Exception as e:
                    _log(f"Warning: Failed to update Notion for {prop.address}: {e}")

            # Wait between properties
            if i < len(selected_properties):
                wait_min = settings.get("delays", {}).get("between_properties_min", 120)
                wait_max = settings.get("delays", {}).get("between_properties_max", 300)
                import random
                wait_time = random.uniform(wait_min, wait_max)
                _log(f"Waiting {int(wait_time)} seconds before next property...")
                await asyncio.sleep(wait_time)

    finally:
        await save_browser_state(context)
        await context.close()
        await browser.close()

    # Clean up old image cache
    cleanup_old_cache()

    _log(f"\n{result.summary}")
    return result


def fetch_properties_for_gui() -> list[Property]:
    """Fetch properties from Notion for display in the GUI.

    Returns properties that are in marketing status (בשיווק בלעדי).
    """
    client = NotionPropertyClient()
    return client.get_marketing_properties()

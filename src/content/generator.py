"""Generate Facebook post content from property data using Jinja2 templates."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.notion.models import Property
from src.utils.config import CONFIG_DIR, get_agent_config, load_settings
from src.utils.logger import get_logger

logger = get_logger()

TEMPLATES_DIR = CONFIG_DIR / "post_templates"


def generate_post(property: Property, template_name: str = "standard") -> str:
    """Generate a Facebook post from property data.

    Args:
        property: Property data from Notion.
        template_name: Name of the Jinja2 template (without .j2 extension).

    Returns:
        Rendered post text ready for Facebook.
    """
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    template = env.get_template(f"{template_name}.j2")

    agent = get_agent_config()
    settings = load_settings()

    context = {
        "property": property,
        "property_type_emoji": property.emoji,
        "listing_label": "למכירה",
        "agent_name": agent["name"],
        "agent_company": agent["company"],
        "agent_phone": agent["phone"],
        "hashtags": property.get_hashtags() if settings["content"]["include_hashtags"] else "",
    }

    rendered = template.render(**context)

    # Clean up extra blank lines
    lines = rendered.split("\n")
    cleaned = []
    prev_empty = False
    for line in lines:
        is_empty = not line.strip()
        if is_empty and prev_empty:
            continue
        cleaned.append(line)
        prev_empty = is_empty

    result = "\n".join(cleaned).strip()
    logger.debug(f"Generated post for {property.address} ({len(result)} chars)")
    return result


def generate_post_preview(property: Property, template_name: str = "standard") -> str:
    """Generate a preview of the post (same as generate_post, for GUI display)."""
    return generate_post(property, template_name)

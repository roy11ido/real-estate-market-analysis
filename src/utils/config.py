"""Configuration loader for settings, environment variables, and Facebook groups."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"

# Load .env file
load_dotenv(PROJECT_ROOT / ".env")


def get_env(key: str, default: str | None = None) -> str:
    """Get environment variable or raise error if not set and no default."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable {key} is not set. Check your .env file.")
    return value


def load_yaml(file_path: Path) -> dict:
    """Load a YAML configuration file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_settings() -> dict:
    """Load the main settings.yaml configuration."""
    return load_yaml(CONFIG_DIR / "settings.yaml")


def load_facebook_groups() -> list[dict]:
    """Load Facebook groups from facebook_groups.yaml. Returns only enabled groups."""
    data = load_yaml(CONFIG_DIR / "facebook_groups.yaml")
    groups = data.get("groups", [])
    return [g for g in groups if g.get("enabled", True)]


def get_notion_config() -> dict:
    """Get Notion API configuration."""
    return {
        "api_key": get_env("NOTION_API_KEY"),
        "database_id": get_env("NOTION_DATABASE_ID"),
    }


def get_agent_config() -> dict:
    """Get agent/broker configuration for post signatures."""
    return {
        "name": get_env("AGENT_NAME", "רוי עידו"),
        "company": get_env("AGENT_COMPANY", "Real Capital"),
        "phone": get_env("AGENT_PHONE", "0505922642"),
        "email": get_env("AGENT_EMAIL", "roy11ido@gmail.com"),
    }


def get_cookies_dir() -> Path:
    """Get the cookies directory path, creating it if needed."""
    path = DATA_DIR / "cookies"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_images_cache_dir() -> Path:
    """Get the images cache directory path, creating it if needed."""
    path = DATA_DIR / "images_cache"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_logs_dir() -> Path:
    """Get the logs directory path, creating it if needed."""
    path = DATA_DIR / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path

"""Notion API client for reading properties and updating posting status."""

from __future__ import annotations

from datetime import datetime

from notion_client import Client

from src.notion.models import Property
from src.utils.config import get_notion_config, load_settings
from src.utils.logger import get_logger

logger = get_logger()


class NotionPropertyClient:
    """Client for interacting with the Notion properties database."""

    def __init__(self):
        config = get_notion_config()
        self.client = Client(auth=config["api_key"])
        self.database_id = config["database_id"]
        self.settings = load_settings()
        self.fields = self.settings["notion_fields"]

    def get_marketing_properties(self) -> list[Property]:
        """Fetch all properties currently in marketing status (בשיווק בלעדי)."""
        try:
            results = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "סטטוס עסקה",
                    "select": {
                        "equals": "שיווק נכס",
                    },
                },
            )
            properties = []
            for page in results.get("results", []):
                prop = self._parse_property(page)
                if prop:
                    properties.append(prop)

            logger.info(f"Fetched {len(properties)} properties in marketing status")
            return properties
        except Exception as e:
            logger.error(f"Failed to fetch properties from Notion: {e}")
            raise

    def get_ready_properties(self) -> list[Property]:
        """Fetch properties with FB status = 'מוכן לפרסום'."""
        try:
            results = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": self.fields["fb_status"],
                    "select": {
                        "equals": self.settings["status_values"]["ready_to_post"],
                    },
                },
            )
            properties = []
            for page in results.get("results", []):
                prop = self._parse_property(page)
                if prop:
                    properties.append(prop)

            logger.info(f"Fetched {len(properties)} properties ready to post")
            return properties
        except Exception as e:
            logger.error(f"Failed to fetch ready properties from Notion: {e}")
            raise

    def _parse_property(self, page: dict) -> Property | None:
        """Parse a Notion page into a Property model."""
        try:
            props = page["properties"]
            page_id = page["id"]

            # Extract title (כתובת הנכס)
            address = self._get_title(props.get(self.fields["address"], {}))
            if not address:
                return None

            # Extract number fields
            price = self._get_number(props.get(self.fields["price"], {}))
            rooms = self._get_number(props.get(self.fields.get("rooms", "חדרים"), {}))
            size_sqm = self._get_number(props.get(self.fields.get("size_sqm", "שטח במ\"ר"), {}))
            floor = self._get_number(props.get(self.fields.get("floor", "קומה"), {}))

            # Extract text fields
            description = self._get_rich_text(props.get(self.fields.get("description", "תיאור נכס"), {}))

            # Extract select fields
            property_type = self._get_select(props.get(self.fields["property_type"], {}))

            # Extract URL
            property_url = self._get_url(props.get(self.fields.get("property_url", "קישור לנכס"), {}))

            # Extract FB status
            fb_status = self._get_select(props.get(self.fields.get("fb_status", "סטטוס פרסום FB"), {}))

            # Extract images from Files & Media property
            image_urls = self._get_files(props.get(self.fields.get("images", "תמונות"), {}))

            return Property(
                page_id=page_id,
                address=address,
                price=price,
                rooms=rooms,
                size_sqm=size_sqm,
                floor=floor,
                description=description,
                image_urls=image_urls,
                property_type=property_type or "דירה",
                property_url=property_url,
                fb_status=fb_status,
            )
        except Exception as e:
            logger.warning(f"Failed to parse property page {page.get('id', 'unknown')}: {e}")
            return None

    def mark_as_posted(self, page_id: str, groups: list[str]) -> None:
        """Update property status to 'פורסם' and record posted groups."""
        try:
            self.client.pages.update(
                page_id=page_id,
                properties={
                    self.fields["fb_status"]: {
                        "select": {"name": self.settings["status_values"]["posted"]},
                    },
                    self.fields["fb_date"]: {
                        "date": {"start": datetime.now().isoformat()[:10]},
                    },
                    self.fields["fb_groups"]: {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": ", ".join(groups)},
                            }
                        ],
                    },
                },
            )
            logger.info(f"Marked property {page_id} as posted to {len(groups)} groups")
        except Exception as e:
            logger.error(f"Failed to update property {page_id}: {e}")
            raise

    def mark_as_failed(self, page_id: str, error: str) -> None:
        """Update property status to 'נכשל'."""
        try:
            self.client.pages.update(
                page_id=page_id,
                properties={
                    self.fields["fb_status"]: {
                        "select": {"name": self.settings["status_values"]["failed"]},
                    },
                    self.fields["fb_groups"]: {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": f"שגיאה: {error[:200]}"},
                            }
                        ],
                    },
                },
            )
            logger.warning(f"Marked property {page_id} as failed: {error}")
        except Exception as e:
            logger.error(f"Failed to update property {page_id} as failed: {e}")

    # --- Helper methods for parsing Notion property types ---

    @staticmethod
    def _get_title(prop: dict) -> str:
        title_list = prop.get("title", [])
        if not title_list:
            return ""
        return "".join(t.get("plain_text", "") for t in title_list)

    @staticmethod
    def _get_rich_text(prop: dict) -> str:
        rt_list = prop.get("rich_text", [])
        if not rt_list:
            return ""
        return "".join(t.get("plain_text", "") for t in rt_list)

    @staticmethod
    def _get_number(prop: dict) -> float | None:
        return prop.get("number")

    @staticmethod
    def _get_select(prop: dict) -> str | None:
        select = prop.get("select")
        if select is None:
            return None
        return select.get("name")

    @staticmethod
    def _get_url(prop: dict) -> str | None:
        return prop.get("url")

    @staticmethod
    def _get_files(prop: dict) -> list[str]:
        files = prop.get("files", [])
        urls = []
        for f in files:
            if f.get("type") == "file":
                url = f.get("file", {}).get("url")
                if url:
                    urls.append(url)
            elif f.get("type") == "external":
                url = f.get("external", {}).get("url")
                if url:
                    urls.append(url)
        return urls

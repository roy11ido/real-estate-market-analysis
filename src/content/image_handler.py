"""Download, validate, and optimize property images from Notion."""

from __future__ import annotations

import hashlib
from pathlib import Path

import requests
from PIL import Image

from src.utils.config import get_images_cache_dir
from src.utils.logger import get_logger

logger = get_logger()

MAX_DIMENSION = 2048
JPEG_QUALITY = 80
MAX_FILE_SIZE_MB = 4


def download_property_images(
    page_id: str, image_urls: list[str], max_images: int = 6
) -> list[Path]:
    """Download and optimize images for a property.

    Args:
        page_id: Notion page ID for cache directory naming.
        image_urls: List of image URLs from Notion.
        max_images: Maximum number of images to download.

    Returns:
        List of local file paths to optimized images.
    """
    if not image_urls:
        return []

    # Create cache directory for this property
    cache_dir = get_images_cache_dir() / page_id.replace("-", "")
    cache_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    for i, url in enumerate(image_urls[:max_images]):
        try:
            local_path = _download_and_optimize(url, cache_dir, i + 1)
            if local_path:
                downloaded.append(local_path)
        except Exception as e:
            logger.warning(f"Failed to download image {i + 1} for {page_id}: {e}")

    logger.info(f"Downloaded {len(downloaded)}/{len(image_urls)} images for {page_id}")
    return downloaded


def _download_and_optimize(url: str, cache_dir: Path, index: int) -> Path | None:
    """Download a single image, validate and optimize it."""
    # Generate filename based on URL hash to avoid re-downloading
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    output_path = cache_dir / f"{index:02d}_{url_hash}.jpg"

    # Skip if already cached
    if output_path.exists():
        logger.debug(f"Image already cached: {output_path}")
        return output_path

    # Download
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Save raw file temporarily
    raw_path = cache_dir / f"raw_{index:02d}.tmp"
    raw_path.write_bytes(response.content)

    try:
        # Open and validate
        img = Image.open(raw_path)

        # Check minimum resolution
        if img.width < 200 or img.height < 200:
            logger.warning(f"Image too small ({img.width}x{img.height}), skipping")
            raw_path.unlink(missing_ok=True)
            return None

        # Convert to RGB (strip alpha channel)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Resize if too large
        if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

        # Strip EXIF metadata for privacy
        clean_img = Image.new(img.mode, img.size)
        clean_img.putdata(list(img.getdata()))

        # Save as optimized JPEG
        clean_img.save(output_path, "JPEG", quality=JPEG_QUALITY, optimize=True)

        # Check file size
        file_size_mb = output_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            # Re-save with lower quality
            clean_img.save(output_path, "JPEG", quality=60, optimize=True)

        logger.debug(f"Optimized image saved: {output_path}")
        return output_path

    finally:
        raw_path.unlink(missing_ok=True)


def cleanup_old_cache(max_age_days: int = 7) -> None:
    """Remove cached images older than max_age_days."""
    import time

    cache_dir = get_images_cache_dir()
    if not cache_dir.exists():
        return

    now = time.time()
    max_age_seconds = max_age_days * 86400

    for subdir in cache_dir.iterdir():
        if subdir.is_dir():
            # Check if all files in the directory are old
            all_old = True
            for f in subdir.iterdir():
                if now - f.stat().st_mtime < max_age_seconds:
                    all_old = False
                    break

            if all_old and any(subdir.iterdir()):
                import shutil
                shutil.rmtree(subdir)
                logger.debug(f"Cleaned up old cache: {subdir}")

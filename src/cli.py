"""CLI interface for manual operations: login, test posting, session check."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.facebook.session import login_interactive, has_saved_session
from src.facebook.browser import create_browser_context
from src.facebook.session import verify_session
from src.main import fetch_properties_for_gui, run_posting
from src.utils.logger import get_logger

logger = get_logger()


def cmd_login():
    """Interactive Facebook login."""
    print("\n=== Facebook Login ===")
    print("A browser window will open. Log into your Facebook account.")
    print("After login, press Enter in this terminal to save the session.\n")
    asyncio.run(login_interactive())


def cmd_check_session():
    """Check if the Facebook session is valid."""
    print("\n=== Session Check ===")

    async def check():
        if not await has_saved_session():
            print("No saved session found. Run 'login' first.")
            return

        browser, context = await create_browser_context()
        try:
            valid = await verify_session(context)
            if valid:
                print("Session is VALID")
            else:
                print("Session is EXPIRED or INVALID. Run 'login' to re-authenticate.")
        finally:
            await context.close()
            await browser.close()

    asyncio.run(check())


def cmd_check_notion():
    """Check Notion connection and list properties."""
    print("\n=== Notion Check ===")
    try:
        properties = fetch_properties_for_gui()
        print(f"Found {len(properties)} properties in marketing status:\n")
        for i, p in enumerate(properties, 1):
            print(f"  {i}. {p.display_summary}")
            if p.description:
                print(f"     תיאור: {p.description[:80]}...")
            print(f"     תמונות: {len(p.image_urls)}")
            print()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure your NOTION_API_KEY is set correctly in .env")


def cmd_dry_run():
    """Generate posts without actually posting (dry run)."""
    print("\n=== Dry Run ===")
    properties = fetch_properties_for_gui()
    if not properties:
        print("No properties found.")
        return

    asyncio.run(run_posting(properties, progress_callback=print, dry_run=True))


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/cli.py <command>")
        print("")
        print("Commands:")
        print("  login           - Log into Facebook (opens browser)")
        print("  check-session   - Check if Facebook session is valid")
        print("  check-notion    - Check Notion connection and list properties")
        print("  dry-run         - Generate posts without posting")
        return

    command = sys.argv[1]
    commands = {
        "login": cmd_login,
        "check-session": cmd_check_session,
        "check-notion": cmd_check_notion,
        "dry-run": cmd_dry_run,
    }

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(commands.keys())}")


if __name__ == "__main__":
    main()

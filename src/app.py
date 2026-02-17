"""Streamlit GUI for the Real Estate Facebook Poster."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from src.main import fetch_properties_for_gui, run_posting
from src.content.generator import generate_post_preview
from src.facebook.session import has_saved_session
from src.utils.config import load_facebook_groups

# --- Page Configuration ---
st.set_page_config(
    page_title="Real Estate FB Poster",
    page_icon="🏠",
    layout="wide",
)

# --- Custom CSS for RTL support ---
st.markdown(
    """
    <style>
    .rtl-text {
        direction: rtl;
        text-align: right;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .property-card {
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #ddd;
        margin-bottom: 0.5rem;
        direction: rtl;
    }
    .success-log {
        color: #28a745;
    }
    .error-log {
        color: #dc3545;
    }
    .stButton > button {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def main():
    st.title("🏠 מפרסם נכסים לפייסבוק")
    st.markdown("**Real Capital** | רוי עידו")
    st.divider()

    # --- Sidebar: Session & Settings ---
    with st.sidebar:
        st.header("הגדרות")

        # Session status
        session_exists = asyncio.run(has_saved_session())
        if session_exists:
            st.success("✅ מחובר לפייסבוק")
        else:
            st.error("❌ לא מחובר לפייסבוק")
            st.info("הרץ בטרמינל:\n```\npython src/cli.py login\n```")

        st.divider()

        # Groups info
        groups = load_facebook_groups()
        st.metric("קבוצות פעילות", len(groups))
        if groups:
            with st.expander("רשימת קבוצות"):
                for g in groups:
                    st.write(f"• {g['name']}")
        else:
            st.warning("לא הוגדרו קבוצות. ערוך את:\n`config/facebook_groups.yaml`")

        st.divider()
        if st.button("🔄 רענן נתונים"):
            st.cache_data.clear()
            st.rerun()

    # --- Main Content ---

    # Fetch properties
    try:
        properties = fetch_properties_for_gui()
    except Exception as e:
        st.error(f"שגיאה בחיבור ל-Notion: {e}")
        st.info("ודא שה-NOTION_API_KEY ב-.env תקין")
        return

    if not properties:
        st.info("אין נכסים בסטטוס שיווק. הוסף נכסים ל-Notion עם סטטוס עסקה = 'שיווק נכס'")
        return

    st.subheader(f"📋 נכסים בשיווק ({len(properties)})")

    # --- Select All / Clear All buttons ---
    col1, col2, col3 = st.columns([1, 1, 4])

    # Initialize selection state
    if "select_all" not in st.session_state:
        st.session_state.select_all = False

    with col1:
        if st.button("✅ סמן הכל"):
            st.session_state.select_all = True
            st.rerun()
    with col2:
        if st.button("❎ נקה הכל"):
            st.session_state.select_all = False
            st.rerun()

    st.divider()

    # --- Property Checkboxes ---
    selected_properties = []

    for i, prop in enumerate(properties):
        col_check, col_info, col_preview = st.columns([0.5, 3, 2])

        with col_check:
            checked = st.checkbox(
                label=f"select_{i}",
                value=st.session_state.select_all,
                key=f"prop_{i}",
                label_visibility="collapsed",
            )
            if checked:
                selected_properties.append(prop)

        with col_info:
            # Property info
            price_str = prop.formatted_price if prop.price else "לא צוין"
            rooms_str = f"{prop.rooms} חד'" if prop.rooms else ""
            size_str = f"{int(prop.size_sqm)} מ\"ר" if prop.size_sqm else ""
            type_str = prop.property_type or ""

            details = " | ".join(filter(None, [type_str, rooms_str, size_str, price_str]))

            st.markdown(f"**{prop.emoji} {prop.address}**")
            st.caption(details)

            if prop.description:
                desc_preview = prop.description[:100] + ("..." if len(prop.description) > 100 else "")
                st.caption(f"📝 {desc_preview}")

            images_count = len(prop.image_urls)
            if images_count:
                st.caption(f"📸 {images_count} תמונות")
            else:
                st.caption("⚠️ אין תמונות")

        with col_preview:
            with st.expander("👁️ תצוגה מקדימה"):
                preview = generate_post_preview(prop)
                st.text(preview)

        st.divider()

    # --- Post Button ---
    st.markdown("---")

    col_btn, col_info = st.columns([2, 3])

    with col_btn:
        selected_count = len(selected_properties)
        groups_count = len(groups)
        total_posts = selected_count * groups_count

        btn_label = f"🚀 פרסם {selected_count} נכסים ב-{groups_count} קבוצות"

        can_post = selected_count > 0 and groups_count > 0 and session_exists
        post_clicked = st.button(
            btn_label,
            type="primary",
            disabled=not can_post,
            use_container_width=True,
        )

    with col_info:
        if selected_count == 0:
            st.warning("בחר לפחות נכס אחד")
        elif not groups_count:
            st.warning("הגדר קבוצות בקובץ facebook_groups.yaml")
        elif not session_exists:
            st.warning("התחבר לפייסבוק קודם")
        else:
            st.info(f"סה\"כ {total_posts} פוסטים יפורסמו")

    # --- Posting Execution ---
    if post_clicked:
        st.markdown("---")
        st.subheader("📡 מפרסם...")

        # Progress container
        progress_bar = st.progress(0)
        log_container = st.container()
        log_messages = []

        def progress_callback(message: str):
            log_messages.append(message)
            # Update progress bar estimate
            progress = min(len(log_messages) / max(total_posts * 3, 1), 0.99)
            progress_bar.progress(progress)
            with log_container:
                if "Successfully" in message or "הצליח" in message or "✅" in message:
                    st.success(message)
                elif "Error" in message or "Failed" in message or "שגיאה" in message or "נכשל" in message:
                    st.error(message)
                else:
                    st.info(message)

        # Run the posting
        try:
            result = asyncio.run(
                run_posting(
                    selected_properties=selected_properties,
                    progress_callback=progress_callback,
                )
            )

            progress_bar.progress(1.0)

            # Show summary
            st.markdown("---")
            st.subheader("📊 סיכום")

            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.metric("נכסים", result.total_properties)
            with col_s2:
                st.metric("פוסטים שהצליחו", result.successful_posts)
            with col_s3:
                failed = result.total_posts - result.successful_posts
                st.metric("פוסטים שנכשלו", failed)

            if result.errors:
                st.error("שגיאות:")
                for err in result.errors:
                    st.write(f"• {err}")

            # Detailed results per property
            for prop_result in result.property_results:
                with st.expander(f"{prop_result.property_address} ({prop_result.success_count}/{prop_result.total_count})"):
                    for gr in prop_result.group_results:
                        if gr.success:
                            st.success(f"✅ {gr.group_name}")
                        else:
                            st.error(f"❌ {gr.group_name}: {gr.error}")

        except Exception as e:
            st.error(f"שגיאה בריצה: {e}")
            logger_import = get_logger()
            logger_import.error(f"Run failed: {e}", exc_info=True)


if __name__ == "__main__":
    from src.utils.logger import get_logger
    main()

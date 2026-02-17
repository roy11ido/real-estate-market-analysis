"""
רכיב השלמה אוטומטית של כתובות בעברית — Google Places API.

שימוש:
    result = address_autocomplete_widget(api_key=GOOGLE_API_KEY)
    if result:
        st.session_state["address"] = result["formatted_address"]
        st.session_state["lat"] = result["lat"]
        st.session_state["lng"] = result["lng"]
"""
from __future__ import annotations

import os
import streamlit as st
import streamlit.components.v1 as components


def _get_api_key() -> str:
    """קרא את מפתח ה-API בזמן ריצה (לא בטעינת המודול)."""
    key = os.environ.get("GOOGLE_PLACES_API_KEY", "")
    if not key:
        try:
            key = st.secrets.get("GOOGLE_PLACES_API_KEY", "")
        except Exception:
            pass
    return key


def address_autocomplete_widget(
    placeholder: str = "הקלד כתובת...",
    height: int = 56,
    key: str = "places_autocomplete",
) -> dict | None:
    """
    מרכיב HTML/JS המבצע השלמה אוטומטית של כתובות דרך Google Places.

    מחזיר:
        dict עם המפתחות:
            formatted_address, street, city, neighborhood,
            postal_code, lat, lng
        או None אם המשתמש עוד לא בחר כתובת.
    """
    api_key = _get_api_key()

    if not api_key:
        # Graceful fallback — שדה טקסט רגיל עם הסבר בעברית
        st.warning("⚠️ מפתח Google Places API לא הוגדר — הקלד כתובת ידנית.")
        val = st.text_input(
            "כתובת הנכס",
            placeholder="לדוגמה: הרצל 15, תל אביב",
            label_visibility="collapsed",
            key=f"{key}_fallback",
        )
        if val:
            return {"formatted_address": val, "street": "", "city": "",
                    "neighborhood": "", "postal_code": "", "lat": None, "lng": None}
        return None

    # ── HTML + JS component ──────────────────────────────────────────────────
    component_html = f"""
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
<meta charset="UTF-8"/>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Heebo', Arial, sans-serif; background: transparent; direction: rtl; }}

  #wrapper {{
    position: relative;
    width: 100%;
  }}

  #address-input {{
    width: 100%;
    height: {height}px;
    padding: 0 1rem;
    font-size: 0.95rem;
    font-family: inherit;
    color: #0B1F3B;
    background: #FFFFFF;
    border: 1.5px solid #D1D9E0;
    border-radius: 10px;
    outline: none;
    direction: rtl;
    text-align: right;
    transition: border-color 0.15s, box-shadow 0.15s;
  }}
  #address-input::placeholder {{ color: #9AABBF; }}
  #address-input:focus {{
    border-color: #1C3F94;
    box-shadow: 0 0 0 3px rgba(28,63,148,0.15);
  }}
  #address-input.loading {{
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24'%3E%3Ccircle cx='12' cy='12' r='10' stroke='%231C3F94' stroke-width='2' fill='none' stroke-dasharray='60' stroke-dashoffset='20'%3E%3CanimateTransform attributeName='transform' type='rotate' from='0 12 12' to='360 12 12' dur='0.8s' repeatCount='indefinite'/%3E%3C/circle%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: left 12px center;
    padding-left: 40px;
  }}

  #suggestions {{
    position: absolute;
    top: calc({height}px + 4px);
    right: 0;
    left: 0;
    background: #FFFFFF;
    border: 1px solid #D1D9E0;
    border-radius: 10px;
    box-shadow: 0 8px 24px rgba(11,31,59,0.12);
    z-index: 9999;
    max-height: 260px;
    overflow-y: auto;
    display: none;
    direction: rtl;
  }}
  #suggestions.visible {{ display: block; }}

  .suggestion-item {{
    padding: 0.75rem 1rem;
    cursor: pointer;
    font-size: 0.875rem;
    color: #0B1F3B;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    border-bottom: 1px solid #F0F3F7;
    transition: background 0.1s;
    direction: rtl;
    text-align: right;
  }}
  .suggestion-item:last-child {{ border-bottom: none; }}
  .suggestion-item:hover,
  .suggestion-item.focused {{
    background: #EEF2F8;
  }}
  .suggestion-icon {{
    color: #4A90D9;
    font-size: 1rem;
    flex-shrink: 0;
  }}
  .suggestion-main {{ font-weight: 600; color: #0B1F3B; }}
  .suggestion-secondary {{ color: #6B7A8D; font-size: 0.78rem; margin-top: 1px; }}

  #error-msg {{
    display: none;
    color: #D32F2F;
    font-size: 0.78rem;
    margin-top: 4px;
    padding-right: 4px;
    direction: rtl;
  }}
  #error-msg.visible {{ display: block; }}
</style>
</head>
<body>
<div id="wrapper">
  <input
    id="address-input"
    type="text"
    placeholder="{placeholder}"
    autocomplete="off"
    aria-label="הזנת כתובת עם השלמה אוטומטית"
    aria-autocomplete="list"
    aria-controls="suggestions"
    aria-haspopup="listbox"
    role="combobox"
  />
  <div id="suggestions" role="listbox" aria-label="הצעות כתובת"></div>
  <div id="error-msg" role="alert"></div>
</div>

<script>
(function() {{
  const input   = document.getElementById('address-input');
  const sugBox  = document.getElementById('suggestions');
  const errMsg  = document.getElementById('error-msg');

  let debounceTimer   = null;
  let focusedIndex    = -1;
  let currentItems    = [];
  let sessionToken    = null;
  let autocompleteService = null;
  let placesService   = null;
  let googleReady     = false;

  // ── Google Maps SDK callback ──────────────────────────────────────────────
  window.initPlaces = function() {{
    autocompleteService = new google.maps.places.AutocompleteService();
    // PlacesService דורש אלמנט DOM
    const dummyMap = document.createElement('div');
    placesService  = new google.maps.places.PlacesService(dummyMap);
    sessionToken   = new google.maps.places.AutocompleteSessionToken();
    googleReady    = true;
  }};

  // ── הצגת שגיאה ───────────────────────────────────────────────────────────
  function showError(msg) {{
    errMsg.textContent = msg;
    errMsg.classList.add('visible');
    setTimeout(() => errMsg.classList.remove('visible'), 4000);
  }}

  // ── ביטול ──────────────────────────────────────────────────────────────────
  function clearSuggestions() {{
    sugBox.innerHTML = '';
    sugBox.classList.remove('visible');
    currentItems   = [];
    focusedIndex   = -1;
  }}

  // ── ניווט מקלדת ──────────────────────────────────────────────────────────
  input.addEventListener('keydown', (e) => {{
    if (!sugBox.classList.contains('visible')) return;
    switch(e.key) {{
      case 'ArrowDown':
        e.preventDefault();
        focusedIndex = (focusedIndex + 1) % currentItems.length;
        updateFocus();
        break;
      case 'ArrowUp':
        e.preventDefault();
        focusedIndex = (focusedIndex - 1 + currentItems.length) % currentItems.length;
        updateFocus();
        break;
      case 'Enter':
        e.preventDefault();
        if (focusedIndex >= 0) selectPlace(currentItems[focusedIndex]);
        break;
      case 'Escape':
        clearSuggestions();
        break;
    }}
  }});

  function updateFocus() {{
    const items = sugBox.querySelectorAll('.suggestion-item');
    items.forEach((el, i) => {{
      if (i === focusedIndex) {{
        el.classList.add('focused');
        el.setAttribute('aria-selected', 'true');
        el.scrollIntoView({{ block: 'nearest' }});
      }} else {{
        el.classList.remove('focused');
        el.removeAttribute('aria-selected');
      }}
    }});
  }}

  // ── Debounced קריאה ל-API ─────────────────────────────────────────────────
  input.addEventListener('input', () => {{
    const q = input.value.trim();
    if (!q || q.length < 2) {{ clearSuggestions(); return; }}
    input.classList.add('loading');
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => fetchSuggestions(q), 300);
  }});

  function fetchSuggestions(query) {{
    if (!googleReady) {{
      input.classList.remove('loading');
      return;
    }}
    autocompleteService.getPlacePredictions(
      {{
        input: query,
        sessionToken: sessionToken,
        componentRestrictions: {{ country: 'il' }},
        language: 'he',
        types: ['address'],
      }},
      (predictions, status) => {{
        input.classList.remove('loading');
        if (status !== google.maps.places.PlacesServiceStatus.OK || !predictions) {{
          if (status === google.maps.places.PlacesServiceStatus.ZERO_RESULTS) {{
            clearSuggestions();
          }} else {{
            showError('שגיאה בטעינת הכתובות. נסה שוב.');
            clearSuggestions();
          }}
          return;
        }}
        renderSuggestions(predictions);
      }}
    );
  }}

  // ── רינדור הצעות ──────────────────────────────────────────────────────────
  function renderSuggestions(predictions) {{
    currentItems = predictions;
    sugBox.innerHTML = '';
    focusedIndex = -1;

    predictions.forEach((pred, idx) => {{
      const item = document.createElement('div');
      item.className = 'suggestion-item';
      item.setAttribute('role', 'option');
      item.setAttribute('id', `suggestion-${{idx}}`);

      const parts   = pred.structured_formatting;
      const main    = parts ? parts.main_text   : pred.description;
      const second  = parts ? parts.secondary_text : '';

      item.innerHTML = `
        <span class="suggestion-icon">📍</span>
        <div>
          <div class="suggestion-main">${{main}}</div>
          ${{second ? `<div class="suggestion-secondary">${{second}}</div>` : ''}}
        </div>
      `;

      item.addEventListener('mousedown', (e) => {{
        e.preventDefault();  // prevent input blur before click
        selectPlace(pred);
      }});
      item.addEventListener('mouseover', () => {{
        focusedIndex = idx;
        updateFocus();
      }});

      sugBox.appendChild(item);
    }});
    sugBox.classList.add('visible');
  }}

  // ── בחירת כתובת → Place Details ─────────────────────────────────────────
  function selectPlace(prediction) {{
    input.value = prediction.description;
    clearSuggestions();
    input.classList.add('loading');

    placesService.getDetails(
      {{
        placeId: prediction.place_id,
        sessionToken: sessionToken,
        fields: ['address_components', 'formatted_address', 'geometry', 'name'],
        language: 'he',
      }},
      (place, status) => {{
        input.classList.remove('loading');
        // חדש sessionToken אחרי כל בחירה
        sessionToken = new google.maps.places.AutocompleteSessionToken();

        if (status !== google.maps.places.PlacesServiceStatus.OK || !place) {{
          showError('לא ניתן לטעון פרטי כתובת. נסה שנית.');
          return;
        }}

        const result = parsePlace(place);
        // שלח תוצאה ל-Streamlit דרך postMessage
        window.parent.postMessage({{
          type: 'places_result',
          key: '{key}',
          data: result,
        }}, '*');
      }}
    );
  }}

  // ── פירוש רכיבי כתובת ────────────────────────────────────────────────────
  function parsePlace(place) {{
    const comps = place.address_components || [];
    const get   = (type) => (comps.find(c => c.types.includes(type)) || {{}}).long_name || '';

    return {{
      formatted_address: place.formatted_address || input.value,
      street:            (get('route') + ' ' + get('street_number')).trim(),
      city:              get('locality') || get('administrative_area_level_2'),
      neighborhood:      get('sublocality_level_1') || get('neighborhood') || get('sublocality'),
      postal_code:       get('postal_code'),
      lat:               place.geometry ? place.geometry.location.lat() : null,
      lng:               place.geometry ? place.geometry.location.lng() : null,
    }};
  }}

  // ── סגירה בלחיצה מחוץ ────────────────────────────────────────────────────
  document.addEventListener('click', (e) => {{
    if (!e.target.closest('#wrapper')) clearSuggestions();
  }});

  // ── טעינת Google Maps SDK ─────────────────────────────────────────────────
  const script = document.createElement('script');
  script.src = 'https://maps.googleapis.com/maps/api/js?key={api_key}&libraries=places&language=he&callback=initPlaces&loading=async';
  script.async = true;
  script.defer = true;
  script.onerror = () => showError('לא ניתן לטעון את שירות הכתובות. בדוק חיבור לאינטרנט.');
  document.head.appendChild(script);
}})();
</script>
</body>
</html>
"""

    # הצג את ה-component ואסוף את ה-postMessage דרך session_state bridge
    result_key = f"_places_result_{key}"

    # JavaScript לקבלת postMessage
    listener_html = f"""
<script>
window.addEventListener('message', function(event) {{
    if (event.data && event.data.type === 'places_result' && event.data.key === '{key}') {{
        // שלח ל-Streamlit
        window.parent.postMessage({{
            type: 'streamlit:setComponentValue',
            args: {{ value: event.data.data }}
        }}, '*');
    }}
}});
</script>
"""

    # הצג רכיב
    result = components.html(
        component_html,
        height=height + 8,
        scrolling=False,
    )

    return result


def address_input_with_autocomplete(key_prefix: str = "addr") -> dict | None:
    """
    ממשק מלא: widget השלמה + מציג הכתובת שנבחרה בתוך Streamlit session_state.

    מחזיר את ה-dict של הכתובת או None.
    """
    api_key = _get_api_key()

    if not api_key:
        # fallback: שדה טקסט רגיל
        st.caption("💡 להפעלת השלמה אוטומטית, הגדר GOOGLE_PLACES_API_KEY")
        val = st.text_input(
            "כתובת הנכס",
            placeholder="לדוגמה: הרצל 15, תל אביב",
            label_visibility="collapsed",
            key=f"{key_prefix}_text",
        )
        if val:
            return {"formatted_address": val, "street": "", "city": "",
                    "neighborhood": "", "postal_code": "", "lat": None, "lng": None}
        return None

    # ── אתחול session state ────────────────────────────────────────────────
    sk = f"{key_prefix}_selected"
    if sk not in st.session_state:
        st.session_state[sk] = None

    # ── הצג את ה-HTML component ────────────────────────────────────────────
    component_result = address_autocomplete_widget(
        placeholder="הקלד כתובת...",
        height=48,
        key=key_prefix,
    )

    # ── עדכן session state אם קיבלנו תוצאה ───────────────────────────────
    if component_result:
        st.session_state[sk] = component_result

    # ── הצג כתובת שנבחרה ─────────────────────────────────────────────────
    selected = st.session_state.get(sk)
    if selected:
        st.markdown(
            f"""<div style="background:#EEF6EE;border:1px solid #2E7D32;border-radius:8px;
                padding:0.5rem 0.75rem;margin-top:0.25rem;direction:rtl;font-size:0.85rem;color:#1B5E20;">
                ✅ {selected.get('formatted_address','')}
                {' | ' + selected['city'] if selected.get('city') else ''}
            </div>""",
            unsafe_allow_html=True,
        )
        return selected

    return None

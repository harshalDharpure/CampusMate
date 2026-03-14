"""
CampusMate – Smart Navigation System for College Campuses (Frontend)
Software-only. Map-first, phone-friendly: search "library" → get directions like Google Maps.
Run from project root: python -m streamlit run frontend/app.py
"""
import os
import sys

# Allow importing backend when running from project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

from backend.database import (
    get_connection,
    get_buildings,
    get_facilities,
    search_faculty,
    get_facility_by_id,
    get_all_facilities_flat,
    add_building,
    add_facility,
    update_facility,
    delete_facility,
    create_booking,
    get_bookings_for_facility,
    get_booked_facility_ids_for_slot,
    get_all_bookings,
    ensure_bookings_table,
    DB_PATH,
)
from backend.config import ADMIN_PIN, CAMPUS_ENTRANCES, CAMPUS_CENTER

# Ensure DB exists (create and seed if not)
if not os.path.exists(DB_PATH):
    from backend import init_db
    init_db.main()

# Page config – mobile-friendly, map-first
st.set_page_config(
    page_title="CampusMate – PR Pote Patil College, Amravati",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session state for map focus (search result → center map & show directions)
if "map_focus" not in st.session_state:
    st.session_state.map_focus = None
# Start location for in-app route (no Google Maps – route drawn on our map)
if "start_from" not in st.session_state:
    st.session_state.start_from = None  # {"name": str, "lat": float, "lng": float}
# Floor filter for map (MazeMap-style: view one floor at a time)
if "selected_floor" not in st.session_state:
    st.session_state.selected_floor = None  # None = all floors, 0 = Ground, 1 = Floor 1, etc.
# Live location: show browser location-request UI
if "show_location_request" not in st.session_state:
    st.session_state.show_location_request = False

# High-contrast mode
if "high_contrast" not in st.session_state:
    st.session_state.high_contrast = False

FACILITY_COLORS = {"lab": "green", "classroom": "blue", "office": "orange", "library": "purple"}

def apply_theme():
    if st.session_state.high_contrast:
        st.markdown("""
        <style>
        .stApp { background-color: #0d0d0d; }
        .block-container { background-color: #0d0d0d; }
        h1, h2, h3, p, .stMarkdown { color: #ffff00 !important; }
        .stSelectbox label, .stTextInput label { color: #ffff00 !important; }
        div[data-testid="stSidebar"] { background-color: #1a1a1a; }
        div[data-testid="stSidebar"] .stMarkdown { color: #ffff00 !important; }
        </style>
        """, unsafe_allow_html=True)
    # Hide Streamlit deploy/toolbar buttons and fix layout
    st.markdown("""
    <style>
    /* Hide deploy and manage app buttons */
    [data-testid="stToolbar"], .stDeployButton, [data-testid="stDecoration"], iframe[title="streamlit_toolbar"] { display: none !important; }
    /* Clean main area – no cut-off, consistent padding */
    .block-container { padding-top: 0.75rem; padding-bottom: 1rem; max-width: 100%%; }
    .stMarkdown { margin-bottom: 0.25rem; }
    /* Compact spacing for map page */
    section[data-testid="stVerticalBlock"] > div { gap: 0.5rem; }
    @media (max-width: 768px) {
        .stButton button { min-height: 44px; padding: 12px 16px; }
        input[type="text"] { min-height: 44px; font-size: 16px; }
    }
    .dir-card { background: #e8f4f8; border-left: 4px solid #1e88e5; padding: 1rem 1.25rem; border-radius: 8px; margin: 0.5rem 0; }
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# Sidebar
with st.sidebar:
    st.title("CampusMate")
    st.caption("Indoor campus navigation – like MazeMap")
    st.caption("PR Pote Patil College of Engineering and Management, Amravati")
    st.session_state.high_contrast = st.toggle("High contrast", value=st.session_state.high_contrast)
    apply_theme()
    st.markdown("---")
    st.markdown("**How it works**")
    st.caption("Your **college admin** adds the campus once (buildings + rooms) in **Admin**. **You** search, get directions, and **book spaces**.")
    with st.expander("**Why campus navigation?**"):
        st.markdown("""
        Finding your way around campus can be a challenge, especially for **new students or visitors**. CampusMate helps with **indoor wayfinding** so you can reach rooms, labs, and the library without stress.

        **Improve student experience**  
        Digital campus wayfinding reduces stress and uncertainty for staff, students, and visitors—and helps reduce lateness or missed classes. It’s also useful for **open days**, showing potential students that settling into campus life is easy.

        **Collaborate better**  
        With **space booking**, students and staff can reserve rooms, lecture halls, or study areas. You can see **available spaces** on the map and find free rooms at a glance, or the closest free room to your current location.
        """)
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["Campus Map", "Book a space", "Search", "Accessibility", "Admin"],
        label_visibility="collapsed"
    )

conn = get_connection()

# ----- Campus Map (MazeMap-style: indoor navigation, floor maps, turn-by-turn) -----
if page == "Campus Map":
    # ----- Live location from browser GPS (e.g. IIT Patna hostel → library) -----
    try:
        qp = st.query_params
        lat_param = qp.get("lat")
        lng_param = qp.get("lng")
        if lat_param is not None and lng_param is not None:
            try:
                lat_val = float(lat_param)
                lng_val = float(lng_param)
                st.session_state.start_from = {
                    "name": "My live location (GPS)",
                    "lat": lat_val,
                    "lng": lng_val,
                }
                st.session_state.show_location_request = False
            except (ValueError, TypeError):
                pass
    except Exception:
        pass

    buildings = get_buildings(conn)
    facilities_all = get_all_facilities_flat(conn)
    focus = st.session_state.map_focus
    start_from = st.session_state.start_from
    selected_floor = st.session_state.selected_floor

    # Filter facilities by selected floor for map and list
    if selected_floor is not None:
        facilities = [f for f in facilities_all if f[4] == selected_floor]  # f[4] = floor
    else:
        facilities = facilities_all

    # ----- MAP FIRST (so it’s visible without scrolling) -----
    if not buildings:
        st.info("No buildings in database. Add them in Admin.")
    else:
        start_from_map = st.session_state.start_from
        focus_map = st.session_state.map_focus
        if focus_map and start_from_map:
            lat0 = (start_from_map["lat"] + focus_map["lat"]) / 2
            lng0 = (start_from_map["lng"] + focus_map["lng"]) / 2
            zoom = 17
        elif focus_map:
            lat0, lng0 = focus_map["lat"], focus_map["lng"]
            zoom = 18
        else:
            lat0, lng0 = buildings[0][2], buildings[0][3]
            zoom = 17
        m = folium.Map(location=[lat0, lng0], zoom_start=zoom, tiles="OpenStreetMap")
        if focus_map and start_from_map:
            route_points = [[start_from_map["lat"], start_from_map["lng"]], [CAMPUS_CENTER["lat"], CAMPUS_CENTER["lng"]], [focus_map["lat"], focus_map["lng"]]]
            folium.PolyLine(locations=route_points, color="#1e88e5", weight=5, opacity=0.8, popup="Walking route").add_to(m)
            folium.Marker([start_from_map["lat"], start_from_map["lng"]], popup=folium.Popup(f"<b>You are here</b><br>{start_from_map['name']}", max_width=200), tooltip="You are here", icon=folium.Icon(color="green", icon="user")).add_to(m)
            folium.Circle(location=[start_from_map["lat"], start_from_map["lng"]], radius=25, color="green", fill=True, fill_color="green", fill_opacity=0.15, weight=2, dash_array="5, 5").add_to(m)
            all_lats = [start_from_map["lat"], CAMPUS_CENTER["lat"], focus_map["lat"]]
            all_lngs = [start_from_map["lng"], CAMPUS_CENTER["lng"], focus_map["lng"]]
            m.fit_bounds([[min(all_lats), min(all_lngs)], [max(all_lats), max(all_lngs)]], padding=(30, 30))
        campus_title_html = """
        <div style="position:fixed; top:10px; left:50%; transform:translateX(-50%); z-index:9999;
                    background:white; padding:10px 16px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.2);
                    font-size:14px; font-weight:bold; text-align:center;">
        PR Pote Patil College of Engineering and Management, Amravati<br>
        <span style="font-size:11px; font-weight:normal;">Pote Estate, Kathora Road, Amravati – 444602</span>
        </div>
        """
        m.get_root().html.add_child(folium.Element(campus_title_html))
        legend_html = """
        <div style="position:fixed; bottom:30px; left:10px; z-index:9999; background:white; padding:8px 12px; border-radius:6px; box-shadow:0 2px 6px rgba(0,0,0,0.2); font-size:12px;">
        <b>Lab</b> <span style="color:green">●</span> &nbsp;
        <b>Classroom</b> <span style="color:blue">●</span> &nbsp;
        <b>Office</b> <span style="color:orange">●</span> &nbsp;
        <b>Library</b> <span style="color:purple">●</span>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))
        for b in buildings:
            bid, name, lat, lng, desc = b
            folium.Marker([lat, lng], popup=folium.Popup(f"<b>{name}</b><br>{desc or ''}", max_width=220), tooltip=name, icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
        for f in facilities:
            fid, fname, room, ftype, floor, desc, bid, bname, lat, lng = f
            color = FACILITY_COLORS.get(ftype, "blue")
            popup_html = f"<b>{fname}</b> (Room {room})<br>{ftype}<br>Floor {floor}<br>{bname}"
            folium.CircleMarker([lat, lng], radius=8, popup=folium.Popup(popup_html, max_width=220), tooltip=f"{fname} – {room}", color=color, fill=True, fillColor=color).add_to(m)
        map_key = f"map_{start_from_map.get('lat') if start_from_map else 's'}_{focus_map.get('lat') if focus_map else 'f'}"
        st_folium(m, use_container_width=True, height=420, key=map_key)
    st.markdown("---")

    # ----- Step 1: One button – Show my live location -----
    st.markdown("**1. Set your current location**")
    loc_col1, loc_col2 = st.columns([1, 2])
    with loc_col1:
        if st.button("📍 Show my live location", key="btn_use_live_loc", type="primary"):
            st.session_state.show_location_request = True
            st.rerun()
    with loc_col2:
        if start_from:
            st.caption(f"📍 **{start_from.get('name', 'Your location')}**")
        else:
            st.caption("Tap the button to use GPS, or pick a place below.")
    if st.session_state.get("show_location_request"):
        st.caption("Allow location in the browser when prompted – the page will refresh with your position.")
        geo_html = """<script>(function(){if(!navigator.geolocation){return;}navigator.geolocation.getCurrentPosition(function(pos){var u=window.location.origin+window.location.pathname+'?lat='+pos.coords.latitude+'&lng='+pos.coords.longitude;window.location.href=u;},function(){},{enableHighAccuracy:true,timeout:10000});})();</script><p style="padding:8px;">Getting location…</p>"""
        st.components.v1.html(geo_html, height=50)
    # Fallback: pick from list if not using GPS
    start_options = [e["name"] for e in CAMPUS_ENTRANCES] + [b[1] for b in buildings]
    if start_from and start_from.get("name") == "My live location (GPS)":
        start_options = ["My live location (GPS)"] + [x for x in start_options if x != "My live location (GPS)"]
    start_choice = st.selectbox("Or pick a place instead", start_options, key="start_choice", label_visibility="collapsed")
    if start_choice != "My live location (GPS)" or not (start_from and start_from.get("name") == "My live location (GPS)"):
        start_from = None
        for e in CAMPUS_ENTRANCES:
            if e["name"] == start_choice:
                start_from = e
                break
        if start_from is None:
            for b in buildings:
                if b[1] == start_choice:
                    start_from = {"name": b[1], "lat": b[2], "lng": b[3]}
                    break
        st.session_state.start_from = start_from

    st.markdown("**2. Where do you want to go?**")
    search_map = st.text_input("Search", placeholder="e.g. library, lab, room number...", key="map_search", label_visibility="collapsed")
    chip_cols = st.columns(4)
    for i, q in enumerate(["Library", "Lab", "Office", "Classroom"]):
        with chip_cols[i]:
            if st.button(f"📌 {q}", key=f"chip_{q}"):
                rows = get_facilities(conn, search=q, facility_type=None) or get_facilities(conn, facility_type=q.lower())
                if rows:
                    r = rows[0]
                    st.session_state.map_focus = {"lat": r[7], "lng": r[8], "name": r[1], "building": r[6], "floor": r[4], "room": r[2], "facility_type": r[3]}
                st.rerun()
    if search_map.strip():
        rows = get_facilities(conn, search=search_map.strip(), facility_type=None)
        for r in (rows or [])[:8]:
            fid, fname, room, ftype, floor, desc, bname, lat, lng = r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]
            if st.button(f"{fname} ({room})", key=f"focus_{fid}_{lat}_{lng}"):
                st.session_state.map_focus = {"lat": lat, "lng": lng, "name": fname, "building": bname, "floor": floor, "room": room, "facility_type": ftype}
                st.rerun()
    # Floor filter (optional, compact)
    floor_options = ["All floors", "Ground (0)", "Floor 1", "Floor 2"]
    floor_idx = 0 if selected_floor is None else (selected_floor + 1)
    floor_choice = st.selectbox("Filter by floor", floor_options, index=min(floor_idx, 3), key="floor_select")
    if floor_choice == "All floors": st.session_state.selected_floor = None
    elif floor_choice == "Ground (0)": st.session_state.selected_floor = 0
    elif floor_choice == "Floor 1": st.session_state.selected_floor = 1
    elif floor_choice == "Floor 2": st.session_state.selected_floor = 2
    selected_floor = st.session_state.selected_floor

    # Turn-by-turn directions
    if focus:
        st.markdown("---")
        floor_word = "Ground floor" if focus["floor"] == 0 else f"Floor {focus['floor']}"
        st.markdown(f"""
        <div class="dir-card">
        <p><b>From</b> {start_from['name'] if start_from else 'Your location'} <b>→ To</b> {focus['building']} – {focus['name']} (Room {focus['room']})</p>
        <p><b>1.</b> Follow the blue route on the map to <b>{focus['building']}</b>.</p>
        <p><b>2.</b> Enter building → <b>{floor_word}</b> → <b>Room {focus['room']}</b>.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Clear destination"):
            st.session_state.map_focus = None
            st.rerun()

    if selected_floor is not None:
        floor_facilities = [f for f in facilities_all if f[4] == selected_floor]
        floor_label = "Ground" if selected_floor == 0 else f"Floor {selected_floor}"
        with st.expander(f"📋 Rooms on {floor_label}"):
            for f in (floor_facilities or []):
                st.caption(f"**{f[1]}** (Room {f[2]}) – {f[7]}")

    conn.close()
    st.stop()

# ----- Book a space (reserve rooms, see availability) -----
if page == "Book a space":
    from datetime import date, timedelta
    ensure_bookings_table(conn)
    st.title("Book a space")
    st.caption("Reserve rooms, lecture halls, or study areas. See available spaces at a glance.")
    facilities_all = get_all_facilities_flat(conn)
    today = date.today()
    slot_options = ["09:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-13:00", "14:00-15:00", "15:00-16:00"]
    col_date, col_slot = st.columns(2)
    with col_date:
        booking_date = st.date_input("Date", value=today, min_value=today, key="book_date")
    with col_slot:
        slot = st.selectbox("Time slot", slot_options, key="book_slot")
    booker_name = st.text_input("Your name (optional)", placeholder="e.g. John", key="booker_name")
    booked_ids = get_booked_facility_ids_for_slot(conn, str(booking_date), slot)
    st.markdown("**Availability for " + str(booking_date) + " – " + slot + "**")
    for f in facilities_all:
        fid, fname, room, ftype, floor, desc, bid, bname, lat, lng = f
        is_booked = fid in booked_ids
        status = "🔴 Booked" if is_booked else "🟢 Available"
        with st.container():
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{fname}** (Room {room}) – {bname}  _{ftype}_")
            with c2:
                if is_booked:
                    st.caption(status)
                else:
                    if st.button("Book", key=f"book_{fid}_{booking_date}_{slot}"):
                        create_booking(conn, fid, str(booking_date), slot, booker_name.strip() or "Student/Staff")
                        st.success(f"Booked {fname} for {booking_date} {slot}.")
                        st.rerun()
    st.markdown("---")
    st.subheader("Your bookings")
    all_bookings = get_all_bookings(conn, str(booking_date))
    if all_bookings:
        for b in all_bookings:
            st.caption(f"**{b[5]}** (Room {b[6]}) – {b[7]} on {b[2]} {b[3]}  _by {b[4] or '—'}_")
    else:
        st.caption("No bookings for this date.")
    conn.close()
    st.stop()

# ----- Search -----
if page == "Search":
    st.title("Facility Search")
    st.caption("Search by room number, name, type, or faculty. No hardware – instant search.")
    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input("Search", placeholder="Room number, facility name, or keyword")
    with col2:
        ftype = st.selectbox("Facility type", ["All", "classroom", "lab", "office", "library"])
    faculty_search = st.text_input("Or search by faculty name", placeholder="e.g. Gadicha, Mishra")
    if faculty_search.strip():
        rows = search_faculty(conn, faculty_search.strip())
        if rows:
            st.subheader("Faculty locations")
            for r in rows:
                st.write(f"**{r[5]}** – {r[1]} (Room {r[2]}, {r[3]}) – Building: {r[4]}")
        else:
            st.info("No faculty found for that name.")
    else:
        building_id = None
        facility_type = None if ftype == "All" else ftype
        rows = get_facilities(conn, building_id=building_id, search=search if search else None, facility_type=facility_type)
        if rows:
            df = pd.DataFrame(rows, columns=["ID", "Name", "Room", "Type", "Floor", "Description", "Building", "Lat", "Lng"])
            st.dataframe(
                df[["Name", "Room", "Type", "Floor", "Building", "Description"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No facilities match your search.")
    conn.close()
    st.stop()

# ----- Accessibility -----
if page == "Accessibility":
    st.title("Accessibility")
    st.caption("High-contrast theme and text-to-speech support – no extra hardware.")
    st.markdown("""
    - **High contrast**: Toggle in the sidebar for yellow-on-black text.
    - **Screen readers**: Use your OS or browser screen reader with this app.
    - **Read aloud**: Use the box below to hear directions read aloud (software TTS).
    """)
    text_to_speak = st.text_area("Text to read aloud (e.g. directions)", placeholder="e.g. Go to Main Block, first floor, Room 101.")
    if st.button("Read aloud") and text_to_speak.strip():
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(text_to_speak.strip())
            engine.runAndWait()
            st.success("Playback started.")
        except Exception as e:
            st.warning(f"TTS not available: {e}. Use your system or browser screen reader.")
    conn.close()
    st.stop()

# ----- Admin -----
if page == "Admin":
    st.title("Admin Dashboard")
    st.caption("Update facilities and buildings. No hardware – all data is stored in the database.")
    admin_pin = st.text_input("Admin PIN", type="password", placeholder="Enter admin PIN (see backend/config.py for default)")
    if admin_pin != ADMIN_PIN:
        st.info("Enter the admin PIN to manage campus data. (Default demo PIN is in **backend/config.py**.)")
        conn.close()
        st.stop()
    tab1, tab2, tab3 = st.tabs(["Add building", "Add facility", "View / Edit / Delete facilities"])
    buildings = get_buildings(conn)
    building_choices = {b[1]: b[0] for b in buildings}
    with tab1:
        with st.form("add_building"):
            bname = st.text_input("Building name")
            blat = st.number_input("Latitude", value=20.9993, format="%.4f")
            blng = st.number_input("Longitude", value=77.7578, format="%.4f")
            bdesc = st.text_input("Description")
            if st.form_submit_button("Add building"):
                add_building(conn, bname, blat, blng, bdesc)
                st.success("Building added.")
                st.rerun()
    with tab2:
        with st.form("add_facility"):
            bsel = st.selectbox("Building", list(building_choices.keys()) or ["(No buildings)"] )
            fname = st.text_input("Facility name")
            room = st.text_input("Room number")
            ftype = st.selectbox("Type", ["classroom", "lab", "office", "library"])
            floor = st.number_input("Floor", value=0, step=1)
            fdesc = st.text_input("Description")
            if st.form_submit_button("Add facility") and bsel in building_choices:
                add_facility(conn, building_choices[bsel], fname, room, ftype, floor, fdesc)
                st.success("Facility added.")
                st.rerun()
    with tab3:
        all_f = get_all_facilities_flat(conn)
        if not all_f:
            st.info("No facilities yet.")
        else:
            for f in all_f:
                fid, fname, room, ftype, floor, desc, bid, bname, lat, lng = f
                with st.expander(f"{fname} ({room}) – {bname}"):
                    st.write(f"Type: {ftype}, Floor: {floor}")
                    st.write(desc or "No description")
                    if st.button("Delete", key=f"del_{fid}"):
                        delete_facility(conn, fid)
                        st.success("Deleted.")
                        st.rerun()
    conn.close()
    st.stop()

conn.close()

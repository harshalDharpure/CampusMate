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
    st.markdown("""
    <style>
    .block-container { padding-top: 1rem; max-width: 100%%; }
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
    buildings = get_buildings(conn)
    facilities_all = get_all_facilities_flat(conn)
    focus = st.session_state.map_focus
    start_from = st.session_state.start_from
    selected_floor = st.session_state.selected_floor

    # ----- MazeMap-style header: Search + My location + Floor -----
    st.markdown("#### 🗺️ Indoor campus map")
    header_col1, header_col2, header_col3 = st.columns([2, 1, 1])
    with header_col1:
        search_map = st.text_input(
            "Search",
            placeholder="Search rooms, library, lab, department...",
            key="map_search"
        )
    with header_col2:
        st.caption("My location")
        if st.button("📍 Show my location", key="btn_my_loc"):
            if start_from:
                st.session_state.map_focus = None  # clear destination so map centers on you
            st.rerun()
    with header_col3:
        floor_options = ["All floors", "Ground (0)", "Floor 1", "Floor 2"]
        floor_idx = 0 if selected_floor is None else (selected_floor + 1)
        floor_choice = st.selectbox("Floor", floor_options, index=min(floor_idx, 3), key="floor_select")
        if floor_choice == "All floors":
            st.session_state.selected_floor = None
        elif floor_choice == "Ground (0)":
            st.session_state.selected_floor = 0
        elif floor_choice == "Floor 1":
            st.session_state.selected_floor = 1
        elif floor_choice == "Floor 2":
            st.session_state.selected_floor = 2
        selected_floor = st.session_state.selected_floor
    st.markdown("---")

    # Filter facilities by selected floor for map and list
    if selected_floor is not None:
        facilities = [f for f in facilities_all if f[4] == selected_floor]  # f[4] = floor
    else:
        facilities = facilities_all

    # Step 1: Where are you now?
    st.markdown("**Step 1: Where are you now?**")
    start_options = [e["name"] for e in CAMPUS_ENTRANCES] + [b[1] for b in buildings]
    start_choice = st.selectbox(
        "Your current location",
        start_options,
        key="start_choice",
        label_visibility="collapsed"
    )
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
    if start_from:
        st.caption(f"📍 Your location: **{start_from['name']}**")

    # Step 2: Where do you want to go?
    st.markdown("**Step 2: Where do you want to go?**")
    chip_cols = st.columns(4)
    quick_queries = ["Library", "Lab", "Office", "Classroom"]
    for i, q in enumerate(quick_queries):
        with chip_cols[i]:
            if st.button(f"📌 {q}", key=f"chip_{q}"):
                rows = get_facilities(conn, search=q, facility_type=None)
                if not rows and q.lower() == "library":
                    rows = get_facilities(conn, facility_type="library")
                if not rows and q.lower() == "lab":
                    rows = get_facilities(conn, facility_type="lab")
                if not rows and q.lower() == "office":
                    rows = get_facilities(conn, facility_type="office")
                if not rows and q.lower() == "classroom":
                    rows = get_facilities(conn, facility_type="classroom")
                if rows:
                    r = rows[0]
                    fid, fname, room, ftype, floor, desc, bname, lat, lng = r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]
                    st.session_state.map_focus = {"lat": lat, "lng": lng, "name": fname, "building": bname, "floor": floor, "room": room, "facility_type": ftype}
                st.rerun()
    if search_map.strip():
        rows = get_facilities(conn, search=search_map.strip(), facility_type=None)
        faculty_rows = search_faculty(conn, search_map.strip())
        if faculty_rows:
            for r in faculty_rows:
                rows.append((r[0], r[1], r[2], r[3], r[4], None, r[5], r[6], r[7]))
        if rows:
            st.caption("Tap a result to set destination:")
            for r in rows[:15]:
                fid, fname, room, ftype, floor, desc, bname, lat, lng = r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8]
                label = f"{fname} (Room {room}) – {bname}"
                if st.button(label, key=f"focus_{fid}_{lat}_{lng}"):
                    st.session_state.map_focus = {
                        "lat": lat, "lng": lng, "name": fname, "building": bname,
                        "floor": floor, "room": room, "facility_type": ftype
                    }
                    st.rerun()
        else:
            st.info("No places found. Try 'library', 'lab', or a room number.")

    # Turn-by-turn directions (MazeMap-style, like GPS indoors)
    if focus:
        st.markdown("---")
        st.markdown("### 🧭 Turn-by-turn directions (indoors)")
        floor_word = "Ground floor" if focus["floor"] == 0 else f"Floor {focus['floor']}"
        st.markdown(f"""
        <div class="dir-card">
        <p><b>From</b> {start_from['name'] if start_from else 'Your location'} <b>→ To</b> {focus['building']} – {focus['name']} (Room {focus['room']})</p>
        <hr style="margin: 8px 0;">
        <p><b>Step 1.</b> Walk from your current location toward <b>{focus['building']}</b>. Follow the blue route on the map.</p>
        <p><b>Step 2.</b> Enter <b>{focus['building']}</b> through the main entrance.</p>
        <p><b>Step 3.</b> Go to <b>{floor_word}</b> (use stairs or lift).</p>
        <p><b>Step 4.</b> Find <b>Room {focus['room']}</b> – {focus['name']}. You have arrived.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Clear destination"):
            st.session_state.map_focus = None
            st.rerun()
        st.markdown("---")

    # Rooms on this floor (MazeMap-style: list of rooms/facilities on selected floor)
    if selected_floor is not None:
        floor_facilities = [f for f in facilities_all if f[4] == selected_floor]
        floor_label = "Ground" if selected_floor == 0 else f"Floor {selected_floor}"
        with st.expander(f"📋 Rooms on {floor_label}"):
            if floor_facilities:
                for f in floor_facilities:
                    fid, fname, room, ftype, fl, desc, bid, bname, lat, lng = f[0], f[1], f[2], f[3], f[4], f[5], f[6], f[7], f[8]
                    st.caption(f"**{fname}** (Room {room}) – {bname}  _{ftype}_")
            else:
                st.caption(f"No rooms on {floor_label} in the database.")
    st.markdown("---")

    if not buildings:
        st.info("No buildings in database. Add them in Admin.")
    else:
        # Map center and zoom to show both start and destination when route is active
        if focus and start_from:
            lat0 = (start_from["lat"] + focus["lat"]) / 2
            lng0 = (start_from["lng"] + focus["lng"]) / 2
            zoom = 17
        elif focus:
            lat0, lng0 = focus["lat"], focus["lng"]
            zoom = 18
        else:
            lat0, lng0 = buildings[0][2], buildings[0][3]
            zoom = 17
        m = folium.Map(location=[lat0, lng0], zoom_start=zoom, tiles="OpenStreetMap")

        # Draw route inside app – goes through campus center so it looks like a walking path
        if focus and start_from:
            start_pt = [start_from["lat"], start_from["lng"]]
            end_pt = [focus["lat"], focus["lng"]]
            # Route: start → campus center (waypoint) → destination (walking path effect)
            route_points = [start_pt, [CAMPUS_CENTER["lat"], CAMPUS_CENTER["lng"]], end_pt]
            folium.PolyLine(
                locations=route_points,
                color="#1e88e5",
                weight=5,
                opacity=0.8,
                popup="Walking route via campus center – stay inside campus",
            ).add_to(m)
            folium.Marker(
                [start_from["lat"], start_from["lng"]],
                popup=folium.Popup(f"<b>You are here</b><br>{start_from['name']}", max_width=200),
                tooltip="You are here",
                icon=folium.Icon(color="green", icon="user"),
            ).add_to(m)
            # Pulsing "current location" effect (MazeMap-style) – semi-transparent circle
            folium.Circle(
                location=[start_from["lat"], start_from["lng"]],
                radius=25,
                color="green",
                fill=True,
                fill_color="green",
                fill_opacity=0.15,
                weight=2,
                dash_array="5, 5",
            ).add_to(m)
            # Fit map to show full route (start + waypoint + destination)
            all_lats = [start_from["lat"], CAMPUS_CENTER["lat"], focus["lat"]]
            all_lngs = [start_from["lng"], CAMPUS_CENTER["lng"], focus["lng"]]
            m.fit_bounds([[min(all_lats), min(all_lngs)], [max(all_lats), max(all_lngs)]], padding=(30, 30))

        # College name on map
        campus_title_html = """
        <div style="position:fixed; top:10px; left:50%; transform:translateX(-50%); z-index:9999;
                    background:white; padding:10px 16px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.2);
                    font-size:14px; font-weight:bold; text-align:center;">
        PR Pote Patil College of Engineering and Management, Amravati<br>
        <span style="font-size:11px; font-weight:normal;">Pote Estate, Kathora Road, Amravati – 444602</span>
        </div>
        """
        m.get_root().html.add_child(folium.Element(campus_title_html))

        # Legend
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
            popup_html = f"<b>{name}</b><br>{desc or ''}<br><br><i>Buildings contain rooms – tap blue/green/orange/purple markers for rooms.</i>"
            folium.Marker(
                [lat, lng],
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=name,
                icon=folium.Icon(color="red", icon="info-sign"),
            ).add_to(m)
        for f in facilities:
            fid, fname, room, ftype, floor, desc, bid, bname, lat, lng = f
            color = FACILITY_COLORS.get(ftype, "blue")
            directions = f"Go to <b>{bname}</b> → Floor {floor} → Room {room}"
            popup_html = f"<b>{fname}</b> (Room {room})<br>Type: {ftype}<br>Floor: {floor}<br>{desc or ''}<br><br><b>Directions:</b> {directions}<br><i>Select this as destination above to see the route on the map.</i>"
            folium.CircleMarker(
                [lat, lng],
                radius=8,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"{fname} – {room} ({ftype})",
                color=color,
                fill=True,
                fillColor=color,
            ).add_to(m)
        st_folium(m, use_container_width=True, height=550)
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

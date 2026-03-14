# CampusMate – Complete User Guide

CampusMate is a **smart indoor navigation and space-booking app** for **PR Pote Patil College of Engineering and Management, Amravati**. Use it to find rooms, get turn-by-turn directions on campus, and book spaces—all inside the app, with no redirect to Google Maps.

---

## Table of contents

1. [Quick start – run the app](#1-quick-start--run-the-app)
2. [Sidebar – navigate the app](#2-sidebar--navigate-the-app)
3. [Campus Map – find your way](#3-campus-map--find-your-way)
4. [Book a space – reserve rooms](#4-book-a-space--reserve-rooms)
5. [Search – find facilities and faculty](#5-search--find-facilities-and-faculty)
6. [Accessibility](#6-accessibility)
7. [Admin – manage campus data](#7-admin--manage-campus-data)
8. [Example: new student going to the library](#8-example-new-student-going-to-the-library)
9. [Tips and troubleshooting](#9-tips-and-troubleshooting)

---

## 1. Quick start – run the app

### First-time setup

Open a terminal (PowerShell or Command Prompt) in the project folder and run:

```bash
cd "c:\Users\HARSHAL\Downloads\FYP-1"
pip install -r requirements.txt
python -m backend.init_db
```

- **First command:** goes to the project folder.  
- **Second command:** installs Python packages (Streamlit, Folium, etc.).  
- **Third command:** creates the database and loads sample campus data (buildings, library, labs, etc.).

### Start the app

```bash
python -m streamlit run frontend/app.py
```

The terminal will show a URL, for example:

- **Local URL:** http://localhost:8501

Open that URL in your browser (Chrome, Edge, etc.). You can use the **same URL on your phone** (replace `localhost` with your computer’s IP if needed, e.g. `http://192.168.1.5:8501`).

### Stop the app

In the terminal where the app is running, press **Ctrl+C**.

---

## 2. Sidebar – navigate the app

On the **left side** you have:

- **CampusMate** title and college name.
- **High contrast** – turn this **On** for yellow-on-black text (accessibility).
- **Why campus navigation?** – expand to read why wayfinding and booking matter.
- **Navigate** – choose where to go:
  - **Campus Map** – indoor map, directions, floor view.
  - **Book a space** – reserve rooms by date and time.
  - **Search** – search facilities and faculty.
  - **Accessibility** – read-aloud and tips.
  - **Admin** – add/edit buildings and rooms (needs Admin PIN).

---

## 3. Campus Map – find your way

Use this to **get from your current location to a room** (e.g. Library, lab) with a **route on the map** and **turn-by-turn directions**. Everything stays inside the app.

### Header (top of Campus Map)

- **Search** – type a room name, “library”, “lab”, or room number. Results appear below; tap one to set it as your **destination**.
- **Show my location** – refocuses the map on your chosen start point.
- **Floor** – choose **All floors**, **Ground (0)**, **Floor 1**, or **Floor 2** to see only rooms on that floor (MazeMap-style). When a floor is selected, **Rooms on [Floor]** lists all rooms on that floor.

### Step 1: Where are you now?

- **Use my live location (turn on location)** – Click this button to use your **phone or PC’s GPS**. The browser will ask for location permission; after you allow it, the app refreshes with **“My live location (GPS)”** as your start point (e.g. hostel at IIT Patna). The map then shows your real position and the route from there to your destination (e.g. Library).
- Or, in the dropdown, select a **fixed place**:
  - **Main Gate (College Entrance)**
  - **North Gate**
  - **Canteen / Student Area**
  - **Parking Lot**
  - Or any **building** (Main Block, Library, etc.).
- The app shows either “**My live location (GPS)**” or “Your location: **Main Gate**” (or whatever you chose).

### Step 2: Where do you want to go?

- Use the **quick buttons**: **Library**, **Lab**, **Office**, **Classroom** – one tap sets that as your destination.
- Or type in the **search** box (e.g. “library”, “101”) and tap one of the results to set destination.

### What you see after choosing a destination

- **Turn-by-turn directions** in a blue card, e.g.:
  - Step 1: Walk from your location toward **Library** (follow the blue route on the map).
  - Step 2: Enter **Library**.
  - Step 3: Go to **Ground floor** (or Floor 1/2).
  - Step 4: Find **Room G-01** – Reading Hall. You have arrived.
- **Map** below with:
  - **Blue line** = walking route from your location → campus center → destination.
  - **Green “You are here”** marker and circle at your start point.
  - **Red** markers = buildings; **coloured** dots = rooms (Library=purple, Lab=green, Office=orange, Classroom=blue).
- **Clear destination** – button to remove the current destination and directions.

### Map tips

- **Click markers** on the map to see building/room names and short descriptions.
- **Floor** dropdown filters which rooms appear on the map and in **Rooms on [Floor]**.
- The app does **not** open Google Maps; all navigation is inside CampusMate.

---

## 4. Book a space – reserve rooms

Use this to **see which rooms are free** for a date and time, and **book** them.

1. Open **Book a space** from the sidebar.
2. **Date** – pick the day (e.g. today or a future date).
3. **Time slot** – choose one slot, e.g. **10:00–11:00**, **11:00–12:00**, etc.
4. **Your name (optional)** – enter your name if you want it stored with the booking.
5. The list shows every room with:
   - **Available** and a **Book** button – you can reserve it for that date and slot.
   - **Booked** – someone else has already booked it.
6. Click **Book** next to an available room to reserve it. A message confirms the booking.
7. **Your bookings** – at the bottom you see bookings for the selected date (room, slot, name).

You can change the date/slot and book other rooms; each combination of room + date + slot can be booked once.

---

## 5. Search – find facilities and faculty

Use this to **search** without using the map.

- **Search** – type a room number, facility name, or keyword (e.g. “lab”, “101”).
- **Facility type** – filter by **All**, **classroom**, **lab**, **office**, **library**.
- **Or search by faculty name** – e.g. “Gadicha”, “Mishra” to see which room they are in.

Results appear as a table (Name, Room, Type, Floor, Building, Description) or as faculty locations. This does not set a route; use **Campus Map** for directions.

---

## 6. Accessibility

- **High contrast** – in the sidebar, turn **High contrast** On for easier reading (yellow text on dark background).
- **Read aloud** – on the Accessibility page, type or paste text (e.g. directions) and click **Read aloud** to hear it (uses your PC’s TTS; may not work on all systems).
- Use your **browser or system screen reader** with the app as needed.

---

## 7. Admin – manage campus data

Only for **staff who maintain** the campus map and rooms.

1. Open **Admin** from the sidebar.
2. Enter the **Admin PIN** (default: **admin123**; can be changed in `backend/config.py`).
3. After entering the correct PIN you get three tabs:
   - **Add building** – name, latitude, longitude, description. Use this for new buildings or to correct locations.
   - **Add facility** – choose a building, then add a room (name, room number, type: classroom/lab/office/library, floor, description).
   - **View / Edit / Delete facilities** – expand a facility to see details and **Delete** if needed (no edit form in this version; delete and re-add to “edit”).

Students and visitors do **not** need the Admin PIN; they only use Campus Map, Book a space, and Search.

---

## 8. Example: new student going to the library

### Option A – Using a fixed start (e.g. Main Gate)

1. Open the app and go to **Campus Map**.
2. **Step 1 – Where are you now?**  
   Select **Main Gate (College Entrance)**.
3. **Step 2 – Where do you want to go?**  
   Click the **Library** button (or search “library” and tap **Reading Hall** or **Issue Counter**).
4. Read the **turn-by-turn directions** (walk to Library → enter → Ground floor → Room G-01).
5. Look at the **map**: the blue line shows the path from Main Gate to the Library building; the green marker is “You are here.”
6. Follow the route on campus; use **Clear destination** when you’re done.

### Option B – Using live location (e.g. at IIT Patna hostel, going to Library)

1. Open the app (on your **phone** or laptop) and go to **Campus Map**.
2. **Step 1 – Where are you now?**  
   Click **“Use my live location (turn on location)”**.  
   Allow **location access** when the browser asks.
3. The page will refresh. You should see **“My live location (GPS)”** as your start (e.g. hostel, IIT Patna).
4. **Step 2 – Where do you want to go?**  
   Click **Library** (or search “library” and tap a result).
5. The **map** shows your current position (green “You are here”) and a **blue route** from there to the Library. Follow the **turn-by-turn directions** on the page.
6. **If your campus is different** (e.g. IIT Patna): the sample data is for PR Pote Patil, Amravati. To get the correct hostel → library route for **IIT Patna**, a staff member should add IIT Patna’s buildings (e.g. Hostel, Library) and their coordinates in **Admin**, so the map and route match your campus.

---

## 9. Tips and troubleshooting

- **App won’t start** – make sure you ran `pip install -r requirements.txt` and `python -m backend.init_db` from the **project root** (`FYP-1`), then `python -m streamlit run frontend/app.py`.
- **Empty map** – run `python -m backend.init_db` again (or delete `backend/campusmate.db` and run it) to load sample buildings and rooms.
- **Admin PIN** – default is **admin123**; change it in **backend/config.py** (`ADMIN_PIN = "your_pin"`).
- **Use on phone** – open the same URL as on your PC (use your computer’s IP instead of `localhost` if you’re on the same Wi‑Fi).
- **Booking** – each room can be booked only once per date and time slot; choose another slot or another room if it’s already booked.
- **Live location** – “Use my live location” needs **browser location permission**. If it doesn’t work, check that the site is allowed to use location (browser or device settings). On **phones**, use **HTTPS** (e.g. deploy on Streamlit Cloud or use a tunnel) for geolocation to work reliably.

---

## Summary

| I want to…              | Do this…                                      |
|-------------------------|-----------------------------------------------|
| Find a room and get there | **Campus Map** → set location → set destination (e.g. Library) |
| Reserve a room          | **Book a space** → pick date & slot → Book    |
| Search rooms/faculty    | **Search** or use search on **Campus Map**    |
| Easier reading / voice  | **High contrast** in sidebar; **Accessibility** for read-aloud |
| Add buildings/rooms     | **Admin** (with Admin PIN)                    |

For more technical details (project structure, run commands, deployment), see **README.md** and **DEPLOY.md**.

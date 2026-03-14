# CampusMate – Smart Navigation System for College Campuses

A **software-only** smart navigation web app for **PR Pote Patil College of Engineering and Management, Amravati**. No hardware. Map + search + directions like Google Maps.

## Project structure (frontend + backend)

```
FYP-1/
├── frontend/          # UI (Streamlit app)
│   ├── app.py         # Main app – Campus Map, Search, Accessibility, Admin
│   └── __init__.py
├── backend/           # Database and config
│   ├── database.py    # SQLite – buildings, facilities, faculty
│   ├── init_db.py     # Create DB and seed sample campus data
│   ├── config.py      # Admin PIN and settings (change ADMIN_PIN here)
│   └── __init__.py
├── requirements.txt
└── README.md
```

The database file `campusmate.db` is created inside **backend/** when you run init.

---

## Admin PIN

- **What it is:** The Admin PIN lets you open the **Admin** section to add/edit buildings and facilities.
- **Default (demo):** `admin123`
- **Where to change it:** Edit **`backend/config.py`** and set `ADMIN_PIN = "your_secret_pin"`.
- **Who uses it:** College staff or admins who maintain the campus map. Students/visitors do not need it.

---

## How to run (from project root)

**1. Install dependencies (first time only)**

```bash
pip install -r requirements.txt
```

**2. Create database and sample data (first time only)**

```bash
python -m backend.init_db
```

**3. Start the app**

```bash
python -m streamlit run frontend/app.py
```

**4. Open in browser**

Use the URL shown (e.g. **http://localhost:8501**). Use the same link on your phone for the campus map.

---

## Do I need to feed something?

- **You (student/visitor):** No. Just search e.g. "library" or "lab" and get directions.
- **College admin:** Add buildings and rooms **once** in **Admin** (after entering the Admin PIN). After that, everyone only searches.

---

## Notes

- **Campus:** Default data is for **PR Pote Patil College of Engineering and Management, Amravati** (Pote Estate, Kathora Road). To reset and reload it, delete **backend/campusmate.db** and run `python -m backend.init_db` again.
- Change **backend/config.py** for Admin PIN and (if you add more) other settings.
- Voice uses **pyttsx3** (offline TTS).

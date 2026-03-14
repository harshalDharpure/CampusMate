"""
CampusMate database layer – SQLite, no hardware.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "campusmate.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_schema(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS buildings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            description TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS facilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            building_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            room_number TEXT,
            facility_type TEXT NOT NULL,
            floor INTEGER DEFAULT 0,
            description TEXT,
            FOREIGN KEY (building_id) REFERENCES buildings(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS faculty_rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            faculty_name TEXT NOT NULL,
            designation TEXT,
            FOREIGN KEY (facility_id) REFERENCES facilities(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            booked_date TEXT NOT NULL,
            slot TEXT NOT NULL,
            booked_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (facility_id) REFERENCES facilities(id)
        )
    """)
    conn.commit()


def seed_sample_data(conn):
    """Seed campus data for PR Pote Patil College of Engineering and Management, Amravati."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM buildings")
    if cur.fetchone()[0] > 0:
        return
    # PR Pote Patil College of Engineering and Management, Amravati – Pote Estate, Kathora Road
    # Center: Kathora, Amravati (approx 20.9993, 77.7578). Buildings spread around campus.
    buildings = [
        (1, "Main Block", 20.9993, 77.7578, "Central academic block – PR Pote Patil College"),
        (2, "Library", 20.9996, 77.7581, "Central library – PR Pote Patil College"),
        (3, "Computer Lab Block", 20.9990, 77.7576, "IT and labs – PR Pote Patil College"),
        (4, "Admin Block", 20.9995, 77.7579, "Administration and offices – PR Pote Patil College"),
    ]
    for b in buildings:
        cur.execute(
            "INSERT INTO buildings (id, name, lat, lng, description) VALUES (?, ?, ?, ?, ?)",
            b
        )
    facilities = [
        (1, "Room 101", "101", "classroom", 1, "General classroom"),
        (1, "Room 102", "102", "classroom", 1, "General classroom"),
        (1, "ECE Lab", "103", "lab", 1, "Electronics lab"),
        (2, "Reading Hall", "G-01", "library", 0, "Main reading area"),
        (2, "Issue Counter", "G-02", "library", 0, "Book issue/return"),
        (3, "Programming Lab", "L-201", "lab", 2, "Computer lab"),
        (3, "Project Lab", "L-202", "lab", 2, "Project lab"),
        (4, "Principal Office", "A-01", "office", 1, "Principal"),
        (4, "Exam Cell", "A-02", "office", 1, "Examination office"),
    ]
    for f in facilities:
        cur.execute(
            """INSERT INTO facilities (building_id, name, room_number, facility_type, floor, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            f
        )
    faculty = [
        (1, "Dr. A.B. Gadicha", "Guide"),
        (4, "Prof. Abhiruchi Mishra", "Co-Guide"),
        (8, "Principal", "Office"),
    ]
    for fac in faculty:
        cur.execute(
            "INSERT INTO faculty_rooms (facility_id, faculty_name, designation) VALUES (?, ?, ?)",
            fac
        )
    conn.commit()


def get_buildings(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, name, lat, lng, description FROM buildings ORDER BY name")
    return cur.fetchall()


def get_facilities(conn, building_id=None, search=None, facility_type=None):
    cur = conn.cursor()
    q = """
        SELECT f.id, f.name, f.room_number, f.facility_type, f.floor, f.description,
               b.name as building_name, b.lat, b.lng
        FROM facilities f
        JOIN buildings b ON f.building_id = b.id
        WHERE 1=1
    """
    params = []
    if building_id:
        q += " AND f.building_id = ?"
        params.append(building_id)
    if search:
        q += " AND (f.name LIKE ? OR f.room_number LIKE ? OR f.description LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s])
    if facility_type:
        q += " AND f.facility_type = ?"
        params.append(facility_type)
    q += " ORDER BY b.name, f.floor, f.room_number"
    cur.execute(q, params)
    return cur.fetchall()


def search_faculty(conn, faculty_name):
    cur = conn.cursor()
    cur.execute("""
        SELECT f.id, f.name, f.room_number, f.facility_type, f.floor, b.name as building_name, b.lat, b.lng
        FROM faculty_rooms fr
        JOIN facilities f ON fr.facility_id = f.id
        JOIN buildings b ON f.building_id = b.id
        WHERE fr.faculty_name LIKE ?
    """, (f"%{faculty_name}%",))
    return cur.fetchall()


def get_facility_by_id(conn, facility_id):
    cur = conn.cursor()
    cur.execute("""
        SELECT f.id, f.name, f.room_number, f.facility_type, f.floor, f.description,
               b.id as building_id, b.name as building_name, b.lat, b.lng
        FROM facilities f
        JOIN buildings b ON f.building_id = b.id
        WHERE f.id = ?
    """, (facility_id,))
    return cur.fetchone()


def add_building(conn, name, lat, lng, description=""):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO buildings (name, lat, lng, description) VALUES (?, ?, ?, ?)",
        (name, lat, lng, description)
    )
    conn.commit()
    return cur.lastrowid


def add_facility(conn, building_id, name, room_number, facility_type, floor=0, description=""):
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO facilities (building_id, name, room_number, facility_type, floor, description)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (building_id, name, room_number, facility_type, floor, description)
    )
    conn.commit()
    return cur.lastrowid


def update_facility(conn, facility_id, name, room_number, facility_type, floor, description):
    cur = conn.cursor()
    cur.execute("""
        UPDATE facilities SET name=?, room_number=?, facility_type=?, floor=?, description=?
        WHERE id=?
    """, (name, room_number, facility_type, floor, description, facility_id))
    conn.commit()


def delete_facility(conn, facility_id):
    cur = conn.cursor()
    cur.execute("DELETE FROM faculty_rooms WHERE facility_id = ?", (facility_id,))
    cur.execute("DELETE FROM facilities WHERE id = ?", (facility_id,))
    conn.commit()


def get_all_facilities_flat(conn):
    cur = conn.cursor()
    cur.execute("""
        SELECT f.id, f.name, f.room_number, f.facility_type, f.floor, f.description, f.building_id,
               b.name as building_name, b.lat, b.lng
        FROM facilities f
        JOIN buildings b ON f.building_id = b.id
        ORDER BY b.name, f.floor, f.room_number
    """)
    return cur.fetchall()


# ----- Space booking (book rooms, see availability) -----
def ensure_bookings_table(conn):
    """Create bookings table if missing (for existing DBs)."""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id INTEGER NOT NULL,
            booked_date TEXT NOT NULL,
            slot TEXT NOT NULL,
            booked_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (facility_id) REFERENCES facilities(id)
        )
    """)
    conn.commit()


def create_booking(conn, facility_id, booked_date, slot, booked_by=""):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO bookings (facility_id, booked_date, slot, booked_by) VALUES (?, ?, ?, ?)",
        (facility_id, booked_date, slot, booked_by)
    )
    conn.commit()
    return cur.lastrowid


def get_bookings_for_facility(conn, facility_id, booked_date=None):
    cur = conn.cursor()
    if booked_date:
        cur.execute(
            "SELECT id, facility_id, booked_date, slot, booked_by FROM bookings WHERE facility_id = ? AND booked_date = ? ORDER BY slot",
            (facility_id, booked_date)
        )
    else:
        cur.execute(
            "SELECT id, facility_id, booked_date, slot, booked_by FROM bookings WHERE facility_id = ? ORDER BY booked_date, slot",
            (facility_id,)
        )
    return cur.fetchall()


def get_booked_facility_ids_for_slot(conn, booked_date, slot):
    """Return set of facility_ids that are booked for the given date and slot."""
    cur = conn.cursor()
    cur.execute(
        "SELECT facility_id FROM bookings WHERE booked_date = ? AND slot = ?",
        (booked_date, slot)
    )
    return {row[0] for row in cur.fetchall()}


def get_all_bookings(conn, booked_date=None):
    cur = conn.cursor()
    if booked_date:
        cur.execute("""
            SELECT b.id, b.facility_id, b.booked_date, b.slot, b.booked_by,
                   f.name as facility_name, f.room_number, bl.name as building_name
            FROM bookings b
            JOIN facilities f ON b.facility_id = f.id
            JOIN buildings bl ON f.building_id = bl.id
            WHERE b.booked_date = ?
            ORDER BY b.slot
        """, (booked_date,))
    else:
        cur.execute("""
            SELECT b.id, b.facility_id, b.booked_date, b.slot, b.booked_by,
                   f.name as facility_name, f.room_number, bl.name as building_name
            FROM bookings b
            JOIN facilities f ON b.facility_id = f.id
            JOIN buildings bl ON f.building_id = bl.id
            ORDER BY b.booked_date, b.slot
        """)
    return cur.fetchall()

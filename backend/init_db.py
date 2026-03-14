"""
Initialize CampusMate SQLite database and seed sample campus data.
Run from project root: python -m backend.init_db
"""
from .database import get_connection, init_schema, seed_sample_data, DB_PATH


def main():
    conn = get_connection()
    try:
        init_schema(conn)
        seed_sample_data(conn)
        print(f"Database initialized: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

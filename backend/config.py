"""
Backend config – admin PIN and campus waypoints for in-app routing.
Change ADMIN_PIN for production. Adjust entrances and campus center to match your campus.
"""
# Admin PIN to access Admin dashboard (add/edit buildings and facilities).
ADMIN_PIN = "admin123"

# Campus entrances / common start points for "Where are you now?" (PR Pote Patil, Amravati).
# Add or edit for your campus. Route will be drawn through CAMPUS_CENTER to look like a walking path.
CAMPUS_ENTRANCES = [
    {"name": "Main Gate (College Entrance)", "lat": 20.9988, "lng": 77.7574},
    {"name": "North Gate", "lat": 20.9998, "lng": 77.7578},
    {"name": "Canteen / Student Area", "lat": 20.9992, "lng": 77.7575},
    {"name": "Parking Lot", "lat": 20.9985, "lng": 77.7572},
]

# Center of campus – route goes through this waypoint so it looks like a walking path, not a straight line.
CAMPUS_CENTER = {"lat": 20.9993, "lng": 77.7578}


from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
import sqlite3
import uuid
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "emergencies.db"

app = Flask(__name__)

# ---------------- DATABASE CONNECTION ----------------

def get_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

# ---------------- DATABASE INITIALIZATION ----------------

def initialize_database():
    with get_db() as connection:

        # Emergency requests table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS emergencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE NOT NULL,
                patient_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                emergency_type TEXT NOT NULL,
                symptoms TEXT NOT NULL,
                location TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Submitted',
                created_at TEXT NOT NULL
            )
        """)

        # Ambulance management table
        connection.execute("""
            CREATE TABLE IF NOT EXISTS ambulances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ambulance_code TEXT UNIQUE NOT NULL,
                ambulance_type TEXT NOT NULL,
                location TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Available',
                assigned_request_id TEXT
            )
        """)

        # Add demo ambulances only if the table is empty
        ambulance_count = connection.execute(
            "SELECT COUNT(*) FROM ambulances"
        ).fetchone()[0]

        if ambulance_count == 0:
            connection.executemany("""
                INSERT INTO ambulances (
                    ambulance_code,
                    ambulance_type,
                    location,
                    status
                )
                VALUES (?, ?, ?, ?)
            """, [
                (
                    "AMB-001",
                    "Basic",
                    "Park Street, Kolkata",
                    "Available"
                ),
                (
                    "AMB-002",
                    "Advanced",
                    "Salt Lake, Kolkata",
                    "Available"
                ),
                (
                    "AMB-003",
                    "Basic",
                    "Howrah, Kolkata",
                    "Available"
                )
            ])

initialize_database()

# ---------------- FRONTEND ROUTES ----------------

@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/style.css")
def stylesheet():
    return send_from_directory(BASE_DIR, "style.css")

@app.route("/script.js")
def javascript():
    return send_from_directory(BASE_DIR, "script.js")

@app.route("/dashboard")
def dashboard():
    return send_from_directory(BASE_DIR, "dashboard.html")

# ---------------- CREATE EMERGENCY ----------------

@app.route("/api/emergencies", methods=["POST"])
def create_emergency():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Please submit valid form data."
        }), 400

    fields = [
        "name", "phone", "type", "symptoms", "location"
    ]

    values = {}

    for field in fields:
        value = data.get(field)

        if not isinstance(value, str) or not value.strip():
            return jsonify({
                "error": f"Please provide a valid {field}."
            }), 400

        values[field] = value.strip()

    if len(values["name"]) > 100:
        return jsonify({"error": "Name is too long."}), 400

    if (
        not values["phone"].isdigit()
        or len(values["phone"]) != 10
    ):
        return jsonify({
            "error": "Enter a valid 10-digit phone number."
        }), 400

    allowed_types = {
        "Medical", "Cardiac", "Accident", "Breathing", "Other"
    }

    if values["type"] not in allowed_types:
        return jsonify({
            "error": "Invalid emergency type."
        }), 400

    if len(values["symptoms"]) > 2000:
        return jsonify({
            "error": "Description is too long."
        }), 400

    if len(values["location"]) > 300:
        return jsonify({
            "error": "Location is too long."
        }), 400

    request_id = "EC-" + uuid.uuid4().hex[:8].upper()
    created_at = datetime.now(timezone.utc).isoformat()

    try:
        with get_db() as connection:
            connection.execute("""
                INSERT INTO emergencies (
                    request_id,
                    patient_name,
                    phone,
                    emergency_type,
                    symptoms,
                    location,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_id,
                values["name"],
                values["phone"],
                values["type"],
                values["symptoms"],
                values["location"],
                "Submitted",
                created_at
            ))

    except sqlite3.Error:
        app.logger.exception(
            "Could not save emergency request"
        )
        return jsonify({
            "error": "Could not save the request. Please try again."
        }), 500

    return jsonify({
        "message": "Emergency request saved successfully.",
        "request_id": request_id,
        "emergency_type": values["type"],
        "status": "Submitted",
        "created_at": created_at
    }), 201

# ---------------- GET EMERGENCIES ----------------

@app.route("/api/emergencies", methods=["GET"])
def get_emergencies():
    try:
        with get_db() as connection:
            rows = connection.execute("""
                SELECT
                    request_id,
                    patient_name,
                    phone,
                    emergency_type,
                    symptoms,
                    location,
                    status,
                    created_at
                FROM emergencies
                ORDER BY id DESC
            """).fetchall()

        return jsonify([
            dict(row) for row in rows
        ]), 200

    except sqlite3.Error:
        app.logger.exception(
            "Could not retrieve emergencies"
        )
        return jsonify({
            "error": "Could not retrieve emergency requests."
        }), 500

# ---------------- GET AMBULANCES ----------------

@app.route("/api/ambulances", methods=["GET"])
def get_ambulances():
    try:
        with get_db() as connection:
            rows = connection.execute("""
                SELECT
                    ambulance_code,
                    ambulance_type,
                    location,
                    status,
                    assigned_request_id
                FROM ambulances
                ORDER BY id
            """).fetchall()

        return jsonify([
            dict(row) for row in rows
        ]), 200

    except sqlite3.Error:
        app.logger.exception(
            "Could not retrieve ambulances"
        )
        return jsonify({
            "error": "Could not retrieve ambulances."
        }), 500

# ---------------- START FLASK ----------------

if __name__ == "__main__":
    app.run(debug=True)
import json
import psycopg2
from datetime import datetime, date
import uuid
import paho.mqtt.client as mqtt

# =====================
# CONFIG
# =====================

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "#"

DB_CONFIG = {
    "host": "localhost",
    "dbname": "healthdb",
    "user": "healthuser",
    "password": "healthpass",
    "port": 5432
}

DEFAULT_USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

ACTIVITY_FACTOR = 1.4  # later replace with training-based model

# =====================
# HELPERS
# =====================

def parse_timestamp(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M%z") if ts else datetime.utcnow()

def calculate_age(dob: date, at: datetime):
    return at.year - dob.year - ((at.month, at.day) < (dob.month, dob.day))

# =====================
# DATABASE
# =====================

def get_user_profile(cur, user_id):
    cur.execute("""
        SELECT height_cm, sex, date_of_birth
        FROM users WHERE id = %s
    """, (str(user_id),))
    row = cur.fetchone()
    if not row:
        raise Exception("User profile not found")
    return row

def insert_raw(cur, data):
    cur.execute("""
        INSERT INTO body_metrics_raw (
            user_id, weight_kg, fat_percent, muscle_percent,
            water_percent, measured_at, source, raw_json
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (
        str(DEFAULT_USER_ID),
        data.get("weight"),
        data.get("fat"),
        data.get("muscle"),
        data.get("water"),
        parse_timestamp(data.get("date")),
        "openscale",
        json.dumps(data)
    ))
    return cur.fetchone()[0]

def compute_features(raw, profile):
    height_cm, sex, dob = profile
    height_m = height_cm / 100
    measured_at = parse_timestamp(raw.get("date"))
    age = calculate_age(dob, measured_at)

    weight = raw.get("weight")
    fat_pct = raw.get("fat")

    bmi = weight / (height_m ** 2)

    if sex == "male":
        bmr = 10*weight + 6.25*height_cm - 5*age + 5
    else:
        bmr = 10*weight + 6.25*height_cm - 5*age - 161

    tdee = bmr * ACTIVITY_FACTOR

    fat_mass = weight * (fat_pct / 100)
    lean_mass = weight - fat_mass

    return bmi, bmr, tdee, fat_mass, lean_mass

def insert_features(cur, data, profile, features):
    bmi, bmr, tdee, fat_mass, lean_mass = features

    cur.execute("""
        INSERT INTO body_metrics_features (
            user_id,
            measured_at,
            weight_kg,
            fat_percent,
            muscle_percent,
            water_percent,
            bmi,
            bmr,
            tdee,
            fat_mass_kg,
            lean_mass_kg
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        str(DEFAULT_USER_ID),
        parse_timestamp(data.get("date")),
        data.get("weight"),
        data.get("fat"),
        data.get("muscle"),
        data.get("water"),
        bmi,
        bmr,
        tdee,
        fat_mass,
        lean_mass
    ))

def on_connect(client, userdata, flags, reason_code, properties):
    print("Connected to MQTT broker")
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)

        print("Received:", data)

        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        insert_raw(cur, data)

        profile = get_user_profile(cur, DEFAULT_USER_ID)
        features = compute_features(data, profile)

        insert_features(cur, data, profile, features)

        print("TOPIC:", msg.topic)
        print("RAW:", msg.payload.decode())

        conn.commit()
        cur.close()
        conn.close()

        print("Saved raw + features")

    except Exception as e:
        print("ERROR:", e)

# =====================
# MAIN
# =====================

def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    start_mqtt()

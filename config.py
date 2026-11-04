"""
config.py - Central configuration for the whole system.

Everything that a viva examiner might ask about (thresholds, zones, MQTT topics,
timings) lives here, so it can be explained and changed in one place.

SIMULATION TIME
    The simulator runs in *accelerated time*: one reading every second, and each
    reading represents ONE MINUTE of river behaviour. So "rising 15 cm / 10 min"
    in the dashboard means 15 cm over the last 10 readings (10 real seconds).
"""

import os

# ---------------------------------------------------------------- paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RUNTIME_DIR = os.path.join(DATA_DIR, "runtime")      # SQLite files (recreated each run)
RESULTS_DIR = os.path.join(DATA_DIR, "results")      # benchmark output
GEO_DIR = os.path.join(DATA_DIR, "geo")              # roads + shelters (simulated)

# ---------------------------------------------------------------- MQTT
MQTT_HOST = "127.0.0.1"
MQTT_PORT = 1883

# Topic layout (all topics start with "flood/")
T_SENSOR = "flood/sensors/{zone}/{sensor}"     # edge  -> fog   (raw readings)
T_FOG_STATUS = "flood/fog/{zone}/status"       # fog   -> local dashboard (every tick)
T_FOG_ALERT = "flood/fog/{zone}/alert"         # fog   -> local sirens / dashboard
T_CLOUD_UPLINK = "flood/cloud/uplink/{zone}"   # fog   -> cloud (summaries + alerts)
T_CLOUD_HEARTBEAT = "flood/cloud/heartbeat"    # cloud -> fog   (alive + acknowledgements)
T_CLOUD_OVERVIEW = "flood/cloud/overview"      # cloud -> dashboard (historical analysis)
T_CTRL_SIM = "flood/control/sim"               # dashboard -> simulator (choose scenario)
T_CTRL_CLOUD = "flood/control/cloud"           # dashboard -> cloud (cut / restore link)

# ---------------------------------------------------------------- timing
TICK_SECONDS = 1.0             # one sensor reading per second (= 1 simulated minute)
SUMMARY_EVERY_TICKS = 10       # fog sends one aggregated summary per 10 readings
HEARTBEAT_TIMEOUT_S = 3.0      # no cloud heartbeat for 3 s  =>  cloud link DOWN
RESEND_AFTER_S = 3.0           # un-acknowledged uplink messages are re-sent after 3 s

# ---------------------------------------------------------------- flood zones
# Demo region: Guwahati, Assam.
# Zones A and C use the published Brahmaputra gauge levels at Guwahati DC Court
# (Warning Level 48.68 m, Danger Level 49.68 m, highest flood level 51.46 m in 2004).
# Zone B (Bharalu, an urban drainage river) uses ILLUSTRATIVE levels.
# Base levels, rates and all sensor readings are SIMULATED.
ZONES = {
    "A": {
        "name": "Pandu - Maligaon Riverside",
        "river": "Brahmaputra",
        "base_level": 47.20,      # normal river stage (m)
        "warning_level": 48.68,   # WL
        "danger_level": 49.68,    # DL
        "caution_margin": 0.50,   # Caution starts 0.5 m below WL
        "spike_threshold": 0.30,  # a jump bigger than this in 1 min = sensor glitch
        "noise": 0.004,
        "center": [26.1690, 91.6840],
        "polygon": [[26.1780, 91.6680], [26.1790, 91.6850], [26.1720, 91.6985],
                    [26.1600, 91.6970], [26.1585, 91.6800], [26.1650, 91.6690]],
    },
    "B": {
        "name": "Anil Nagar - Nabin Nagar (Bharalu basin)",
        "river": "Bharalu",
        "base_level": 1.20,
        "warning_level": 2.50,
        "danger_level": 3.20,
        "caution_margin": 0.40,
        "spike_threshold": 0.25,
        "noise": 0.003,
        "center": [26.1675, 91.7810],
        "polygon": [[26.1750, 91.7690], [26.1745, 91.7830], [26.1680, 91.7930],
                    [26.1600, 91.7910], [26.1600, 91.7740], [26.1680, 91.7680]],
    },
    "C": {
        "name": "Uzan Bazar - Bharalumukh Riverfront",
        "river": "Brahmaputra",
        "base_level": 47.30,
        "warning_level": 48.68,
        "danger_level": 49.68,
        "caution_margin": 0.50,
        "spike_threshold": 0.30,
        "noise": 0.004,
        "center": [26.1840, 91.7420],
        "polygon": [[26.1800, 91.7230], [26.1860, 91.7350], [26.1935, 91.7480],
                    [26.1950, 91.7620], [26.1885, 91.7650], [26.1840, 91.7500],
                    [26.1770, 91.7350], [26.1735, 91.7260]],
    },
}

# ---------------------------------------------------------------- risk engine
# Points-based score (0-100). Each rule adds points and a human-readable reason.
SEVERE_ABOVE_DL = 0.50                       # DL + 0.5 m = severe flooding
LEVEL_POINTS = {"severe": 70, "danger": 50, "warning": 35, "caution": 15}
RATE_POINTS = [(15, 25), (8, 15), (3, 5)]    # (cm rise per 10 min, points)
RAIN_POINTS = [(50, 20), (30, 15), (15, 10), (7.5, 5)]   # (mm/hr, points)
PREDICTION_POINTS = [(30, 15), (60, 8)]      # (minutes until Danger Level, points)
HIGH_VELOCITY = 2.5                          # m/s river flow velocity
VELOCITY_POINTS = 5

# Score -> alert level
ALERT_LEVELS = ["NORMAL", "CAUTION", "WARNING", "CRITICAL"]
LEVEL_BANDS = [(70, "CRITICAL"), (45, "WARNING"), (20, "CAUTION"), (0, "NORMAL")]
DEESCALATE_AFTER_TICKS = 8     # hysteresis: step down only after 8 calm readings

FILTER_WINDOW = 5              # median filter size
STUCK_READINGS = 20            # identical readings in a row = stuck sensor
PREDICTION_WINDOW = 15         # readings used for linear-regression prediction

# ---------------------------------------------------------------- notifications
# Simulated recipients - messages are shown in the dashboard outbox, NOT sent.
SUBSCRIBERS = [
    {"channel": "Telegram", "to": "@zone_{zone}_residents (community group)", "min_level": "WARNING"},
    {"channel": "Email", "to": "ward-officer-zone-{zone}@example.org", "min_level": "CAUTION"},
    {"channel": "Email", "to": "ddma-kamrup-metro@example.org (disaster mgmt)", "min_level": "CRITICAL"},
]
MAINTENANCE_CONTACT = "fog-maintenance@example.org"

# ---------------------------------------------------------------- benchmark
BENCH_WAN_DELAY_MS = 120       # simulated one-way village -> cloud delay
BENCH_WAN_JITTER_MS = 60       # +/- random jitter
BENCH_TICK_MS = 40             # benchmark replays faster than real time

# ---------------------------------------------------------------- news
NEWS_REFRESH_MINUTES = 10
NEWS_QUERIES = {
    "assam": "Assam flood",
    "nepal": "Nepal flood",
    "india": "India flood",
    "global": "flood disaster",
}

WEB_HOST = "127.0.0.1"
WEB_PORT = 5000

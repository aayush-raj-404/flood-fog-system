# Smart Disaster Early Warning and Evacuation System using Fog Computing

A flood early-warning system for Guwahati (Assam) built as a three-layer IoT
architecture: **IoT sensors → 3 fog nodes → cloud**. All three layers talk to each
other over MQTT.

| Module | What it does |
|---|---|
| 1. Flood early warning | 9 simulated sensors. Each of the 3 fog nodes filters its zone's data, predicts the river level and raises local alerts (Normal / Caution / Warning / Critical) with reasons, even when the cloud is unreachable |
| 2. Smart evacuation | Leaflet map. Finds the safest shelter with Dijkstra on a risk-weighted road graph and avoids the zones the fog nodes have flagged |
| 3. Flood news | Real headlines (Google News / Bing News RSS) for Assam, Nepal, India and global floods. For information only and never triggers alerts |
| Fog vs Cloud | A measured experiment: alert latency, upstream bandwidth and behaviour during an internet outage |

---

## 1. Setup on Windows 11 (one time)

1. **Python 3.10 or newer**: https://www.python.org/downloads/
   During install, tick **"Add python.exe to PATH"**.
2. **Mosquitto MQTT broker**: https://mosquitto.org/download/ (Windows x64 installer, default options).
   `run.py` starts Mosquitto automatically if it isn't already running.
3. Open a terminal **in this folder** (in File Explorer: right-click → *Open in Terminal*) and run:
   ```
   pip install -r requirements.txt
   ```

## 2. Run

```
python run.py
```
The dashboard opens at **http://127.0.0.1:5000**. Press **Ctrl+C** in the terminal to stop everything.

`run.py` starts six separate processes: cloud, fog A, fog B, fog C, sensor simulator and web dashboard.
To show that the fog nodes are independent, you can also run any part on its own in its own terminal:
```
python -m cloud.cloud_server
python -m fog.fog_node A
python -m sensors.simulator
python -m web.app
```

Internet is needed only for **map tiles** and **news**. Everything else works offline.

### Troubleshooting
| Problem | Fix |
|---|---|
| "Mosquitto was not found" | Install Mosquitto, or start it yourself: `"C:\Program Files\mosquitto\mosquitto.exe" -v` |
| Port 5000 already in use | Change `WEB_PORT` in `config.py` |
| `pip` not recognised | Use `py -m pip install -r requirements.txt` and `py run.py` |
| News page empty | Check the internet connection, then press **Refresh** |

---

## 3. Live demo script (about 5 minutes)

1. **Overview.** Three zones, each watched by its own fog node. Click **Flash flood in Zone A**.
   Within about 45 s Zone A goes NORMAL → CAUTION → WARNING → CRITICAL, and each step shows its reasons
   (level above WL, rising X cm / 10 min, rainfall, predicted time to Danger Level).
2. Click **Sensor fault in Zone C**. Glitches appear as red ✕ marks and are rejected by the fog's filter,
   so there is no false flood alarm. When the sensor freezes, a maintenance email appears in the outbox.
3. **Fog Network** → **Cut cloud link**. Then go back to Overview and click **River rise in Zone B**.
   The alert is still raised locally (the Alerts page shows *cloud OFFLINE*), and the
   "buffered" counters go up.
   Click **Restore cloud link**: the backlog syncs, and triangles appear in the cloud chart (data delivered late).
4. **Evacuation** → choose **Pandu Port (Zone A)**. The route leads out of the critical zone to high ground.
   Then try **Anil Nagar (Zone B)**.
5. **Fog vs Cloud** → **Run experiment** (~15 s). Explain the latency, bandwidth and outage results.
6. **Flood News**: real headlines, with source, time and a link to each article.
7. **Alerts**: alert history and the simulated Telegram / email outbox.

Press **All normal** to reset the river levels.

---

## 4. How it works

### Architecture and MQTT topics
```
flood/sensors/{zone}/{sensor}   sensor -> fog       raw reading every second
flood/fog/{zone}/status         fog -> dashboard    filtered values, score, reasons
flood/fog/{zone}/alert          fog -> sirens/dash  alert-level changes (decided locally)
flood/cloud/uplink/{zone}       fog -> cloud        10-minute summaries + alerts (QoS 1)
flood/cloud/heartbeat           cloud -> fog        "I'm alive" + acknowledgements
flood/cloud/overview            cloud -> dashboard  historical analysis
flood/control/sim | cloud       dashboard -> ...    demo controls
```

### Fog node pipeline (`fog/risk_engine.py`)
1. **Validate**: physical range check; stuck-sensor detection (20 identical readings).
2. **Filter**: spike rejection against the recent median, then a 5-point median filter.
3. **Features**: rise per 10 min, rainfall intensity, rain in the last hour, flow velocity.
4. **Predict**: least-squares linear regression on the last 15 levels gives the minutes until the Danger Level.
5. **Score (0–100)**:

| Rule | Points |
|---|---|
| Level ≥ DL + 0.5 m / ≥ DL / ≥ WL / within 0.5 m of WL | 70 / 50 / 35 / 15 |
| Rise per 10 min ≥ 15 / 8 / 3 cm | 25 / 15 / 5 |
| Rain ≥ 50 / 30 / 15 / 7.5 mm/hr | 20 / 15 / 10 / 5 |
| Predicted to reach DL in ≤ 30 / ≤ 60 min | 15 / 8 |
| Flow velocity ≥ 2.5 m/s | 5 |

   Score ≥ 70 → CRITICAL, ≥ 45 → WARNING, ≥ 20 → CAUTION, otherwise NORMAL.
6. **Hysteresis**: alerts go up immediately, but only come down after 8 calm readings, so they don't flicker.

### Offline operation (store-and-forward)
- The cloud sends a heartbeat every second. If the fog node hears nothing for 3 s, it marks the cloud as offline.
- Uplink messages are always written to a local SQLite outbox first.
- They are deleted only after the cloud acknowledges them. The cloud acknowledges only a gap-free sequence, so nothing is lost.

### Evacuation (`web/routing.py`)
- Edge cost = length × risk penalty: Normal ×1, Caution ×1.5, Warning ×6, Critical ×40.
- Shelters inside Warning/Critical zones, and shelters that are full or closed, are excluded.
- The remaining shelters are ranked by route cost + occupancy penalty + low-elevation penalty.

### Fog vs Cloud experiment (`benchmark/fog_vs_cloud.py`)
- Both architectures get the same seeded sensor data and use the same risk engine over the real broker.
- The internet link is **simulated**: 120 ± 60 ms each way, with an outage in minutes 160–230.
- Results are saved to `data/results/`.

---

## 5. Honest limitations (say these in the viva)
- Sensors are **simulated** in accelerated time: 1 s of demo time = 1 minute of river behaviour.
- Gauge levels, shelters, capacities, elevations and the road network are **illustrative demo data**,
  not official or verified safety information.
- All processes run on one laptop and share one MQTT broker, with zones separated by topic.
  A real deployment would put a gateway/broker in each zone.
- Notifications are simulated (outbox only).
- The WAN delay in the benchmark is simulated, so absolute numbers depend on that setting.
  The fog advantage itself is measured.

## 6. Folder structure
```
run.py                  one-command launcher
config.py               zones, thresholds, topics, timings
common.py               MQTT + logging helpers
sensors/                IoT layer (simulator + physical model)
fog/                    fog node + risk engine
cloud/                  cloud server (SQLite history + analysis)
benchmark/              fog vs cloud experiment
web/                    Flask API, routing, news, dashboard (static/)
data/geo/               simulated roads + shelters
data/runtime/           SQLite databases (recreated each run)
data/results/           benchmark output (JSON + CSV)
```

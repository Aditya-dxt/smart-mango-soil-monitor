import json, sqlite3, threading
from pathlib import Path

_lock = threading.Lock()


class DB:
    def __init__(self, path: str = "data/orchard.db"):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS telemetry(
          id INTEGER PRIMARY KEY, ts TEXT, node_id TEXT, zone TEXT, soil_moisture REAL,
          soil_temp REAL, air_temp REAL, humidity REAL, battery REAL,
          nitrogen REAL, phosphorus REAL, potassium REAL, ph REAL, soil_type TEXT);
        CREATE TABLE IF NOT EXISTS decisions(id INTEGER PRIMARY KEY, ts TEXT, zone TEXT, body TEXT);
        CREATE TABLE IF NOT EXISTS commands(id INTEGER PRIMARY KEY, ts TEXT, zone TEXT,
          minutes INTEGER, source TEXT, delivered INTEGER DEFAULT 0);
        CREATE INDEX IF NOT EXISTS ix_t ON telemetry(zone, ts);
        """)
        # Migrate existing schema if columns don't exist
        for col, col_type in [("nitrogen", "REAL"), ("phosphorus", "REAL"), ("potassium", "REAL"),
                              ("ph", "REAL"), ("soil_type", "TEXT")]:
            try:
                self.conn.execute(f"ALTER TABLE telemetry ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass

    def add_telemetry(self, r: dict):
        with _lock:
            self.conn.execute(
                "INSERT INTO telemetry(ts,node_id,zone,soil_moisture,soil_temp,air_temp,humidity,battery,"
                "nitrogen,phosphorus,potassium,ph,soil_type)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (r["ts"], r["node_id"], r["zone"], r["soil_moisture"], r.get("soil_temp"),
                 r["air_temp"], r["humidity"], r.get("battery"),
                 r.get("nitrogen", 140.0), r.get("phosphorus", 25.0), r.get("potassium", 180.0),
                 r.get("ph", 6.5), r.get("soil_type", "Alluvial Loam")))
            self.conn.commit()

    def telemetry(self, zone=None, limit=500):
        q, a = "SELECT * FROM telemetry", []
        if zone:
            q += " WHERE zone=?"; a.append(zone)
        q += " ORDER BY id DESC LIMIT ?"; a.append(limit)
        return [dict(x) for x in self.conn.execute(q, a)][::-1]

    def add_decision(self, d: dict):
        with _lock:
            self.conn.execute("INSERT INTO decisions(ts,zone,body) VALUES(?,?,?)",
                              (d["ts"], d["zone"], json.dumps(d)))
            self.conn.commit()

    def decisions(self, limit=50):
        return [json.loads(x["body"]) for x in
                self.conn.execute("SELECT body FROM decisions ORDER BY id DESC LIMIT ?", (limit,))]

    def add_command(self, ts, zone, minutes, source):
        with _lock:
            self.conn.execute("INSERT INTO commands(ts,zone,minutes,source) VALUES(?,?,?,?)",
                              (ts, zone, minutes, source))
            self.conn.commit()

    def pending_commands(self, zone):
        rows = [dict(x) for x in self.conn.execute(
            "SELECT * FROM commands WHERE zone=? AND delivered=0 ORDER BY id", (zone,))]
        with _lock:
            self.conn.execute("UPDATE commands SET delivered=1 WHERE zone=? AND delivered=0", (zone,))
            self.conn.commit()
        return rows

    def recent_commands(self, limit=50):
        return [dict(x) for x in self.conn.execute(
            "SELECT * FROM commands ORDER BY id DESC LIMIT ?", (limit,))]

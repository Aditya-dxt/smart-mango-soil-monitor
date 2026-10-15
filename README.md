<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:2e7d32,50:f9a825,100:ef6c00&height=200&section=header&text=Smart%20Mango%20Soil%20Monitor&fontSize=44&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=IoT%20%2B%20Cloud%20%2B%20Agentic%20AI%20for%20Healthier%20Mango%20Orchards&descAlignY=60&descSize=18" alt="Smart Mango Soil Monitor banner" />

<a href="https://github.com/Aditya-dxt/smart-mango-soil-monitor">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=20&duration=3200&pause=900&color=F9A825&center=true&vCenter=true&width=720&lines=%F0%9F%8C%B1+Sense+the+soil+in+real+time;%E2%98%81%EF%B8%8F+Stream+data+to+the+cloud+over+MQTT;%F0%9F%A4%96+Let+an+AI+agent+diagnose+what+is+wrong;%F0%9F%A5%AD+Get+exact+steps+to+grow+better+mangoes" alt="Typing animation" />
</a>

<br/>

![Status](https://img.shields.io/badge/status-in%20development-orange?style=for-the-badge)
![Domain](https://img.shields.io/badge/domain-IoT%20%2B%20AI-2e7d32?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)

![ESP32](https://img.shields.io/badge/ESP32-000000?style=flat-square&logo=espressif&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-660066?style=flat-square&logo=mqtt&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)
![Claude](https://img.shields.io/badge/Agent-Claude%20API-D97757?style=flat-square&logo=anthropic&logoColor=white)

**A solar-powered soil sensing device that reads soil health live, ships it to the cloud, and uses an agentic AI to tell a mango farmer exactly what to fix and how.**

[Overview](#-overview) •
[Features](#-features) •
[Architecture](#-system-architecture) •
[Hardware](#-hardware) •
[Agentic AI](#-agentic-ai-engine) •
[Getting Started](#-getting-started) •
[Roadmap](#-roadmap)

</div>

---

## 📑 Table of Contents

- [🌱 Overview](#-overview)
- [🎯 Problem and Solution](#-problem-and-solution)
- [✨ Features](#-features)
- [🏗️ System Architecture](#-system-architecture)
- [🔌 Hardware](#-hardware)
- [📡 Data Pipeline](#-data-pipeline)
- [🤖 Agentic AI Engine](#-agentic-ai-engine)
- [📊 Soil Health Score](#-soil-health-score)
- [🖥️ Dashboard](#-dashboard)
- [🧰 Tech Stack](#-tech-stack)
- [📁 Repository Structure](#-repository-structure)
- [🚀 Getting Started](#-getting-started)
- [🗺️ Roadmap](#-roadmap)
- [⚠️ Limitations and Honest Notes](#-limitations-and-honest-notes)
- [🤝 Contributing](#-contributing)
- [👤 Author](#-author)

---

## 🌱 Overview

**Smart Mango Soil Monitor** is a hardware + software (IoT) project for **mango orchards**. A field-deployed node measures key soil parameters, sends them to the cloud, and a dashboard turns the raw numbers into something a farmer can act on:

1. **Sense**: probes buried at root depth measure moisture, pH, NPK, salinity and temperature.
2. **Send**: an ESP32 publishes readings to the cloud over MQTT.
3. **Think**: an **agentic AI** compares readings with mango requirements, diagnoses problems, and plans fixes.
4. **Act**: the dashboard shows a health score and step-by-step recommendations, and can trigger irrigation or alerts.

> 💡 **What makes it different:** most mango-AI work stops at classifying images offline. This project closes the loop from **soil → cloud → decision → action**, in real time.

---

## 🎯 Problem and Solution

| 😟 Problem | ✅ Our approach |
|---|---|
| Farmers guess soil condition by eye or wait days for a lab test | Continuous, live soil readings from in-field sensors |
| Raw numbers (pH 8.1, N = low) are hard to interpret | An AI agent translates them into plain-language diagnoses |
| Generic fertilizer advice ignores growth stage and weather | Context-aware advice using growth stage, history and forecast |
| Over- or under-irrigation wastes water and hurts yield | Threshold and AI-driven irrigation control |
| Advice is often only in English | Planned Hindi output and WhatsApp/SMS alerts |

---

## ✨ Features

### 🔧 Device
- 🌡️ Multi-sensor soil probing: **moisture, pH, N-P-K, EC (salinity), soil temperature**
- 🌤️ Ambient **air temperature and humidity**
- 🔋 **Solar + battery** with deep-sleep cycles for long field life
- 📶 Wi-Fi first, with an optional GSM/LoRa path for remote orchards
- 💦 Optional **relay output** for pump or valve control

### ☁️ Cloud and Data
- 📨 Lightweight **MQTT** telemetry
- 🗄️ Time-series storage with history and trend queries
- 🔔 Threshold alerts (push, email, SMS)

### 🤖 Intelligence
- 🧠 **Agentic AI** with tool calling (readings, history, weather, guidelines, actions)
- 📚 **RAG** over mango cultivation guidelines so advice is grounded, not invented
- 🥭 **Growth-stage-aware** recommendations (dormant, flowering, fruit set, fruit growth)
- 🛡️ **Rule-based safety layer** underneath the AI, so critical limits are never missed

### 🖥️ Dashboard
- 📈 Live gauges and historical charts
- 💯 **Soil Health Score** from 0 to 100
- 💬 Chat with the agent: *"Why is my score low?"*
- 🗺️ Multi-node support for large orchards

---

## 🏗️ System Architecture

```mermaid
flowchart LR
    subgraph FIELD["🌳 Orchard Field"]
        direction TB
        S1["💧 Moisture"]
        S2["⚗️ pH"]
        S3["🧪 NPK + EC"]
        S4["🌡️ Soil / Air Temp"]
        MCU["🔌 ESP32 Node<br/>solar + battery"]
        RLY["🚰 Relay<br/>pump / valve"]
        S1 --> MCU
        S2 --> MCU
        S3 --> MCU
        S4 --> MCU
        MCU --> RLY
    end

    subgraph CLOUD["☁️ Cloud"]
        direction TB
        BRK["📨 MQTT Broker"]
        API["⚙️ Backend API"]
        DB[("🗄️ Database")]
        AGT["🤖 AI Agent<br/>LLM + Tools + RAG"]
        KB[("📚 Mango Knowledge Base")]
        BRK --> API
        API --> DB
        API <--> AGT
        AGT <--> KB
        DB --> AGT
    end

    subgraph USER["👨‍🌾 Farmer"]
        direction TB
        DASH["🖥️ Web Dashboard"]
        ALERT["📱 Alerts<br/>SMS / Push / WhatsApp"]
    end

    MCU -- "JSON over MQTT / TLS" --> BRK
    API -- "WebSocket / REST" --> DASH
    AGT --> ALERT
    AGT -- "irrigation command" --> BRK
    BRK -- "command" --> MCU

    style FIELD fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style CLOUD fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    style USER fill:#fff8e1,stroke:#f9a825,stroke-width:2px
```

---

## 🔌 Hardware

### 🧾 Bill of Materials (suggested)

| # | Component | Purpose | Notes |
|---|---|---|---|
| 1 | **ESP32 DevKit** | Main controller, Wi-Fi | Use **ADC1** pins for analog sensors (ADC2 conflicts with Wi-Fi) |
| 2 | Capacitive soil moisture sensor | Water content | Prefer capacitive over resistive (resistive probes corrode) |
| 3 | Analog soil pH sensor | Acidity / alkalinity | Needs calibration with buffer solutions |
| 4 | RS485 NPK + EC probe | N, P, K and salinity | Approximate indicator, not lab grade |
| 5 | MAX485 / RS485-TTL module | Talk to the NPK probe | Modbus RTU |
| 6 | DS18B20 (waterproof) | Soil temperature | 1-Wire |
| 7 | BME280 or DHT22 | Air temperature and humidity | BME280 over I2C is more accurate |
| 8 | Relay module (optional) | Pump / valve control | Opto-isolated |
| 9 | Solar panel + 18650 Li-ion + charge controller | Off-grid power | Deep sleep between readings |
| 10 | IP65 enclosure, glands, probe cables | Weatherproofing | Bury probes at root depth |

### 📍 Suggested ESP32 Pin Map

| Signal | ESP32 pin | Interface |
|---|---|---|
| Soil moisture | `GPIO34` | ADC1 |
| Soil pH | `GPIO35` | ADC1 |
| DS18B20 | `GPIO4` | 1-Wire |
| BME280 SDA / SCL | `GPIO21` / `GPIO22` | I2C |
| RS485 RX / TX | `GPIO16` / `GPIO17` | UART2 |
| RS485 DE/RE | `GPIO5` | Digital out |
| Relay | `GPIO26` | Digital out |

> 🔧 This is a starting plan. Adjust it to your board and verify against your sensor datasheets.

### 🔋 Node Lifecycle

```mermaid
stateDiagram-v2
    [*] --> DeepSleep
    DeepSleep --> WakeUp: timer (every 15-30 min)
    WakeUp --> ReadSensors
    ReadSensors --> ValidateData
    ValidateData --> ConnectWiFi: values sane
    ValidateData --> DeepSleep: sensor error (log and retry)
    ConnectWiFi --> PublishMQTT
    PublishMQTT --> CheckCommands
    CheckCommands --> RunIrrigation: command received
    CheckCommands --> DeepSleep: nothing to do
    RunIrrigation --> DeepSleep
```

---

## 📡 Data Pipeline

```mermaid
sequenceDiagram
    autonumber
    participant N as 🔌 ESP32 Node
    participant B as 📨 MQTT Broker
    participant A as ⚙️ Backend API
    participant D as 🗄️ Database
    participant G as 🤖 AI Agent
    participant U as 🖥️ Dashboard

    N->>B: publish soil/{node_id}/telemetry (JSON)
    B->>A: forward message
    A->>A: validate and normalize
    A->>D: store reading
    A-->>U: push live update (WebSocket)
    A->>G: trigger analysis (schedule or threshold)
    G->>D: fetch history and trends
    G->>G: reason with mango guidelines (RAG)
    G-->>A: diagnosis + recommended actions
    A-->>U: show score and advice
    opt Irrigation needed
        G->>B: publish soil/{node_id}/command
        B->>N: relay ON for N minutes
    end
```

### 📦 Example MQTT Payload

**Topic:** `soil/{node_id}/telemetry`

```json
{
  "node_id": "mango-node-01",
  "timestamp": "2026-10-16T09:30:00Z",
  "soil": {
    "moisture_pct": 34.2,
    "ph": 6.8,
    "temperature_c": 27.5,
    "ec_ms_cm": 0.9,
    "n_mg_kg": 42,
    "p_mg_kg": 18,
    "k_mg_kg": 160
  },
  "air": {
    "temperature_c": 31.0,
    "humidity_pct": 58
  },
  "battery_v": 3.92
}
```

> The values above are illustrative sample data, not real measurements.

---

## 🤖 Agentic AI Engine

The agent is more than a chatbot. It **observes, reasons, and acts** using tools.

```mermaid
flowchart TD
    T(["⏰ Trigger<br/>schedule or threshold crossed"]) --> R["📥 Get latest readings and history"]
    R --> RB{"🛡️ Rule-based safety checks<br/>any hard limit breached?"}
    RB -- "Yes" --> AL["🚨 Immediate alert"]
    RB -- "No" --> CTX["🧩 Add context<br/>growth stage, weather, season"]
    AL --> CTX
    CTX --> RAG["📚 Retrieve mango guidelines (RAG)"]
    RAG --> LLM["🧠 LLM reasoning<br/>diagnose and plan"]
    LLM --> DEC{"Action needed?"}
    DEC -- "Irrigate" --> IR["🚰 Trigger irrigation"]
    DEC -- "Fertilize / amend" --> REC["📝 Recommendation with quantities"]
    DEC -- "All good" --> OK["✅ Log: soil healthy"]
    IR --> LOG[("🗄️ Log decision and reasoning")]
    REC --> NOTIFY["📱 Notify farmer"]
    NOTIFY --> LOG
    OK --> LOG
```

### 🛠️ Agent Tools

| Tool | What it does |
|---|---|
| `get_latest_readings` | Current soil and air values for a node |
| `get_history` | Trends over hours, days or weeks |
| `get_weather_forecast` | Rain and temperature outlook, to skip needless irrigation |
| `search_mango_guidelines` | RAG lookup in the knowledge base |
| `compute_health_score` | Deterministic score calculation |
| `trigger_irrigation` | Switch the relay for a set duration (with safety caps) |
| `send_alert` | Push, SMS or WhatsApp notification |
| `log_recommendation` | Save the advice and its reasoning for audit |

### 🧭 Design Principles
- **Grounded:** recommendations cite the guideline passage they came from.
- **Safe by default:** hard rules and caps sit below the LLM, and irrigation has maximum durations.
- **Explainable:** every recommendation shows *why* it was made.
- **Human in the loop:** fertilizer advice is a suggestion, and the farmer decides.

### 📚 Knowledge Base Sources (planned)
Mango cultivation guidance from agricultural bodies and universities such as **ICAR**, **NHB** and state agricultural universities.

---

## 📊 Soil Health Score

Each parameter is scored against the mango target range, then combined with weights into a **0 to 100** score.

| Parameter | Indicative target for mango* | Role |
|---|---|---|
| 🧪 pH | about 5.5 to 7.5 | Controls nutrient availability |
| 💧 Moisture | moderate, well-drained (no waterlogging) | Root health and fruit set |
| 🌿 N, P, K | balanced, by growth stage | Growth, flowering, fruit quality |
| 🧂 EC (salinity) | low | Mango is sensitive to salinity |
| 🌡️ Soil temperature | within a healthy root-zone range | Root activity |

> \*These are **indicative starting ranges**. Final thresholds will be validated against ICAR/NHB guidance and local soil test data before use.

```mermaid
stateDiagram-v2
    direction LR
    [*] --> Optimal
    Optimal: 🟢 Optimal (80-100)
    Watch: 🟡 Watch (50-79)
    Critical: 🔴 Critical (0-49)
    Optimal --> Watch: parameter drifts
    Watch --> Critical: limit breached
    Critical --> Watch: corrective action works
    Watch --> Optimal: back in range
```

```text
Score = Σ ( weight_i × parameter_score_i )     where parameter_score_i ∈ [0, 1]
```

---

## 🖥️ Dashboard

| Module | Description |
|---|---|
| 🏠 **Overview** | Soil Health Score, live gauges, node status and battery |
| 📈 **Trends** | Daily, weekly and seasonal charts for every parameter |
| 🤖 **Advisor** | AI diagnosis, step-by-step recommendations with quantities |
| 💬 **Chat** | Ask the agent questions in natural language |
| 🚰 **Irrigation** | Manual and automatic control with a history log |
| 🔔 **Alerts** | Configurable thresholds and notification channels |
| 🗺️ **Nodes** | Multi-sensor view across the orchard |

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| 🔌 Firmware | ESP32, Arduino framework (C++) or PlatformIO |
| 📨 Messaging | MQTT (Mosquitto / HiveMQ), TLS |
| ⚙️ Backend | Python, FastAPI, WebSockets |
| 🗄️ Database | PostgreSQL (Supabase) with time-series tables |
| 🖥️ Frontend | Next.js, React, Recharts, Tailwind CSS |
| 🤖 AI | Claude API with tool calling, RAG (vector search) |
| 🔁 Workflows | Scheduled jobs (LangGraph or n8n) |
| ☀️ Power | Solar panel, 18650 Li-ion, charge controller |

---

## 📁 Repository Structure

```text
smart-mango-soil-monitor/
├── 📂 firmware/          # ESP32 code (sensors, MQTT, deep sleep)
├── 📂 backend/           # FastAPI service, MQTT consumer, REST + WebSocket
├── 📂 dashboard/         # Next.js web app
├── 📂 agent/             # LLM agent, tools, RAG pipeline, safety rules
│   ├── tools/
│   └── knowledge_base/
├── 📂 hardware/          # Wiring diagrams, BOM, enclosure notes
├── 📂 docs/              # Architecture notes, calibration data, reports
├── 📂 scripts/           # Seed data, simulators, utilities
├── 📄 .env.example
├── 📄 LICENSE
└── 📄 README.md
```

---

## 🚀 Getting Started

> 🚧 The project is under active development. Commands below show the intended workflow and will be finalized as each module lands.

### 1️⃣ Clone

```bash
git clone https://github.com/Aditya-dxt/smart-mango-soil-monitor.git
cd smart-mango-soil-monitor
```

### 2️⃣ Configure environment

```bash
cp .env.example .env
```

```env
# MQTT
MQTT_HOST=your-broker-host
MQTT_PORT=8883
MQTT_USERNAME=your-user
MQTT_PASSWORD=your-password

# Database
DATABASE_URL=postgresql://user:password@host:5432/soil

# AI agent
ANTHROPIC_API_KEY=your-key

# Weather (optional)
WEATHER_API_KEY=your-key
```

### 3️⃣ Flash the firmware

1. Open `firmware/` in **PlatformIO** or the **Arduino IDE**.
2. Set Wi-Fi and MQTT credentials in the config header.
3. Flash to the ESP32 and open the serial monitor at `115200` baud to confirm readings.

### 4️⃣ Run the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 5️⃣ Run the dashboard

```bash
cd dashboard
npm install
npm run dev
```

### 6️⃣ No hardware yet? Use the simulator

```bash
python scripts/simulate_node.py --node mango-node-01
```

This publishes fake telemetry so you can build and test the backend, dashboard and agent before the sensors arrive.

---

## 🗺️ Roadmap

```mermaid
gantt
    title Project Phases (tentative)
    dateFormat YYYY-MM-DD
    axisFormat %b %d
    section Hardware
    Moisture, pH, temp on ESP32        :p1, 2026-10-17, 14d
    NPK + EC probe integration         :p4, after p3, 14d
    Solar power and enclosure          :p6, after p5, 14d
    section Cloud
    MQTT pipeline and database         :p2, after p1, 14d
    section Software
    Basic live dashboard               :p3, after p2, 14d
    Agentic AI with RAG                :p5, after p4, 21d
    section Validation
    Field testing and calibration      :p7, after p6, 21d
```

### ✅ Progress Checklist

- [x] Repository created
- [ ] **Phase 1:** ESP32 reading moisture, pH and temperature over serial
- [ ] **Phase 2:** MQTT pipeline and database storage
- [ ] **Phase 3:** Live dashboard with charts
- [ ] **Phase 4:** NPK and EC sensing, Soil Health Score
- [ ] **Phase 5:** Agentic AI with RAG and tool calling
- [ ] **Phase 6:** Alerts, irrigation relay, solar power and enclosure
- [ ] **Phase 7:** Field testing, sensor calibration, accuracy report

### 🔮 Future Scope
- 🌐 Hindi and regional-language advice, with voice and WhatsApp delivery
- 🍃 Link soil data with leaf-image disease detection for a whole-plant view
- 📉 Predictive alerts (e.g. moisture reaching critical in 2 days)
- 📡 LoRa mesh for large orchards without Wi-Fi
- 💰 Fertilizer cost estimation

---

## ⚠️ Limitations and Honest Notes

- 🧪 Low-cost **NPK and pH sensors drift** and are **indicative, not lab grade**. We plan to calibrate against lab soil tests and publish the results.
- 🌦️ Recommendations are **decision support**, not a replacement for an agronomist or a lab soil test.
- 📏 Target ranges are starting values and will be refined with expert guidance.
- 🔬 Real-world accuracy, battery life and latency will be measured and reported as the project matures.

---

## 🤝 Contributing

Contributions, ideas and issues are welcome.

1. 🍴 Fork the repository
2. 🌿 Create a branch: `git checkout -b feature/your-feature`
3. 💾 Commit: `git commit -m "Add your feature"`
4. 📤 Push: `git push origin feature/your-feature`
5. 🔁 Open a Pull Request

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for details.

---

## 👥 Team

<div align="center">

| 👤 Member | 🛠️ Role | 🔗 GitHub |
|:---:|:---:|:---:|
| **Aditya Dixit** | _Add role_ | [@Aditya-dxt](https://github.com/Aditya-dxt) |
| **Vaibhav Tripathi** | _Add role_ | [@github-username](https://github.com/github-username) |
| **Atharva Gupta** | _Add role_ | [@github-username](https://github.com/github-username) |
| **Sonakshi Verma** | _Add role_ | [@github-username](https://github.com/github-username) |
| **Aastha Tiwari** | _Add role_ | [@github-username](https://github.com/github-username) |
| **Satakshi Saxena** | _Add role_ | [@github-username](https://github.com/github-username) |

<br/>

⭐ **If this project helps you, please give it a star!** ⭐

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:ef6c00,50:f9a825,100:2e7d32&height=120&section=footer" alt="footer" />

</div>

const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, ImageRun, LevelFormat, Footer, PageNumber } = require("docx");

const FONT = "Calibri";
const W = 9026; // A4 content width (DXA) with 1" margins
const P = (t, o = {}) => new Paragraph({ spacing: { after: 140, line: 300 }, alignment: o.align, children: [new TextRun({ text: t, font: FONT, size: 23, ...o.run })] });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 140 }, children: [new TextRun({ text: t, font: FONT, bold: true, size: 30, color: "1B5E20" })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 220, after: 100 }, children: [new TextRun({ text: t, font: FONT, bold: true, size: 25, color: "2E7D32" })] });
const B = (t) => new Paragraph({ numbering: { reference: "b", level: 0 }, spacing: { after: 90, line: 290 }, children: [new TextRun({ text: t, font: FONT, size: 23 })] });
const Nr = (ref) => (t) => new Paragraph({ numbering: { reference: ref, level: 0 }, spacing: { after: 110, line: 300 }, children: [new TextRun({ text: t, font: FONT, size: 23 })] });
const N = Nr("n"), N2 = Nr("n2"), N3 = Nr("n3");
const cap = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [new TextRun({ text: t, font: FONT, italics: true, size: 20, color: "555555" })] });
const img = (f, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(f), transformation: { width: w, height: h }, altText: { title: f, description: f, name: f } })] });

const border = { style: BorderStyle.SINGLE, size: 4, color: "BFC9BD" };
const borders = { top: border, bottom: border, left: border, right: border };
function table(widths, rows, headerFill = "2E7D32") {
  return new Table({
    width: { size: widths.reduce((a, b) => a + b), type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({ tableHeader: i === 0, children: r.map((c, j) => new TableCell({
      width: { size: widths[j], type: WidthType.DXA }, borders,
      shading: { type: ShadingType.CLEAR, fill: i === 0 ? headerFill : (i % 2 ? "FFFFFF" : "F3F7F2") },
      margins: { top: 70, bottom: 70, left: 110, right: 110 },
      children: [new Paragraph({ children: [new TextRun({ text: String(c), font: FONT, size: 20, bold: i === 0, color: i === 0 ? "FFFFFF" : "000000" })] })] })) })) });
}
const styles = { default: { document: { run: { font: FONT, size: 23 } } },
  paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 30, bold: true }, paragraph: { outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 25, bold: true }, paragraph: { outlineLevel: 1 } }] };
const numbering = { config: [
  { reference: "b", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
  ...["n", "n2", "n3"].map(r => ({ reference: r, levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }))] };
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Page ", font: FONT, size: 18, color: "777777" }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: "777777" })] })] });
const section = (children) => ({ properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } }, footers: { default: footer }, children });

/* ---------------------------------------------------------------- INTRODUCTION */
const intro = [
  new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: "An Agentic AI and IoT-Based Intelligent Soil Monitoring and Precision Management System for Mango Orchards", font: FONT, bold: true, size: 34, color: "1B5E20" })] }),
  H1("1. Introduction"),
  P("Farming still carries much of the weight of national food security. It keeps rural households employed, and fruit that is sold abroad brings in foreign income. Among tree fruits, mango has a special place: people buy it in large quantities at home, and good-quality fruit finds buyers overseas as well."),
  P("A mango tree reacts to its surroundings through almost the whole year. The moisture held in the soil, the temperature of the air and the humidity around the canopy all shape when the tree flowers, how well the fruit sets, how fast it swells, and how likely the orchard is to meet disease or insect pressure. Water is the most delicate of these factors, because more is not simply better. Growers usually hold back irrigation in the weeks before flowering, keep the soil adequately moist from flowering until the fruit is nearly mature, and then ease off again shortly before harvest. An orchard manager therefore has to know two things at once: how wet the soil is right now, and how wet it should be at this point in the season."),
  P("The usual way of finding out is to walk the rows, press a hand into the ground and irrigate by habit or by the calendar. This costs almost nothing to start, which explains why it is so common. Its weakness is that it needs people and time, it cannot be done around the clock, and what the grower notices is seldom written down in a form that could later guide a decision. As orchards grow larger and fewer people want to work on the land, this approach becomes harder to sustain."),
  P("Cheap sensors and wireless links offer a way out. A wireless sensor network places small battery-powered nodes across the orchard, each with a soil-moisture probe and an air temperature and humidity sensor, and sends their readings to a gateway and then to the cloud. With this in place, a grower can see conditions on a phone without visiting every block. Many deployments, however, stop at showing numbers on a screen or at a single fixed moisture threshold. Such systems do not know which growth stage the trees are in, they cannot allow for rain that is about to fall, and they have no way to tell a dry field from a broken sensor."),
  P("Artificial intelligence can fill part of that gap. Reinforcement learning is a natural fit for irrigation, since the controller learns by acting, receiving a reward and adjusting. A Deep Q-Network (DQN) extends the idea by using a neural network to estimate how good each possible action is in the current situation. More recently, the notion of an agentic system has gained ground: software that observes its environment, reasons about what to do, acts through tools, and keeps a record of what happened. In an orchard this means reading the sensors, taking account of growth stage and weather, proposing an irrigation amount, checking that proposal against safety rules, driving the valve, and explaining the outcome to the farmer in plain words. A learned policy should not be given unchecked control of a valve, so a rule-based safety layer sits between the learner and the hardware."),
  P("Earlier studies have combined sensor networks, IoT platforms and learning methods for agriculture, but most of them fall into one of three groups. Some only collect and forward data. Others train a controller in simulation without describing how it would run on real hardware. A few offer a working pipeline but give no explanation of their decisions and no protection against sensor faults. Very few build the stage-dependent water pattern of mango into the control logic. This leaves room for a complete system that joins field sensing, a decision-making agent and a farmer-facing interface."),
  P("This work presents such a system for mango orchards. Soil-moisture, air-temperature and humidity readings are gathered by ESP32 nodes and sent over MQTT to a FastAPI service. There, an agent combines a DQN planner trained on a mango-specific soil-water model with a deterministic safety guard and an optional language-model advisor that writes the explanation. The farmer follows everything on a web dashboard, can override the valve by hand, and receives alerts about dry soil, low batteries, suspect sensors and weather that favours disease."),
  P("The main contributions of the study are as follows:", { run: { bold: true } }),
  N("An end-to-end pipeline, from field node to dashboard, that senses the orchard, transmits data over MQTT or HTTP, stores it, and returns valve commands to the field."),
  N("An agent that pairs a DQN irrigation planner with a safety guard, so that every learned proposal is checked against rain, soil state, growth stage, water budget and sensor health before the valve moves."),
  N("A stage-aware soil-water simulator for mango, used to train the planner and to compare policies under many different synthetic weather years."),
  N("An evaluation against three reference strategies, namely no irrigation, a fixed calendar schedule and a conventional threshold rule, measured by time spent in the target moisture band, water applied, drainage loss and days of water stress, together with a plan for validating the results in a real orchard."),
];
const introDoc = new Document({ styles, numbering, sections: [section(intro)] });

/* ---------------------------------------------------------------- REPORT */
const R = "../results/";
const rep = [
  new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: "Research and Implementation Report", font: FONT, size: 22, color: "777777" })] }),
  new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "An Agentic AI and IoT-Based Intelligent Soil Monitoring and Precision Management System for Mango Orchards", font: FONT, bold: true, size: 34, color: "1B5E20" })] }),

  H1("1. Summary"),
  P("This report documents the design, implementation and simulated evaluation of an agentic irrigation-management system for mango orchards. The software package accompanying it contains ESP32 firmware, an MQTT/HTTP backend, a DQN-based decision agent with a deterministic safety guard, a web dashboard, a soil-water simulator and a test suite of 21 automated tests."),
  P("In simulation on 30 unseen random weather years, the agentic policy kept the root zone inside its stage-specific target band on 61.8% of days, against 54.3% for a conventional threshold rule, 21.4% with no irrigation and 18.1% for a fixed calendar schedule. It reduced days below the target band from 8.2% (threshold rule) to 0.3%, at the price of about 52 mm more irrigation water per year (683 mm against 631 mm). The fixed schedule used more than twice as much water as any adaptive policy and lost about 1,040 mm a year to deep drainage."),
  P("These numbers come from a simulator with assumed soil constants and target bands. They show that the approach is sound under those assumptions, not that it will give the same gains in a particular orchard. Section 8 lists what must be done before field use.", { run: { bold: true } }),

  H1("2. Background and literature"),
  H2("2.1 Why stage-aware irrigation matters for mango"),
  P("Guidance from mango-growing regions agrees on the broad pattern. The Northern Territory Department of Agriculture advises that irrigation is highly recommended from flowering until late fruit maturity, that it normally stops a few weeks before harvest and does not restart until flowering in the next season, and that the actual rate should be set for each site using soil-moisture monitoring (tensiometers, neutron probes or capacitance sensors). The Queensland Water for Profit benchmark lists the same phases: withholding water in the pre-flowering dormancy period to improve flowering, avoiding stress during flowering, fruit set and fruit development, reducing irrigation one to two weeks before harvest, and restarting irrigation immediately after harvest."),
  P("Field trials support deficit strategies rather than constant wetting. An Indian Council of Agricultural Research study on the hybrid Amrapali compared deficit drip irrigation levels with mulching, and Hahn and Garcia (2022) found that reduced deficit irrigation gave yield similar to daily irrigation in a high-density orchard while improving water-use efficiency. The practical lesson for a controller is that the target moisture changes with the season, and that a policy which simply keeps soil wet all year wastes water and may harm flowering."),
  H2("2.2 Sensing and decision methods"),
  P("Soil-moisture sensing in mango orchards is usually done with capacitance probes or tensiometers placed in the root zone, often combined with plant-based sensors such as dendrometers. Capacitance probes are cheap and suit a low-cost IoT node, but they need soil-specific calibration. On the decision side, reinforcement learning has been applied to irrigation because the problem is sequential, weather is uncertain and the cost of mistakes is delayed. The DQN of Mnih et al. (2015) and its Double-DQN refinement by van Hasselt et al. (2016) are standard value-based methods. The agentic pattern of reasoning, acting through tools and observing results is described in general form by Yao et al. (2023); here the pattern is applied conservatively, with learned and language-model components restricted to proposing and explaining while a fixed rule set holds the final say over the valve."),
  H2("2.3 Gap addressed"),
  B("Monitoring-only systems display data but do not decide or explain."),
  B("Simulation-only learners rarely describe a deployment path or protect against hardware faults."),
  B("Few systems encode mango's stage-dependent water requirement, including the deliberate dry period before flowering."),

  H1("3. System architecture"),
  table([1900, 3600, 3526], [
    ["Layer", "Components", "Role"],
    ["Field node", "ESP32, capacitive soil probe, DHT22, relay and solenoid valve", "Sample every 15 min, publish JSON, close the valve on a local timer even if offline"],
    ["Transport", "MQTT (Mosquitto) and HTTP", "Telemetry in, valve commands out"],
    ["Backend", "FastAPI, SQLite", "Validation, storage, scheduling, REST API, optional API key"],
    ["Agent", "DQN planner, safety guard, advisories, optional LLM explainer", "Perceive, propose, check, act, remember"],
    ["Interface", "Web dashboard", "Live chart, decision log, alerts, manual valve, weather input"],
    ["Simulator", "Soil-water balance and weather generator", "Training and offline evaluation"],
  ]),
  P(""),
  H2("3.1 Agent loop"),
  N2("Perceive: take the median soil moisture over the last 24 hours, mean temperature and humidity, weather input, calendar-derived growth stage and days since the last irrigation."),
  N2("Reason: the DQN scores four actions (0, 6, 12 or 20 mm) and proposes the best."),
  N2("Guard: the proposal is reviewed. Irrigation is blocked if rain is falling or forecast, if the soil is already above the band, or during the pre-flowering dry phase unless the soil is close to wilting. Events are capped at 20 mm and a rolling 7-day budget of 60 mm applies. If the sensor is missing, implausible or stuck, no irrigation is issued and an alert is raised. Near the wilting point outside pre-flowering, the guard forces an emergency 12 mm."),
  N2("Act: millimetres are converted to valve minutes using the drip application rate and sent over MQTT or returned in the HTTP reply."),
  N2("Remember and explain: the decision, reasons, alerts and a plain-language note are stored. If an Anthropic API key is configured, a language model rewrites the note for the farmer; if the call fails, a template note is used. The language model never changes the amount."),

  H1("4. Methodology"),
  H2("4.1 Soil-water model"),
  P("The root zone is modelled as a single layer 500 mm deep, so 1 mm of water changes volumetric water content (VWC) by 0.2 percentage points. Each day: store = previous store + rain + irrigation - actual evapotranspiration - drainage. Reference evapotranspiration follows a Hargreaves-type temperature formulation (Allen et al., 1998 describe the underlying FAO approach), scaled by a stage-specific crop coefficient (0.70 to 1.00) and reduced when the soil is dry. Half of any water above field capacity (32% VWC) drains each day; anything above saturation (42%) is lost at once. The wilting point is 12%."),
  H2("4.2 Target bands"),
  table([2200, 1600, 5226], [
    ["Stage (months, N. India)", "Band (VWC %)", "Reasoning"],
    ["Pre-flowering (Oct-Jan)", "12 - 20", "Deliberate mild dryness before flowering"],
    ["Flowering (Feb-Mar)", "22 - 30", "Avoid stress during flowering and fruit set"],
    ["Fruit development (Apr-May)", "24 - 32", "Highest demand, protect fruit growth"],
    ["Pre-harvest (Jun)", "19 - 26", "Reduced irrigation ahead of harvest"],
    ["Post-harvest (Jul-Sep)", "22 - 30", "Restart growth after harvest, mostly rain-fed"],
  ]),
  P("The bands are defaults chosen to follow the qualitative guidance in Section 2.1. They are not measured values for any variety or soil, and they are the first thing to calibrate locally.", { run: { italics: true } }),
  H2("4.3 DQN formulation"),
  B("State (12 values): scaled soil moisture, one-hot stage, temperature, humidity, rain today, forecast rain, days since irrigation, reference evapotranspiration."),
  B("Actions: 0, 6, 12 or 20 mm of irrigation per day."),
  B("Reward: +1 inside the band; a distance penalty outside it (steeper for dryness); 0.03 per mm of water; extra penalties for irrigating soil that is already too wet, for irrigating ahead of forecast rain of 8 mm or more, and for drainage loss."),
  B("Network: two hidden layers of 64 units, Double-DQN targets, Huber loss, Adam, replay buffer of 30,000, target sync every 400 updates, discount 0.97, 700 training episodes on different synthetic years."),
  H2("4.4 Policies compared"),
  B("No irrigation: rain only."),
  B("Fixed schedule: 12 mm every third day all year."),
  B("Threshold rule: irrigate toward the middle of the stage band whenever soil moisture falls below its lower bound."),
  B("DQN: the learned policy on its own."),
  B("Agentic (DQN + guard): the deployed configuration."),

  H1("5. Implementation"),
  H2("5.1 Repository layout"),
  table([2900, 6126], [
    ["Path", "Content"],
    ["mangoagent/", "config, weather, env (simulator), dqn, policies, guard, agent, llm_advisor"],
    ["backend/", "FastAPI app, SQLite layer, MQTT bridge, optional Open-Meteo weather"],
    ["firmware/esp32_node/", "Arduino sketch for the field node"],
    ["dashboard/index.html", "Single-page dashboard served by the backend"],
    ["scripts/", "train_dqn.py, evaluate.py, simulate_node.py"],
    ["tests/", "21 pytest tests (core logic and API)"],
    ["deploy/, docker-compose.yml", "Mosquitto, Dockerfile, compose file"],
    ["results/", "Trained weights, summary tables and figures"],
  ]),
  P(""),
  H2("5.2 Hardware list (per node)"),
  table([3200, 5826], [
    ["Item", "Notes"],
    ["ESP32 dev board", "Use ADC1 pins; ADC2 is unavailable while Wi-Fi is active"],
    ["Capacitive soil-moisture sensor v1.2", "Two-point calibration in your own soil is essential"],
    ["DHT22", "Air temperature and humidity"],
    ["Relay module and 12 V solenoid valve", "Fail-safe: valve closed at boot; firmware caps any command at 240 minutes"],
    ["Li-ion cell, 1:2 divider, small solar panel", "Battery voltage is reported and alerted below 3.4 V"],
    ["Weatherproof enclosure", "Seal cable glands; keep the probe electronics above the soil line"],
  ]),
  P(""),
  H2("5.3 What was and was not tested"),
  B("Tested: simulator, DQN training, guard, agent, database and REST API (21 automated tests), plus a 150-day end-to-end run in which a simulated node posted data to a live server and received agent decisions."),
  B("Not tested: the ESP32 firmware on real hardware, the MQTT path against a real broker, the optional language-model explainer and the Open-Meteo feed, because these need physical devices, network services or API keys that were not available."),

  H1("6. Results"),
  P("Each policy was run on the same 30 weather years that were never used for training. Values are means over those years."),
  table([2300, 1100, 1100, 1000, 1200, 1226, 1100], [
    ["Policy", "In band %", "Below band %", "Above band %", "Water mm/yr", "Drainage mm/yr", "Events"],
    ["No irrigation", "21.4", "44.1", "34.4", "0", "272", "0"],
    ["Fixed schedule", "18.1", "8.8", "73.1", "1460", "1042", "122"],
    ["Threshold rule", "54.3", "8.2", "37.5", "631", "312", "32"],
    ["DQN", "61.6", "0.2", "38.2", "703", "323", "73"],
    ["Agentic (DQN + guard)", "61.8", "0.3", "37.9", "683", "307", "70"],
  ]),
  cap("Table 1. Simulated annual performance (mean of 30 unseen years)."),
  img(R + "policy_comparison.png", 600, 171),
  cap("Figure 1. Target-band attainment, irrigation water and drainage loss by policy (error bars: standard deviation)."),
  img(R + "agentic_year.png", 600, 200),
  cap("Figure 2. One simulated year under the agentic policy. Soil moisture stays near the stage band; irrigation is absent in the dry pre-flowering phase."),
  img(R + "training_curve.png", 400, 200),
  cap("Figure 3. DQN training curve (10-episode moving average)."),

  H1("7. Analysis"),
  B("Adaptive beats calendar. The fixed schedule spent 1,460 mm and still spent 73% of days above the band, because it ignores rain and growth stage. Its drainage loss of about 1,040 mm is the clearest sign of waste."),
  B("The learned policy trades a little water for much less stress. Compared with the threshold rule, the agentic policy gives roughly 7.5 more days per hundred inside the band and nearly removes days below it (8.2% to 0.3%), but uses about 8% more water. Whether that trade is worth making depends on water cost and on how much a day of stress costs the crop, which this study does not measure."),
  B("The guard changed little in simulation, and that is fine. DQN alone and DQN with the guard are almost identical, because the reward already penalises the behaviours the guard blocks. The guard's value is in situations the simulator does not contain: a failed probe, a stuck value, a forecast the learner misread. Those cases are covered by unit tests rather than by the yearly averages."),
  B("Above-band days are mostly rain. Roughly 38% of days sit above the band even for good policies, largely during the monsoon when no controller can remove water. This figure should not be read as controller error. Better drainage design, mulching or raised beds would be the lever, not a smarter valve."),
  B("Variation between years is large. Standard deviations of 5 to 6 percentage points show that single-year comparisons can mislead; trials should span more than one season."),

  H1("8. Limitations and validation plan"),
  B("Soil constants, band limits and crop coefficients are assumed, not measured. Calibrate field capacity, wilting point and bands with soil tests and an agronomist, and compare against a tensiometer or neutron-probe reference."),
  B("The simulator uses one soil layer and synthetic weather. Re-train on real historical weather for your site, and consider a multi-layer root-zone model for deep-rooted trees."),
  B("The learner knows nothing about yield or fruit quality. A trial should include blocks run by the agent and by the grower's usual practice, with yield, fruit size and water use recorded."),
  B("Sensor drift and salinity affect capacitive probes. Re-calibrate each season and cross-check with a manual reading."),
  B("Disease advisories are simple temperature and humidity heuristics and should be checked with local plant-protection guidance."),
  B("Secure the system before field use: set API_KEY, enable MQTT authentication and TLS, and run behind HTTPS."),
  B("Keep a manual override. The dashboard supports it, and the firmware's local timer closes the valve even if the network drops."),

  H1("9. Running the system"),
  N3("Install dependencies: pip install -r requirements-dev.txt"),
  N3("Run tests: python -m pytest -q"),
  N3("Retrain (optional): python scripts/train_dqn.py --episodes 700, then python scripts/evaluate.py"),
  N3("Start the server: uvicorn backend.app:app --port 8000, and open http://localhost:8000"),
  N3("Try it without hardware: python scripts/simulate_node.py --days 60"),
  N3("With hardware: edit Wi-Fi, broker, zone and calibration values in the .ino file, flash the ESP32, and start the stack with docker compose up --build"),

  H1("References"),
  P("Allen, R. G., Pereira, L. S., Raes, D., and Smith, M. (1998). Crop evapotranspiration: guidelines for computing crop water requirements. FAO Irrigation and Drainage Paper 56. Food and Agriculture Organization of the United Nations."),
  P("Hahn, F., and Garcia, J. A. (2022). Mango stem response under different irrigation regimes. International Journal of Fruit Science, 22(1), 35-56. https://doi.org/10.1080/15538362.2021.1970080"),
  P("Indian Council of Agricultural Research. Effect of deficit drip irrigation and mulching on mango hybrid 'Amrapali'. JISCAR (ICAR e-Pubs). https://epubs.icar.org.in/index.php/JISCAR/article/download/79587/33352/202120"),
  P("Mnih, V., et al. (2015). Human-level control through deep reinforcement learning. Nature, 518, 529-533."),
  P("Northern Territory Department of Agriculture and Fisheries. Mango irrigation management guidelines. https://daf.nt.gov.au/__data/assets/pdf_file/0004/232969/587.pdf"),
  P("van Hasselt, H., Guez, A., and Silver, D. (2016). Deep reinforcement learning with double Q-learning. Proceedings of the AAAI Conference on Artificial Intelligence."),
  P("Water for Profit. Benchmark: irrigating mangoes in north Queensland. https://www.industry.mangoes.net.au/cmsb/uploads/wfp-benchmark-irrigating-mangoes-in-north-queensland.pdf"),
  P("Yao, S., et al. (2023). ReAct: synergizing reasoning and acting in language models. International Conference on Learning Representations."),
];
const repDoc = new Document({ styles, numbering, sections: [section(rep)] });

Packer.toBuffer(introDoc).then(b => fs.writeFileSync("Introduction_Humanized.docx", b));
Packer.toBuffer(repDoc).then(b => fs.writeFileSync("Research_and_Implementation_Report.docx", b));

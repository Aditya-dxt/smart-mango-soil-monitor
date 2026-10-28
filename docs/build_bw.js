// Black-and-white edition: all text black, no colour fills, grayscale figures.
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, ImageRun, LevelFormat, Footer, PageNumber } = require("docx");

const FONT = "Times New Roman", BLACK = "000000";
const run = (t, o = {}) => new TextRun({ text: t, font: FONT, size: 24, color: BLACK, ...o });
const P = (t, o = {}) => new Paragraph({ spacing: { after: 140, line: 312 }, alignment: o.align || AlignmentType.JUSTIFIED, children: [run(t, o.run)] });
const TITLE = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [run(t, { bold: true, size: 32 })] });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 140 }, children: [run(t, { bold: true, size: 28 })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 220, after: 100 }, children: [run(t, { bold: true, italics: true, size: 25 })] });
const Bu = (t) => new Paragraph({ numbering: { reference: "b", level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { after: 90, line: 300 }, children: [run(t)] });
const Nr = (ref) => (t) => new Paragraph({ numbering: { reference: ref, level: 0 }, alignment: AlignmentType.JUSTIFIED, spacing: { after: 110, line: 306 }, children: [run(t)] });
const [N1, N2, N3, N4] = ["n1", "n2", "n3", "n4"].map(Nr);
const cap = (t) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [run(t, { italics: true, size: 21 })] });
const img = (f, w, h) => new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 }, children: [new ImageRun({ type: "png", data: fs.readFileSync(f), transformation: { width: w, height: h }, altText: { title: f, description: f, name: f } })] });

const thin = { style: BorderStyle.SINGLE, size: 6, color: BLACK };
const thick = { style: BorderStyle.SINGLE, size: 14, color: BLACK };
function table(widths, rows) {
  return new Table({
    width: { size: widths.reduce((a, b) => a + b), type: WidthType.DXA }, columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({ tableHeader: i === 0, children: r.map((c, j) => new TableCell({
      width: { size: widths[j], type: WidthType.DXA },
      borders: { top: i === 0 ? thick : thin, bottom: i === 0 ? thick : thin, left: thin, right: thin },
      shading: { type: ShadingType.CLEAR, fill: "FFFFFF" },
      margins: { top: 70, bottom: 70, left: 110, right: 110 },
      children: [new Paragraph({ children: [run(String(c), { size: 21, bold: i === 0 })] })] })) })) });
}
const styles = { default: { document: { run: { font: FONT, size: 24, color: BLACK } } },
  paragraphStyles: [
    { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 28, bold: true, color: BLACK }, paragraph: { outlineLevel: 0 } },
    { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { size: 25, bold: true, italics: true, color: BLACK }, paragraph: { outlineLevel: 1 } }] };
const lvl = (fmt, text) => [{ level: 0, format: fmt, text, alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } }, run: { color: BLACK } } }];
const numbering = { config: [{ reference: "b", levels: lvl(LevelFormat.BULLET, "\u2022") },
  ...["n1", "n2", "n3", "n4"].map(r => ({ reference: r, levels: lvl(LevelFormat.DECIMAL, "%1.") }))] };
const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [run("Page ", { size: 18 }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18, color: BLACK })] })] });
const section = (children) => ({ properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } }, footers: { default: footer }, children });
const TITLE_TEXT = "An Agentic AI and IoT-Based Intelligent Soil Monitoring and Precision Management System for Mango Orchards";

/* ================================================= REPORT ================================================= */
const R = "../results/";
const rep = [
  TITLE(TITLE_TEXT),
  H1("Abstract"),
  P("This report describes how an agent-driven irrigation management system for mango orchards was designed, built and tested in simulation. The accompanying code base includes firmware for an ESP32 field node, a backend that speaks MQTT and HTTP, a decision agent built on a Deep Q-Network with a rule-based safety guard, a browser dashboard, a soil-water simulator, and 21 automated tests."),
  P("The simulation used 30 random weather years that the learner had never seen. Under the agentic policy the root zone stayed inside the target moisture band for its growth stage on 61.8% of days. The comparison figures were 54.3% for an ordinary threshold rule, 18.1% for a fixed calendar schedule and 21.4% when no irrigation was applied. Days spent below the band fell from 8.2% with the threshold rule to 0.3%, and the cost was roughly 52 mm of extra irrigation a year (683 mm against 631 mm). The calendar schedule applied more than double the water of any adaptive method and lost about 1,040 mm every year to deep drainage."),
  P("Every figure here comes from a simulator whose soil constants and target bands are assumptions. The results show that the method works under those assumptions. They do not promise the same improvement in any particular orchard. Section 8 sets out the work needed before the system is used in the field.", { run: { bold: true } }),

  H1("1. Introduction"),
  P("Agriculture remains central to a country's food security. It gives work to people in rural areas, and fruit shipped overseas earns foreign currency. Mango holds a prominent place among tree crops, since consumers at home buy it in large volumes and fruit of good quality is also in demand abroad."),
  P("Through most of the year a mango tree responds to its environment. Soil moisture, air temperature and the humidity surrounding the canopy influence the timing of flowering, the success of fruit set, the speed of fruit growth, and the chance that disease or insects will cause trouble. Of these, water is the trickiest, because giving the tree more of it does not always help. Growers commonly withhold water in the weeks leading up to flowering, keep the soil reasonably moist from flowering until the fruit is close to mature, and cut back again a little before harvest. The person managing an orchard therefore needs two pieces of knowledge together: the present wetness of the soil, and the wetness that is appropriate at this time of year."),
  P("Most growers answer that question by walking between the trees, pressing a hand into the soil, and watering out of habit or according to the calendar. Starting this way costs next to nothing, which is why it is so widespread. It does, however, demand labour and time, it cannot continue day and night, and what the grower observes is rarely recorded in a form that can inform later choices. As orchards expand and fewer people are willing to do farm work, the method gets harder to keep up."),
  P("Inexpensive sensors and wireless communication provide an alternative. A wireless sensor network spreads small battery-powered nodes through the orchard. Each node carries a soil-moisture probe and a sensor for air temperature and humidity, and passes its readings to a gateway and on to the cloud. A grower can then check conditions from a phone instead of visiting every block. Yet many installations do no more than display numbers or apply one fixed moisture limit. They are unaware of the growth stage, they cannot account for rain that is about to arrive, and they cannot distinguish a dry field from a faulty sensor."),
  P("Artificial intelligence can close part of this gap. Reinforcement learning suits irrigation well, because a controller improves by acting, collecting a reward and adjusting its behaviour. A Deep Q-Network (DQN) builds on that idea with a neural network that estimates the value of each available action in the present situation. A more recent concept is the agentic system, meaning software that observes its surroundings, decides what to do, acts through tools and keeps a record of the results. In an orchard such software reads the sensors, considers the growth stage and the weather, suggests how much water to apply, tests that suggestion against safety rules, operates the valve, and tells the farmer in everyday language what happened. Because a learned policy should never hold unchecked authority over a valve, a rule-based safety layer is placed between the learner and the equipment."),
  P("Previous research has joined sensor networks, IoT platforms and machine learning for farming, and most of it belongs to one of three types. Some work simply gathers and relays data. Some trains a controller in simulation and says little about running it on real hardware. A small number provides a working pipeline but offers no reasons for its decisions and no defence against sensor failure. Almost none builds the stage-dependent water pattern of mango into the control logic. A complete system that combines field sensing, a decision-making agent and an interface for farmers is therefore still needed."),
  P("The present study offers such a system for mango. ESP32 nodes collect soil moisture, air temperature and humidity and send them by MQTT to a FastAPI service. Inside that service, an agent brings together a DQN planner, trained on a soil-water model built for mango, a deterministic safety guard, and an optional language-model advisor that writes the explanation. The farmer follows events on a web dashboard, can take over the valve manually, and is warned about dry soil, weak batteries, doubtful sensors and weather that encourages disease."),
  P("The study makes four main contributions:", { run: { bold: true } }),
  N1("A complete pipeline from the field node to the dashboard, which senses the orchard, carries data over MQTT or HTTP, stores it and sends valve commands back to the field."),
  N1("An agent that couples a DQN irrigation planner with a safety guard, so that each learned proposal is tested against rain, soil condition, growth stage, water budget and sensor health before the valve is moved."),
  N1("A growth-stage-aware soil-water simulator for mango, used both to train the planner and to compare policies across many synthetic weather years."),
  N1("An assessment against three reference strategies (no irrigation, a fixed calendar schedule and a standard threshold rule), judged on time inside the target moisture band, water applied, drainage loss and days of water stress, together with a plan for confirming the findings in a real orchard."),

  H1("2. Background and literature"),
  H2("2.1 The case for stage-aware irrigation in mango"),
  P("Advice from mango-growing regions follows a common outline. The Northern Territory Department of Agriculture recommends strongly that irrigation run from flowering to late fruit maturity. It says watering usually ends a few weeks ahead of harvest and begins again only when the next flowering season arrives, and that the right rate for a given site should be worked out by monitoring soil moisture with tensiometers, neutron probes or capacitance sensors. The Queensland Water for Profit benchmark describes the same sequence: keep water back during the dormant period before flowering to improve flower production, avoid stress through flowering, fruit set and fruit growth, ease irrigation one to two weeks before harvest, and resume watering straight after harvest."),
  P("Trials in the field favour deficit strategies over constant wetting. An Indian Council of Agricultural Research study on the Amrapali hybrid tested several levels of deficit drip irrigation along with mulching. Hahn and Garcia (2022) reported that, in a high-density orchard, reduced deficit irrigation produced a yield comparable to daily watering while using water more efficiently. For a controller the message is that the moisture target should shift with the season, and that a policy which keeps the soil wet all year wastes water and may interfere with flowering."),
  H2("2.2 Sensing and decision-making methods"),
  P("Orchard soil moisture is typically measured with capacitance probes or tensiometers placed in the root zone, sometimes alongside plant-based instruments such as dendrometers. Capacitance probes are cheap and fit a low-cost IoT node, but they must be calibrated for the soil in which they are used. On the decision side, reinforcement learning has been tried for irrigation because the task is sequential, the weather is uncertain and the consequences of an error appear later. The DQN of Mnih et al. (2015) and the Double-DQN improvement of van Hasselt et al. (2016) are widely used value-based methods. Yao et al. (2023) describe in general terms the agentic pattern of reasoning, acting through tools and observing the outcome. In this work the pattern is applied cautiously: the learned and language-model parts may only propose and explain, while a fixed set of rules has the last word on the valve."),
  H2("2.3 The gap this work addresses"),
  Bu("Systems that only monitor show data but neither decide nor explain."),
  Bu("Learners confined to simulation seldom describe how they would be deployed or how they would cope with hardware faults."),
  Bu("Few systems capture the water needs of mango across its growth stages, including the planned dry spell before flowering."),

  H1("3. System architecture"),
  table([1900, 3600, 3526], [
    ["Layer", "Components", "Role"],
    ["Field node", "ESP32, capacitive soil probe, DHT22, relay and solenoid valve", "Reads every 15 minutes, publishes JSON, closes the valve on a local timer even when offline"],
    ["Transport", "MQTT (Mosquitto) and HTTP", "Carries telemetry in and valve commands out"],
    ["Backend", "FastAPI, SQLite", "Checks input, stores data, schedules work, serves the REST API, optional API key"],
    ["Agent", "DQN planner, safety guard, advisories, optional LLM explainer", "Perceive, propose, check, act, remember"],
    ["Interface", "Web dashboard", "Live chart, decision log, alerts, manual valve control, weather entry"],
    ["Simulator", "Soil-water balance and weather generator", "Used for training and offline testing"],
  ]),
  P(""),
  H2("3.1 The agent loop"),
  N2("Perceive. Gather the median soil moisture of the previous 24 hours, the mean temperature and humidity, the weather input, the growth stage taken from the calendar, and the number of days since irrigation last ran."),
  N2("Reason. The DQN assigns a score to four actions (0, 6, 12 or 20 mm) and proposes the one with the highest score."),
  N2("Guard. The proposal is inspected. Irrigation is stopped if rain is falling or expected, if the soil already sits above the band, or if it is the dry pre-flowering phase and the soil is not near wilting. A single event is limited to 20 mm, and a rolling seven-day budget of 60 mm applies. When the sensor is absent, implausible or stuck, no water is released and an alert is raised. Outside pre-flowering, a soil moisture close to the wilting point makes the guard order an emergency 12 mm."),
  N2("Act. The number of millimetres is converted into valve minutes using the drip application rate, then sent by MQTT or returned in the HTTP reply."),
  N2("Remember and explain. The decision, its reasons, any alerts and a plain-language note are saved. If an Anthropic API key has been configured, a language model rewrites the note for the farmer, and if that call fails a template note is used instead. The language model never alters the amount of water."),

  H1("4. Methodology"),
  H2("4.1 Soil-water model"),
  P("The root zone is represented as one layer 500 mm deep, so each millimetre of water shifts volumetric water content (VWC) by 0.2 percentage points. Every day the water store equals the previous store plus rain plus irrigation, minus actual evapotranspiration and drainage. Reference evapotranspiration comes from a temperature-based formula of the Hargreaves type (the underlying FAO method is described by Allen et al., 1998). It is multiplied by a crop coefficient specific to the growth stage, ranging from 0.70 to 1.00, and is lowered when the soil is dry. Half of any water above field capacity (32% VWC) drains away each day, and anything above saturation (42%) is lost immediately. The wilting point is set at 12%."),
  H2("4.2 Target bands"),
  table([2200, 1600, 5226], [
    ["Stage (months, N. India)", "Band (VWC %)", "Reasoning"],
    ["Pre-flowering (Oct-Jan)", "12 - 20", "Planned mild dryness ahead of flowering"],
    ["Flowering (Feb-Mar)", "22 - 30", "Prevent stress during flowering and fruit set"],
    ["Fruit development (Apr-May)", "24 - 32", "Peak demand, so fruit growth is protected"],
    ["Pre-harvest (Jun)", "19 - 26", "Lower irrigation before harvest"],
    ["Post-harvest (Jul-Sep)", "22 - 30", "Growth resumes after harvest, mainly rain-fed"],
  ]),
  P(""),
  P("The bands are default values chosen to follow the qualitative advice in Section 2.1. They are not measurements for any variety or soil, and they should be the first items calibrated for a local site.", { run: { italics: true } }),
  H2("4.3 DQN formulation"),
  Bu("State (12 values): scaled soil moisture, one-hot growth stage, temperature, humidity, rain today, forecast rain, days since irrigation and reference evapotranspiration."),
  Bu("Actions: 0, 6, 12 or 20 mm of irrigation per day."),
  Bu("Reward: +1 when the soil is inside the band, and a penalty that grows with distance outside it (steeper on the dry side). Water costs 0.03 per mm. Further penalties apply for irrigating soil that is already too wet, for irrigating ahead of a forecast of 8 mm of rain or more, and for drainage loss."),
  Bu("Network: two hidden layers of 64 units, Double-DQN targets, Huber loss, Adam optimiser, a replay buffer of 30,000 transitions, target synchronisation every 400 updates, a discount factor of 0.97, and 700 training episodes on different synthetic years."),
  H2("4.4 Policies compared"),
  Bu("No irrigation: rainfall only."),
  Bu("Fixed schedule: 12 mm every third day throughout the year."),
  Bu("Threshold rule: whenever soil moisture drops below the lower limit of the stage band, irrigate toward the middle of the band."),
  Bu("DQN: the learned policy used alone."),
  Bu("Agentic (DQN + guard): the configuration intended for deployment."),

  H1("5. Implementation"),
  H2("5.1 Repository layout"),
  table([2900, 6126], [
    ["Path", "Content"],
    ["mangoagent/", "config, weather, env (simulator), dqn, policies, guard, agent, llm_advisor"],
    ["backend/", "FastAPI app, SQLite layer, MQTT bridge, optional Open-Meteo weather"],
    ["firmware/esp32_node/", "Arduino sketch for the field node"],
    ["dashboard/index.html", "Single-page dashboard served by the backend"],
    ["scripts/", "train_dqn.py, evaluate.py, simulate_node.py"],
    ["tests/", "21 pytest tests covering core logic and the API"],
    ["deploy/, docker-compose.yml", "Mosquitto, Dockerfile and compose file"],
    ["results/", "Trained weights, summary tables and figures"],
  ]),
  P(""),
  H2("5.2 Hardware list (per node)"),
  table([3200, 5826], [
    ["Item", "Notes"],
    ["ESP32 development board", "Use ADC1 pins, because ADC2 cannot be used while Wi-Fi is active"],
    ["Capacitive soil-moisture sensor v1.2", "A two-point calibration in your own soil is essential"],
    ["DHT22", "Measures air temperature and humidity"],
    ["Relay module and 12 V solenoid valve", "Fail-safe design: valve is closed at start-up, and the firmware limits any command to 240 minutes"],
    ["Li-ion cell, 1:2 divider, small solar panel", "Battery voltage is reported, with an alert below 3.4 V"],
    ["Weatherproof enclosure", "Seal the cable glands and keep the probe electronics above ground level"],
  ]),
  P(""),
  H2("5.3 What was tested and what was not"),
  Bu("Tested: the simulator, DQN training, guard, agent, database and REST API (21 automated tests), and a 150-day end-to-end run in which a simulated node sent data to a live server and received the agent's decisions."),
  Bu("Not tested: the ESP32 firmware on real hardware, the MQTT path against a real broker, the optional language-model explainer and the Open-Meteo feed. Each of these needs physical devices, network services or API keys that were not available."),

  H1("6. Results"),
  P("Each policy was run on the same 30 weather years, none of which were used during training. The values are averages over those years."),
  table([2300, 1100, 1100, 1000, 1200, 1226, 1100], [
    ["Policy", "In band %", "Below band %", "Above band %", "Water mm/yr", "Drainage mm/yr", "Events"],
    ["No irrigation", "21.4", "44.1", "34.4", "0", "272", "0"],
    ["Fixed schedule", "18.1", "8.8", "73.1", "1460", "1042", "122"],
    ["Threshold rule", "54.3", "8.2", "37.5", "631", "312", "32"],
    ["DQN", "61.6", "0.2", "38.2", "703", "323", "73"],
    ["Agentic (DQN + guard)", "61.8", "0.3", "37.9", "683", "307", "70"],
  ]),
  cap("Table 1. Simulated yearly performance (average of 30 unseen years)."),
  img(R + "bw_policy_comparison.png", 600, 171),
  cap("Figure 1. Time in the target band, irrigation water and drainage loss for each policy (error bars show standard deviation)."),
  img(R + "bw_agentic_year.png", 600, 200),
  cap("Figure 2. A single simulated year under the agentic policy. Soil moisture stays close to the stage band, and no irrigation is given in the dry pre-flowering phase."),
  img(R + "bw_training_curve.png", 400, 200),
  cap("Figure 3. DQN training curve (moving average over 10 episodes)."),

  H1("7. Analysis"),
  Bu("Adaptive control outperforms the calendar. The fixed schedule applied 1,460 mm and still left the soil above the band on 73% of days, since it pays no attention to rain or growth stage. Its drainage loss of about 1,040 mm is the plainest evidence of waste."),
  Bu("The learned policy spends a little more water to cut stress sharply. Against the threshold rule, the agentic policy puts about 7.5 more days in every hundred inside the band and almost eliminates days below it (8.2% down to 0.3%), at the price of roughly 8% more water. Whether this exchange is worthwhile depends on what water costs and on what a day of stress costs the crop, neither of which was measured here."),
  Bu("The guard made little difference in simulation, which is acceptable. The DQN alone and the DQN with the guard behave almost identically, since the reward already discourages the actions the guard would block. The guard matters in cases the simulator never produces, such as a dead probe, a frozen reading or a forecast the learner misjudged. Unit tests cover those cases instead of the yearly averages."),
  Bu("Days above the band are mostly caused by rain. About 38% of days lie above the band even for the better policies, chiefly in the monsoon, when no controller is able to take water out of the soil. This number should not be treated as a controller mistake. Improving drainage, adding mulch or using raised beds would help here, whereas a cleverer valve would not."),
  Bu("Differences between years are large. Standard deviations of 5 to 6 percentage points mean that a one-year comparison can be misleading, so trials should last more than one season."),

  H1("8. Limitations and validation plan"),
  Bu("The soil constants, band limits and crop coefficients are assumed rather than measured. Calibrate field capacity, wilting point and the bands through soil tests and with an agronomist, and check them against a tensiometer or neutron-probe reference."),
  Bu("The simulator has a single soil layer and synthetic weather. Retrain with real historical weather from the site, and think about a multi-layer root-zone model for deep-rooted trees."),
  Bu("The learner has no knowledge of yield or fruit quality. A trial should include blocks managed by the agent and blocks managed by the grower's usual practice, recording yield, fruit size and water use."),
  Bu("Sensor drift and soil salinity affect capacitive probes. Recalibrate each season and cross-check with manual readings."),
  Bu("The disease advisories are simple temperature and humidity rules and should be confirmed against local plant-protection advice."),
  Bu("Secure the system before using it in the field: set API_KEY, turn on MQTT authentication and TLS, and serve it over HTTPS."),
  Bu("Keep manual override available. The dashboard provides it, and the firmware's local timer shuts the valve even if the network goes down."),

  H1("9. Running the system"),
  N3("Install the dependencies: pip install -r requirements-dev.txt"),
  N3("Run the tests: python -m pytest -q"),
  N3("Retrain if desired: python scripts/train_dqn.py --episodes 700, followed by python scripts/evaluate.py"),
  N3("Start the server: uvicorn backend.app:app --port 8000, then open http://localhost:8000"),
  N3("Try it without hardware: python scripts/simulate_node.py --days 60"),
  N3("With hardware: edit the Wi-Fi, broker, zone and calibration values in the .ino file, flash the ESP32, and bring up the stack with docker compose up --build"),

  H1("References"),
  N4("Allen, R. G., Pereira, L. S., Raes, D., and Smith, M. (1998). Crop evapotranspiration: guidelines for computing crop water requirements. FAO Irrigation and Drainage Paper 56. Food and Agriculture Organization of the United Nations."),
  N4("Hahn, F., and Garcia, J. A. (2022). Mango stem response under different irrigation regimes. International Journal of Fruit Science, 22(1), 35-56. https://doi.org/10.1080/15538362.2021.1970080"),
  N4("Indian Council of Agricultural Research. Effect of deficit drip irrigation and mulching on mango hybrid 'Amrapali'. JISCAR (ICAR e-Pubs). https://epubs.icar.org.in/index.php/JISCAR/article/download/79587/33352/202120"),
  N4("Mnih, V., et al. (2015). Human-level control through deep reinforcement learning. Nature, 518, 529-533."),
  N4("Northern Territory Department of Agriculture and Fisheries. Mango irrigation management guidelines. https://daf.nt.gov.au/__data/assets/pdf_file/0004/232969/587.pdf"),
  N4("van Hasselt, H., Guez, A., and Silver, D. (2016). Deep reinforcement learning with double Q-learning. Proceedings of the AAAI Conference on Artificial Intelligence."),
  N4("Water for Profit. Benchmark: irrigating mangoes in north Queensland. https://www.industry.mangoes.net.au/cmsb/uploads/wfp-benchmark-irrigating-mangoes-in-north-queensland.pdf"),
  N4("Yao, S., et al. (2023). ReAct: synergizing reasoning and acting in language models. International Conference on Learning Representations."),
];
Packer.toBuffer(new Document({ styles, numbering, sections: [section(rep)] })).then(b => fs.writeFileSync("Research_and_Implementation_Report_BW.docx", b));

/* ================================================= INTRODUCTION (B&W, standalone) ================================================= */
const intro = [
  TITLE(TITLE_TEXT),
  H1("1. Introduction"),
  P("Agriculture still underpins food security in most countries. It provides rural employment, and fruit sold to foreign buyers brings in income from abroad. Among fruit trees, mango is especially valuable, because demand at home is strong and good fruit sells well in export markets."),
  P("A mango tree reacts to its environment for much of the year. How much water the soil holds, how warm the air is and how humid it is under the canopy all affect when flowering starts, how well fruit sets, how quickly it grows, and how exposed the orchard is to pests and disease. Water needs the most care, since extra irrigation can do harm. Growers usually keep water back before flowering, supply enough from flowering until the fruit is nearly ripe, and then reduce it again shortly before the harvest. Managing an orchard well therefore means knowing the current soil wetness and also the wetness the tree needs at that moment in the season."),
  P("The traditional method is to walk the rows, feel the soil and irrigate from habit or by the calendar. It is cheap to begin with, but it consumes labour, it cannot run through the night, and the grower's observations are seldom written down in a way that helps future decisions. With larger orchards and a shrinking farm workforce, it becomes harder to continue."),
  P("Low-cost sensors and wireless links change this picture. A wireless sensor network sets battery-powered nodes across the orchard, each combining a soil-moisture probe with an air temperature and humidity sensor, and forwards the readings through a gateway to the cloud. The grower can view the orchard from a phone. Many systems nevertheless stop at displaying readings or at applying a single threshold, so they ignore the growth stage, miss coming rain and cannot separate a dry field from a broken probe."),
  P("Artificial intelligence can help fill that gap. In reinforcement learning, a controller improves through trial, reward and adjustment, which fits irrigation naturally. A Deep Q-Network (DQN) uses a neural network to estimate how good every possible action is in the current state. An agentic system goes further: it observes, decides, acts through tools and remembers what happened. For an orchard, that means reading sensors, weighing growth stage and weather, proposing an amount of water, checking it against safety rules, operating the valve and explaining the result to the farmer in simple language. As a learned policy should not control a valve without limits, a rule-based safety layer stands between the learner and the equipment."),
  P("Earlier work has combined sensor networks, IoT and machine learning in agriculture, but typically in one of three ways: collecting and forwarding data only, training a controller in simulation without a route to real hardware, or building a working pipeline that neither explains itself nor guards against sensor faults. Very few encode the stage-dependent water needs of mango. A complete system that unites field sensing, a decision-making agent and a farmer-friendly interface is therefore still missing."),
  P("This study proposes that system. ESP32 nodes measure soil moisture, air temperature and humidity and send them over MQTT to a FastAPI service. In the service, an agent combines a DQN planner trained on a mango-specific soil-water model, a deterministic safety guard and an optional language-model advisor that writes the explanation. The farmer watches a web dashboard, can control the valve by hand, and receives warnings about dry soil, low batteries, questionable sensors and weather that favours disease."),
  P("The contributions of this study are:", { run: { bold: true } }),
  N1("A full pipeline from field node to dashboard that senses the orchard, moves data over MQTT or HTTP, stores it and returns valve commands."),
  N1("An agent that pairs a DQN irrigation planner with a safety guard, so each learned proposal is checked against rain, soil state, growth stage, water budget and sensor health before the valve moves."),
  N1("A growth-stage-aware soil-water simulator for mango that is used to train the planner and to compare policies over many synthetic weather years."),
  N1("A comparison with no irrigation, a fixed calendar schedule and a standard threshold rule, judged on time in the target band, water use, drainage loss and days of stress, plus a plan for validating the results in a real orchard."),
];
Packer.toBuffer(new Document({ styles, numbering, sections: [section(intro)] })).then(b => fs.writeFileSync("Introduction_BW.docx", b));

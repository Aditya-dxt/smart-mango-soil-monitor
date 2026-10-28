"""Mango Variety Feasibility and Soil Compatibility Analysis Engine.

Evaluates suitability of major commercial mango varieties against:
- Soil type (texture, drainage, water holding capacity)
- Soil pH (acidity / alkalinity)
- Soil NPK nutrient concentrations (mg/kg)
- Soil moisture (VWC %) & Climate (temperature, humidity)
"""
from __future__ import annotations
from typing import Dict, Any, List

VARIETY_DATABASE: Dict[str, Dict[str, Any]] = {
    "Alphonso (Hapus)": {
        "id": "alphonso",
        "name": "Alphonso (Hapus)",
        "native_region": "Ratnagiri, Konkan (Maharashtra), Karnataka",
        "description": "The 'King of Mangoes'. Known for supreme aroma, rich saffron pulp, and thin skin.",
        "ideal_soil_types": ["Laterite Soil", "Red Loam", "Red Sandy Loam", "Alluvial Loam"],
        "unsuitable_soil_types": ["Heavy Black Clay", "Saline Soil", "Waterlogged Clay"],
        "ph_min": 5.5,
        "ph_opt_min": 5.8,
        "ph_opt_max": 7.0,
        "ph_max": 7.5,
        "n_opt": (120, 180),
        "p_opt": (20, 45),
        "k_opt": (150, 250),
        "temp_opt": (24, 35),
        "humidity_opt": (50, 75),
        "drainage_importance": "Critical - prone to spongy tissue in waterlogged or heavy black soil.",
        "yield_potential": "8 - 12 tonnes/ha (alternate bearer without paclobutrazol)",
        "special_advice": "Avoid excessive nitrogen in bearing trees to prevent spongy tissue disorder. Requires strict post-monsoon dry spell for flowering."
    },
    "Kesar (Gir Kesar)": {
        "id": "kesar",
        "name": "Kesar (Gir Kesar)",
        "native_region": "Saurashtra / Gir (Gujarat), Marathwada",
        "description": "Queen of Mangoes. Intense saffron-colored pulp, highly sweet, excellent shelf life.",
        "ideal_soil_types": ["Medium Black Soil", "Alluvial Loam", "Red Sandy Loam", "Limestone Gravel Loam"],
        "unsuitable_soil_types": ["Poorly Drained Marshy Clay", "Extremely Acidic Peat"],
        "ph_min": 6.0,
        "ph_opt_min": 6.5,
        "ph_opt_max": 7.8,
        "ph_max": 8.2,
        "n_opt": (130, 190),
        "p_opt": (20, 45),
        "k_opt": (160, 260),
        "temp_opt": (25, 40),
        "humidity_opt": (40, 70),
        "drainage_importance": "High - very drought tolerant once established.",
        "yield_potential": "10 - 15 tonnes/ha",
        "special_advice": "Tolerates slightly alkaline soil and arid hot winds better than Alphonso. Excellent for semi-arid zones."
    },
    "Dasheri": {
        "id": "dasheri",
        "name": "Dasheri",
        "native_region": "Malihabad, Lucknow (Uttar Pradesh), North India",
        "description": "Slender aromatic fruit with sweet fibrousless pulp, highly popular northern variety.",
        "ideal_soil_types": ["Alluvial Loam", "Deep Silt Loam", "Fertile Sandy Loam"],
        "unsuitable_soil_types": ["Shallow Rocky Soil", "Saline Alkaline Usar"],
        "ph_min": 6.0,
        "ph_opt_min": 6.2,
        "ph_opt_max": 7.5,
        "ph_max": 8.0,
        "n_opt": (140, 210),
        "p_opt": (25, 50),
        "k_opt": (150, 240),
        "temp_opt": (22, 38),
        "humidity_opt": (45, 80),
        "drainage_importance": "High - prefers deep alluvial plains with water table > 2.5m.",
        "yield_potential": "10 - 14 tonnes/ha (alternate bearing tendency)",
        "special_advice": "Protect against mango malformation during winter flowering. Regular zinc and boron foliar sprays recommended."
    },
    "Langra": {
        "id": "langra",
        "name": "Langra (Banarasi)",
        "native_region": "Varanasi (UP), Bihar, West Bengal",
        "description": "Green skin even when ripe, distinct zesty aroma and melt-in-mouth pulp.",
        "ideal_soil_types": ["Alluvial Loam", "Gangetic Silt Loam", "Deep Sandy Loam"],
        "unsuitable_soil_types": ["Hardpan Laterite", "Saline Clay"],
        "ph_min": 5.8,
        "ph_opt_min": 6.0,
        "ph_opt_max": 7.4,
        "ph_max": 7.8,
        "n_opt": (130, 200),
        "p_opt": (20, 50),
        "k_opt": (150, 250),
        "temp_opt": (22, 38),
        "humidity_opt": (50, 85),
        "drainage_importance": "Moderate - tolerates seasonal flood plains if drainage resumes rapidly.",
        "yield_potential": "11 - 15 tonnes/ha",
        "special_advice": "Vigorous tree architecture. Needs canopy pruning post-harvest to allow sunlight penetration."
    },
    "Banganapalli (Safeda)": {
        "id": "banganapalli",
        "name": "Banganapalli (Benishan / Safeda)",
        "native_region": "Kurnool (Andhra Pradesh), Telangana, South India",
        "description": "Large oval golden fruit with firm, fiberless pulp, ideal for table use and canning.",
        "ideal_soil_types": ["Red Sandy Loam", "Red Loam", "Alluvial Loam", "Light Black Soil"],
        "unsuitable_soil_types": ["Compact Hard Clay", "Acidic Marsh"],
        "ph_min": 6.2,
        "ph_opt_min": 6.5,
        "ph_opt_max": 7.8,
        "ph_max": 8.3,
        "n_opt": (130, 190),
        "p_opt": (20, 45),
        "k_opt": (160, 250),
        "temp_opt": (24, 40),
        "humidity_opt": (45, 75),
        "drainage_importance": "High - performs exceptionally well in well-drained tropical peninsular soils.",
        "yield_potential": "12 - 18 tonnes/ha",
        "special_advice": "Responds well to drip fertigation and potassium supplementation during marble-size fruit development."
    },
    "Totapuri": {
        "id": "totapuri",
        "name": "Totapuri (Collector / Ginimoothi)",
        "native_region": "Andhra Pradesh, Karnataka, Tamil Nadu",
        "description": "Parrot-beak shaped mango. Heavy regular bearer, #1 commercial pulp extraction variety.",
        "ideal_soil_types": ["Sandy Loam", "Red Loam", "Laterite Soil", "Clayey Loam", "Alluvial Loam"],
        "unsuitable_soil_types": ["Severe Waterlogging"],
        "ph_min": 6.0,
        "ph_opt_min": 6.5,
        "ph_opt_max": 8.0,
        "ph_max": 8.5,
        "n_opt": (140, 220),
        "p_opt": (20, 50),
        "k_opt": (150, 260),
        "temp_opt": (22, 42),
        "humidity_opt": (35, 80),
        "drainage_importance": "Moderate - very hardy, tolerates lower grade and slightly saline/calcareous soils.",
        "yield_potential": "18 - 25 tonnes/ha (consistent regular bearer)",
        "special_advice": "Excellent candidate for moderate soil amendments or marginal lands where sensitive cultivars fail."
    },
    "Amrapali": {
        "id": "amrapali",
        "name": "Amrapali (Dasheri x Neelum)",
        "native_region": "Bred by ICAR-IARI (Delhi), widely grown pan-India",
        "description": "Dwarf hybrid variety bearing regular heavy crops of intense orange, high-carotene pulp.",
        "ideal_soil_types": ["Alluvial Loam", "Fertile Red Loam", "Sandy Loam"],
        "unsuitable_soil_types": ["Rocky Barren Land", "Waterlogged Heavy Silt"],
        "ph_min": 5.8,
        "ph_opt_min": 6.2,
        "ph_opt_max": 7.5,
        "ph_max": 8.0,
        "n_opt": (150, 220),
        "p_opt": (25, 55),
        "k_opt": (170, 270),
        "temp_opt": (20, 38),
        "humidity_opt": (45, 80),
        "drainage_importance": "High - shallow roots in High Density Planting (HDP) require good drainage.",
        "yield_potential": "16 - 22 tonnes/ha under High Density Planting (1600 plants/ha)",
        "special_advice": "Ideal for close spacing (2.5m x 2.5m). Requires frequent nutrient replenishment and pruning."
    },
    "Chaunsa": {
        "id": "chaunsa",
        "name": "Chaunsa (Samar Bahisht)",
        "native_region": "North India (Punjab, Haryana, UP)",
        "description": "Late-season mango with golden yellow color, heavenly fragrance, and exceptionally sweet nectar.",
        "ideal_soil_types": ["Deep Alluvial Loam", "Fertile River Silt Loam"],
        "unsuitable_soil_types": ["Shallow Rocky Ground", "Saline Soil"],
        "ph_min": 6.0,
        "ph_opt_min": 6.3,
        "ph_opt_max": 7.4,
        "ph_max": 7.9,
        "n_opt": (140, 200),
        "p_opt": (20, 45),
        "k_opt": (160, 250),
        "temp_opt": (22, 38),
        "humidity_opt": (40, 75),
        "drainage_importance": "High - deep root system needs porous soil down to 2m.",
        "yield_potential": "10 - 15 tonnes/ha",
        "special_advice": "Late ripening in July-August. Protect developing fruits from fruit fly with pheromone traps."
    },
    "Mallika": {
        "id": "mallika",
        "name": "Mallika (Neelum x Dasheri)",
        "native_region": "ICAR-IARI bred, suited to both North and South India",
        "description": "Large oblong fruit, rich fiberless honey pulp with the highest vitamin A content among hybrids.",
        "ideal_soil_types": ["Red Sandy Loam", "Alluvial Loam", "Well Drained Clay Loam"],
        "unsuitable_soil_types": ["Stagnant Wet Clay"],
        "ph_min": 5.8,
        "ph_opt_min": 6.2,
        "ph_opt_max": 7.5,
        "ph_max": 8.0,
        "n_opt": (130, 200),
        "p_opt": (20, 50),
        "k_opt": (160, 260),
        "temp_opt": (22, 39),
        "humidity_opt": (40, 80),
        "drainage_importance": "High - regular bearer with high nutrient uptake.",
        "yield_potential": "14 - 20 tonnes/ha",
        "special_advice": "Fruit should be harvested when mature green with slight color break to avoid internal breakdown."
    },
    "Neelum": {
        "id": "neelum",
        "name": "Neelum",
        "native_region": "Tamil Nadu, Karnataka, Andhra Pradesh",
        "description": "Late season variety, compact tree, regular bearer with bright yellow skin and good keeping quality.",
        "ideal_soil_types": ["Laterite Soil", "Red Loam", "Sandy Loam", "Alluvial Loam"],
        "unsuitable_soil_types": ["Waterlogged Soils"],
        "ph_min": 5.8,
        "ph_opt_min": 6.2,
        "ph_opt_max": 7.8,
        "ph_max": 8.2,
        "n_opt": (120, 190),
        "p_opt": (20, 45),
        "k_opt": (150, 240),
        "temp_opt": (22, 40),
        "humidity_opt": (40, 75),
        "drainage_importance": "Moderate - very resilient against drought and variable rainfall.",
        "yield_potential": "12 - 16 tonnes/ha",
        "special_advice": "Highly dependable pollinator and parent variety. Excellent for rainfed conditions."
    }
}


def score_parameter(val: float, opt_min: float, opt_max: float, abs_min: float, abs_max: float) -> float:
    """Calculates a normalized score (0-100) based on optimal and tolerable ranges."""
    if opt_min <= val <= opt_max:
        return 100.0
    if val < abs_min or val > abs_max:
        return 20.0
    if val < opt_min:
        return 20.0 + 80.0 * ((val - abs_min) / max(0.001, opt_min - abs_min))
    # val > opt_max
    return 100.0 - 80.0 * ((val - opt_max) / max(0.001, abs_max - opt_max))


def evaluate_mango_feasibility(
    soil_type: str,
    ph: float,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    moisture: float,
    air_temp: float,
    humidity: float
) -> Dict[str, Any]:
    """Evaluates all varieties and returns sorted feasibility rankings with detailed diagnostic feedback."""
    normalized_soil = (soil_type or "Alluvial Loam").strip()
    results: List[Dict[str, Any]] = []

    # Assess overall soil health summary
    soil_health_notes = []
    if ph < 5.5:
        soil_health_notes.append("Soil is strongly acidic (pH < 5.5). Aluminum toxicity risk; apply agricultural lime (calcium carbonate).")
    elif ph > 7.8:
        soil_health_notes.append("Soil is moderately to strongly alkaline (pH > 7.8). Iron/Zinc lockup risk; apply gypsum and organic compost.")
    else:
        soil_health_notes.append(f"Soil pH ({ph:.1f}) is within the optimal fertility range (5.5 - 7.5) for mango orchards.")

    if nitrogen < 110:
        soil_health_notes.append("Nitrogen is low (<110 mg/kg). Tree canopy vigour may be sluggish; incorporate vermicompost or split urea.")
    elif nitrogen > 230:
        soil_health_notes.append("Nitrogen is excessive (>230 mg/kg). Risk of vegetative overgrowth and spongy tissue; suspend nitrogenous fertilizer.")

    if phosphorus < 18:
        soil_health_notes.append("Phosphorus is deficient (<18 mg/kg). Impairs root branching and panicle development; apply Single Super Phosphate (SSP).")
    if potassium < 140:
        soil_health_notes.append("Potassium is low (<140 mg/kg). Can lead to poor fruit sizing and weak drought defense; apply Muriate of Potash (MOP).")

    for vname, vdata in VARIETY_DATABASE.items():
        # 1. Soil Type Match (30% weight)
        is_ideal_soil = any(s.lower() in normalized_soil.lower() or normalized_soil.lower() in s.lower()
                            for s in vdata["ideal_soil_types"])
        is_unsuitable_soil = any(s.lower() in normalized_soil.lower()
                                 for s in vdata["unsuitable_soil_types"])
        if is_unsuitable_soil:
            soil_score = 25.0
            soil_match_label = "Unsuitable Soil Texture"
        elif is_ideal_soil:
            soil_score = 98.0
            soil_match_label = "Ideal Soil Type"
        else:
            soil_score = 70.0
            soil_match_label = "Acceptable with Aeration / Drainage"

        # 2. pH Match (25% weight)
        ph_score = score_parameter(ph, vdata["ph_opt_min"], vdata["ph_opt_max"], vdata["ph_min"], vdata["ph_max"])

        # 3. NPK Nutrient Match (25% weight)
        n_min, n_max = vdata["n_opt"]
        p_min, p_max = vdata["p_opt"]
        k_min, k_max = vdata["k_opt"]
        n_sc = score_parameter(nitrogen, n_min, n_max, n_min * 0.5, n_max * 1.5)
        p_sc = score_parameter(phosphorus, p_min, p_max, p_min * 0.4, p_max * 1.6)
        k_sc = score_parameter(potassium, k_min, k_max, k_min * 0.5, k_max * 1.5)
        npk_score = (n_sc + p_sc + k_sc) / 3.0

        # 4. Climate & Moisture Match (20% weight)
        t_min, t_max = vdata["temp_opt"]
        h_min, h_max = vdata["humidity_opt"]
        t_sc = score_parameter(air_temp, t_min, t_max, 15.0, 45.0)
        h_sc = score_parameter(humidity, h_min, h_max, 20.0, 95.0)
        m_sc = 95.0 if (12.0 <= moisture <= 28.0) else (60.0 if moisture < 12.0 else 70.0)
        climate_score = (t_sc * 0.4) + (h_sc * 0.3) + (m_sc * 0.3)

        # Composite weighted score
        final_score = (soil_score * 0.30) + (ph_score * 0.25) + (npk_score * 0.25) + (climate_score * 0.20)
        final_score = round(max(10.0, min(99.0, final_score)), 1)

        # Categorization
        if final_score >= 84.0:
            status = "Highly Recommended"
            badge_color = "emerald"
        elif final_score >= 65.0:
            status = "Feasible with Amendments"
            badge_color = "amber"
        else:
            status = "Not Recommended / Challenging"
            badge_color = "rose"

        # Actionable insights specific to this variety
        reasons = []
        if is_ideal_soil:
            reasons.append(f"Soil '{normalized_soil}' perfectly matches native growing conditions.")
        elif is_unsuitable_soil:
            reasons.append(f"Current soil texture is prone to root compaction/disease for this variety.")
        else:
            reasons.append(f"Soil is workable; ensure raised bed planting or organic matter integration.")

        if ph < vdata["ph_opt_min"]:
            reasons.append(f"Current pH {ph:.1f} is lower than ideal ({vdata['ph_opt_min']}-{vdata['ph_opt_max']}).")
        elif ph > vdata["ph_opt_max"]:
            reasons.append(f"Current pH {ph:.1f} is higher than ideal ({vdata['ph_opt_min']}-{vdata['ph_opt_max']}).")
        else:
            reasons.append(f"Soil pH {ph:.1f} is optimal.")

        results.append({
            "id": vdata["id"],
            "name": vdata["name"],
            "native_region": vdata["native_region"],
            "description": vdata["description"],
            "score": final_score,
            "status": status,
            "badge_color": badge_color,
            "soil_match_label": soil_match_label,
            "soil_score": round(soil_score, 1),
            "ph_score": round(ph_score, 1),
            "npk_score": round(npk_score, 1),
            "climate_score": round(climate_score, 1),
            "reasons": reasons,
            "yield_potential": vdata["yield_potential"],
            "drainage_importance": vdata["drainage_importance"],
            "special_advice": vdata["special_advice"],
            "ideal_ph_range": f"{vdata['ph_opt_min']} - {vdata['ph_opt_max']}",
            "ideal_npk": f"N: {n_min}-{n_max}, P: {p_min}-{p_max}, K: {k_min}-{k_max} mg/kg"
        })

    # Sort descending by score
    results.sort(key=lambda x: x["score"], reverse=True)

    return {
        "current_parameters": {
            "soil_type": normalized_soil,
            "ph": round(ph, 2),
            "nitrogen": round(nitrogen, 1),
            "phosphorus": round(phosphorus, 1),
            "potassium": round(potassium, 1),
            "moisture": round(moisture, 1),
            "air_temp": round(air_temp, 1),
            "humidity": round(humidity, 1)
        },
        "soil_health_notes": soil_health_notes,
        "top_pick": results[0]["name"] if results else None,
        "recommendations": results
    }

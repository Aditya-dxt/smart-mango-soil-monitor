"""AI Agronomist Chatbot for Mango Orchards.

Provides conversational intelligence in English and Hindi/Hinglish for:
- Soil NPK, pH, and texture diagnostics
- Variety feasibility recommendations
- Stage-based irrigation & fertilizer scheduling
- Pest and disease warnings
Uses Claude/Anthropic if ANTHROPIC_API_KEY is available, or an expert agronomic rule-engine.
"""
from __future__ import annotations
import os, re
from typing import Dict, Any, Optional
from .feasibility import evaluate_mango_feasibility, VARIETY_DATABASE


SYSTEM_PROMPT = """You are Bhoomi-IQ, an expert AI Agronomist and Horticultural Consultant specialized in commercial mango orchards (*Mangifera indica*).
You advise farmers and orchard managers on soil health (N, P, K, pH, soil type), irrigation moisture management, crop stage phenology, pest/disease prevention, and cultivar feasibility (Alphonso, Kesar, Dasheri, Langra, Banganapalli, Totapuri, Amrapali, etc.).
You communicate fluently and warmly in both English and natural Hindi/Hinglish depending on how the farmer asks.
Provide precise, actionable agricultural advice including specific fertilizers (Urea, DAP, SSP, MOP, Vermicompost) and soil amendments (Agricultural Lime, Gypsum).
Keep answers structured with bullet points and clear takeaways.
"""


def _rule_based_reply(query: str, ctx: Dict[str, Any]) -> str:
    """Expert agronomist fallback engine for answering questions with real sensor numbers."""
    q = query.lower().strip()
    
    # Extract context values safely
    soil_type = ctx.get("soil_type", "Alluvial Loam")
    ph = float(ctx.get("ph", 6.5))
    n = float(ctx.get("nitrogen", 140))
    p = float(ctx.get("phosphorus", 25))
    k = float(ctx.get("potassium", 180))
    moisture = float(ctx.get("soil_moisture", 18.0))
    temp = float(ctx.get("air_temp", 30.0))
    humidity = float(ctx.get("humidity", 55.0))
    stage = ctx.get("stage", "flowering").replace("_", " ")

    # Run feasibility for instant context
    eval_res = evaluate_mango_feasibility(soil_type, ph, n, p, k, moisture, temp, humidity)
    top_pick = eval_res["top_pick"]
    top_score = eval_res["recommendations"][0]["score"] if eval_res["recommendations"] else 85

    is_hindi = any(w in q for w in ["kaise", "kya", "kaunsa", "kon", "mitti", "kare", "chahiye", "aam", "paani", "kitna", "ke liye", "namaste", "batao", "lagega", "karein", "aur", "mere", "mera"])

    # 1. Feasibility / Best variety questions
    if any(k in q for k in ["feasible", "variety", "which mango", "kaunsa aam", "kaunsi variety", "suit", "best mango", "kon sa aam", "plant feasible"]):
        if is_hindi:
            recs = eval_res["recommendations"][:3]
            out = [
                f"🌱 **Aapke Soil aur Climate ke anusaar Feasibility Analysis:**",
                f"• **Current Soil Type:** {soil_type}",
                f"• **Soil pH:** {ph:.1f} | **NPK:** N: {n:.0f}, P: {p:.0f}, K: {k:.0f} mg/kg",
                "",
                f"🏆 **Sabse Best Mango Variety:** **{top_pick}** ({top_score}% Match)",
                "",
                "**Top 3 Recommended Varieties:**"
            ]
            for r in recs:
                out.append(f"1. **{r['name']}** - **{r['score']}% Feasibility** ({r['status']})\n   • *Soil Fit:* {r['soil_match_label']}\n   • *Advice:* {r['special_advice']}")
            out.append(f"\n💡 **Mitti Sudhaar Tip:** Agar aap Alphonso lagana chahte hain toh well-drained soil aur pH 5.8-6.8 chahiye. Kesar aur Totapuri slightly alkaline ya medium black soil mein bhi achha perform karte hain.")
            return "\n".join(out)
        else:
            recs = eval_res["recommendations"][:3]
            out = [
                f"🌱 **Mango Cultivar Feasibility Analysis for your Orchard:**",
                f"• **Detected Soil:** {soil_type} | **pH:** {ph:.2f}",
                f"• **Nutrients (NPK):** N: {n:.0f} mg/kg, P: {p:.0f} mg/kg, K: {k:.0f} mg/kg",
                f"• **Climate:** {temp:.1f}°C, {humidity:.0f}% RH | **Moisture:** {moisture:.1f}%",
                "",
                f"🏆 **Top Match:** **{top_pick}** with **{top_score}% Feasibility**",
                "",
                "**Top Recommended Cultivars:**"
            ]
            for idx, r in enumerate(recs, 1):
                out.append(f"{idx}. **{r['name']}** ({r['score']}% Match - {r['status']})\n   • *Soil Affinity:* {r['soil_match_label']}\n   • *Expected Yield:* {r['yield_potential']}\n   • *Agronomic Note:* {r['special_advice']}")
            out.append("\n💡 *Need specific soil treatment advice for a specific variety? Just ask me!*")
            return "\n".join(out)

    # 2. Specific Variety Checks (Alphonso, Kesar, Dasheri, etc.)
    for vname, vdata in VARIETY_DATABASE.items():
        vkey = vdata["id"]
        if vkey in q or vname.lower() in q:
            match_data = next((r for r in eval_res["recommendations"] if r["id"] == vkey), None)
            score = match_data["score"] if match_data else 75
            status = match_data["status"] if match_data else "Feasible"
            if is_hindi:
                return (
                    f"🥭 **{vname} ke liye Compatibility Report:**\n\n"
                    f"• **Suitability Score:** **{score}%** ({status})\n"
                    f"• **Aapki Mitti:** {soil_type} (Ideal mitti: {', '.join(vdata['ideal_soil_types'])})\n"
                    f"• **pH Status:** Current pH {ph:.1f} (Ideal: {vdata['ph_opt_min']} - {vdata['ph_opt_max']})\n"
                    f"• **Drainage:** {vdata['drainage_importance']}\n"
                    f"• **Yield Anumaan:** {vdata['yield_potential']}\n\n"
                    f"📌 **Vishesh Salaah:** {vdata['special_advice']}"
                )
            else:
                return (
                    f"🥭 **Compatibility Evaluation for {vname}:**\n\n"
                    f"• **Feasibility Score:** **{score}%** ({status})\n"
                    f"• **Soil Requirement:** Prefers {', '.join(vdata['ideal_soil_types'])}. Current soil: {soil_type}.\n"
                    f"• **pH Check:** Current pH is {ph:.1f} vs optimal {vdata['ph_opt_min']} - {vdata['ph_opt_max']}.\n"
                    f"• **Nutrients (NPK):** Optimal N: {vdata['n_opt'][0]}-{vdata['n_opt'][1]}, P: {vdata['p_opt'][0]}-{vdata['p_opt'][1]}, K: {vdata['k_opt'][0]}-{vdata['k_opt'][1]} mg/kg.\n"
                    f"• **Key Guidance:** {vdata['special_advice']}"
                )

    # 3. pH questions
    if "ph" in q or "acid" in q or "alkali" in q or "acidic" in q or "chuna" in q or "gypsum" in q:
        if is_hindi:
            if ph < 6.0:
                return (
                    f"⚗️ **Soil pH Analysis (Current: {ph:.1f} - Acidic):**\n\n"
                    f"Aapki mitti acidic hai. Aam ke podhon ke liye ideal pH 6.0 se 7.2 hota hai.\n\n"
                    f"**Upay (Remedy):**\n"
                    f"1. **Agricultural Lime (Chuna / CaCO3):** 1.5 - 2.5 kg prati tree canopy area mein milayein.\n"
                    f"2. **Dolomite:** Agar magnesium ki kami ho toh dolomite lime dalein.\n"
                    f"3. **Organic Compost / Cow Dung:** Well-rotted Gobar khad mitti ke buffer capacity ko badhati hai."
                )
            elif ph > 7.5:
                return (
                    f"⚗️ **Soil pH Analysis (Current: {ph:.1f} - Alkaline):**\n\n"
                    f"Aapki mitti slightly alkaline hai. High pH mein Iron (Fe) aur Zinc (Zn) ki kami ho sakti hai.\n\n"
                    f"**Upay (Remedy):**\n"
                    f"1. **Agricultural Gypsum (Calcium Sulfate):** 2 - 3 kg prati ped dalein mitti ke drainage aur sodium balance ke liye.\n"
                    f"2. **Elemental Sulfur:** 300 - 500g sulfur powder daal kar pH normalize karein.\n"
                    f"3. **Foliar Spray:** Micronutrient mixture (Zinc EDTA + Ferrous Sulfate) ka chhidkaw karein."
                )
            else:
                return (
                    f"⚗️ **Soil pH Status (Current: {ph:.1f} - Optimal):**\n\n"
                    f"Shabaash! Aapka soil pH 6.0 - 7.2 ke ideal range mein hai. Isme N, P, K aur micronutrients aam ki jado'n (roots) dwara asani se absorb ho jaate hain."
                )
        else:
            return (
                f"⚗️ **Soil pH Evaluation (Current: {ph:.2f}):**\n\n"
                f"• **Optimal Mango Range:** 5.8 to 7.2 (Tolerable: 5.5 to 7.8)\n"
                f"• **Status:** {'Slightly Acidic' if ph < 6.0 else ('Slightly Alkaline' if ph > 7.5 else 'Ideal Range')}\n\n"
                f"**Management Protocols:**\n"
                f"• If pH < 5.8: Broadcast Agricultural Limestone (CaCO3) @ 200-400 g/m² under drip line.\n"
                f"• If pH > 7.6: Apply Agricultural Gypsum or elemental sulfur, combined with humic acid to free locked micronutrients (Fe, Zn, Mn)."
            )

    # 4. NPK & Fertilizer questions
    if any(k in q for k in ["npk", "nitrogen", "phosphorus", "potash", "potassium", "fertilizer", "khad", "dap", "urea", "mop"]):
        if is_hindi:
            return (
                f"🧪 **NPK Nutrient Status aur Fertilizer Recommendation:**\n\n"
                f"• **Nitrogen (N):** {n:.0f} mg/kg ({'Kam (Low)' if n < 120 else ('Adhik (High)' if n > 220 else 'Optimal')})\n"
                f"• **Phosphorus (P):** {p:.0f} mg/kg ({'Kam (Low)' if p < 20 else 'Swasth (Healthy)'})\n"
                f"• **Potassium (K):** {k:.0f} mg/kg ({'Kam (Low)' if k < 150 else 'Balanced'})\n\n"
                f"**Fertilizer Schedule (Per mature tree/year):**\n"
                f"1. **Nitrogen:** Urea (~1.0 kg) 2 se 3 split doses mein dein. Note: Flowering stage mein excessive Urea na dein!\n"
                f"2. **Phosphorus:** DAP (Single Super Phosphate / SSP best hai - 2 kg) post-monsoon mitti mein milayein.\n"
                f"3. **Potassium:** MOP (Muriate of Potash - 1.2 kg) fruit development stage mein dein jisse aam ka size aur meethapan (Brix) badhe.\n"
                f"4. **Organic Khad:** 40-50 kg gobar khad (FYM) ya vermicompost har saal pit circumference mein dein."
            )
        else:
            return (
                f"🧪 **NPK Nutritional Assessment & Fertilizer Plan:**\n\n"
                f"• **Nitrogen (N):** {n:.1f} mg/kg | Benchmark: 120 - 180 mg/kg\n"
                f"• **Phosphorus (P):** {p:.1f} mg/kg | Benchmark: 20 - 45 mg/kg\n"
                f"• **Potassium (K):** {k:.1f} mg/kg | Benchmark: 150 - 250 mg/kg\n\n"
                f"**Action Steps:**\n"
                f"• **N Maintenance:** Apply Urea in split applications during vegetative flushes. Restrict before flowering.\n"
                f"• **P Maintenance:** Apply Single Super Phosphate (SSP) or DAP incorporated into the top 15 cm ring under the canopy edge.\n"
                f"• **K Fruit Quality:** Supplement Sulfate/Muriate of Potash during pea-to-marble fruit development for higher fruit weight and sweetness."
            )

    # 5. Moisture & Irrigation questions
    if any(k in q for k in ["moisture", "water", "irrigation", "sinchai", "paani", "nami"]):
        if is_hindi:
            return (
                f"💧 **Soil Moisture & Sinchai (Irrigation) Salah:**\n\n"
                f"• **Current Moisture:** {moisture:.1f}% (VWC)\n"
                f"• **Current Stage:** {stage.title()}\n"
                f"• **Air Temp & Humidity:** {temp:.1f}°C, {humidity:.0f}%\n\n"
                f"**Sinchai Niyam:**\n"
                f"1. **Pre-flowering (Flower aane se pehle):** Paani band ya kam rakhein (mild stress zaroori hai flower buds trigger karne ke liye).\n"
                f"2. **Fruit Set (Aam chhota hone par):** Drip irrigation se regular sinchai dein taki fruit drop na ho.\n"
                f"3. **Fruit Maturity:** Harvest se 15 din pehle sinchai band kar dein taaki shelf life achhi rahe."
            )
        else:
            return (
                f"💧 **Orchard Irrigation & Moisture Advisory:**\n\n"
                f"• **Observed Moisture:** {moisture:.1f}% VWC\n"
                f"• **Crop Phenological Stage:** {stage.title()}\n"
                f"• **Atmospheric Demand:** Temp {temp:.1f}°C, RH {humidity:.0f}%\n\n"
                f"**Irrigation Directives:**\n"
                f"• Ensure deep root saturation without surface ponding.\n"
                f"• Maintain regulated deficit irrigation (RDI) prior to panicle emergence to stimulate flowering rather than vegetative flush."
            )

    # 6. Default comprehensive agronomist advice
    if is_hindi:
        return (
            f"Namaste! Main hoon aapka AI Orchard Agronomist (Bhoomi-IQ).\n\n"
            f"📊 **Aapke Orchard ke Current Data:**\n"
            f"• **Mitti (Soil Type):** {soil_type}\n"
            f"• **pH:** {ph:.1f} | **NPK:** N: {n:.0f}, P: {p:.0f}, K: {k:.0f} mg/kg\n"
            f"• **Moisture:** {moisture:.1f}% | **Temp:** {temp:.1f}°C | **Humidity:** {humidity:.0f}%\n"
            f"• **Sabse Upayukt Aam:** **{top_pick}** ({top_score}% Feasible)\n\n"
            f"Aap mujhse pooch sakte hain:\n"
            f"1. *'Mere mitti ke hisab se kaun sa aam best hai?'*\n"
            f"2. *'Alphonso ya Kesar ke liye mitti kaise taiyar karein?'*\n"
            f"3. *'pH aur NPK khad ka anupaat kitna hona chahiye?'*\n"
            f"4. *'Abhi kitna paani/sinchai dena chahiye?'*"
        )
    else:
        return (
            f"Hello! I am Bhoomi-IQ, your AI Horticultural & Soil Consultant.\n\n"
            f"📊 **Current Sensor Snapshot:**\n"
            f"• **Soil Texture:** {soil_type} (pH: {ph:.2f})\n"
            f"• **Nutrients:** N: {n:.0f}, P: {p:.0f}, K: {k:.0f} mg/kg\n"
            f"• **Moisture:** {moisture:.1f}% | **Climate:** {temp:.1f}°C, {humidity:.0f}% RH\n"
            f"• **Top Ranked Variety:** **{top_pick}** ({top_score}% Feasibility)\n\n"
            f"Feel free to ask questions like:\n"
            f"• *'Which mango variety is most feasible for my soil?'*\n"
            f"• *'How do I correct my soil pH or NPK deficiencies?'*\n"
            f"• *'Can I plant Alphonso or Kesar in this location?'*\n"
            f"• *'What is the optimal irrigation schedule for the current stage?'*"
        )


async def answer_query(query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Answers farmer query using LLM if available, else rich agronomic fallback engine."""
    ctx = context or {}
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=api_key)
            prompt_context = (
                f"Current Orchard Status:\n"
                f"- Soil Type: {ctx.get('soil_type', 'Alluvial Loam')}\n"
                f"- Soil pH: {ctx.get('ph', 6.5)}\n"
                f"- Nitrogen (N): {ctx.get('nitrogen', 140)} mg/kg\n"
                f"- Phosphorus (P): {ctx.get('phosphorus', 25)} mg/kg\n"
                f"- Potassium (K): {ctx.get('potassium', 180)} mg/kg\n"
                f"- Soil Moisture: {ctx.get('soil_moisture', 18)}% VWC\n"
                f"- Air Temp: {ctx.get('air_temp', 30)}°C, Humidity: {ctx.get('humidity', 55)}%\n"
                f"- Stage: {ctx.get('stage', 'pre_flowering')}\n"
            )
            msg = await client.messages.create(
                model=os.getenv("ADVISOR_MODEL", "claude-3-5-haiku-latest"),
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": f"{prompt_context}\n\nFarmer Query: {query}"}
                ]
            )
            reply = msg.content[0].text
            return {"reply": reply, "engine": "anthropic-llm"}
        except Exception as e:
            # Fallback gracefully
            pass

    reply = _rule_based_reply(query, ctx)
    return {"reply": reply, "engine": "agronomist-expert-engine"}

import os
import json
import asyncio
import urllib.request
import urllib.error
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["advisory"])

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"


class AdvisoryRequest(BaseModel):
    crop: str
    query: str = Field(..., description="Farmer's question")
    temperature: Optional[float] = 28.0
    rainfall: Optional[float] = 0.0
    wind_speed: Optional[float] = 5.0
    humidity: Optional[float] = 50.0
    language: str = "hinglish"  # hinglish, dogri, pahari


DIALECT_STYLE_GUIDES = {
    "dogri": {
        "greeting": "Namaste Kisan Veer!",
        "words": {"rain": "mheeh", "water": "paani", "wind": "hawa"},
    },
    "pahari": {
        "greeting": "Aadaab Kisan Bura!",
        "words": {"rain": "baraash", "water": "paani", "wind": "vaah"},
    },
    "hinglish": {"greeting": "Namaste Kisan Bhai!", "words": {}},
}


def _call_llm_sync(query: str, crop: str, lang: str, weather_ctx: dict) -> str:
    # Safe Local Agronomy Fallback
    if not ANTHROPIC_API_KEY:
        rain = weather_ctx.get("rainfall") or 0.0
        wind = weather_ctx.get("wind_speed") or 0.0

        if lang == "dogri":
            if rain > 5.0:
                return f"Namaste Kisan Veer! Ajj mheeh ({rain} mm) da khatra ae. {crop} gi paani matt deyo, te spray theeri jaao."
            elif wind > 15.0:
                return f"Namaste Kisan Veer! Hawa tej chaldi payi ae ({wind} km/h). Spray uddi jaana, shaant hone di udheek karo."
            return f"Namaste Kisan Veer! Ajj mausam khushk ae. {crop} gi drip raahi paani deyo, dophar baad spray kari sakde o."

        elif lang == "pahari":
            if rain > 5.0:
                return f"Aadaab Kisan Bura! Tez baraash aani aali ae ({rain} mm). {crop} ki paani na laayo, zameen vich paani jama na hosi."
            elif wind > 15.0:
                return f"Aadaab Kisan Bura! Vaah tej chalni payi ae ({wind} km/h). Dawaai bekaar jaasi, vaah theerne di udheek karo."
            return f"Aadaab Kisan Bura! Ajj dhupp kaddhsi. {crop} ki sinchai karo, shaam vele spray safe hosi."

        else:
            if rain > 5.0:
                return f"Namaste Kisan Bhai! Aaj {rain} mm barish ki sambhavna hai. {crop} me sinchai aur spray dono rok dein."
            elif wind > 15.0:
                return f"Namaste Kisan Bhai! Hawa tez hai ({wind} km/h). Spray hawa me drift ho jayega, wait karein."
            return f"Namaste Kisan Bhai! Aaj mausam saaf hai. {crop} ko normal paani dein, shaam 3 baje ke baad spray safe hai."

    # Live API Call
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    system_prompt = f"You are an agricultural advisor for Rajouri farmers. Crop: {crop}. Answer in short practical tone in {lang}."
    payload = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 250,
            "system": system_prompt,
            "messages": [{"role": "user", "content": query}],
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        ANTHROPIC_URL, data=payload, headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            return res.get("content", [{}])[0].get("text", "").strip()
    except Exception:
        return f"Mausam Update: {crop} ke liye mausam normal hai."


@router.post("/farmer-advisory")
async def get_farmer_advisory(req: AdvisoryRequest):
    lang = req.language.lower()
    if lang not in DIALECT_STYLE_GUIDES:
        lang = "hinglish"

    weather_ctx = {
        "temperature": req.temperature,
        "rainfall": req.rainfall,
        "wind_speed": req.wind_speed,
        "humidity": req.humidity,
    }

    advisory_text = await asyncio.to_thread(
        _call_llm_sync, req.query, req.crop, lang, weather_ctx
    )

    return {
        "language": lang,
        "crop": req.crop,
        "query": req.query,
        "advisory": advisory_text,
    }

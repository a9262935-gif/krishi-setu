"""
main.py
--------
Slim entrypoint: just wiring routers, middleware, models, and the dashboard.
All advisory logic now lives in app/services/advisory_service.py +
app/routers/advisory.py — keep it that way so this file stays clean.
"""

import os
import joblib
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.services.weather import OpenMeteoWeatherService
from app.routers.advisory import router as advisory_router

app = FastAPI(title="Krishi Setu Core")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("app/templates", exist_ok=True)
templates = Jinja2Templates(directory="app/templates")
weather_service = OpenMeteoWeatherService()

# ML models — loaded once at startup. Paths are relative to wherever you run
# `uvicorn` from, so always launch from the project root.
hazard_model = joblib.load("ml_models/hazard_classifier.pkl")
price_model = joblib.load("ml_models/mandi_dynamic_model.pkl")

# Advisory endpoint (POST /api/v1/farmer-advisory) now comes from this router
app.include_router(advisory_router)


@app.get("/api/v1/live-weather")
async def live_weather_api(model: str = "best_match"):
    w = await weather_service.fetch_live_weather(33.3764, 74.3168, models=[model])
    return JSONResponse(
        content={
            "temp": w.get("temperature_2m"),
            "humidity": w.get("relative_humidity_2m"),
            "wind_speed": w.get("wind_speed_10m"),
            "rain_prob": w.get("precipitation", 0.0),
            "weather_code": w.get("weather_code", 0),
            "active_model": model,
        }
    )


@app.post("/api/v1/predict-price")
async def dynamic_predict(req: Request):
    body = await req.json()
    crop = body.get("crop", "Maize")
    elevation = float(body.get("elevation", 900.0))
    arrival = float(body.get("arrival", 45.0))
    sel_model = body.get("weather_model", "best_match")

    raw_w = await weather_service.fetch_live_weather(
        33.3764, 74.3168, models=[sel_model]
    )
    temp = float(raw_w.get("temperature_2m", 18.5))
    hum = float(raw_w.get("relative_humidity_2m", 70.0))
    wind = float(raw_w.get("wind_speed_10m", 4.0))
    rain = float(raw_w.get("precipitation", 0.0))

    features_price = pd.DataFrame(
        [
            {
                "Crop": crop,
                "Rainfall_mm": rain,
                "Wind_kmh": wind,
                "Temp_C": temp,
                "Arrival_Tonnes": arrival,
                "Elevation_m": elevation,
            }
        ]
    )
    pred_price = round(float(price_model.predict(features_price)[0]), 2)

    features_hazard = pd.DataFrame(
        [
            {
                "Rainfall_mm": rain,
                "Wind_kmh": wind,
                "Temp_C": temp,
                "Humidity": hum,
                "Elevation_m": elevation,
            }
        ]
    )
    risk_level = int(hazard_model.predict(features_hazard)[0])

    return JSONResponse(
        content={
            "crop": crop,
            "predicted_price": pred_price,
            "risk_level": risk_level,
            "live_metrics": {
                "temp": temp,
                "humidity": hum,
                "wind": wind,
                "rain": rain,
            },
        }
    )


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

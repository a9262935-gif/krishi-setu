import time
from enum import Enum
from typing import Iterable, Optional
import httpx

BASE_URL = 'https://api.open-meteo.com/v1/forecast'

DEFAULT_CURRENT_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "precipitation",
    "weather_code",
]

DEFAULT_HOURLY_FIELDS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation_probability",
    "precipitation",
    "wind_speed_10m",
    "weather_code",
]

DEFAULT_DAILY_FIELDS = [
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "precipitation_probability_max",
    "weather_code",
]


class WeatherModel(str, Enum):
    BEST_MATCH = "best_match"
    GFS_SEAMLUSS = "gfs_seamless"
    ICON_SEAMLESS = "icon_seamless"
    ECMWF_IFS025 = "ecmwf_ifs025"
    UKMO_SEAMLUSS = "ukmo_seamless"
    ECMWF_AIFS = "ecmwf_aifs025_single"
    GFS_GRAPHCAST = "gfs_graphcast025"
    NCEP_AIGFS = "ncep_aigfs025"


class OpenMeteoWeatherService:
    def __init__(self, base_url: str = BASE_URL, timeout: float = 10.0):
        self.base_url = base_url
        self.timeout = timeout

    def _models_param(self, models: Optional[Iterable[str]]) -> Optional[str]:
        if not models:
            return None
        return ",".join(m.value if isinstance(m, WeatherModel)
else str(m) for m in models)

    async def _get(self, params: dict) -> dict:
        params["_"] = int(time.time())
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            res = await client.get(self.base_url, params=params)
            res.raise_for_status()
            return res.json()

    async def fetch_live_weather(
        self,
        lat: float,
        lon: float,
        models: Optional[Iterable[str]] = None,
        fields: Iterable[str] = DEFAULT_CURRENT_FIELDS,
    ) -> dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ",".join(fields),
        }
        model_str = self._models_param(models)
        if model_str:
            params["models"] = model_str

        data = await self._get(params)
        return self._extract("current", data, fields, model_str)

    async def fetch_hourly_forecast(
        self,
        lat: float,
        lon: float,
        models: Optional[Iterable[str]] = None,
        fields: Iterable[str] = DEFAULT_HOURLY_FIELDS,
        forecast_days: int = 7,
    ) -> dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ",".join(fields),
            "forecast_days": forecast_days,
        }
        model_str = self._models_param(models)
        if model_str:
            params["models"] = model_str

        data = await self._get(params)
        return self._extract("hourly", data, fields, model_str)


    async def fetch_daily_forecast(
        self,
        lat: float,
        lon: float,
        models: Optional[Iterable[str]] = None,
        fields: Iterable[str] = DEFAULT_DAILY_FIELDS,
        forecast_days: int = 7,
        past_days: int = 0,
    ) -> dict:
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ",".join(fields),
            "forecast_days": forecast_days,
            "timezone": "auto",
        }
        if past_days:
            params["past_days"] = past_days
        model_str = self._models_param(models)
        if model_str:
            params["models"] = model_str

        data = await self._get(params)
        result = self._extract("daily", data, fields, model_str)
        result["_dates"] = data.get("daily", {}).get("time", [])
        return result


    @staticmethod
    def _extract(block: str, data: dict, fields: Iterable[str], model_str: Optional[str]) -> dict:
        section = data.get(block, {})
        if not model_str or "," not in model_str:
            return {f: section.get(f) for f in fields}

        result = {}
        for model in model_str.split(","):
            result[model] = {
                f: section.get(f"{f}_{model}", section.get(f))
                for f in fields
            }
        return result


async def fetch_live_weather(
    lat: float = 33.3764,
    lon: float = 74.3168,
    model: str = WeatherModel.BEST_MATCH.value,
):
    service = OpenMeteoWeatherService()
    res = await service.fetch_live_weather(lat, lon, models=[model])
    return {
        "temp": res.get("temperature_2m", 20.0),
        "humidity": res.get("relative_humidity_2m", 65),
        "wind_speed": res.get("wind_speed_10m", 3.0),
        "rain_prob": res.get("precipitation", 0.0),
        "weather_code": res.get("weather_code", 0),
    }

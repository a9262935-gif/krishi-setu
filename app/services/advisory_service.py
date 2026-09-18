import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime

# 1 Kanal = 505.857 Square Meters (Himalayan / North Indian land conversion)
KANAL_TO_SQ_METERS = 505.857


class FarmerMemoryStore:
    """In-Memory user query and historical adaptation engine."""

    def __init__(self):
        self.history: Dict[str, List[dict]] = {}

    def log_interaction(self, farmer_id: str, query: dict, recommendation: dict):
        if farmer_id not in self.history:
            self.history[farmer_id] = []
        self.history[farmer_id].append(
            {
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "result": recommendation,
            }
        )

    def get_past_crops(self, farmer_id: str) -> List[str]:
        if farmer_id not in self.history:
            return []
        return [
            entry["result"]["recommended_crop"] for entry in self.history[farmer_id]
        ]


memory_engine = FarmerMemoryStore()


class DynamicCropAdvisor:
    """Dynamic ML & Mathematical Crop Suitability Engine with Precision Water & Spray Advisory."""

    # Reference ideal agronomic vectors: [N, P, K, Temp, Humidity, pH, Rainfall]
    CROP_PROFILES = {
        "Rice": np.array([80.0, 40.0, 40.0, 24.0, 80.0, 6.5, 200.0]),
        "Wheat": np.array([120.0, 60.0, 40.0, 15.0, 55.0, 6.8, 75.0]),
        "Maize": np.array([100.0, 50.0, 40.0, 22.0, 65.0, 6.2, 100.0]),
        "Cotton": np.array([120.0, 60.0, 50.0, 26.0, 60.0, 7.5, 80.0]),
        "Mustard": np.array([80.0, 40.0, 30.0, 18.0, 50.0, 7.0, 45.0]),
        "Pulses (Moong)": np.array([20.0, 45.0, 20.0, 28.0, 60.0, 7.2, 50.0]),
    }

    BASE_YIELDS = {
        "Rice": 45.0,
        "Wheat": 48.0,
        "Maize": 40.0,
        "Cotton": 22.0,
        "Mustard": 18.0,
        "Pulses (Moong)": 14.0,
    }

    MSP_RATES = {
        "Rice": 2300.0,
        "Wheat": 2425.0,
        "Maize": 2225.0,
        "Cotton": 7120.0,
        "Mustard": 5650.0,
        "Pulses (Moong)": 8558.0,
    }

    @classmethod
    def calculate_precision_irrigation(
        cls,
        temp_c: float,
        humidity_pct: float,
        rain_mm: float,
        land_kanals: float = 2.0,
        language: str = "hi",
    ) -> Dict[str, Any]:
        """Calculates exact volumetric water requirements scaled directly to the farmer's landholding in Kanals."""
        # 1. Base agronomic requirement: 25 Litres per square meter
        base_litres_per_sqm = 25.0

        # 2. Physics-based heat and atmospheric dryness stress
        temp_stress = 15.0 if temp_c >= 32.0 else (10.0 if temp_c >= 28.0 else 0.0)
        humidity_stress = 5.0 if humidity_pct <= 40.0 else 0.0

        # 3. Direct rain deduction (1 mm rain = 1 Litre per square meter)
        net_litres_per_sqm = max(
            0.0, (base_litres_per_sqm + temp_stress + humidity_stress) - rain_mm
        )

        # If natural rain is >= 5 mm, halt artificial irrigation completely
        if rain_mm >= 5.0:
            net_litres_per_sqm = 0.0

        total_area_sqm = land_kanals * KANAL_TO_SQ_METERS
        total_water_litres = int(round(net_litres_per_sqm * total_area_sqm))

        # Multilingual natural advisories
        if net_litres_per_sqm > 0:
            advice_dict = {
                "hi": f"आज वर्षा {rain_mm} mm है। प्रति वर्ग मीटर {round(net_litres_per_sqm, 1)} L पानी दें। आपकी {land_kanals} कनाal ({int(total_area_sqm)} वर्ग मी.) भूमि के लिए कुल {total_water_litres:,} लीटर पानी की आवश्यकता है।",
                "dogri": f"Ajj mheeh: {rain_mm} mm. Ik square meter ch {round(net_litres_per_sqm, 1)} Litre paani deyo. Thundi {land_kanals} kanal zameen vaste kul {total_water_litres:,} Litre paani lagna ahe.",
                "pahari": f"Ajj baraash: {rain_mm} mm. Fasal vaste {round(net_litres_per_sqm, 1)} L/sq.m paani darkaar e. Thundiyaan {land_kanals} kanaalan vaste kul {total_water_litres:,} Litre paani paao.",
                "en": f"Forecasted rain is {rain_mm} mm. Apply {round(net_litres_per_sqm, 1)} L/sq.m. For your {land_kanals} Kanal ({int(total_area_sqm)} sq.m), deliver ~{total_water_litres:,} Litres.",
            }
        else:
            advice_dict = {
                "hi": f"आज {rain_mm} mm वर्षा का अनुमान है। आज सिंचाई पूरी तरह बंद रखें, इससे पानी और बिजली की बचत होगी और जड़ सड़न रुकेगी।",
                "dogri": f"Ajj {rain_mm} mm mheeh/jhari peyni ahe. Sinchai bilkul band rakho, paani bachega te fasal bachegi.",
                "pahari": f"Ajj {rain_mm} mm baraash hosi. Sinchai band rakkho taaki fasal bach sake.",
                "en": f"Forecasted rainfall is {rain_mm} mm. Halt all manual watering today to prevent root rot and conserve inputs.",
            }

        return {
            "litres_per_sqm": round(net_litres_per_sqm, 1),
            "land_kanals": land_kanals,
            "total_area_sqm": round(total_area_sqm, 1),
            "total_water_litres": total_water_litres,
            "irrigation_needed": net_litres_per_sqm > 0,
            "advisory": advice_dict.get(language, advice_dict["hi"]),
        }

    @classmethod
    def evaluate_spray_window(
        cls, wind_kmh: float, rain_mm: float, language: str = "hi"
    ) -> Dict[str, Any]:
        """Prevents aerodynamic chemical drift (>15 km/h) and precipitation runoff."""
        can_spray = (wind_kmh < 15.0) and (rain_mm < 2.0)

        hazards = []
        if wind_kmh >= 15.0:
            hazards.append(f"Hawa ki raftaar {wind_kmh} km/h hai (>15 km/h limit).")
        if rain_mm >= 2.0:
            hazards.append(f"Agli baarish {rain_mm} mm anumanit hai.")

        if can_spray:
            advice_dict = {
                "hi": f"छिड़काव के लिए मौसम अनुकूल है। हवा की गति ({wind_kmh} km/h) सीमा में है। 11:00 AM से पहले स्प्रे पूरा करें।",
                "dogri": f"Ajj davaai spray karne da vela theek ahe. Hawa di raftaar ({wind_kmh} km/h) bilkul theek ahe.",
                "pahari": f"Ajj davaai chhidkane vaste mausam saaf e. Hawa ({wind_kmh} km/h) theek chalni ahe.",
                "en": f"Safe spray window open. Wind velocity ({wind_kmh} km/h) and rainfall are optimal.",
            }
        else:
            advice_dict = {
                "hi": f"चेतावनी: रासायनिक छिड़काव तुरंत रोक दें! {' '.join(hazards)} इससे 45% से अधिक रसायन हवा में उड़कर नष्ट हो जाएगा।",
                "dogri": f"Khabardaar: Ajj spray bilkul na karo! {' '.join(hazards)} Davaai hawa ch uddi jaani ahe.",
                "pahari": f"Khabardaar: Ajj davaai na chhidko! {' '.join(hazards)} Dawaai kharab ho jasi.",
                "en": f"ALERT: Halt foliar chemical spraying. {' '.join(hazards)} High risk of severe drift/washout.",
            }

        return {
            "can_spray": can_spray,
            "wind_speed_kmh": wind_kmh,
            "status": "OPTIMAL WINDOW" if can_spray else "HALT SPRAYING",
            "advisory": advice_dict.get(language, advice_dict["hi"]),
        }

    @classmethod
    def evaluate(cls, farmer_id: Optional[str], params: dict) -> dict:
        user_vector = np.array(
            [
                params["nitrogen"],
                params["phosphorus"],
                params["potassium"],
                params["temperature"],
                params["humidity"],
                params["ph"],
                params["rainfall"],
            ]
        )

        scores = {}
        # Dynamic Euclidean distance scoring with normalization weights
        weights = np.array([0.15, 0.15, 0.10, 0.15, 0.10, 0.15, 0.20])

        past_crops = memory_engine.get_past_crops(farmer_id) if farmer_id else []

        for crop, profile in cls.CROP_PROFILES.items():
            # Normalized difference
            diff = np.abs(user_vector - profile) / (profile + 1e-5)
            weighted_error = np.dot(diff, weights)
            confidence = float(np.clip(1.0 / (1.0 + weighted_error), 0.1, 0.99))

            # Crop Rotation Adaptation: Penalize repetitive single-crop exhaustion
            rotation_penalty = 1.0
            if past_crops and past_crops[-1] == crop:
                rotation_penalty = 0.82  # 18% penalty for soil depletion risk

            scores[crop] = confidence * rotation_penalty

        # Best candidate selection
        best_crop = max(scores, key=scores.get)
        confidence = float(scores[best_crop])

        # Dynamic yield & revenue computation based on soil health match
        estimated_yield = round(
            cls.BASE_YIELDS[best_crop] * (0.85 + 0.3 * confidence), 2
        )
        estimated_revenue = round(estimated_yield * cls.MSP_RATES[best_crop], 2)

        rotation_advice = "Optimal for continuous cultivation."
        if past_crops and past_crops[-1] == best_crop:
            rotation_advice = f"WARNING: Monoculture risk detected. Consider rotating to Pulses to restore soil Nitrogen."

        # Precision Irrigation & Spray Integration
        land_kanals = float(params.get("land_kanals", 2.0))
        wind_kmh = float(params.get("wind_speed", 8.0))
        lang = params.get("language", "hi")

        water_advisory = cls.calculate_precision_irrigation(
            temp_c=params["temperature"],
            humidity_pct=params["humidity"],
            rain_mm=params["rainfall"],
            land_kanals=land_kanals,
            language=lang,
        )

        spray_advisory = cls.evaluate_spray_window(
            wind_kmh=wind_kmh, rain_mm=params["rainfall"], language=lang
        )

        result = {
            "farmer_id": farmer_id or "ANONYMOUS",
            "recommended_crop": best_crop,
            "confidence_score": round(confidence, 3),
            "potential_yield_quintal_per_hectare": estimated_yield,
            "estimated_revenue_per_hectare": estimated_revenue,
            "crop_rotation_status": rotation_advice,
            "precision_irrigation": water_advisory,
            "spray_decision": spray_advisory,
            "evaluated_metrics": {k: round(v, 3) for k, v in scores.items()},
        }

        if farmer_id:
            memory_engine.log_interaction(farmer_id, params, result)

        return result

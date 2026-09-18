import numpy as np
from typing import Dict, List, Optional
from datetime import datetime


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
    """Dynamic ML & Mathematical Crop Suitability Engine."""

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

        result = {
            "farmer_id": farmer_id or "ANONYMOUS",
            "recommended_crop": best_crop,
            "confidence_score": round(confidence, 3),
            "potential_yield_quintal_per_hectare": estimated_yield,
            "estimated_revenue_per_hectare": estimated_revenue,
            "crop_rotation_status": rotation_advice,
            "evaluated_metrics": {k: round(v, 3) for k, v in scores.items()},
        }

        if farmer_id:
            memory_engine.log_interaction(farmer_id, params, result)

        return result

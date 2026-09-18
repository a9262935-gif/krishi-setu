from datetime import date, datetime
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, ConfigDict, model_validator, computed_field


# ==============================================================================
# Market & Mandi Contracts
# ==============================================================================
class MandiRecord(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "state": "Punjab",
                "district": "Ludhiana",
                "market": "Khanna",
                "commodity": "Wheat",
                "variety": "Dara",
                "arrival_date": "2026-09-15",
                "min_price": 2275.0,
                "max_price": 2450.0,
                "modal_price": 2350.0,
                "source": "agmarknet",
                "fetched_at": "2026-09-15T08:00:00",
            }
        }
    )

    state: str
    district: str
    market: str
    commodity: str
    variety: str
    arrival_date: date
    min_price: float = Field(..., ge=0.0)
    max_price: float = Field(..., ge=0.0)
    modal_price: float = Field(..., ge=0.0)
    source: Literal["agmarknet", "manual_seed", "cached"] = "agmarknet"
    fetched_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_price_bounds(self) -> "MandiRecord":
        if self.max_price < self.min_price:
            raise ValueError("max_price cannot be less than min_price")
        if self.modal_price < self.min_price:
            raise ValueError("modal_price cannot be below min_price")
        if self.modal_price > self.max_price:
            raise ValueError("modal_price cannot exceed max_price")
        return self

    @computed_field
    @property
    def price_spread_pct(self) -> float:
        if self.modal_price == 0:
            return 0.0
        return round((self.max_price - self.min_price) / self.modal_price * 100, 2)


class PriceAnalyticsResponse(BaseModel):
    commodity: str
    market: str
    current_modal_price: float
    moving_avg_7d: float
    volatility_index: float
    recommended_action: str = Field(
        ..., example="HOLD (Expected price surge of 4.2% within 72h)"
    )


class PaginatedMandiResponse(BaseModel):
    total_count: int
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=200)
    results: List[MandiRecord]

    @computed_field
    @property
    def has_next_page(self) -> bool:
        return self.page * self.page_size < self.total_count


# ==============================================================================
# Crop Advisory Contracts
# ==============================================================================
class CropPredictionInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nitrogen": 90.0,
                "phosphorus": 42.0,
                "potassium": 43.0,
                "temperature": 20.8,
                "humidity": 82.0,
                "ph": 6.5,
                "rainfall": 202.9,
            }
        }
    )

    nitrogen: float = Field(..., ge=0, le=300)
    phosphorus: float = Field(..., ge=0, le=300)
    potassium: float = Field(..., ge=0, le=300)
    temperature: float = Field(..., ge=-10, le=60)
    humidity: float = Field(..., ge=0, le=100)
    ph: float = Field(..., ge=0, le=14)
    rainfall: float = Field(..., ge=0, le=3000)


class ModelMetadata(BaseModel):
    engine_type: Literal["rule_engine", "trained_ml_model", "llm_reasoning"] = (
        "rule_engine"
    )
    engine_version: str = "v1.0"
    inference_time_ms: Optional[float] = None


class CropPredictionResponse(BaseModel):
    recommended_crop: str
    suitability_score: float = Field(..., ge=0.0, le=1.0)
    potential_yield_quintal_per_hectare: float
    estimated_revenue_per_hectare: float
    model_meta: ModelMetadata = Field(default_factory=ModelMetadata)

    @computed_field
    @property
    def revenue_per_quintal(self) -> float:
        if self.potential_yield_quintal_per_hectare == 0:
            return 0.0
        return round(
            self.estimated_revenue_per_hectare
            / self.potential_yield_quintal_per_hectare,
            2,
        )


# ==============================================================================
# Logistics Pooling Contracts
# ==============================================================================
class FarmerTransitRequest(BaseModel):
    farmer_id: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    produce_weight_quintals: float = Field(..., gt=0.0)
    destination_mandi: str


class PoolingBatchResponse(BaseModel):
    batch_id: str
    total_volume_quintals: float
    aggregated_farmers: List[str]
    estimated_cost_per_farmer: float
    savings_percentage: float


# ==============================================================================
# Farmer Query Understanding & History
# ==============================================================================
class FarmerQueryInput(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "farmer_id": "FARMER_1042",
                "raw_text": "mera gehu ka bhav kya hai khanna mandi mein aaj",
                "language_hint": "hi",
            }
        }
    )

    farmer_id: str
    raw_text: str = Field(..., min_length=1)
    language_hint: Optional[str] = None


class FarmerQueryResponse(BaseModel):
    intent: Literal[
        "price_check",
        "irrigation_advice",
        "disease_check",
        "crop_recommendation",
        "logistics_help",
        "unclear",
    ]
    extracted_commodity: Optional[str] = None
    extracted_location: Optional[str] = None
    natural_language_reply: str
    needs_clarification: bool = False
    model_meta: ModelMetadata = Field(
        default_factory=lambda: ModelMetadata(engine_type="llm_reasoning")
    )


class FarmerHistoryEntry(BaseModel):
    timestamp: datetime
    query_text: str
    intent: str
    crop_involved: Optional[str] = None
    outcome_note: Optional[str] = None


class FarmerProfile(BaseModel):
    farmer_id: str
    preferred_language: Optional[str] = None
    land_size_hectares: Optional[float] = Field(default=None, ge=0)
    typical_crops: List[str] = Field(default_factory=list)
    history: List[FarmerHistoryEntry] = Field(default_factory=list)

    @computed_field
    @property
    def most_common_crop(self) -> Optional[str]:
        if not self.history:
            return None
        counts: Dict[str, int] = {}
        for entry in self.history:
            if entry.crop_involved:
                counts[entry.crop_involved] = counts.get(entry.crop_involved, 0) + 1
        return max(counts, key=counts.get) if counts else None


class ErrorResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_code": "INVALID_MANDI_RECORD",
                "message": "modal_price cannot exceed max_price",
                "path": "/api/v1/market/records",
            }
        }
    )

    error_code: str
    message: str
    path: Optional[str] = None

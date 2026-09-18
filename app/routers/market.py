from fastapi import APIRouter, status
from pydantic import BaseModel, Field
from typing import Optional, Dict
from app.services.advisory_service import DynamicCropAdvisor

router = APIRouter(prefix="/advisory", tags=["ML Crop & Yield Advisory Engine"])


class DynamicAdvisoryInput(BaseModel):
    farmer_id: Optional[str] = Field(
        "FARMER_RAJ_01",
        description="Farmer unique ID for tracking past rotations",
        example="FARMER_RAJ_01",
    )
    nitrogen: float = Field(..., ge=0, le=300, example=95.0)
    phosphorus: float = Field(..., ge=0, le=300, example=45.0)
    potassium: float = Field(..., ge=0, le=300, example=40.0)
    temperature: float = Field(..., ge=-10, le=60, example=24.5)
    humidity: float = Field(..., ge=0, le=100, example=78.0)
    ph: float = Field(..., ge=0, le=14, example=6.8)
    rainfall: float = Field(..., ge=0, le=3000, example=190.0)


@router.post("/recommend", status_code=status.HTTP_200_OK)
async def recommend_crop(payload: DynamicAdvisoryInput):
    data = payload.model_dump()
    farmer_id = data.pop("farmer_id", None)
    return DynamicCropAdvisor.evaluate(farmer_id=farmer_id, params=data)

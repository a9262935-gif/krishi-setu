from fastapi import APIRouter, status
from typing import List
from app.models.schemas import FarmerTransitRequest, PoolingBatchResponse

router = APIRouter(prefix="/logistics", tags=["Transit Pooling & Logistics Engine"])


@router.post(
    "/pool-batches", response_model=PoolingBatchResponse, status_code=status.HTTP_200_OK
)
async def compute_transit_pooling(requests: List[FarmerTransitRequest]):
    farmer_ids = [r.farmer_id for r in requests]
    total_vol = sum(r.produce_weight_quintals for r in requests)

    # Mathematical aggregation savings estimation
    base_individual_cost = total_vol * 120.0
    pooled_cost = base_individual_cost * 0.65
    savings_pct = round(
        ((base_individual_cost - pooled_cost) / (base_individual_cost + 1e-5)) * 100, 2
    )
    cost_per_farmer = round(pooled_cost / max(len(farmer_ids), 1), 2)

    return PoolingBatchResponse(
        batch_id="BATCH_POOL_001",
        total_volume_quintals=round(total_vol, 2),
        aggregated_farmers=farmer_ids,
        estimated_cost_per_farmer=cost_per_farmer,
        savings_percentage=savings_pct,
    )

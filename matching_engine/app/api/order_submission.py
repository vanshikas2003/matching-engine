from fastapi import APIRouter, HTTPException
from app.models.order import OrderRequest, OrderType, OrderSide
from app.core.engine_manager import engine_manager  # singleton manager for OrderBooks

router = APIRouter()

@router.post("/order")
async def submit_order(order: OrderRequest):
    try:
        trades = await engine_manager.submit_order(order)
        return {"message": "Order processed", "trades": trades}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

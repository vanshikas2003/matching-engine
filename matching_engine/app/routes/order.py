from fastapi import APIRouter
from app.models.order import Order

router = APIRouter()

@router.post("/order")
def submit_order(order: Order):
    # Handle logic here, e.g., order_book.add_order(order)
    return {"status": "ok", "received": order.dict()}


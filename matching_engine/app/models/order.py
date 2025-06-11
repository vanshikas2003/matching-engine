from pydantic import BaseModel, Field
from enum import Enum
from uuid import uuid4
from typing import Optional
from datetime import datetime


class OrderSide(str, Enum):
    buy = "buy"
    sell = "sell"


class OrderType(str, Enum):
    market = "market"
    limit = "limit"
    ioc = "ioc"
    fok = "fok"
    stop_loss = "stop_loss"
    stop_limit = "stop_limit"
    take_profit = "take_profit"


class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    symbol: str
    type: OrderType
    side: OrderSide
    quantity: float
    price: Optional[float] = None  # Not needed for market orders
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trigger_price: Optional[float] = None

class OrderSide(str, Enum):
    buy = "buy"
    sell = "sell"

class OrderType(str, Enum):
    market = "market"
    limit = "limit"
    ioc = "ioc"
    fok = "fok"

class OrderRequest(BaseModel):
    symbol: str
    order_type: OrderType
    side: OrderSide
    quantity: float
    price: float = None  # Optional for market orders

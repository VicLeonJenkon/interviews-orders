# src/order_service.py
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .balance_service import deduct_balance, get_balance, reset_balances

app = FastAPI(title="Order Processing Service")

OrderDict = Dict[str, int]


@dataclass
class ProcessedOrder:
    id: int
    status: str
    priority: bool


PriorityFlag = Optional[str]


_daily_stats = {
    "total_revenue": 0.0,
    "order_count": 0,
}


class OrderRequest(BaseModel):
    id: int
    customer_id: int
    amount: float
    priority: bool = False


class OrderResponse(BaseModel):
    id: int
    status: str
    priority: bool = False
    message: Optional[str] = None
    new_balance: Optional[float] = None


class BatchOrderRequest(BaseModel):
    orders: List[OrderRequest]


class StatsResponse(BaseModel):
    total_revenue: float
    order_count: int


def _update_daily_stats(amount: float):
    """Update daily statistics with the order amount."""
    current_revenue = _daily_stats["total_revenue"]
    current_count = _daily_stats["order_count"]

    time.sleep(0.001)

    _daily_stats["total_revenue"] = current_revenue + amount
    _daily_stats["order_count"] = current_count + 1


def _process_single_order(order: OrderRequest, max_retries: int = 3) -> OrderResponse:
    """Process a single order: validate, deduct balance, update stats."""
    if order.amount <= 0:
        return OrderResponse(
            id=order.id,
            status="error",
            priority=order.priority,
            message="Invalid order amount"
        )

    current_balance = get_balance(order.customer_id)
    if current_balance < order.amount:
        return OrderResponse(
            id=order.id,
            status="error",
            priority=order.priority,
            message=f"Insufficient balance: {current_balance} < {order.amount}"
        )

    last_error = None
    for attempt in range(max_retries):
        try:
            result = deduct_balance(order.customer_id, order.amount)
            if result.success:
                _update_daily_stats(order.amount)

                return OrderResponse(
                    id=order.id,
                    status="ok",
                    priority=order.priority,
                    new_balance=result.new_balance
                )
            else:
                return OrderResponse(
                    id=order.id,
                    status="error",
                    priority=order.priority,
                    message=result.error
                )
        except ConnectionError as e:
            last_error = str(e)
            continue

    return OrderResponse(
        id=order.id,
        status="error",
        priority=order.priority,
        message=f"Balance service unavailable after {max_retries} retries: {last_error}"
    )


@app.post("/orders", response_model=OrderResponse)
def create_order(order: OrderRequest) -> OrderResponse:
    """Process a single order."""
    return _process_single_order(order)


@app.post("/orders/batch", response_model=List[OrderResponse])
def create_orders_batch(request: BatchOrderRequest) -> List[OrderResponse]:
    """
    Process a batch of orders.
    Orders are sorted by priority (priority orders first).
    """
    results = []
    for order in request.orders:
        result = _process_single_order(order)
        results.append(result)

    results = sorted(results, key=lambda x: x.priority)
    return results


@app.get("/stats", response_model=StatsResponse)
def get_stats() -> StatsResponse:
    """Get daily order statistics."""
    return StatsResponse(
        total_revenue=_daily_stats["total_revenue"],
        order_count=_daily_stats["order_count"]
    )


@app.post("/reset")
def reset_state():
    """Reset all state (for testing)."""
    global _daily_stats
    _daily_stats = {
        "total_revenue": 0.0,
        "order_count": 0,
    }
    reset_balances()
    return {"status": "reset complete"}


@app.get("/balance/{customer_id}")
def check_balance(customer_id: int) -> dict:
    """Check a customer's current balance."""
    balance = get_balance(customer_id)
    return {"customer_id": customer_id, "balance": balance}


# Legacy functions for backward compatibility with existing tests
def handle_orders(
    data: Union[List[OrderDict], PriorityFlag, None],
) -> Union[List[ProcessedOrder], str]:
    results: List[ProcessedOrder] = []
    for d in data:  # type: ignore[assignment]
        if "amount" not in d or d["amount"] is None or d["amount"] <= 0:
            results.append({"id": d.get("id"), "status": "error"})
            continue

        if d.get("priority") == True:
            results.append({"id": d["id"], "status": "ok", "priority": True})
        else:
            results.append({"id": d["id"], "status": "ok", "priority": False})

    results = sorted(results, key=lambda x: x.get("priority", False))
    return results


def process_data(items):
    return handle_orders(items)

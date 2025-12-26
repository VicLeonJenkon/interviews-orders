# src/balance_service.py
"""
External customer balance service stub.

This simulates an external microservice that manages customer account balances.
Orders should deduct from customer balances when processed.
"""
import time
import random
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class BalanceResponse:
    success: bool
    customer_id: int
    new_balance: float
    error: Optional[str] = None


_customer_balances: Dict[int, float] = {
    1: 500.00,
    2: 1000.00,
    3: 250.00,
    4: 750.00,
    5: 100.00,
}


def get_balance(customer_id: int) -> float:
    """Get current balance for a customer."""
    return _customer_balances.get(customer_id, 0.0)


def deduct_balance(customer_id: int, amount: float) -> BalanceResponse:
    """Deduct amount from customer balance."""
    time.sleep(random.uniform(0.01, 0.05))

    if random.random() < 0.1:
        raise ConnectionError("Balance service temporarily unavailable")

    current_balance = _customer_balances.get(customer_id, 0.0)

    if current_balance < amount:
        return BalanceResponse(
            success=False,
            customer_id=customer_id,
            new_balance=current_balance,
            error="Insufficient balance"
        )

    new_balance = current_balance - amount
    _customer_balances[customer_id] = new_balance

    return BalanceResponse(
        success=True,
        customer_id=customer_id,
        new_balance=new_balance
    )


def reset_balances():
    """Reset balances to initial state (for testing)."""
    global _customer_balances
    _customer_balances = {
        1: 500.00,
        2: 1000.00,
        3: 250.00,
        4: 750.00,
        5: 100.00,
    }

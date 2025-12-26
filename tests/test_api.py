# tests/test_api.py
"""API tests for the order service."""
import concurrent.futures

import pytest
from fastapi.testclient import TestClient

from src.order_service import app
from src.balance_service import get_balance


@pytest.fixture
def client():
    """Create a test client and reset state before each test."""
    with TestClient(app) as c:
        c.post("/reset")
        yield c


class TestBasicAPI:
    """Basic API functionality tests."""

    def test_create_order_success(self, client):
        """Test creating a valid order."""
        response = client.post("/orders", json={
            "id": 1,
            "customer_id": 1,
            "amount": 50.0,
            "priority": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["id"] == 1

    def test_create_order_invalid_amount(self, client):
        """Test order with invalid amount."""
        response = client.post("/orders", json={
            "id": 1,
            "customer_id": 1,
            "amount": 0,
            "priority": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"

    def test_create_order_insufficient_balance(self, client):
        """Test order exceeding customer balance."""
        response = client.post("/orders", json={
            "id": 1,
            "customer_id": 1,
            "amount": 10000.0,
            "priority": False
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Insufficient balance" in data["message"]

    def test_check_balance(self, client):
        """Test balance check endpoint."""
        response = client.get("/balance/1")
        assert response.status_code == 200
        data = response.json()
        assert data["customer_id"] == 1
        assert data["balance"] == 500.0

    def test_get_stats(self, client):
        """Test stats endpoint."""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert "order_count" in data


class TestConcurrency:
    """Tests for concurrent order processing."""

    def test_concurrent_stats_update(self, client):
        """Test that concurrent order processing correctly updates stats."""
        num_orders = 100
        amount_per_order = 10.0

        client.post("/reset")

        def create_order(order_id):
            return client.post("/orders", json={
                "id": order_id,
                "customer_id": 2,
                "amount": amount_per_order,
                "priority": False
            })

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_order, i) for i in range(num_orders)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        stats_response = client.get("/stats")
        stats = stats_response.json()

        successful = sum(1 for r in results if r.json()["status"] == "ok")

        assert stats["order_count"] == successful, (
            f"Stats show {stats['order_count']} orders but {successful} succeeded."
        )

    def test_balance_consistency(self, client):
        """Test that balance deductions are consistent."""
        client.post("/reset")
        initial_balance = 500.0
        order_amount = 50.0

        balance_before = client.get("/balance/1").json()["balance"]
        assert balance_before == initial_balance

        response = client.post("/orders", json={
            "id": 1,
            "customer_id": 1,
            "amount": order_amount,
            "priority": False
        })

        if response.json()["status"] == "ok":
            balance_after = client.get("/balance/1").json()["balance"]
            expected_balance = initial_balance - order_amount

            assert balance_after == expected_balance, (
                f"Expected balance {expected_balance} but got {balance_after}."
            )


class TestBatchOrdering:
    """Test batch order processing and priority sorting."""

    def test_batch_priority_ordering(self, client):
        """Test that batch results are ordered by priority."""
        response = client.post("/orders/batch", json={
            "orders": [
                {"id": 1, "customer_id": 1, "amount": 10.0, "priority": False},
                {"id": 2, "customer_id": 1, "amount": 10.0, "priority": True},
                {"id": 3, "customer_id": 1, "amount": 10.0, "priority": False},
            ]
        })
        assert response.status_code == 200
        results = response.json()

        priorities = [r["priority"] for r in results]

        assert priorities == [True, False, False], (
            f"Expected priority orders first [True, False, False] but got {priorities}."
        )

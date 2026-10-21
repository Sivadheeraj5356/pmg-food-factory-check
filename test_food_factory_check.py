import unittest
from datetime import date
from decimal import Decimal

from food_factory_check import (
    IngredientLotForm,
    ProductionBatchForm,
    QualityCheckForm,
    batch_readiness,
)


def lot_data(**overrides):
    values = {
        "name": "Milk powder",
        "quantity_kg": "100.00",
        "received_on": "2026-10-01",
        "expires_on": "2026-12-01",
        "allergen": "milk",
    }
    values.update(overrides)
    return values


def batch_data(**overrides):
    values = {
        "product_name": "Protein bar",
        "planned_kg": "25.00",
        "produced_on": "2026-10-21",
        "lot_quantity_kg": "100.00",
        "lot_expires_on": "2026-12-01",
    }
    values.update(overrides)
    return values


def valid_batch():
    form = ProductionBatchForm(batch_data())
    assert form.is_valid(), form.errors
    return form.cleaned_data


class FoodFactoryCheckTests(unittest.TestCase):
    def test_batch_with_passing_quality_check_is_ready(self):
        result = batch_readiness(valid_batch(), [{"passed": True, "temperature_c": Decimal("22.50")}])
        self.assertTrue(result.ready)
        self.assertEqual(result.reasons, ())

    def test_missing_quality_check_blocks_release(self):
        result = batch_readiness(valid_batch(), [])
        self.assertFalse(result.ready)
        self.assertEqual(result.reasons, ("quality check missing",))

    def test_failed_quality_checks_block_release(self):
        result = batch_readiness(valid_batch(), [{"passed": False, "temperature_c": Decimal("24.00")}])
        self.assertEqual(result.reasons, ("no passing quality check",))

    def test_expired_lot_is_rejected(self):
        form = ProductionBatchForm(batch_data(produced_on="2026-12-02"))
        self.assertFalse(form.is_valid())
        self.assertIn("produced_on", form.errors)

    def test_oversized_batch_is_blocked(self):
        batch = valid_batch() | {"planned_kg": Decimal("125.00")}
        result = batch_readiness(batch, [{"passed": True, "temperature_c": Decimal("22.00")}])
        self.assertEqual(result.reasons, ("planned quantity exceeds ingredient lot quantity",))

    def test_lot_expiry_before_receipt_is_rejected(self):
        form = IngredientLotForm(lot_data(received_on="2026-10-10", expires_on="2026-10-01"))
        self.assertFalse(form.is_valid())
        self.assertIn("expires_on", form.errors)

    def test_unsafe_temperature_is_rejected(self):
        form = QualityCheckForm({"passed": "on", "temperature_c": "91.00"})
        self.assertFalse(form.is_valid())
        self.assertIn("temperature_c", form.errors)


if __name__ == "__main__":
    unittest.main()

"""Django validation helpers for food-factory batch release checks."""

from dataclasses import dataclass
from decimal import Decimal

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="development-only-food-factory-check",
        USE_TZ=True,
    )
    django.setup()

from django import forms
from django.core.exceptions import ValidationError

MIN_QUALITY_TEMPERATURE_C = Decimal("-30")
MAX_QUALITY_TEMPERATURE_C = Decimal("80")


class IngredientLotForm(forms.Form):
    name = forms.CharField(max_length=120)
    quantity_kg = forms.DecimalField(min_value=Decimal("0.01"), max_digits=10, decimal_places=2)
    received_on = forms.DateField()
    expires_on = forms.DateField()
    allergen = forms.CharField(max_length=80, required=False)

    def clean(self):
        cleaned = super().clean()
        received = cleaned.get("received_on")
        expires = cleaned.get("expires_on")
        if received and expires and expires < received:
            raise ValidationError({"expires_on": "Expiry cannot be before receipt."})
        return cleaned


class ProductionBatchForm(forms.Form):
    product_name = forms.CharField(max_length=120)
    planned_kg = forms.DecimalField(min_value=Decimal("0.01"), max_digits=10, decimal_places=2)
    produced_on = forms.DateField()
    lot_quantity_kg = forms.DecimalField(min_value=Decimal("0.01"), max_digits=10, decimal_places=2)
    lot_expires_on = forms.DateField()

    def clean(self):
        cleaned = super().clean()
        produced = cleaned.get("produced_on")
        expires = cleaned.get("lot_expires_on")
        if produced and expires and produced > expires:
            raise ValidationError({"produced_on": "Batch cannot be produced after the lot expires."})
        return cleaned


class QualityCheckForm(forms.Form):
    passed = forms.BooleanField(required=False)
    temperature_c = forms.DecimalField(max_digits=5, decimal_places=2)

    def clean_temperature_c(self):
        temperature = self.cleaned_data["temperature_c"]
        if temperature < MIN_QUALITY_TEMPERATURE_C or temperature > MAX_QUALITY_TEMPERATURE_C:
            raise ValidationError("Temperature is outside the supported food-production range.")
        return temperature


@dataclass(frozen=True)
class ReadinessResult:
    ready: bool
    reasons: tuple[str, ...]


def batch_readiness(batch: dict, quality_checks: list[dict]) -> ReadinessResult:
    """Return release readiness for one validated production batch."""
    reasons = []

    if batch["planned_kg"] > batch["lot_quantity_kg"]:
        reasons.append("planned quantity exceeds ingredient lot quantity")
    if batch["produced_on"] > batch["lot_expires_on"]:
        reasons.append("ingredient lot expired before production")
    if not quality_checks:
        reasons.append("quality check missing")
    elif not any(check["passed"] for check in quality_checks):
        reasons.append("no passing quality check")

    return ReadinessResult(ready=not reasons, reasons=tuple(reasons))

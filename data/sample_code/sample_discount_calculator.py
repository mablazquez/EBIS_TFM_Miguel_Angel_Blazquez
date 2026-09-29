"""
Módulo de cálculo de descuentos y validación de suscripciones comerciales.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Optional


class UserPlan(str, Enum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


@dataclass(frozen=True)
class PricingResult:
    plan: UserPlan
    base_price: Decimal
    discount_percentage: Decimal
    discount_amount: Decimal
    final_price: Decimal


class DiscountCalculator:
    """Calculadora de tarifas con deducciones por volumen y permanencia anual."""

    PRO_MONTHLY_FEE = Decimal("29.99")
    ENTERPRISE_MONTHLY_FEE = Decimal("199.99")
    ANNUAL_PROMO_DISCOUNT = Decimal("0.20")  # 20% descuento por pago anual
    COUPON_PROMO_DISCOUNT = Decimal("0.10")  # 10% adicional por cupón promocional

    def calculate_annual_subscription(
        self,
        plan: UserPlan,
        coupon_code: Optional[str] = None
    ) -> PricingResult:
        """
        Calcula el coste anualizado con descuentos aplicados.

        Args:
            plan: Tipo de suscripción contratada.
            coupon_code: Cupón de fidelización opcional (ej: 'WELCOME10').

        Returns:
            PricingResult con el desglose exacto de los importes.
        """
        if plan == UserPlan.FREE:
            return PricingResult(
                plan=plan,
                base_price=Decimal("0.00"),
                discount_percentage=Decimal("0.00"),
                discount_amount=Decimal("0.00"),
                final_price=Decimal("0.00")
            )

        monthly_fee = (
            self.PRO_MONTHLY_FEE if plan == UserPlan.PRO else self.ENTERPRISE_MONTHLY_FEE
        )
        base_annual_price = monthly_fee * Decimal("12")

        # Descuento base por modalidad anual
        total_discount_rate = self.ANNUAL_PROMO_DISCOUNT

        # Aplicación condicional de cupón válido
        if coupon_code and coupon_code.strip().upper() == "WELCOME10":
            total_discount_rate += self.COUPON_PROMO_DISCOUNT

        discount_amount = (base_annual_price * total_discount_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        final_price = (base_annual_price - discount_amount).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return PricingResult(
            plan=plan,
            base_price=base_annual_price.quantize(Decimal("0.01")),
            discount_percentage=(total_discount_rate * Decimal("100")).quantize(Decimal("0.01")),
            discount_amount=discount_amount,
            final_price=final_price
        )
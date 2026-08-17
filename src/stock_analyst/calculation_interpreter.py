"""Run every per-field interpretation function in :mod:`interpretation` over
one :class:`calculated_metrics.CalculatedMetrics` — the interpretation
counterpart to ``run_all_calculations.py``.

The master function calls each ``interpret_<field_name>`` in the model's
declaration order, under the same section banners, and collects the resulting
:class:`interpretation.CalculationInterpretation` objects into a list. Order
is meaningful for prompt construction, and the completeness test in
``tests/test_calculation_interpreter.py`` proves every field is covered.
"""

from stock_analyst import interpretation
from stock_analyst.calculated_metrics import CalculatedMetrics
from stock_analyst.interpretation import CalculationInterpretation


def interpret_all_calculations(
    calculated_metrics: CalculatedMetrics,
) -> list[CalculationInterpretation]:
    """Interpret every ``CalculatedMetrics`` field, in declaration order."""
    return [
        # ------------------------------------------------------------------
        # Building blocks shared across pillars
        # ------------------------------------------------------------------
        interpretation.interpret_gross_profit(calculated_metrics.gross_profit),
        interpretation.interpret_earnings_before_interest_taxes_depreciation_and_amortization(
            calculated_metrics.earnings_before_interest_taxes_depreciation_and_amortization
        ),
        interpretation.interpret_effective_tax_rate(calculated_metrics.effective_tax_rate),
        interpretation.interpret_net_operating_profit_after_tax(
            calculated_metrics.net_operating_profit_after_tax
        ),
        interpretation.interpret_total_debt(calculated_metrics.total_debt),
        interpretation.interpret_net_debt(calculated_metrics.net_debt),
        interpretation.interpret_working_capital(calculated_metrics.working_capital),
        interpretation.interpret_invested_capital(calculated_metrics.invested_capital),
        interpretation.interpret_earnings_per_share(calculated_metrics.earnings_per_share),
        interpretation.interpret_enterprise_value(calculated_metrics.enterprise_value),
        interpretation.interpret_free_cash_flow(calculated_metrics.free_cash_flow),
        # ------------------------------------------------------------------
        # Profitability
        # ------------------------------------------------------------------
        interpretation.interpret_gross_profit_margin(calculated_metrics.gross_profit_margin),
        interpretation.interpret_operating_margin(calculated_metrics.operating_margin),
        interpretation.interpret_net_profit_margin(calculated_metrics.net_profit_margin),
        interpretation.interpret_earnings_before_interest_taxes_depreciation_and_amortization_margin(
            calculated_metrics.earnings_before_interest_taxes_depreciation_and_amortization_margin
        ),
        # ------------------------------------------------------------------
        # Liquidity
        # ------------------------------------------------------------------
        interpretation.interpret_current_ratio(calculated_metrics.current_ratio),
        interpretation.interpret_quick_ratio(calculated_metrics.quick_ratio),
        interpretation.interpret_cash_ratio(calculated_metrics.cash_ratio),
        interpretation.interpret_operating_cash_flow_ratio(
            calculated_metrics.operating_cash_flow_ratio
        ),
        interpretation.interpret_defensive_interval_ratio(
            calculated_metrics.defensive_interval_ratio
        ),
        # ------------------------------------------------------------------
        # Solvency & leverage
        # ------------------------------------------------------------------
        interpretation.interpret_debt_to_equity(calculated_metrics.debt_to_equity),
        interpretation.interpret_debt_to_assets(calculated_metrics.debt_to_assets),
        interpretation.interpret_debt_to_capital(calculated_metrics.debt_to_capital),
        interpretation.interpret_net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization(
            calculated_metrics.net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization
        ),
        interpretation.interpret_interest_coverage(calculated_metrics.interest_coverage),
        interpretation.interpret_earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage(
            calculated_metrics.earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage
        ),
        interpretation.interpret_operating_cash_flow_to_debt(
            calculated_metrics.operating_cash_flow_to_debt
        ),
        # ------------------------------------------------------------------
        # Cash flow - generation & quality
        # ------------------------------------------------------------------
        interpretation.interpret_free_cash_flow_margin(calculated_metrics.free_cash_flow_margin),
        interpretation.interpret_operating_cash_flow_to_net_income(
            calculated_metrics.operating_cash_flow_to_net_income
        ),
        interpretation.interpret_sloan_accruals_ratio(calculated_metrics.sloan_accruals_ratio),
        interpretation.interpret_free_cash_flow_conversion(
            calculated_metrics.free_cash_flow_conversion
        ),
        interpretation.interpret_capital_expenditure_intensity(
            calculated_metrics.capital_expenditure_intensity
        ),
        interpretation.interpret_capital_expenditures_to_depreciation(
            calculated_metrics.capital_expenditures_to_depreciation
        ),
        # ------------------------------------------------------------------
        # Growth
        # ------------------------------------------------------------------
        interpretation.interpret_retention_rate(calculated_metrics.retention_rate),
        # ------------------------------------------------------------------
        # Valuation
        # ------------------------------------------------------------------
        interpretation.interpret_price_to_earnings(calculated_metrics.price_to_earnings),
        interpretation.interpret_earnings_yield(calculated_metrics.earnings_yield),
        interpretation.interpret_earnings_before_interest_and_taxes_to_enterprise_value(
            calculated_metrics.earnings_before_interest_and_taxes_to_enterprise_value
        ),
        interpretation.interpret_price_to_book(calculated_metrics.price_to_book),
        interpretation.interpret_price_to_sales(calculated_metrics.price_to_sales),
        interpretation.interpret_enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization(
            calculated_metrics.enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization
        ),
        interpretation.interpret_enterprise_value_to_earnings_before_interest_and_taxes(
            calculated_metrics.enterprise_value_to_earnings_before_interest_and_taxes
        ),
        interpretation.interpret_enterprise_value_to_sales(
            calculated_metrics.enterprise_value_to_sales
        ),
        interpretation.interpret_free_cash_flow_yield(calculated_metrics.free_cash_flow_yield),
        interpretation.interpret_dividend_yield(calculated_metrics.dividend_yield),
        interpretation.interpret_payout_ratio(calculated_metrics.payout_ratio),
        interpretation.interpret_shareholder_yield(calculated_metrics.shareholder_yield),
        # ------------------------------------------------------------------
        # Composite scores
        # ------------------------------------------------------------------
        interpretation.interpret_altman_z_score(calculated_metrics.altman_z_score),
        interpretation.interpret_altman_z_zone(calculated_metrics.altman_z_zone),
        interpretation.interpret_altman_z_double_prime(calculated_metrics.altman_z_double_prime),
        interpretation.interpret_altman_z_double_prime_zone(
            calculated_metrics.altman_z_double_prime_zone
        ),
    ]

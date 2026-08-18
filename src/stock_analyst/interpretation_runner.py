"""Run every per-field interpretation function in :mod:`interpretation` over
one :class:`calculated_metrics.CalculatedMetrics` — the interpretation
counterpart to ``run_all_calculations.py``.

The master function calls each ``interpret_<field_name>`` in the model's
declaration order, under the same section banners, and collects the resulting
:class:`interpretation.CalculationInterpretation` objects into a list. Order
is meaningful for prompt construction, and the completeness test in
``tests/test_calculation_interpreter.py`` proves every field is covered.
"""

from stock_analyst import interpretations as interpretations
from stock_analyst.calculated_values import CalculatedValues
from stock_analyst.interpretations import CalculationInterpretation


def interpret_calculated_values(
    calculated_values: CalculatedValues,
) -> list[CalculationInterpretation]:
    """Interpret every ``CalculatedMetrics`` field, in declaration order."""
    return [
        # ------------------------------------------------------------------
        # Building blocks shared across pillars
        # ------------------------------------------------------------------
        interpretations.interpret_gross_profit(calculated_values.gross_profit),
        interpretations.interpret_earnings_before_interest_taxes_depreciation_and_amortization(
            calculated_values.earnings_before_interest_taxes_depreciation_and_amortization
        ),
        interpretations.interpret_effective_tax_rate(calculated_values.effective_tax_rate),
        interpretations.interpret_net_operating_profit_after_tax(
            calculated_values.net_operating_profit_after_tax
        ),
        interpretations.interpret_total_debt(calculated_values.total_debt),
        interpretations.interpret_net_debt(calculated_values.net_debt),
        interpretations.interpret_working_capital(calculated_values.working_capital),
        interpretations.interpret_invested_capital(calculated_values.invested_capital),
        interpretations.interpret_earnings_per_share(calculated_values.earnings_per_share),
        interpretations.interpret_enterprise_value(calculated_values.enterprise_value),
        interpretations.interpret_free_cash_flow(calculated_values.free_cash_flow),
        # ------------------------------------------------------------------
        # Profitability
        # ------------------------------------------------------------------
        interpretations.interpret_gross_profit_margin(calculated_values.gross_profit_margin),
        interpretations.interpret_operating_margin(calculated_values.operating_margin),
        interpretations.interpret_net_profit_margin(calculated_values.net_profit_margin),
        interpretations.interpret_earnings_before_interest_taxes_depreciation_and_amortization_margin(
            calculated_values.earnings_before_interest_taxes_depreciation_and_amortization_margin
        ),
        # ------------------------------------------------------------------
        # Liquidity
        # ------------------------------------------------------------------
        interpretations.interpret_current_ratio(calculated_values.current_ratio),
        interpretations.interpret_quick_ratio(calculated_values.quick_ratio),
        interpretations.interpret_cash_ratio(calculated_values.cash_ratio),
        interpretations.interpret_operating_cash_flow_ratio(
            calculated_values.operating_cash_flow_ratio
        ),
        interpretations.interpret_defensive_interval_ratio(
            calculated_values.defensive_interval_ratio
        ),
        # ------------------------------------------------------------------
        # Solvency & leverage
        # ------------------------------------------------------------------
        interpretations.interpret_debt_to_equity(calculated_values.debt_to_equity),
        interpretations.interpret_debt_to_assets(calculated_values.debt_to_assets),
        interpretations.interpret_debt_to_capital(calculated_values.debt_to_capital),
        interpretations.interpret_net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization(
            calculated_values.net_debt_to_earnings_before_interest_taxes_depreciation_and_amortization
        ),
        interpretations.interpret_interest_coverage(calculated_values.interest_coverage),
        interpretations.interpret_earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage(
            calculated_values.earnings_before_interest_taxes_depreciation_and_amortization_interest_coverage
        ),
        interpretations.interpret_operating_cash_flow_to_debt(
            calculated_values.operating_cash_flow_to_debt
        ),
        # ------------------------------------------------------------------
        # Cash flow - generation & quality
        # ------------------------------------------------------------------
        interpretations.interpret_free_cash_flow_margin(calculated_values.free_cash_flow_margin),
        interpretations.interpret_operating_cash_flow_to_net_income(
            calculated_values.operating_cash_flow_to_net_income
        ),
        interpretations.interpret_sloan_accruals_ratio(calculated_values.sloan_accruals_ratio),
        interpretations.interpret_free_cash_flow_conversion(
            calculated_values.free_cash_flow_conversion
        ),
        interpretations.interpret_capital_expenditure_intensity(
            calculated_values.capital_expenditure_intensity
        ),
        interpretations.interpret_capital_expenditures_to_depreciation(
            calculated_values.capital_expenditures_to_depreciation
        ),
        # ------------------------------------------------------------------
        # Growth
        # ------------------------------------------------------------------
        interpretations.interpret_retention_rate(calculated_values.retention_rate),
        # ------------------------------------------------------------------
        # Valuation
        # ------------------------------------------------------------------
        interpretations.interpret_price_to_earnings(calculated_values.price_to_earnings),
        interpretations.interpret_earnings_yield(calculated_values.earnings_yield),
        interpretations.interpret_earnings_before_interest_and_taxes_to_enterprise_value(
            calculated_values.earnings_before_interest_and_taxes_to_enterprise_value
        ),
        interpretations.interpret_price_to_book(calculated_values.price_to_book),
        interpretations.interpret_price_to_sales(calculated_values.price_to_sales),
        interpretations.interpret_enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization(
            calculated_values.enterprise_value_to_earnings_before_interest_taxes_depreciation_and_amortization
        ),
        interpretations.interpret_enterprise_value_to_earnings_before_interest_and_taxes(
            calculated_values.enterprise_value_to_earnings_before_interest_and_taxes
        ),
        interpretations.interpret_enterprise_value_to_sales(
            calculated_values.enterprise_value_to_sales
        ),
        interpretations.interpret_free_cash_flow_yield(calculated_values.free_cash_flow_yield),
        interpretations.interpret_dividend_yield(calculated_values.dividend_yield),
        interpretations.interpret_payout_ratio(calculated_values.payout_ratio),
        interpretations.interpret_shareholder_yield(calculated_values.shareholder_yield),
        # ------------------------------------------------------------------
        # Composite scores
        # ------------------------------------------------------------------
        interpretations.interpret_altman_z_score(calculated_values.altman_z_score),
        interpretations.interpret_altman_z_zone(calculated_values.altman_z_zone),
        interpretations.interpret_altman_z_double_prime(calculated_values.altman_z_double_prime),
        interpretations.interpret_altman_z_double_prime_zone(
            calculated_values.altman_z_double_prime_zone
        ),
    ]

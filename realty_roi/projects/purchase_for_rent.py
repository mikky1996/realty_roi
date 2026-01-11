import pandas as pd
import typing as tp

from dataclasses import dataclass
from functools import lru_cache

from .base import Project


# Constants for default calculations
DEFAULT_REPAIR_EXPENSE_RATE = 0.01  # 1% of purchase price
DEFAULT_INSURANCE_RATE = 0.005  # 0.5% of purchase price


@dataclass
class PropertyDetails:
    """Core property information"""
    purchase_price: float
    monthly_rent: float
    monthly_hoa_expenses: float
    annual_repair_expenses: tp.Optional[float] = None
    annual_insurance: tp.Optional[float] = None

    def __post_init__(self):
        """Set default values for optional expenses if not provided."""
        if self.annual_repair_expenses is None:
            self.annual_repair_expenses = DEFAULT_REPAIR_EXPENSE_RATE * self.purchase_price
        if self.annual_insurance is None:
            self.annual_insurance = DEFAULT_INSURANCE_RATE * self.purchase_price


@dataclass
class LoanTerms:
    """Loan and financing details"""
    downpayment_percent: float = 20.0  # As percentage (e.g., 20 for 20%)
    interest_rate: float = 6.9  # As percentage (e.g., 6.9 for 6.9%)
    loan_term_years: float = 30.0


@dataclass
class RateAssumptions:
    """Economic and tax rate assumptions"""
    vacancy_rate: float = 1.0 / 12  # 1 month per year
    property_tax_rate: float = 2.2  # As percentage
    appreciation_rate: float = 1.0  # As percentage
    tax_rate: float = 25.0  # As percentage (e.g., 25 for 25%)
    depreciation_period: float = 27.5  # Years (27.5 for residential rental)
    inflation_rate: float = 2.0  # As percentage


class PurchaseForRent(Project):
    """
    Analyzes the financial viability of purchasing a property for rental income.

    Calculates various metrics including cash flow, ROI, cap rate, and break-even
    occupancy over time, accounting for inflation, appreciation, taxes, and debt service.

    Year Convention:
        - Year 0: Initial state (before any payments or operations)
        - Year 1: End of first year (after 12 months of operations/payments)
        - Year N: End of Nth year
        
        All methods default to year=1 (first year) for consistency.
    """

    def __init__(
        self,
        property_details: PropertyDetails,
        loan_terms: tp.Optional[LoanTerms] = None,
        rate_assumptions: tp.Optional[RateAssumptions] = None,
    ):
        """
        Initialize the PurchaseForRent project.
        
        :param PropertyDetails property_details: PropertyDetails dataclass with property information
        :param tp.Optional[LoanTerms] loan_terms: LoanTerms dataclass with financing details (optional, uses defaults)
        :param tp.Optional[RateAssumptions] rate_assumptions: RateAssumptions dataclass with economic assumptions (optional, uses defaults)
        
        Example:
            >>> property = PropertyDetails(
            ...     purchase_price=500_000,
            ...     monthly_rent=3_000,
            ...     monthly_hoa_expenses=200
            ... )
            >>> loan = LoanTerms(downpayment_percent=20, interest_rate=6.9)
            >>> rates = RateAssumptions(appreciation_rate=3.0, inflation_rate=2.5)
            >>> project = PurchaseForRent(property, loan, rates)
        """
        # Use default dataclasses if not provided
        loan_terms = loan_terms or LoanTerms()
        rate_assumptions = rate_assumptions or RateAssumptions()

        # Store property details
        self.purchase_price = property_details.purchase_price
        self.monthly_rent = property_details.monthly_rent
        self.monthly_hoa_expenses = property_details.monthly_hoa_expenses
        self.annual_repair_expenses = property_details.annual_repair_expenses
        self.annual_insurance = property_details.annual_insurance

        # Store and convert loan terms (from percentage to decimal)
        self.downpayment_percent = loan_terms.downpayment_percent / 100
        self.interest_rate = loan_terms.interest_rate / 100
        self.loan_term = loan_terms.loan_term_years

        # Calculate loan amount
        self.loan_amount = self.purchase_price * (1 - self.downpayment_percent)

        # Store and convert rate assumptions (from percentage to decimal where needed)
        self.vacancy_rate = rate_assumptions.vacancy_rate
        self.property_tax_rate = rate_assumptions.property_tax_rate / 100
        self.appreciation_rate = rate_assumptions.appreciation_rate / 100
        self.tax_rate = rate_assumptions.tax_rate / 100
        self.depreciation_period = rate_assumptions.depreciation_period
        self.inflation_rate = rate_assumptions.inflation_rate / 100

        # Calculate fixed annual costs
        self.property_taxes = self.purchase_price * self.property_tax_rate

    def __setattr__(self, name: str, value: tp.Any) -> None:
        """Clear all method caches when any attribute is modified."""
        # Set the attribute
        object.__setattr__(self, name, value)

        # Clear all cached methods
        for attr_name in dir(self):
            if not attr_name.startswith('_'):  # Skip private/magic methods
                try:
                    attr = getattr(self, attr_name)
                    if hasattr(attr, 'cache_clear'):
                        attr.cache_clear()
                except AttributeError:
                    # Some attributes may not be accessible yet during initialization
                    pass

    def __repr__(self) -> str:
        """Return a detailed string representation of the PurchaseForRent project."""
        return (
            f"Property Details:\n"
            f"  Purchase Price: ${self.purchase_price:,.0f}\n"
            f"  Monthly Rent: ${self.monthly_rent:,.0f}\n"
            f"  Monthly HOA: ${self.monthly_hoa_expenses:,.0f}\n"
            f"  Annual Repairs: ${self.annual_repair_expenses:,.0f}\n"
            f"  Annual Insurance: ${self.annual_insurance:,.0f}\n"
            f"Loan Terms:\n"
            f"  Down Payment: {self.downpayment_percent * 100:.1f}%\n"
            f"  Loan Amount: ${self.loan_amount:,.0f}\n"
            f"  Interest Rate: {self.interest_rate * 100:.2f}%\n"
            f"  Loan Term: {self.loan_term:.0f} years\n"
            f"Rate Assumptions:\n"
            f"  Vacancy Rate: {self.vacancy_rate * 100:.1f}%\n"
            f"  Property Tax Rate: {self.property_tax_rate * 100:.2f}%\n"
            f"  Appreciation Rate: {self.appreciation_rate * 100:.2f}%\n"
            f"  Inflation Rate: {self.inflation_rate * 100:.2f}%\n"
            f"  Income Tax Rate: {self.tax_rate * 100:.1f}%\n"
            f"  Depreciation Period: {self.depreciation_period:.1f} years"
        )

    # ============================================================================
    # INCOME CALCULATIONS
    # ============================================================================

    @lru_cache(maxsize=None)
    def gross_income(self, year: int = 1) -> float:
        """
        Calculate gross rental income for a given year, adjusted for inflation.
        
        Year 0 returns 0 (no operations before purchase).
        Year 1 represents the first year of operation.
        """
        if year == 0:
            return 0.0
        return self.monthly_rent * 12 * self.inflation_multiplier(year)

    @lru_cache(maxsize=None)
    def effective_gross_income(self, year: int = 1) -> float:
        """
        Calculate gross income after accounting for vacancy.
        
        Year 0 returns 0 (no operations before purchase).
        """
        if year == 0:
            return 0.0
        return self.gross_income(year) * (1 - self.vacancy_rate)

    @lru_cache(maxsize=None)
    def net_operating_income(self, year: int = 1) -> float:
        """
        Calculate Net Operating Income (NOI).
        NOI = Effective Gross Income - Operating Expenses
        
        Year 0 returns 0 (no operations before purchase).
        """
        if year == 0:
            return 0.0
        return self.effective_gross_income(year) - self.operating_expenses(year)

    # ============================================================================
    # EXPENSE CALCULATIONS
    # ============================================================================

    @lru_cache(maxsize=None)
    def operating_expenses(self, year: int = 1) -> float:
        """
        Calculate total operating expenses for a given year.

        Includes property taxes (adjusted for appreciation), HOA fees, repairs,
        and insurance (all adjusted for inflation).
        
        Year 0 returns 0 (no expenses incurred before operations begin).
        """
        if year == 0:
            return 0.0

        property_taxes = self.property_taxes * self.appreciation_multiplier(year)
        hoa_expenses = (self.monthly_hoa_expenses * 12) * self.inflation_multiplier(year)
        repairs = self.annual_repair_expenses * self.inflation_multiplier(year)
        insurance = self.annual_insurance * self.inflation_multiplier(year)

        return property_taxes + hoa_expenses + repairs + insurance

    @lru_cache(maxsize=None)
    def monthly_total_expenses(self, year: int = 1) -> float:
        """
        Calculate total monthly expenses including debt service and operating costs.
        
        Year 0 returns 0 (no expenses incurred before operations begin).
        """
        if year == 0:
            return 0.0
        return self.monthly_debt_service() + self.operating_expenses(year) / 12

    # ============================================================================
    # LOAN/DEBT CALCULATIONS
    # ============================================================================

    def monthly_debt_service(self) -> float:
        """
        Calculate monthly mortgage payment using standard amortization formula.
        
        Formula: M = P * [r(1+r)^n] / [(1+r)^n - 1]
        where M = monthly payment, P = principal, r = monthly rate, n = number of payments
        """
        rate_per_month = self.interest_rate / 12
        num_payments = self.loan_term * 12

        if rate_per_month == 0:
            return self.loan_amount / num_payments

        return (self.loan_amount * rate_per_month * (1 + rate_per_month) ** num_payments) / \
               ((1 + rate_per_month) ** num_payments - 1)

    @lru_cache(maxsize=None)
    def annual_debt_service(self, year: int = 1) -> float:
        """
        Calculate annual debt service for a given year (zero if loan is paid off).

        Year 0 returns 0 (no payments made before operations begin).
        Year 1 represents payments made during the first year of operation.
        Checks the loan balance at the beginning of the year (end of year-1).
        """
        if year == 0:
            return 0.0

        # Check if there's any loan at the beginning of the year
        if self.remaining_loan(year - 1) <= 0:
            return 0
        return self.monthly_debt_service() * 12

    @lru_cache(maxsize=None)
    def remaining_loan(self, year: int = 1) -> float:
        """
        Calculate remaining loan balance at the end of a specified year.

        Year 0 returns the initial loan amount (before any payments).
        Year 1 returns the balance after 12 months of payments (end of first year).
        Year N returns the balance after N years of payments.

        Iterates through monthly payments, calculating principal reduction each month.
        """
        if year == 0:
            return self.loan_amount

        rate_per_month = self.interest_rate / 12
        monthly_payment = self.monthly_debt_service()
        remaining_loan = self.loan_amount
        months_elapsed = year * 12

        for _ in range(months_elapsed):
            if remaining_loan <= 0:
                break

            interest_payment = remaining_loan * rate_per_month
            principal_payment = monthly_payment - interest_payment
            remaining_loan -= principal_payment

        return max(remaining_loan, 0)

    @lru_cache(maxsize=None)
    def interest_paid(self, year: int = 1) -> float:
        """
        Calculate total interest paid during a specific year.
        
        Year 0 returns 0 (no payments made before operations begin).
        Year 1 represents interest paid during the first year of operation.
        This is important for tax deductions as mortgage interest is tax-deductible.
        """
        if year == 0:
            return 0.0
        
        rate_per_month = self.interest_rate / 12
        monthly_payment = self.monthly_debt_service()

        # Start with the loan balance at the beginning of the target year
        remaining_loan = self.remaining_loan(year - 1)
        total_interest = 0

        # Calculate interest for each month of the target year
        for _ in range(12):
            if remaining_loan <= 0:
                break

            interest_payment = remaining_loan * rate_per_month
            total_interest += interest_payment

            principal_payment = monthly_payment - interest_payment
            remaining_loan -= principal_payment

        return total_interest

    # ============================================================================
    # TAX CALCULATIONS
    # ============================================================================

    def depreciation(self) -> float:
        """Calculate annual depreciation expense for tax purposes."""
        return self.purchase_price / self.depreciation_period

    @lru_cache(maxsize=None)
    def pre_tax_revenue(self, year: int = 1) -> float:
        """
        Calculate pre-tax cash flow (NOI minus debt service).
        
        Year 0 returns 0 (no operations before purchase).
        """
        if year == 0:
            return 0.0
        return self.net_operating_income(year) - self.annual_debt_service(year)

    @lru_cache(maxsize=None)
    def post_tax_revenue(self, year: int = 1) -> float:
        """
        Calculate after-tax cash flow.
        
        Year 0 returns 0 (no operations before purchase).
        Taxable income = Pre-tax revenue - Interest paid - Depreciation
        After-tax revenue = Pre-tax revenue - Tax liability
        """
        if year == 0:
            return 0.0

        pre_tax = self.pre_tax_revenue(year)
        deductible_interest = self.interest_paid(year)
        depreciation_expense = self.depreciation()

        taxable_income = pre_tax - deductible_interest - depreciation_expense
        tax_liability = max(taxable_income * self.tax_rate, 0)

        return pre_tax - tax_liability

    # ============================================================================
    # PERFORMANCE METRICS
    # ============================================================================

    @lru_cache(maxsize=None)
    def cash_flow(self, year: int = 1) -> float:
        """
        Calculate annual cash flow.
        Cash Flow = Net Operating Income - Annual Debt Service
        
        Year 0 returns 0 (no operations before purchase).
        """
        if year == 0:
            return 0.0
        return self.net_operating_income(year) - self.annual_debt_service(year)

    @lru_cache(maxsize=None)
    def cap_rate(self, year: int = 1) -> float:
        """
        Calculate Capitalization Rate (Cap Rate).
        Cap Rate = (Net Operating Income / Purchase Price) * 100
        
        Year 0 returns 0 (no operations before purchase).
        """
        if year == 0:
            return 0.0
        return (self.net_operating_income(year) / self.purchase_price) * 100

    @lru_cache(maxsize=None)
    def roi(self, year: int = 1) -> float:
        """
        Calculate Cash-on-Cash Return on Investment.
        ROI = (Annual Cash Flow / Initial Cash Investment) * 100
        
        Year 0 returns 0 (no operations before purchase).
        """
        if year == 0:
            return 0.0
        initial_investment = self.purchase_price - self.loan_amount
        return (self.cash_flow(year) / initial_investment) * 100

    @lru_cache(maxsize=None)
    def break_even_occupancy_rate(self, year: int = 1) -> float:
        """
        Calculate the occupancy rate needed to break even.
        Break-Even Rate = (Total Expenses / Gross Income) * 100
        
        Year 0 returns 0 (no operations before purchase).
        """
        if year == 0:
            return 0.0
        return ((12 * self.monthly_total_expenses(year)) / self.gross_income(year)) * 100

    @lru_cache(maxsize=None)
    def property_value(self, year: int = 1) -> float:
        """
        Calculate expected property value after appreciation.
        
        Year 0 returns the purchase price (no appreciation yet).
        Year 1 returns value at end of first year, etc.
        """
        # Use year as-is so that year 1 reflects the value at end of year 1
        return self.purchase_price * self.appreciation_multiplier(year + 1)

    @lru_cache(maxsize=None)
    def net_gain(self, year: int = 1) -> float:
        """
        Calculate net gain over multiple years.

        Year 0 returns 0 (no gains yet at time of purchase).
        Net gain considers both:
        1. Current equity (property value minus remaining loan)
        2. Cumulative cash flow over all years
        3. Minus initial investment

        :param int year: Year to calculate net gain for
        :return: Net gain in dollars
        :rtype: float
        """
        if year == 0:
            return 0.0

        property_value = self.property_value(year)
        remaining_loan_at_year = self.remaining_loan(year)
        current_equity = property_value - remaining_loan_at_year

        total_cash_flow = sum(self.cash_flow(y) for y in range(1, year + 1))
        initial_investment = self.purchase_price * self.downpayment_percent

        # Total value is current equity plus accumulated cash flows
        total_value = current_equity + total_cash_flow
        net_gain = total_value - initial_investment

        return net_gain

    @lru_cache(maxsize=None)
    def total_roi(self, year: int = 1) -> float:
        """
        Calculate total return on investment over multiple years.

        Year 0 returns 0 (no gains yet at time of purchase).
        Total ROI considers both:
        1. Current equity (property value minus remaining loan)
        2. Cumulative cash flow over all years

        :param int year: Year to calculate total ROI for
        :return: Total ROI as a percentage
        :rtype: float
        """
        if year == 0:
            return 0.0

        net_gain = self.net_gain(year)
        initial_investment = self.purchase_price * self.downpayment_percent

        return (net_gain / initial_investment) * 100

    @lru_cache(maxsize=None)
    def constant_rate_of_return(self, year: int = 1) -> float:
        """
        Calculate annualized return (CAGR).

        Year 0 returns 0 (no time has passed for annualized calculations).
        Converts total ROI into an equivalent annual compound growth rate.

        :param int year: Year to calculate CAGR for
        :return: Annualized return as a percentage
        :rtype: float
        """
        if year == 0:
            return 0.0
        roi = self.total_roi(year)
        return ((1 + roi / 100) ** (1 / year) - 1) * 100

    @lru_cache(maxsize=None)
    def constant_rate_of_real_return(self, year: int = 1) -> float:
        """
        Calculate annualized real return (CAGR adjusted for inflation).

        Year 0 returns 0 (no time has passed for annualized calculations).
        Converts total ROI into an equivalent annual compound growth rate,
        adjusted for inflation using the Fisher equation.

        :param int year: Year to calculate real CAGR for
        :return: Inflation-adjusted annualized return as a percentage
        :rtype: float
        """
        if year == 0:
            return 0.0
        nominal_return = self.constant_rate_of_return(year) / 100
        # Fisher equation: (1 + real) = (1 + nominal) / (1 + inflation)
        real_return = ((1 + nominal_return) / (1 + self.inflation_rate)) - 1
        return real_return * 100

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    @lru_cache(maxsize=None)
    def inflation_multiplier(self, year: int) -> float:
        """
        Calculate inflation adjustment multiplier for a given year.
        
        Year 0 returns 1.0 (no inflation at purchase time).
        """
        if year == 0:
            return 1.0
        return (1 + self.inflation_rate) ** (year - 1)

    @lru_cache(maxsize=None)
    def appreciation_multiplier(self, year: int) -> float:
        """
        Calculate appreciation adjustment multiplier for a given year.
        
        Year 0 returns 1.0 (no appreciation at purchase time).
        """
        if year == 0:
            return 1.0
        return (1 + self.appreciation_rate) ** (year - 1)

    # ============================================================================
    # REPORTING METHODS
    # ============================================================================

    def input_summary(self) -> str:
        """Generate a formatted summary of input parameters."""
        return f"""
        Purchase Price: ${self.purchase_price:,.0f}
        Monthly Rent: ${self.monthly_rent:,.0f}
        Downpayment: {self.downpayment_percent * 100:.2f}%
        Loan Amount: ${self.loan_amount:,.0f}
        Interest Rate: {self.interest_rate * 100:.2f}%
        Loan Term: {self.loan_term} years
        Appreciation Rate: {self.appreciation_rate * 100:.2f}%
        Inflation Rate: {self.inflation_rate * 100:.2f}%
        Tax Rate: {self.tax_rate * 100:.2f}%
        """

    def evaluate(self, years: int = 30, from_year: int = 1) -> pd.DataFrame:
        """
        Generate a comprehensive financial projection over time.

        Returns a DataFrame with key metrics calculated for each year,
        including income, expenses, cash flow, and various profitability metrics.

        :param int years: Number of years to project
        :return: DataFrame with yearly projections of all key metrics
        :rtype: pd.DataFrame
        """
        stats = []
        for year in range(from_year, years + 1):
            stats.append({
                "Year": year,
                "CAGR": self.constant_rate_of_return(year),
                "Real CAGR": self.constant_rate_of_real_return(year),
                "Remaining Loan": self.remaining_loan(year),
                "Gross Income": self.gross_income(year),
                "Operating Expenses": self.operating_expenses(year),
                "Net Operating Income": self.net_operating_income(year),
                "Annual Debt Service": self.annual_debt_service(year),
                "Cash Flow": self.cash_flow(year),
                "Cap Rate": self.cap_rate(year),
                "Break-Even Occupancy Rate": self.break_even_occupancy_rate(year),
                "Property Value": self.property_value(year),
                "Net Gain": self.net_gain(year),
                "Total ROI": self.total_roi(year),
            })

        return pd.DataFrame(stats)

import pandas as pd
from .abs import Project


class PurchaseForRent(Project):

    def __init__(
        self,
        purchase_price: float = 575e3,
        monthly_rent: float = 4300,
        vacancy_rate: float = 1./12,
        monthly_hoa_expenses: float = 200,
        property_tax_rate: float = 2.2,
        annual_repair_expenses: float = 5e3,
        loan_amount: float = 500e3,
        interest_rate: float = 2,
        loan_term: float = 30,
        appreciation_rate: float = 1,
        annual_insurance: float = 1200,
        tax_rate: float = 0.25,
        depreciation_period: float = 27.5,
        inflation_rate: float = 0.02,
    ):
        self.purchase_price = purchase_price
        self.monthly_rent = monthly_rent
        self.vacancy_rate = vacancy_rate
        self.monthly_hoa_expenses = monthly_hoa_expenses
        self.annual_repair_expenses = annual_repair_expenses
        self.annual_insurance = annual_insurance
        self.depreciation_period = depreciation_period
        self.property_tax_rate = property_tax_rate / 100
        self.property_taxes = self.purchase_price * self.property_tax_rate
        self.operating_expenses = (self.monthly_hoa_expenses * 12) + self.property_taxes + self.annual_repair_expenses + self.annual_insurance
        self.loan_amount = loan_amount
        self.loan_term = loan_term
        self.tax_rate = tax_rate / 100
        self.interest_rate = interest_rate / 100
        self.appreciation_rate = appreciation_rate / 100
        self.inflation_rate = inflation_rate / 100

    def gross_income(self, year: int = 1) -> float:
        return self.monthly_rent * 12 * ((1 + self.inflation_rate) ** (year - 1))

    def effective_gross_income(self, year: int = 1) -> float:
        return self.gross_income(year) * (1 - self.vacancy_rate)

    def operating_expenses_adjusted(self, year: int = 1) -> float:
        """
        Calculates the total operating expenses for a given year, taking into
        account the inflation rate and appreciation rate.

        :param year: The year for which to calculate the operating expenses
        :return: The total operating expenses for the given year
        """
        property_taxes_adjusted = self.property_taxes * ((1 + self.appreciation_rate) ** (year - 1))
        hoa_expenses_adjusted = (self.monthly_hoa_expenses * 12) * ((1 + self.inflation_rate) ** (year - 1))
        annual_repair_expenses_adjusted = self.annual_repair_expenses * ((1 + self.inflation_rate) ** (year - 1))
        annual_insurance_adjusted = self.annual_insurance * ((1 + self.inflation_rate) ** (year - 1))
        return hoa_expenses_adjusted + property_taxes_adjusted + annual_repair_expenses_adjusted + annual_insurance_adjusted

    def net_operating_income(self, year: int = 1) -> float:
        return self.effective_gross_income(year) - self.operating_expenses_adjusted(year)

    def monthly_debt_service(self) -> float:
        rate_per_month = self.interest_rate / 12
        num_payments = self.loan_term * 12
        return (self.loan_amount * rate_per_month * (1 + rate_per_month) ** num_payments) / \
               ((1 + rate_per_month) ** num_payments - 1)

    def annual_debt_service(self) -> float:
        return self.monthly_debt_service() * 12

    def monthly_total_expenses(self, year: int = 1) -> float:
        return self.monthly_debt_service() + self.operating_expenses_adjusted(year) / 12

    def remaining_loan(self, year: int = 1) -> float:
        rate_per_month = self.interest_rate / 12
        monthly_payment = self.monthly_debt_service()
        remaining_loan = self.loan_amount
        months_elapsed = year * 12

        for _ in range(months_elapsed):
            interest_payment = remaining_loan * rate_per_month
            principal_payment = monthly_payment - interest_payment
            remaining_loan -= principal_payment
            if remaining_loan <= 0:
                remaining_loan = 0
                break

        return remaining_loan

    def interest_paid(self, year: int = 1) -> float:
        rate_per_month = self.interest_rate / 12
        remaining_loan = self.loan_amount
        total_interest = 0

        start_month = (year - 1) * 12 + 1
        end_month = year * 12

        for month in range(1, end_month + 1):
            interest_payment = remaining_loan * rate_per_month
            if start_month <= month <= end_month:
                total_interest += interest_payment
            principal_payment = self.monthly_debt_service() - interest_payment
            remaining_loan -= principal_payment
            if remaining_loan <= 0:
                break

        return total_interest

    def depreciation(self) -> float:
        return self.purchase_price / self.depreciation_period

    def pre_tax_revenue(self, year: int = 1) -> float:
        return self.net_operating_income(year) - self.annual_debt_service()

    def post_tax_revenue(self, year: int = 1) -> float:
        pre_tax = self.pre_tax_revenue(year)
        deductible_interest = self.interest_paid(year)
        depreciation_expense = self.depreciation()
        taxable_income = pre_tax - deductible_interest - depreciation_expense
        tax_liability = max(taxable_income * self.tax_rate, 0)
        return pre_tax - tax_liability

    def cash_flow(self, year: int = 1) -> float:
        return self.net_operating_income(year) - self.annual_debt_service()

    def cap_rate(self, year: int = 1) -> float:
        return (self.net_operating_income(year) / self.purchase_price) * 100

    def roi(self, year: int = 1) -> float:
        initial_investment = self.purchase_price - self.loan_amount
        return (self.cash_flow(year) / initial_investment) * 100

    def break_even_occupancy_rate(self, year: int = 1) -> float:
        return ((12 * self.monthly_total_expenses(year)) / self.gross_income(year)) * 100

    def future_value(self, year: int = 30) -> float:
        return self.purchase_price * (1 + self.appreciation_rate) ** year

    def total_roi(self, year: int = 1) -> float:
        """
        Calculates total ROI for a given year.

        This method takes into account both the equity growth and the total cash flow
        for a given year.

        :param year: the year for which to calculate the total ROI
        :return: the total ROI as a percentage
        """
        future_value = self.future_value(year)
        remaining_loan_at_year = self.remaining_loan(year)
        equity_growth = future_value - remaining_loan_at_year
        total_cash_flow = sum([self.cash_flow(y) for y in range(1, year + 1)])
        initial_investment = self.purchase_price - self.loan_amount
        net_gain = equity_growth + total_cash_flow - initial_investment
        return (net_gain / initial_investment) * 100

    def input_summary(self) -> str:
        input_summary = f"""
        Purchase Price: ${self.purchase_price:,.0f}
        Monthly Rent: ${self.monthly_rent:,.0f}
        Loan Amount: ${self.loan_amount:,.0f}
        Interest Rate: {self.interest_rate * 100:.2f}%
        Loan Term: {self.loan_term} years
        Appreciation Rate: {self.appreciation_rate * 100:.2f}%
        Inflation Rate: {self.inflation_rate * 100:.2f}%
        """
        return input_summary

    def evaluate(self, years: int = 30) -> pd.DataFrame:
        """
        Evolves the property statistics over time.

        This method calculates key statistics for the property over a given
        number of years. The statistics calculated include remaining loan balance,
        gross income, operating expenses, net operating income, annual debt service,
        cash flow, cap rate, break-even occupancy rate, future value and total ROI.

        :param years: the number of years to evolve the statistics
        :return: a pandas DataFrame with the statistics
        """
        stats = []
        for year in range(1, years + 1):
            stats.append({
                "Year": year,
                "Remaining Loan": self.remaining_loan(year),
                "Gross Income": self.gross_income(year),
                "Operating Expenses": self.operating_expenses_adjusted(year),
                "Net Operating Income": self.net_operating_income(year),
                "Annual Debt Service": self.annual_debt_service(),
                "Cash Flow": self.cash_flow(year),
                "Cap Rate": self.cap_rate(year),
                "Break-Even Occupancy Rate": self.break_even_occupancy_rate(year),
                "Future Value": self.future_value(year),
                "Total ROI": self.total_roi(year),
            })

        return pd.DataFrame(stats)

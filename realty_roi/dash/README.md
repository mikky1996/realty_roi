# Purchase For Rent Dashboard

This folder contains Streamlit dashboards for the realty_roi project.

## Purchase For Rent Dashboard

An interactive dashboard for analyzing rental property investments.

### Features

- **Interactive Input Controls**: Adjust all property, loan, and rate parameters
- **Real-time Analysis**: Click "Analyse" to run projections for any number of years
- **Visual Analytics**: Grid of 13 interactive plots showing key metrics over time
- **Summary Metrics**: Quick view of final year statistics
- **Data Export**: Download full analysis results as CSV

### Installation

Make sure you have the required dependencies:

```bash
pip install streamlit plotly pandas
```

### Usage

From the project root directory:

```bash
streamlit run realty_roi/dash/purchase_for_rent_dashboard.py
```

Or from any directory:

```bash
cd /path/to/realty_roi
streamlit run realty_roi/dash/purchase_for_rent_dashboard.py
```

The dashboard will open in your default web browser at `http://localhost:8501`

### Input Parameters

#### Property Details
- **Purchase Price**: Total cost of the property
- **Monthly Rent**: Expected monthly rental income
- **Monthly HOA Expenses**: Homeowners association fees
- **Annual Repair Expenses**: Yearly maintenance costs (default: 1% of purchase price)
- **Annual Insurance**: Property insurance costs (default: 0.5% of purchase price)

#### Loan Terms
- **Down Payment**: Percentage paid upfront (default: 20%)
- **Interest Rate**: Annual interest rate on the loan (default: 6.9%)
- **Loan Term**: Length of the mortgage in years (default: 30)

#### Rate Assumptions
- **Vacancy Rate**: Expected months vacant per year (default: 1)
- **Property Tax Rate**: Annual property tax as % of value (default: 2.2%)
- **Appreciation Rate**: Annual property value growth (default: 1%)
- **Income Tax Rate**: Personal income tax rate (default: 25%)
- **Depreciation Period**: IRS depreciation period (default: 27.5 years for residential)
- **Inflation Rate**: Annual inflation rate (default: 2%)

### Metrics Displayed

The dashboard calculates and displays 13 key metrics over time:

1. **CAGR**: Compound Annual Growth Rate (nominal)
2. **Real CAGR**: Inflation-adjusted CAGR
3. **Remaining Loan**: Outstanding mortgage balance
4. **Gross Income**: Total rental income before expenses
5. **Operating Expenses**: Total annual operating costs
6. **Net Operating Income**: Gross income minus operating expenses
7. **Annual Debt Service**: Total mortgage payments per year
8. **Cash Flow**: Net income after all expenses
9. **Cap Rate**: Return on investment percentage
10. **Break-Even Occupancy Rate**: Minimum occupancy needed to break even
11. **Property Value**: Appreciated property value
12. **Net Gain**: Total profit including equity and cash flow
13. **Total ROI**: Overall return on investment

### Tips

- Adjust parameters to compare different scenarios
- Use the interactive plots to zoom and explore specific time periods
- Download the CSV data for further analysis in Excel or other tools
- The analysis accounts for inflation, taxes, depreciation, and property appreciation

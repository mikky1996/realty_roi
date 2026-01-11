import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from realty_roi.projects.purchase_for_rent import (
    PurchaseForRent,
    PropertyDetails,
    LoanTerms,
    RateAssumptions
)


def create_plots(df: pd.DataFrame):
    """
    Create a grid of plots for all statistics.
    
    Args:
        df: DataFrame from evaluate() method containing all statistics
    """
    # Define metrics to plot (excluding Year)
    metrics = [
        ("CAGR", "%"),
        ("Real CAGR", "%"),
        ("Remaining Loan", "$"),
        ("Gross Income", "$"),
        ("Operating Expenses", "$"),
        ("Net Operating Income", "$"),
        ("Annual Debt Service", "$"),
        ("Cash Flow", "$"),
        ("Cap Rate", "%"),
        ("Break-Even Occupancy Rate", "%"),
        ("Property Value", "$"),
        ("Net Gain", "$"),
        ("Total ROI", "%"),
    ]
    
    # Create a 4x4 subplot grid (adjust as needed)
    rows = 4
    cols = 4
    
    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=[metric[0] for metric in metrics[:rows*cols]],
        vertical_spacing=0.08,
        horizontal_spacing=0.08
    )
    
    # Plot each metric
    for idx, (metric, unit) in enumerate(metrics):
        if metric not in df.columns:
            continue
            
        row = (idx // cols) + 1
        col = (idx % cols) + 1
        
        # Format values based on unit
        if unit == "$":
            hover_template = f'Year: %{{x}}<br>{metric}: $%{{y:,.0f}}<extra></extra>'
        else:  # percentage
            hover_template = f'Year: %{{x}}<br>{metric}: %{{y:.2f}}%<extra></extra>'
        
        fig.add_trace(
            go.Scatter(
                x=df["Year"],
                y=df[metric],
                mode='lines+markers',
                name=metric,
                hovertemplate=hover_template,
                line=dict(width=2),
                marker=dict(size=4)
            ),
            row=row,
            col=col
        )
        
        # Update axes labels
        fig.update_xaxes(title_text="Year", row=row, col=col)
        if unit == "$":
            fig.update_yaxes(title_text="Value ($)", row=row, col=col)
        else:
            fig.update_yaxes(title_text="Rate (%)", row=row, col=col)
    
    # Update layout
    fig.update_layout(
        height=1200,
        showlegend=False,
        title_text="Purchase for Rent Analysis - Key Metrics Over Time",
        title_font_size=20
    )
    
    return fig


def main():
    st.set_page_config(
        page_title="Purchase For Rent Analysis",
        page_icon="🏠",
        layout="wide"
    )
    
    st.title("🏠 Purchase For Rent Analysis Dashboard")
    st.markdown("---")
    
    # ========================================================================
    # INPUT SECTION
    # ========================================================================
    
    st.header("📊 Input Parameters")
    
    # Create three columns for inputs
    col1, col2, col3 = st.columns(3)
    
    # Column 1: Property Details
    with col1:
        st.subheader("Property Details")
        purchase_price = st.number_input(
            "Purchase Price ($)",
            min_value=0.0,
            value=500000.0,
            step=10000.0,
            format="%.0f"
        )
        
        monthly_rent = st.number_input(
            "Monthly Rent ($)",
            min_value=0.0,
            value=3000.0,
            step=100.0,
            format="%.0f"
        )
        
        monthly_hoa_expenses = st.number_input(
            "Monthly HOA Expenses ($)",
            min_value=0.0,
            value=200.0,
            step=10.0,
            format="%.0f"
        )
        
        annual_repair_expenses = st.number_input(
            "Annual Repair Expenses ($)",
            min_value=0.0,
            value=purchase_price * 0.01,
            step=100.0,
            format="%.0f",
            help="Default is 1% of purchase price"
        )
        
        annual_insurance = st.number_input(
            "Annual Insurance ($)",
            min_value=0.0,
            value=purchase_price * 0.005,
            step=100.0,
            format="%.0f",
            help="Default is 0.5% of purchase price"
        )
    
    # Column 2: Loan Terms
    with col2:
        st.subheader("Loan Terms")
        downpayment_percent = st.number_input(
            "Down Payment (%)",
            min_value=0.0,
            max_value=100.0,
            value=20.0,
            step=1.0,
            format="%.1f"
        )
        
        interest_rate = st.number_input(
            "Interest Rate (%)",
            min_value=0.0,
            max_value=30.0,
            value=6.9,
            step=0.1,
            format="%.2f"
        )
        
        loan_term_years = st.number_input(
            "Loan Term (years)",
            min_value=1.0,
            max_value=50.0,
            value=30.0,
            step=1.0,
            format="%.0f"
        )
    
    # Column 3: Rate Assumptions
    with col3:
        st.subheader("Rate Assumptions")
        vacancy_rate = st.number_input(
            "Vacancy Rate (months/year)",
            min_value=0.0,
            max_value=12.0,
            value=1.0,
            step=0.1,
            format="%.1f",
            help="Number of months property is vacant per year"
        )
        
        property_tax_rate = st.number_input(
            "Property Tax Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=2.2,
            step=0.1,
            format="%.1f"
        )
        
        appreciation_rate = st.number_input(
            "Appreciation Rate (%)",
            min_value=-10.0,
            max_value=20.0,
            value=1.0,
            step=0.1,
            format="%.1f"
        )
        
        tax_rate = st.number_input(
            "Income Tax Rate (%)",
            min_value=0.0,
            max_value=50.0,
            value=25.0,
            step=1.0,
            format="%.1f"
        )
        
        depreciation_period = st.number_input(
            "Depreciation Period (years)",
            min_value=1.0,
            max_value=50.0,
            value=27.5,
            step=0.5,
            format="%.1f",
            help="IRS standard for residential rental is 27.5 years"
        )
        
        inflation_rate = st.number_input(
            "Inflation Rate (%)",
            min_value=0.0,
            max_value=20.0,
            value=2.0,
            step=0.1,
            format="%.1f"
        )
    
    # Analysis Parameters
    st.markdown("---")
    st.subheader("Analysis Parameters")
    col_years, col_button = st.columns([1, 3])
    
    with col_years:
        num_years = st.number_input(
            "Number of Years to Analyze",
            min_value=1,
            max_value=50,
            value=30,
            step=1
        )
    
    with col_button:
        st.write("")  # Spacing
        st.write("")  # Spacing
        analyze_button = st.button("🔍 Analyse", type="primary", use_container_width=False)
    
    st.markdown("---")
    
    # ========================================================================
    # ANALYSIS SECTION
    # ========================================================================
    
    if analyze_button:
        with st.spinner("Running analysis..."):
            # Create dataclass instances
            property_details = PropertyDetails(
                purchase_price=purchase_price,
                monthly_rent=monthly_rent,
                monthly_hoa_expenses=monthly_hoa_expenses,
                annual_repair_expenses=annual_repair_expenses,
                annual_insurance=annual_insurance
            )
            
            loan_terms = LoanTerms(
                downpayment_percent=downpayment_percent,
                interest_rate=interest_rate,
                loan_term_years=loan_term_years
            )
            
            rate_assumptions = RateAssumptions(
                vacancy_rate=vacancy_rate / 12,  # Convert months to fraction
                property_tax_rate=property_tax_rate,
                appreciation_rate=appreciation_rate,
                tax_rate=tax_rate,
                depreciation_period=depreciation_period,
                inflation_rate=inflation_rate
            )
            
            # Create project instance
            project = PurchaseForRent(
                property_details=property_details,
                loan_terms=loan_terms,
                rate_assumptions=rate_assumptions
            )
            
            # Run evaluation
            df = project.evaluate(years=num_years)
            
            # Display summary statistics
            st.header("📈 Summary Statistics")
            
            # Show key metrics in columns
            metric_cols = st.columns(4)
            
            final_year = df.iloc[-1]
            
            with metric_cols[0]:
                st.metric(
                    "Total ROI (Final Year)",
                    f"{final_year['Total ROI']:.2f}%"
                )
                st.metric(
                    "Net Gain (Final Year)",
                    f"${final_year['Net Gain']:,.0f}"
                )
            
            with metric_cols[1]:
                st.metric(
                    "CAGR (Final Year)",
                    f"{final_year['CAGR']:.2f}%"
                )
                st.metric(
                    "Real CAGR (Final Year)",
                    f"{final_year['Real CAGR']:.2f}%"
                )
            
            with metric_cols[2]:
                st.metric(
                    "Property Value (Final Year)",
                    f"${final_year['Property Value']:,.0f}"
                )
                st.metric(
                    "Remaining Loan (Final Year)",
                    f"${final_year['Remaining Loan']:,.0f}"
                )
            
            with metric_cols[3]:
                st.metric(
                    "Cash Flow (Final Year)",
                    f"${final_year['Cash Flow']:,.0f}"
                )
                st.metric(
                    "Cap Rate (Final Year)",
                    f"{final_year['Cap Rate']:.2f}%"
                )
            
            st.markdown("---")
            
            # Display plots
            st.header("📊 Detailed Analysis")
            fig = create_plots(df)
            st.plotly_chart(fig, use_container_width=True)
            
            # Display data table
            st.markdown("---")
            st.header("📋 Detailed Data Table")
            
            # Format the dataframe for display
            display_df = df.copy()
            
            # Format currency columns
            currency_cols = [
                "Remaining Loan", "Gross Income", "Operating Expenses",
                "Net Operating Income", "Annual Debt Service", "Cash Flow",
                "Property Value", "Net Gain"
            ]
            for col in currency_cols:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: f"${x:,.0f}")

            # Format percentage columns
            percentage_cols = [
                "CAGR", "Real CAGR", "Cap Rate", "Break-Even Occupancy Rate", "Total ROI"
            ]
            for col in percentage_cols:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: f"{x:.2f}%")

            st.dataframe(display_df, use_container_width=True)

            # Download button for CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv,
                file_name=f"purchase_for_rent_analysis_{num_years}years.csv",
                mime="text/csv"
            )


if __name__ == "__main__":
    main()

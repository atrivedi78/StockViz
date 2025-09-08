import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
from datetime import datetime, timedelta
import io
from portfolio_analyzer import PortfolioAnalyzer
from technical_indicators import calculate_macd

# Page configuration
st.set_page_config(
    page_title="Portfolio Analysis Dashboard",
    page_icon="📈",
    layout="wide")

st.title("📈 Portfolio Analysis Dashboard")
st.markdown("Upload your portfolio holdings to analyze weights, current prices, and technical indicators.")

# Initialize session state
if 'portfolio_data' not in st.session_state:
    st.session_state.portfolio_data = None
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None

# Sidebar for file upload and controls
st.sidebar.header("Upload Portfolio Data")

uploaded_file = st.sidebar.file_uploader(
    "Choose a CSV or Excel file",
    type=['csv', 'xlsx', 'xls'],
    help="Upload a file with your portfolio holdings. Supports columns like: Slice/Symbol, Owned quantity/Shares, or Weight"
)

if uploaded_file is not None:
    try:
        # Read the file based on its extension
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.session_state.portfolio_data = df
        st.session_state.analyzer = PortfolioAnalyzer(df)
        
        st.sidebar.success(f"✅ File uploaded successfully! Found {len(df)} holdings.")
        
        # Display file preview
        st.sidebar.subheader("Data Preview")
        st.sidebar.dataframe(df.head())
        
    except Exception as e:
        st.sidebar.error(f"❌ Error reading file: {str(e)}")
        st.sidebar.info("Please ensure your file has columns like 'Slice'/'Symbol', 'Owned quantity'/'Shares' or 'Weight'")

# Main content area
if st.session_state.portfolio_data is not None and st.session_state.analyzer is not None:
    analyzer = st.session_state.analyzer
    
    # Portfolio Overview Section
    st.header("📊 Portfolio Overview")
    
    with st.spinner("Fetching current market data..."):
        try:
            portfolio_summary = analyzer.get_portfolio_summary()
            
            if portfolio_summary is not None and not portfolio_summary.empty:
                # Display key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_value = portfolio_summary['Market Value'].sum() if 'Market Value' in portfolio_summary.columns else 0
                    st.metric("Total Portfolio Value", f"${total_value:,.2f}")
                
                with col2:
                    num_holdings = len(portfolio_summary)
                    st.metric("Number of Holdings", num_holdings)
                
                with col3:
                    if 'Current Price' in portfolio_summary.columns:
                        avg_price = portfolio_summary['Current Price'].mean()
                        st.metric("Average Price", f"${avg_price:.2f}")
                    else:
                        st.metric("Average Price", "N/A")
                
                with col4:
                    if 'Weight' in portfolio_summary.columns:
                        max_weight = portfolio_summary['Weight'].max() * 100
                        st.metric("Largest Position", f"{max_weight:.1f}%")
                    else:
                        st.metric("Largest Position", "N/A")
                
                # Display detailed holdings table
                st.subheader("Holdings Details")
                row_height = 35  # adjust based on font/spacing

                # Let the user pick which columns to display
                columns_to_show = st.multiselect(
                    "Select columns to display:",
                    options=portfolio_summary.columns.tolist(),  # all available columns
                    default=["Symbol", "Company Name", "Current Price", "Currency", "Daily Change (%)", "Weight (%)"]  # pre-selected defaults
                )
                
                st.dataframe(
                    portfolio_summary[columns_to_show],
                    height=(len(df) + 1) * row_height,
                    use_container_width=True,
                    hide_index=True
                )

                # Top & Bottom 5
                st.header("🏆 / 💔 - Top 5 Winners vs Losers")
                col1, col2 = st.columns(2)
                top5_cols_to_show=["Symbol", "Company Name", "P&L %"]
                
                with col1:
                    top5_df = portfolio_summary.nlargest(5, "P&L %")  # top 5 rows by P&L %
                    st.dataframe(
                        top5_df[top5_cols_to_show],
                        height=6 * row_height,
                        use_container_width=True,
                        hide_index=True
                    )

                with col2:
                    bottom5_df = portfolio_summary.nsmallest(5, "P&L %")  # top 5 rows by P&L %
                    st.dataframe(
                        bottom5_df[top5_cols_to_show],
                        height=6 * row_height,
                        use_container_width=True,
                        hide_index=True
                    )
                
                # Heat Map Section
                st.header("🔥 Portfolio Weight Heat Map")
                
                if 'Weight' in portfolio_summary.columns and 'Symbol' in portfolio_summary.columns:
                    # Create treemap for portfolio weights
                    fig_treemap = px.treemap(
                        portfolio_summary,
                        path=['Symbol'],
                        values='Weight',
                        # title="Portfolio Holdings by Weight",
                        color='P&L %',
                        color_continuous_scale=['red', 'green'],  # red = negative, green = positive
                        labels={'Weight': 'Portfolio Weight'}
                    )
                    
                    fig_treemap.update_layout(
                        height=500,
                        font_size=12
                    )
                    
                    st.plotly_chart(fig_treemap, use_container_width=True, key="portfolio_treemap")
                    
                    # Bar chart for weights
                    fig_bar = px.bar(
                        portfolio_summary.sort_values('Weight (%)', ascending=False),
                        x='Symbol',
                        y='Weight (%)',
                        title="Holdings by Weight",
                        labels={'Weight (%)': 'Portfolio Weight', 'Symbol': 'Stock Symbol'}
                    )
                    fig_bar.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_bar, use_container_width=True, key="portfolio_weights_bar")
                    
                    # Bar chart for pnl vs cost
                    fig_pnl = px.bar(
                        portfolio_summary.sort_values('Weight (%)', ascending=False),
                        x='Symbol',
                        y='Weight (%)',
                        title="Holdings by Weight",
                        labels={'Weight (%)': 'Portfolio Weight', 'Symbol': 'Stock Symbol'}
                    )
                    fig_pnl.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_pnl, use_container_width=True, key="portfolio_pnl_bar")
                
                else:
                    st.warning("Weight information not available. Please ensure your portfolio file includes weight or shares data.")
                
                # MACD Analysis Section
                st.header("📈 MACD Technical Analysis")
                
                # Symbol selection for MACD analysis
                symbols = portfolio_summary['Symbol'].tolist() if 'Symbol' in portfolio_summary.columns else []
                
                if symbols:
                    selected_symbol = st.selectbox(
                        "Select a symbol for MACD analysis:",
                        symbols,
                        help="Choose a stock symbol from your portfolio to analyze MACD trends"
                    )
                    
                    # Time period selection
                    col1, col2 = st.columns(2)
                    with col1:
                        period = st.selectbox(
                            "Analysis Period:",
                            ["1y", "2y", "5y", "max"],
                            index=2,
                            help="Select the time period for MACD analysis"
                        )
                    
                    with col2:
                        interval = st.selectbox(
                            "Data Interval:",
                            ["1mo", "1wk", "1d"],
                            index=0,
                            help="Monthly data recommended for trend analysis"
                        )
                    
                    if st.button("Generate MACD Analysis", type="primary"):
                        with st.spinner(f"Analyzing MACD for {selected_symbol}..."):
                            try:
                                # Fetch historical data
                                ticker = yf.Ticker(selected_symbol)
                                hist_data = ticker.history(period=period, interval=interval)
                                
                                if not hist_data.empty:
                                    # Calculate MACD
                                    macd_data = calculate_macd(hist_data['Close'])
                                    
                                    if macd_data is not None:
                                        # Create MACD visualization
                                        fig = make_subplots(
                                            rows=3, cols=1,
                                            shared_xaxes=True,
                                            vertical_spacing=0.05,
                                            subplot_titles=(
                                                f'{selected_symbol} Price',
                                                'MACD (1mo)'
                                            ),
                                            row_heights=[0.5, 0.5, 0.5]
                                        )
                                        
                                        # Price chart
                                        fig.add_trace(
                                            go.Scatter(
                                                x=hist_data.index,
                                                y=hist_data['Close'],
                                                name='Price',
                                                line=dict(color='blue')
                                            ),
                                            row=1, col=1
                                        )
                                        
                                        # MACD line
                                        fig.add_trace(
                                            go.Scatter(
                                                x=macd_data.index,
                                                y=macd_data['MACD'],
                                                name='MACD',
                                                line=dict(color='red')
                                            ),
                                            row=2, col=1
                                        )
                                        
                                        # Signal line
                                        fig.add_trace(
                                            go.Scatter(
                                                x=macd_data.index,
                                                y=macd_data['Signal'],
                                                name='Signal',
                                                line=dict(color='orange')
                                            ),
                                            row=2, col=1
                                        )
                                        
                                        # MACD histogram
                                        colors = ['green' if val >= 0 else 'red' for val in macd_data['Histogram']]
                                        fig.add_trace(
                                            go.Bar(
                                                x=macd_data.index,
                                                y=macd_data['Histogram'],
                                                name='Histogram',
                                                marker_color=colors
                                            ),
                                            row=2, col=1
                                        )
                                        
                                        fig.update_layout(
                                            title=f'MACD Analysis for {selected_symbol}',
                                            height=800,
                                            showlegend=False
                                        )
                                        
                                        fig.update_xaxes(title_text="Date", row=3, col=1)
                                        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
                                        fig.update_yaxes(title_text="MACD", row=2, col=1)
                                        fig.update_yaxes(title_text="Histogram", row=3, col=1)
                                        
                                        st.plotly_chart(fig, use_container_width=True, key="macd_analysis")
                                        
                                        # MACD insights
                                        st.subheader("MACD Insights")
                                        
                                        latest_macd = macd_data.iloc[-1]
                                        
                                        # Signal interpretation
                                        if latest_macd['MACD'] > latest_macd['Signal']:
                                            st.success("🟢 **Bullish Signal**: MACD is above the signal line, indicating potential upward momentum.")
                                        else:
                                            st.error("🔴 **Bearish Signal**: MACD is below the signal line, indicating potential downward momentum.")
                                        
                                    else:
                                        st.error("Failed to calculate MACD. Insufficient data points.")
                                else:
                                    st.error(f"No historical data found for {selected_symbol}")
                                    
                            except Exception as e:
                                st.error(f"Error analyzing MACD for {selected_symbol}: {str(e)}")
                
                else:
                    st.warning("No symbols available for MACD analysis. Please check your portfolio data.")
                
            else:
                st.error("Failed to fetch portfolio data. Please check your internet connection and try again.")
                
        except Exception as e:
            st.error(f"Error processing portfolio data: {str(e)}")
            st.info("Please ensure your portfolio file has the correct format with columns like 'Slice'/'Symbol', 'Owned quantity'/'Shares' or 'Weight'")

else:
    # Welcome message when no file is uploaded
    st.info("👆 Please upload a portfolio file using the sidebar to get started.")
    
    st.markdown("""
    ### 📋 Supported File Formats
    - **CSV files** (.csv)
    - **Excel files** (.xlsx, .xls)
    
    ### 📊 Required Columns
    Your portfolio file should include:
    - **Slice** or **Symbol**: Stock ticker symbols (e.g., AAPL, GOOGL, MSFT)
    - **Owned quantity** or **Shares**: Number of shares owned, OR
    - **Weight**: Portfolio weight percentage (0-1 or 0-100)
    - **Name**: Company names (optional)
    - **Value**: Current portfolio value (optional)
    
    ### ✨ Features
    - 📈 Real-time price fetching
    - 🔥 Interactive heat map visualization
    - 📊 MACD technical analysis
    - 📋 Detailed portfolio metrics
    - 🚫 Automatic filtering of summary rows
    
    ### 📝 Example File Format
    ```
    Slice,Name,Owned quantity
    AAPL,Apple Inc,100
    GOOGL,Alphabet Inc,50
    MSFT,Microsoft,75
    ```
    
    or
    
    ```
    Symbol,Weight
    AAPL,0.4
    GOOGL,0.35
    MSFT,0.25
    ```
    """)

# Footer
st.markdown("---")
st.markdown("*Built with Streamlit • Data powered by Yahoo Finance*")

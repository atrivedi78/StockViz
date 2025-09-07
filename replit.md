# Portfolio Analysis Dashboard

## Overview

A Streamlit-based web application for portfolio analysis that allows users to upload their investment holdings and analyze portfolio weights, current market prices, and technical indicators. The application supports CSV and Excel file uploads and provides interactive visualizations using Plotly. Users can track portfolio performance, view technical analysis indicators like MACD, and gain insights into their investment allocations.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Streamlit Framework**: Web-based dashboard with file upload capabilities and interactive widgets
- **Plotly Visualization**: Interactive charts and graphs for portfolio analysis and technical indicators
- **Session State Management**: Maintains uploaded data and analyzer instances across user interactions
- **Responsive Layout**: Wide page layout optimized for data visualization and analysis

### Data Processing Layer
- **Portfolio Analyzer Class**: Core business logic for processing and validating portfolio data
- **Flexible Data Validation**: Handles multiple column naming conventions (Symbol/symbol/ticker, Shares/shares/quantity, Weight/weight/allocation)
- **Data Standardization**: Automatic cleaning and normalization of ticker symbols and numeric values
- **Weight Calculation**: Supports both share-based and weight-based portfolio definitions

### Technical Analysis Module
- **MACD Indicator**: Moving Average Convergence Divergence calculation with configurable periods
- **EMA Calculations**: Exponential Moving Average functions for technical analysis
- **Modular Design**: Separate technical indicators module for extensibility

### Data Storage
- **In-Memory Processing**: Session-based data storage using Streamlit's session state
- **File Format Support**: CSV and Excel file parsing with pandas
- **No Persistent Database**: Application operates on uploaded data without permanent storage

### Market Data Integration
- **Yahoo Finance API**: Real-time stock price data retrieval via yfinance library
- **Historical Data**: Supports time-series analysis for technical indicators
- **Symbol Validation**: Handles ticker symbol lookup and validation

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework for the dashboard interface
- **Pandas**: Data manipulation and analysis for portfolio processing
- **NumPy**: Numerical computing for mathematical calculations
- **Plotly**: Interactive visualization library for charts and graphs

### Financial Data Services
- **yfinance**: Yahoo Finance API wrapper for stock market data retrieval
- **Real-time Pricing**: Current market prices and historical data access

### File Processing
- **Excel Support**: openpyxl/xlrd for Excel file reading capabilities
- **CSV Processing**: Built-in pandas CSV parsing functionality

### Utility Libraries
- **datetime**: Date and time manipulation for time-series analysis
- **io**: File input/output operations for uploaded files
- **typing**: Type hints for better code documentation and validation
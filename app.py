import pandas as pd
import streamlit as st
import yfinance as yf
import requests
from io import StringIO

SP500_URL = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'


# Cache static data (Wikipedia components list)
@st.cache_data
def load_sp500_components():
    url = SP500_URL
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = requests.get(url, headers=headers)
    html_data = StringIO(response.text)
    components = pd.read_html(html_data)[0]
    components.set_index('Symbol', inplace=True)
    return components


# Cache API calls for quotes
@st.cache_data
def load_quotes(symbol):
    data = yf.download(symbol, period='max', auto_adjust=False)
    # Properly handle MultiIndex columns
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data


def format_symbol_label(symbol, components):
    company = components.loc[symbol]
    return f"{symbol} - {company.Security}"


def main():
    # Sets the page title and expands layout.
    st.set_page_config(page_title="S&P 500 Finance Dashboard", layout="wide")

    # Loads the S&P 500 company list and sets up sidebar.
    components = load_sp500_components()
    st.sidebar.title("Options")

    # Optional: View entire list
    if st.sidebar.checkbox('View Companies List'):
        st.dataframe(
            components[['Security', 'GICS Sector', 'Date added', 'Founded']])

    # Asset selection
    st.sidebar.subheader("Select Asset")
    asset = st.sidebar.selectbox(
        'Choose an asset',
        components.index.sort_values(),
        index=1,
        format_func=lambda x: format_symbol_label(x, components)
    )

    company_info = components.loc[asset]

    if st.sidebar.checkbox("View Company Info", True):
        st.title(company_info.Security)
        st.table(company_info.to_frame().T)

    st.title(company_info.Security)

    # Load quotes
    data = load_quotes(asset).dropna()
    data.index.name = None

    # Quote selection range
    section = st.sidebar.slider(
        'Number of Quotes', 30, min(2000, len(data)), 500, 10)
    data_view = data[-section:][['Adj Close']].copy()

    # SMA options
    if st.sidebar.checkbox("SMA"):
        period = st.sidebar.slider("SMA Period", 5, 500, 20)
        data_view[f"SMA {period}"] = data['Adj Close'].rolling(
            period).mean().reindex(data_view.index)

    if st.sidebar.checkbox("SMA 2"):
        period2 = st.sidebar.slider("SMA 2 Period", 5, 500, 100)
        data_view[f"SMA2 {period2}"] = data['Adj Close'].rolling(
            period2).mean().reindex(data_view.index)

    # Chart
    st.subheader("Chart")
    st.line_chart(data_view)

    # Statistics
    if st.sidebar.checkbox("View Statistics"):
        st.subheader("Statistics")
        st.table(data_view.describe())

    # Full Quotes
    if st.sidebar.checkbox("View Quotes"):
        st.subheader(f"{asset} Historical Data")
        st.write(data_view)

    # About section
    st.sidebar.title("About")
    st.sidebar.info(
        "This app is a simple example of using Streamlit to create a financial "
        "data web app.\n\nMaintained by [Paduel](https://twitter.com/paduel_py).\n\n"
        "Source: https://github.com/paduel/streamlit_finance_chart"
    )


if __name__ == "__main__":
    main()

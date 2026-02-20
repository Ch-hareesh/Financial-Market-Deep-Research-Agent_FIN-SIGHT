"""
src/data_fetcher.py
FIN-SIGHT – Real financial data fetcher using yfinance.
Extracts company ticker from query, fetches live metrics from Yahoo Finance,
and returns a structured dict ready for prompt injection and contradiction detection.
"""

from __future__ import annotations
import re
import warnings
from typing import Any

# Suppress noisy deprecation warnings from yfinance's internal pandas usage
warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")
warnings.filterwarnings("ignore", message=".*Timestamp.utcnow.*")
warnings.filterwarnings("ignore", message=".*Pandas4Warning.*")

import yfinance as yf


# ---------------------------------------------------------------------------
# Company name → ticker mapping (expandable)
# ---------------------------------------------------------------------------
_NAME_TO_TICKER: dict[str, str] = {
    # US Tech
    "apple": "AAPL", "aapl": "AAPL",
    "microsoft": "MSFT", "msft": "MSFT",
    "google": "GOOGL", "alphabet": "GOOGL", "googl": "GOOGL", "goog": "GOOG",
    "amazon": "AMZN", "amzn": "AMZN",
    "meta": "META", "facebook": "META",
    "nvidia": "NVDA", "nvda": "NVDA",
    "tesla": "TSLA", "tsla": "TSLA",
    "netflix": "NFLX", "nflx": "NFLX",
    "salesforce": "CRM", "crm": "CRM",
    "adobe": "ADBE", "adbe": "ADBE",
    "intel": "INTC", "intc": "INTC",
    "amd": "AMD", "advanced micro devices": "AMD",
    "qualcomm": "QCOM", "qcom": "QCOM",
    "broadcom": "AVGO", "avgo": "AVGO",
    "oracle": "ORCL", "orcl": "ORCL",
    "ibm": "IBM",
    "uber": "UBER",
    "lyft": "LYFT",
    "airbnb": "ABNB", "abnb": "ABNB",
    "palantir": "PLTR", "pltr": "PLTR",
    "snowflake": "SNOW", "snow": "SNOW",
    "shopify": "SHOP", "shop": "SHOP",
    "spotify": "SPOT", "spot": "SPOT",
    "twitter": "TWTR",
    "coinbase": "COIN", "coin": "COIN",
    "robinhood": "HOOD", "hood": "HOOD",
    # US Finance
    "jpmorgan": "JPM", "jp morgan": "JPM", "jpm": "JPM",
    "goldman sachs": "GS", "goldman": "GS", "gs": "GS",
    "morgan stanley": "MS",
    "bank of america": "BAC", "bofa": "BAC", "bac": "BAC",
    "wells fargo": "WFC", "wfc": "WFC",
    "citigroup": "C", "citi": "C",
    "visa": "V",
    "mastercard": "MA",
    "paypal": "PYPL", "pypl": "PYPL",
    "blackrock": "BLK", "blk": "BLK",
    # US Healthcare / Pharma
    "johnson & johnson": "JNJ", "johnson and johnson": "JNJ", "jnj": "JNJ",
    "pfizer": "PFE", "pfe": "PFE",
    "moderna": "MRNA", "mrna": "MRNA",
    "abbvie": "ABBV", "abbv": "ABBV",
    "unitedhealth": "UNH", "unh": "UNH",
    "merck": "MRK", "mrk": "MRK",
    "eli lilly": "LLY", "lilly": "LLY", "lly": "LLY",
    # US Consumer / Retail
    "walmart": "WMT", "wmt": "WMT",
    "target": "TGT", "tgt": "TGT",
    "costco": "COST", "cost": "COST",
    "home depot": "HD", "hd": "HD",
    "nike": "NKE", "nke": "NKE",
    "starbucks": "SBUX", "sbux": "SBUX",
    "mcdonald's": "MCD", "mcdonalds": "MCD", "mcd": "MCD",
    "coca-cola": "KO", "coca cola": "KO", "ko": "KO",
    "pepsico": "PEP", "pepsi": "PEP", "pep": "PEP",
    # Energy
    "exxon": "XOM", "exxonmobil": "XOM", "xom": "XOM",
    "chevron": "CVX", "cvx": "CVX",
    "conocophillips": "COP", "cop": "COP",
    # Indian companies (NSE)
    "reliance": "RELIANCE.NS", "reliance industries": "RELIANCE.NS",
    "tcs": "TCS.NS", "tata consultancy": "TCS.NS",
    "infosys": "INFY", "infy": "INFY",
    "wipro": "WIPRO.NS",
    "hdfc bank": "HDFCBANK.NS", "hdfc": "HDFCBANK.NS",
    "icici bank": "ICICIBANK.NS", "icici": "ICICIBANK.NS",
    "asian paints": "ASIANPAINT.NS",
    "bajaj finance": "BAJFINANCE.NS",
    "hindustan unilever": "HINDUNILVR.NS", "hul": "HINDUNILVR.NS",
    "itc": "ITC.NS",
    "maruti": "MARUTI.NS", "maruti suzuki": "MARUTI.NS",
    "ola": "OLA.NS",
}


def extract_ticker(query: str) -> str | None:
    """
    Extract a stock ticker from a natural language query.

    Strategy:
    1. Look for explicit uppercase ticker patterns (e.g. AAPL, NVDA)
    2. Match company names against the lookup table
    3. Return None if no confident match found
    """
    # 1. Direct uppercase ticker (2–5 letters, standalone)
    explicit = re.findall(r"\b([A-Z]{2,5}(?:\.[A-Z]{2})?)\b", query)
    for candidate in explicit:
        if candidate.lower() in _NAME_TO_TICKER:
            return _NAME_TO_TICKER[candidate.lower()]
        # Check if it itself is a valid ticker (try to verify via yf)
        if candidate not in {"YOY", "KPI", "FCF", "ROE", "DCF", "EPS", "IPO",
                              "CEO", "CFO", "COO", "CTO", "PE", "PB", "EV",
                              "USD", "EUR", "INR", "GBP", "GDP", "CPI", "FY",
                              "QOQ", "AND", "FOR", "THE", "NOT", "ALL"}:
            return candidate  # pass raw ticker directly to yfinance

    # 2. Name matching
    normalized = query.lower()
    # Sort by length descending so "goldman sachs" matches before "goldman"
    for name, ticker in sorted(_NAME_TO_TICKER.items(), key=lambda x: -len(x[0])):
        if name in normalized:
            return ticker

    return None


def _safe_float(value: Any, divisor: float = 1.0) -> float | None:
    """Convert a value to float safely, applying an optional divisor."""
    try:
        if value is None:
            return None
        return round(float(value) / divisor, 2)
    except (TypeError, ValueError):
        return None


def _fmt_billions(value: float | None) -> str:
    """Format a dollar value in billions."""
    if value is None:
        return "N/A"
    if abs(value) >= 1e12:
        return f"${value / 1e12:.2f}T"
    if abs(value) >= 1e9:
        return f"${value / 1e9:.2f}B"
    if abs(value) >= 1e6:
        return f"${value / 1e6:.2f}M"
    return f"${value:,.0f}"


def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def _fmt_x(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.1f}x"


def fetch_financial_data(ticker: str) -> dict[str, Any]:
    """
    Fetch comprehensive financial metrics for a ticker using yfinance.

    Returns a structured dict with:
    - company metadata (name, sector, exchange)
    - income statement metrics (revenue, net income, EBITDA, margins)
    - balance sheet (total debt, cash)
    - cash flow (free cash flow)
    - valuation (PE, EV/EBITDA, market cap)
    - price performance (1M, 3M, YTD, 1Y)
    - quarterly revenue trend (last 4 quarters)
    - raw values for contradiction detection
    """
    result: dict[str, Any] = {
        "ticker": ticker,
        "fetch_status": "error",
        "error_message": None,
    }

    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}

        # --- Company metadata ---
        result["company_name"] = info.get("longName") or info.get("shortName") or ticker
        result["sector"] = info.get("sector", "N/A")
        result["industry"] = info.get("industry", "N/A")
        result["exchange"] = info.get("exchange", "N/A")
        result["currency"] = info.get("financialCurrency") or info.get("currency", "USD")

        # --- Valuation ---
        market_cap = info.get("marketCap")
        result["market_cap"] = _safe_float(market_cap)
        result["market_cap_fmt"] = _fmt_billions(market_cap)

        result["pe_ratio"] = _safe_float(info.get("trailingPE"))
        result["forward_pe"] = _safe_float(info.get("forwardPE"))
        result["ev_ebitda"] = _safe_float(info.get("enterpriseToEbitda"))
        result["price_to_book"] = _safe_float(info.get("priceToBook"))
        result["price_to_sales"] = _safe_float(info.get("priceToSalesTrailing12Months"))

        # --- Price performance ---
        result["current_price"] = _safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
        result["52w_high"] = _safe_float(info.get("fiftyTwoWeekHigh"))
        result["52w_low"] = _safe_float(info.get("fiftyTwoWeekLow"))

        hist = stock.history(period="1y")
        if not hist.empty:
            p_now = hist["Close"].iloc[-1]
            p_1m = hist["Close"].iloc[-22] if len(hist) >= 22 else hist["Close"].iloc[0]
            p_3m = hist["Close"].iloc[-63] if len(hist) >= 63 else hist["Close"].iloc[0]
            p_1y = hist["Close"].iloc[0]
            result["return_1m_pct"] = round((p_now / p_1m - 1) * 100, 1)
            result["return_3m_pct"] = round((p_now / p_3m - 1) * 100, 1)
            result["return_1y_pct"] = round((p_now / p_1y - 1) * 100, 1)
        else:
            result["return_1m_pct"] = None
            result["return_3m_pct"] = None
            result["return_1y_pct"] = None

        # --- Income statement (TTM from info) ---
        revenue_ttm = info.get("totalRevenue")
        result["revenue_ttm"] = _safe_float(revenue_ttm)
        result["revenue_ttm_fmt"] = _fmt_billions(revenue_ttm)
        result["revenue_growth_yoy"] = _safe_float(info.get("revenueGrowth"))
        result["revenue_growth_yoy_fmt"] = _fmt_pct(info.get("revenueGrowth"))

        result["gross_margin"] = _safe_float(info.get("grossMargins"))
        result["gross_margin_fmt"] = _fmt_pct(info.get("grossMargins"))
        result["operating_margin"] = _safe_float(info.get("operatingMargins"))
        result["operating_margin_fmt"] = _fmt_pct(info.get("operatingMargins"))
        result["net_margin"] = _safe_float(info.get("profitMargins"))
        result["net_margin_fmt"] = _fmt_pct(info.get("profitMargins"))

        net_income_ttm = info.get("netIncomeToCommon")
        result["net_income_ttm"] = _safe_float(net_income_ttm)
        result["net_income_ttm_fmt"] = _fmt_billions(net_income_ttm)

        ebitda = info.get("ebitda")
        result["ebitda_ttm"] = _safe_float(ebitda)
        result["ebitda_ttm_fmt"] = _fmt_billions(ebitda)

        result["eps_ttm"] = _safe_float(info.get("trailingEps"))
        result["eps_forward"] = _safe_float(info.get("forwardEps"))

        # --- Balance sheet ---
        total_debt = info.get("totalDebt")
        total_cash = info.get("totalCash")
        result["total_debt"] = _safe_float(total_debt)
        result["total_debt_fmt"] = _fmt_billions(total_debt)
        result["total_cash"] = _safe_float(total_cash)
        result["total_cash_fmt"] = _fmt_billions(total_cash)
        result["net_debt_fmt"] = _fmt_billions(
            (total_debt or 0) - (total_cash or 0)
        )
        result["debt_to_equity"] = _safe_float(info.get("debtToEquity"))

        # --- Cash flow ---
        fcf = info.get("freeCashflow")
        result["free_cash_flow"] = _safe_float(fcf)
        result["free_cash_flow_fmt"] = _fmt_billions(fcf)
        result["operating_cash_flow_fmt"] = _fmt_billions(info.get("operatingCashflow"))

        # --- ROE / ROA ---
        result["roe"] = _safe_float(info.get("returnOnEquity"))
        result["roe_fmt"] = _fmt_pct(info.get("returnOnEquity"))
        result["roa"] = _safe_float(info.get("returnOnAssets"))

        # --- Dividend ---
        result["dividend_yield"] = _safe_float(info.get("dividendYield"))
        result["dividend_yield_fmt"] = _fmt_pct(info.get("dividendYield")) if info.get("dividendYield") else "None"

        # --- Quarterly revenue (last 4 quarters) ---
        try:
            q_fin = stock.quarterly_financials
            if q_fin is not None and not q_fin.empty and "Total Revenue" in q_fin.index:
                q_rev = q_fin.loc["Total Revenue"].dropna().head(4)
                result["quarterly_revenue"] = {
                    str(col.date()): _fmt_billions(val)
                    for col, val in q_rev.items()
                }
            else:
                result["quarterly_revenue"] = {}
        except Exception:
            result["quarterly_revenue"] = {}

        # --- For contradiction engine (raw numeric, in original currency units) ---
        result["revenue_growth_reported"] = result.get("revenue_growth_yoy")
        result["operating_margin_current"] = result.get("operating_margin")
        result["total_debt_current"] = result.get("total_debt")
        result["net_income_current"] = result.get("net_income_ttm")
        result["free_cash_flow_raw"] = result.get("free_cash_flow")
        result["source_count"] = 2  # yfinance + LLM synthesis
        result["guidance_verified"] = False  # no earnings call transcript

        result["fetch_status"] = "ok"

    except Exception as exc:
        result["fetch_status"] = "error"
        result["error_message"] = str(exc)

    return result


def format_data_for_prompt(data: dict[str, Any]) -> str:
    """
    Format the fetched financial data into a clean block for prompt injection.
    The model receives this as grounded context — it must not deviate from these numbers.
    """
    if data.get("fetch_status") != "ok":
        return (
            f"[Data fetch failed for {data.get('ticker', 'unknown')}: "
            f"{data.get('error_message', 'unknown error')}. "
            f"Proceed using training knowledge with appropriate caveats.]"
        )

    lines = [
        "=== VERIFIED FINANCIAL DATA (Yahoo Finance / yfinance) ===",
        f"Company       : {data.get('company_name', 'N/A')} ({data.get('ticker')})",
        f"Sector        : {data.get('sector', 'N/A')} | {data.get('industry', 'N/A')}",
        f"Exchange      : {data.get('exchange', 'N/A')} | Currency: {data.get('currency', 'USD')}",
        "",
        "-- VALUATION --",
        f"Market Cap    : {data.get('market_cap_fmt', 'N/A')}",
        f"P/E Ratio     : {data.get('pe_ratio', 'N/A')}x (TTM) | Forward P/E: {data.get('forward_pe', 'N/A')}x",
        f"EV/EBITDA     : {data.get('ev_ebitda', 'N/A')}x",
        f"P/S Ratio     : {data.get('price_to_sales', 'N/A')}x",
        f"P/B Ratio     : {data.get('price_to_book', 'N/A')}x",
        "",
        "-- INCOME STATEMENT (TTM) --",
        f"Revenue       : {data.get('revenue_ttm_fmt', 'N/A')}",
        f"YoY Growth    : {data.get('revenue_growth_yoy_fmt', 'N/A')}",
        f"Gross Margin  : {data.get('gross_margin_fmt', 'N/A')}",
        f"Operating Mrg : {data.get('operating_margin_fmt', 'N/A')}",
        f"Net Margin    : {data.get('net_margin_fmt', 'N/A')}",
        f"Net Income    : {data.get('net_income_ttm_fmt', 'N/A')}",
        f"EBITDA        : {data.get('ebitda_ttm_fmt', 'N/A')}",
        f"EPS (TTM)     : ${data.get('eps_ttm', 'N/A')} | Forward EPS: ${data.get('eps_forward', 'N/A')}",
        "",
        "-- BALANCE SHEET --",
        f"Total Debt    : {data.get('total_debt_fmt', 'N/A')}",
        f"Total Cash    : {data.get('total_cash_fmt', 'N/A')}",
        f"Net Debt      : {data.get('net_debt_fmt', 'N/A')}",
        f"Debt/Equity   : {data.get('debt_to_equity', 'N/A')}",
        "",
        "-- CASH FLOW --",
        f"Free Cash Flow: {data.get('free_cash_flow_fmt', 'N/A')}",
        f"Operating CFO : {data.get('operating_cash_flow_fmt', 'N/A')}",
        "",
        "-- PROFITABILITY --",
        f"ROE           : {data.get('roe_fmt', 'N/A')}",
        f"Dividend Yield: {data.get('dividend_yield_fmt', 'N/A')}",
        "",
        "-- PRICE PERFORMANCE --",
        f"Current Price : ${data.get('current_price', 'N/A')}",
        f"52W High/Low  : ${data.get('52w_high', 'N/A')} / ${data.get('52w_low', 'N/A')}",
        f"Return 1M     : {data.get('return_1m_pct', 'N/A')}%",
        f"Return 3M     : {data.get('return_3m_pct', 'N/A')}%",
        f"Return 1Y     : {data.get('return_1y_pct', 'N/A')}%",
    ]

    if data.get("quarterly_revenue"):
        lines.append("")
        lines.append("-- QUARTERLY REVENUE TREND --")
        for period, rev in data["quarterly_revenue"].items():
            lines.append(f"  {period}: {rev}")

    lines += [
        "",
        "INSTRUCTION: Base your entire analysis on the above data. Do not deviate from",
        "these figures. Where data shows N/A, state it is not available from this source.",
        "=================================================================",
    ]

    return "\n".join(lines)

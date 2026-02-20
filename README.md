# FIN-SIGHT — Financial & Market Deep Research Agent

> An analyst-grade AI research terminal that fetches **live financial data** from Yahoo Finance and generates structured investment analysis using **Groq's free LLM API** — no paid data subscriptions required.

---

## Features

| Feature | Details |
|---|---|
| **Live Data Fetching** | Pulls 30+ real metrics from Yahoo Finance automatically (revenue, EBITDA, FCF, PE, market cap, price performance, quarterly trend) |
| **Quick Mode** | Concise KPI snapshot — company, revenue, growth, margins, net income, confidence score |
| **Deep Mode** | Full 14-section investment memo — thesis, financials, peer comparison, risks, bull/bear cases, scenarios, assumptions, contradiction check |
| **Auto Ticker Detection** | Extracts stock ticker from natural language — supports 80+ companies including Indian NSE stocks |
| **Contradiction Detection** | Flags mismatches between model claims and verified data |
| **Confidence Scoring** | 0–1 score based on data completeness, source count, and guidance verification |
| **Token & Cost Tracking** | Every response shows prompt tokens, completion tokens, cost in USD, and latency |
| **Session Memory** | Remembers your risk tolerance, investment horizon, preferred KPIs across queries |
| **Groq Backend (Free)** | Uses `llama-3.3-70b-versatile` by default — fast, capable, zero API cost on free tier |
| **Gemini Fallback** | Falls back to Google Gemini if Groq is unavailable |

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/your-username/fin-sight.git
cd fin-sight
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up API keys

Copy `.env.example` to `.env` and add your Groq API key:

```bash
cp .env.example .env
```

```env
# .env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL_NAME=llama-3.3-70b-versatile

# Optional: Gemini fallback
# GEMINI_API_KEY=your_gemini_api_key_here
# MODEL_NAME=gemini-2.0-flash
```

Get a **free** Groq API key at [console.groq.com](https://console.groq.com).

### 4. Run the agent

```bash
python main.py
```

---

## Usage

The agent runs as an interactive terminal session. Mode is **auto-detected** from how you phrase your query — no commands needed.

### Quick Mode

For concise KPI snapshots. Triggers on earnings summaries, single-metric lookups, and short factual queries.

**Example queries:**
```
FIN-SIGHT > summarize Apple's last quarterly earnings
FIN-SIGHT > what is Nvidia's revenue growth?
FIN-SIGHT > Google's current PE ratio and market cap
FIN-SIGHT > show me Microsoft's free cash flow
FIN-SIGHT > TCS quarterly revenue
```

**Output includes:**
- Company, Reporting Period, Revenue, YoY Growth
- EBITDA, Net Profit, Key Risks, Management Guidance
- Confidence Score, Data Gaps
- Token usage and cost

---

### Deep Mode

For full investment research memos. Triggers on comparisons, thesis requests, bull/bear analysis, and valuation queries.

**Example queries:**
```
FIN-SIGHT > full analysis of Apple
FIN-SIGHT > bull vs bear case for Nvidia
FIN-SIGHT > compare Microsoft vs Google
FIN-SIGHT > investment thesis for Tesla
FIN-SIGHT > scenario analysis for Amazon under high interest rates
FIN-SIGHT > valuation and DCF perspective on Meta
FIN-SIGHT > is Reliance Industries a buy?
```

**Output includes 14 sections:**
1. Executive Summary
2. Investment Thesis
3. Financial Breakdown (Revenue, Margins, ROE, FCF, Debt)
4. Peer Benchmarking
5. Competitive Positioning
6. Risk Analysis (Operational, Financial, Macro, Regulatory)
7. Scenario & Sensitivity Table (Base / Downside / Stress)
8. Bull Case
9. Bear Case
10. Valuation Perspective
11. Explicit Assumptions
12. Contradiction Check ← verified against live data
13. Confidence Score
14. Token Usage & Cost

---

### Session Commands

```
/help          — Show available commands
/memory        — View your stored preferences
/reset-memory  — Clear all stored preferences
/quit          — Exit the session
```

---

### Setting Preferences

State your profile naturally at any point. It gets saved for all future queries:

```
FIN-SIGHT > I prefer FCF and ROE. Long-term horizon, moderate risk.
FIN-SIGHT > I'm an aggressive investor focused on US tech. 3-year horizon.
```

When starting a Deep Mode query for the first time, the agent may ask:
- Investment horizon (e.g., 1 year, 3 years, long-term)
- Risk tolerance (Conservative / Moderate / Aggressive)

Just type your answer naturally and press Enter.

---

## Supported Companies

The agent auto-detects tickers from natural language for 80+ companies:

**US Tech:** Apple, Microsoft, Google/Alphabet, Amazon, Meta, Nvidia, Tesla, Netflix, Adobe, Salesforce, Intel, AMD, Qualcomm, Broadcom, Oracle, IBM, Uber, Airbnb, Palantir, Snowflake, Shopify, Spotify, Coinbase

**US Finance:** JPMorgan, Goldman Sachs, Morgan Stanley, Bank of America, Wells Fargo, Visa, Mastercard, PayPal, BlackRock

**US Healthcare:** J&J, Pfizer, Moderna, AbbVie, UnitedHealth, Merck, Eli Lilly

**US Consumer:** Walmart, Target, Costco, Home Depot, Nike, Starbucks, McDonald's, Coca-Cola, PepsiCo

**Energy:** ExxonMobil, Chevron, ConocoPhillips

**Indian (NSE):** Reliance Industries, TCS, Infosys, Wipro, HDFC Bank, ICICI Bank, Asian Paints, Bajaj Finance, HUL, ITC, Maruti Suzuki

You can also type any ticker directly: `AAPL`, `NVDA`, `RELIANCE.NS`

---

## Data Sources

| Source | What it provides |
|---|---|
| **Yahoo Finance (yfinance)** | Live: revenue, EBITDA, FCF, net income, PE ratio, market cap, margins, debt, cash, quarterly trend, 1Y/3M/1M price return |
| **Groq LLM (llama-3.3-70b)** | Analysis, qualitative assessment, thesis, risks, bull/bear cases — grounded in the fetched data |

> **Note:** All quantitative figures in the output originate from Yahoo Finance. The LLM provides interpretation and structure, not raw numbers.

---

## Project Structure

```
fin-sight/
├── main.py                  # CLI entry point — interactive session loop
├── requirements.txt         # Dependencies
├── .env.example             # Environment variable template
│
├── src/
│   ├── agent.py             # Core orchestrator — coordinates all modules
│   ├── config.py            # API keys, model names, generation config
│   ├── data_fetcher.py      # Yahoo Finance data fetcher + ticker extractor
│   ├── mode_classifier.py   # Auto-detects Quick vs Deep Mode from query
│   ├── clarification.py     # Asks for missing user preferences
│   ├── confidence_engine.py # Calculates confidence score (0–1)
│   ├── contradiction_detector.py  # Flags claim vs data mismatches
│   ├── scenario_engine.py   # Base / Downside / Stress scenario builder
│   ├── cost_tracker.py      # Token usage and cost estimation
│   ├── memory.py            # Persistent user preference storage
│   └── output_formatter.py  # Structured output renderer
│
├── prompts/
│   ├── system_prompt.py     # Agent persona and operating rules
│   ├── quick_mode.py        # Quick Mode prompt template
│   └── deep_mode.py         # Deep Mode prompt template (14 sections)
│
└── data/
    └── memory.json          # Persisted user preferences (auto-created)
```

---

## Requirements

```
google-generativeai>=0.8.0
groq>=0.11.0
yfinance>=0.2.40
python-dotenv>=1.0.0
rich>=13.7.0
pytest>=8.0.0
pytest-cov>=5.0.0
```

Python 3.10+ required.

---

## Cost

Running on Groq's free tier:

| Model | Input | Output | Typical Deep Mode query |
|---|---|---|---|
| llama-3.3-70b-versatile | $0.59 / 1M tokens | $0.79 / 1M tokens | ~$0.0003 |

A full session of 10–20 Deep Mode queries costs less than **$0.01**.

---

## License

MIT License — free to use, modify, and distribute.

---

## Contributing

Pull requests welcome. Areas for improvement:
- Additional financial data sources (SEC EDGAR, Alpha Vantage)
- Export to PDF / Markdown file
- Web UI (Streamlit or FastAPI)
- Earnings call transcript integration
- Multi-company portfolio analysis
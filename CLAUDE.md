# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a natural gas price prediction project that combines:
1. **News Scraping**: A concurrent web scraper that fetches financial news from AlphaVantage API
2. **Sentiment Analysis**: FinBERT-based sentiment analysis to predict natural gas price changes
3. **Price Data**: Historical Henry Hub Natural Gas Spot Price (DHHNGSP) data

The goal is to correlate news sentiment with natural gas price movements.

## Project Structure

```
.
├── scraper/              # AlphaVantage news scraper
│   ├── scraper.py       # Main scraper implementation
│   ├── scraper_config.json  # API keys and scraper configuration
│   ├── p_http.txt       # Proxy list (optional)
│   ├── requirements.txt # Python dependencies
│   └── venv/            # Python virtual environment
├── notebooks/           # Jupyter notebooks for analysis
│   └── natural_gas_price_prediction.ipynb  # FinBERT sentiment analysis
├── DHHNGSP.csv         # Historical natural gas price data (1997-present)
└── .cursor/rules/      # Development rules for Cursor/AI tools
```

## Development Commands

### Python Environment Setup

**IMPORTANT**: Always activate the virtual environment before running Python commands:

```bash
# From project root
cd scraper
source venv/bin/activate
```

### Installing Dependencies

```bash
cd scraper
source venv/bin/activate
pip install -r requirements.txt
```

When adding new dependencies, ensure you use the latest version unless constrained by other requirements.

### Running the News Scraper

```bash
cd scraper
source venv/bin/activate
python scraper.py
```

Configuration is in `scraper/scraper_config.json`. Before running:
- Set valid AlphaVantage API key (replace "youramonkeyy")
- Adjust date ranges, worker count, and retry settings as needed

Output is written to `scraper/sources/headlines_TIMESTAMP.jsonl` (JSONL format, one article per line).

### Running the Jupyter Notebook

```bash
# From project root
jupyter notebook notebooks/natural_gas_price_prediction.ipynb
```

The notebook is self-contained with all dependencies installed via pip in the first cell.

## Architecture

### News Scraper (`scraper/scraper.py`)

The scraper uses a concurrent architecture designed to handle API rate limits and maximize throughput:

- **ThreadPoolExecutor**: Concurrent job processing with configurable worker count
- **Client Rotation**: Automatically rotates between direct connections and HTTP proxies when rate limited
- **Job Queue**: Dynamic job generation - when API returns 1000 articles (max), creates follow-up job for next time window
- **Time Chunking**: Splits date range into 24-hour chunks for parallel processing
- **Retry Logic**: Configurable retries with exponential backoff per client before rotating

Key classes:
- `Config`: Load configuration from JSON file
- `Job`: Represents a time range to scrape
- `Result`: Contains articles, pagination info, and errors
- `NewsScraper`: Main scraper orchestrator

The scraper queries AlphaVantage's `NEWS_SENTIMENT` endpoint filtered by `topics=energy_transportation` and sorted by `EARLIEST`.

### Sentiment Analysis Pipeline (Jupyter Notebook)

The notebook implements a FinBERT-based sentiment analysis pipeline:

1. **Model**: Uses `ProsusAI/finbert` - a BERT model fine-tuned on financial text
2. **Sentiment Scoring**: Each article gets positive/negative/neutral probabilities
3. **Aggregation**: Computes mean sentiment across all articles for a day
4. **Price Prediction**: Maps sentiment score (-1 to +1) to predicted price change using configurable sensitivity

Key functions:
- `analyze_sentiment(text)`: Returns sentiment probabilities for single text
- `aggregate_sentiment(news_articles)`: Averages sentiment across multiple articles
- `predict_price_change(previous_price, news_articles, sensitivity)`: Predicts price delta
- `estimate_price_difference(previous_price, news_articles)`: Main API function

### Data Format

**DHHNGSP.csv**: Historical price data
```csv
observation_date,DHHNGSP
1997-01-07,3.82
```

**Scraped news output** (`sources/*.jsonl`):
Each line is a JSON object with AlphaVantage feed schema including:
- `title`, `summary`, `time_published`
- `overall_sentiment_score`, `overall_sentiment_label`
- `ticker_sentiment` array with per-ticker sentiment

## Development Rules

### File Encoding
All files must use UTF-8 encoding only.

### Python Development
- Always check for and activate `venv` before running Python commands
- Install latest package versions unless constrained by compatibility

### Documentation
- When adding features, document in `./docs/{feature}.md` or appropriate docs folder
- Keep README.md files updated as features are implemented or modified

## Data Pipeline Flow

```
1. scraper.py → Fetch news from AlphaVantage
2. Output → sources/headlines_TIMESTAMP.jsonl
3. Jupyter notebook → Load JSONL + DHHNGSP.csv
4. FinBERT → Analyze sentiment
5. Model → Predict price changes
```

## Common Development Tasks

### Testing the Scraper with Date Range
Edit `scraper_config.json`:
```json
{
  "start_date": "20230101T0000",
  "end_date": "20230201T2359"
}
```

### Adjusting Scraper Concurrency
Modify `num_workers` in `scraper_config.json` (default: 10)

### Tuning Sentiment Sensitivity
In notebook, adjust `sensitivity` parameter in `predict_price_change()` (default: 0.5)

### Adding Proxies
Add proxies to `scraper/p_http.txt` (one per line, format: `host:port`)

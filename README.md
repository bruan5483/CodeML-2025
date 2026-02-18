# 🏆 Natural Gas Price Prediction using News Sentiment

> **1st Place Winner** — Code-ML 2025 Hackathon | Videns Challenge

Predicting daily natural gas prices by combining NLP-based sentiment analysis of global news with historical price data.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![FinBERT](https://img.shields.io/badge/Model-FinBERT-orange.svg)
![XGBoost](https://img.shields.io/badge/Model-XGBoost-red.svg)

---

## 📖 Overview

Energy prices are highly susceptible to global events—political decisions, geopolitical tensions, natural disasters, and major economic announcements. These price fluctuations are often reflected in news coverage sentiment *before* they materialize in the market.

This project leverages this insight by:
1. **Collecting 70,000+ news headlines** from multiple sources
2. **Analyzing sentiment** using FinBERT (financial domain-specific BERT)
3. **Combining with time-series features** (lagged prices, rolling averages, volatility)
4. **Training an XGBoost model** optimized with Optuna for price prediction

---

## 🚀 Key Features

- **Multi-source news scraping** — GDELT, NewsAPI, and custom scrapers
- **FinBERT sentiment analysis** — Domain-specific NLP for financial text
- **Feature engineering** — Lagged prices, rolling averages, volatility, seasonality
- **Hyperparameter optimization** — Optuna-based tuning for XGBoost
- **End-to-end pipeline** — From raw news to price predictions

---

## 🏗️ Project Structure

```
├── notebooks/
│   ├── CodeML_BERT.ipynb          # Main model: FinBERT + XGBoost pipeline
│   ├── CodeML_LLM.ipynb           # LLM-based sentiment experiments
│   ├── CodeML_QWEN.ipynb          # QWEN model experiments
│   ├── CodeML_headline_filter.ipynb # News filtering and preprocessing
│   └── final_submission.ipynb     # Final submission notebook
├── scraper/
│   ├── main_scraper.py            # Primary news scraping script
│   ├── gdelt_scraper.py           # GDELT news source scraper
│   └── helpers/                   # Data cleaning utilities
├── scripts/
│   ├── calc_score.py              # Evaluation metrics
│   ├── sentiment_correlation.py   # Sentiment-price correlation analysis
│   └── ...                        # Other utility scripts
├── data/                          # Historical price data (not tracked)
├── requirements.txt
└── README.md
```

---

## 📊 Methodology

### 1. Data Collection
- Scraped **70,000+ news headlines** from energy and financial news sources
- Filtered to retain only energy- and economy-related content
- Date range: 2020–2024

### 2. Sentiment Analysis
- Used **FinBERT** (ProsusAI/finbert) for financial sentiment classification
- Aggregated daily sentiment scores (positive, negative, neutral)
- Computed rolling sentiment averages

### 3. Feature Engineering
- **Lagged prices**: 1-day, 7-day, 30-day lags
- **Rolling statistics**: Moving averages, standard deviation
- **Volatility indicators**: Price momentum, rate of change
- **Seasonality**: Day of week, month encoding

### 4. Model Training
- **XGBoost Regressor** with Optuna hyperparameter optimization
- Cross-validation with time-series split
- Feature importance analysis

---

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/codeml-natural-gas.git
cd codeml-natural-gas

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Data Setup

Download the required datasets and place them in the `data/` folder:
- [DHHNGSP.csv](https://fred.stlouisfed.org/series/DHHNGSP) — Historical natural gas prices
- [News_Category_Dataset_v3.json](https://www.kaggle.com/datasets/rmisra/news-category-dataset) — News categories (optional)

---

## 📈 Usage

### Run the main prediction pipeline:
```bash
jupyter notebook notebooks/CodeML_BERT.ipynb
```

### Scrape new headlines:
```bash
cd scraper
pip install -r requirements.txt
python main_scraper.py
```

---

## 👥 Team

| Name | Role | Links |
|------|------|-------|
| **Peizhe Guan** | ML Engineering | [LinkedIn](https://linkedin.com) |
| **Adrian Luk** | Data Engineering | [LinkedIn](https://linkedin.com) |
| **Sivabalan Sandh Muthurajan** | NLP & Sentiment | [LinkedIn](https://linkedin.com) |
| **Bryant Ruan** | Full Stack & Integration | [LinkedIn](https://linkedin.com) |

*University of Waterloo students — Code-ML 2025*

---

## 🙏 Acknowledgments

- **Code-ML 2025** organizers and Videns for the challenge
- **ProsusAI** for the FinBERT model
- **FRED** for historical price data

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <b>⭐ Star this repo if you found it helpful!</b>
</p>
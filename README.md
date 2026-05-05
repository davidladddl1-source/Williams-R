# MNQ 5-Minute Williams %R + MACD Strategy for TopstepX

Complete backtesting script for **Micro E-mini Nasdaq-100 futures (MNQ)** using 5-minute data from EODHD.

### Features
- Williams %R (14) + MACD (12/26/9) crossover
- **TopstepX trading hours fully enforced** (Sunday 6 PM EST open + forced flat 4–6 PM EST Mon–Fri)
- Proper MNQ P&L ($2 per point)
- 5-minute intraday data

### How to Run

```bash
pip install -r requirements.txt
python mnq_5min_wr_macd_topstepx.py

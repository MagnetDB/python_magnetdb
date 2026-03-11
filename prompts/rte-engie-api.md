This Markdown guide organizes everything we've discussed into a clean, implementable roadmap for your organization. You can copy this directly into a file named `README.md` or `IMPLEMENTATION.md`.

---

# ⚡ Electricity Bill Estimator: Engie "Dynamic Clic"

This project implements an automated electricity bill estimator for professional organizations. It correlates **Enedis** consumption data with **RTE** market prices to simulate the Engie "Dynamic Clic" (Market-indexed) contract.

## 📋 Prerequisites

1. **Enedis Data Hub:** Register an application to get your `Client ID` and `Client Secret`.
2. **RTE Data Portal:** Register for the "Wholesale Market" API.
3. **Meter ID (PRM):** Your 14-digit identifier found on your Engie bill.
4. **Contract Details:** Know your "Clicked" (fixed) price and your volume ratio if you have locked in a part of your consumption.

---

## 🛠 Project Structure

### 1. Authentication (OAuth2)

Since Enedis requires user consent, use the **FastAPI** listener to capture your permanent tokens.

```python
# Save as auth_server.py
from fastapi import FastAPI
import requests, webbrowser, uvicorn

app = FastAPI()
# Config: REDIRECT_URI must match Enedis Dashboard exactly
CONFIG = {"id": "...", "secret": "...", "url": "http://localhost:8000/callback"}

@app.get("/callback")
def callback(code: str):
    res = requests.post("https://ext.api.enedis.fr/oauth2/v3/token", data={
        "grant_type": "authorization_code", "code": code, 
        "client_id": CONFIG["id"], "client_secret": CONFIG["secret"],
        "redirect_uri": CONFIG["url"]
    })
    return res.json() # Save 'refresh_token' from here

if __name__ == "__main__":
    url = f"https://mon-compte-client.enedis.fr/dataconnect/v1/oauth2/authorize?client_id={CONFIG['id']}&response_type=code&duration=P3Y&redirect_uri={CONFIG['url']}"
    webbrowser.open(url)
    uvicorn.run(app, port=8000)

```

### 2. Data Retrieval (RTE + Enedis)

Fetch market prices (hourly) and consumption (30-min intervals).

| API | Endpoint | Key Info |
| --- | --- | --- |
| **RTE** | `/open_api/wholesale_market/v2/day_ahead` | Prices in €/MWh (convert to €/kWh) |
| **Enedis** | `/metering_data/v5/load_curve` | Values in Watts (W) |

### 3. The "Dynamic Clic" Logic

The bill is calculated by weighting the market price against your fixed "clicked" price.

```python
def calculate_bill(data_intervals, spot_prices, clic_price=0.15, clic_ratio=0.4):
    """
    clic_ratio: 0.4 means 40% of volume is at clic_price, 60% is at spot_price.
    """
    energy_cost = 0
    for entry in data_intervals:
        kwh = (float(entry['value']) * 0.5) / 1000
        p_spot = spot_prices.get(entry['date'], 0.10) # Fallback price
        
        # Weighted Price Formula
        effective_price = (p_spot * (1 - clic_ratio)) + (clic_price * clic_ratio)
        energy_cost += kwh * effective_price
        
    return energy_cost

```

---

## 📑 Estimation Components (Summary)

| Category | Component | 2026 Estimated Value |
| --- | --- | --- |
| **Energy** | Dynamic Clic | $(Spot \times Ratio) + (Fixed \times Ratio)$ |
| **Margin** | Engie Fee | $\approx 0.007$ €/kWh |
| **Fixed** | Subscription | $\approx 45.00$ €/month (varies by kVA) |
| **Grid** | TURPE | Based on "Puissance Souscrite" |
| **Taxes** | Accise (TICFE) | $\approx 0.021$ €/kWh |
| **VAT** | TVA | 5.5% (Fixed) / 20% (Energy) |

---

## 🚀 Deployment Steps

1. **Authorize:** Run `auth_server.py` once to get your `refresh_token`.
2. **Schedule:** Set up a cron job to run your main script every morning at 9:00 AM (after RTE publishes tomorrow's spot prices).
3. **Alert:** Add a check to see if tomorrow's `p_spot` exceeds 0.30 €/kWh and trigger a Slack/Email alert to reduce load.

---

**Would you like me to generate the complete `requirements.txt` file and a sample `config.json` structure to keep your credentials safe?**

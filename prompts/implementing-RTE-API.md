# Implementation Guide: RTE & Enedis API for Professional Bill Estimation

This guide details the technical implementation of an electricity bill estimator for professional organizations using a **"Dynamic Clic"** (Market-indexed) contract.

## 1. Architecture Overview
The solution correlates two distinct data streams:
* **Enedis Data-Connect API:** Provides the 30-minute interval consumption (load curve) from your Linky or professional meter.
* **RTE Data Portal API:** Provides the hourly **Epex Spot** market prices (€/MWh).

---

## 2. Authentication & Token Management
Professional data access requires a permanent `refresh_token`. Access tokens expire every 2 hours, so your script must handle automatic renewal.

```python
import requests

def refresh_enedis_access(client_id, client_secret, refresh_token):
    """Exchanges a permanent Refresh Token for a temporary Access Token."""
    url = "[https://ext.api.enedis.fr/oauth2/v3/token](https://ext.api.enedis.fr/oauth2/v3/token)"
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(url, data=payload)
    return response.json() # Use ['access_token'] for your API calls

```

---

## 3. Fetching Market Data (RTE)

RTE provides wholesale market prices. For a "Dynamic Clic" contract, you need the **Day-Ahead** prices.

```python
def get_market_prices(rte_token):
    """Fetches Day-Ahead prices and converts €/MWh to €/kWh."""
    url = "[https://digital.iservices.rtc-france.com/open_api/wholesale_market/v2/day_ahead](https://digital.iservices.rtc-france.com/open_api/wholesale_market/v2/day_ahead)"
    headers = {"Authorization": f"Bearer {rte_token}"}
    
    res = requests.get(url, headers=headers)
    # Parse the JSON to create a lookup dictionary {timestamp: price_kwh}
    prices = {item['start_date']: item['value'] / 1000 for item in res.json()['values']}
    return prices

```

---

## 4. The "Dynamic Clic" Calculation

This is the core logic for your Engie contract. It weights the market price against the volume you have "clicked" (fixed).

**The Formula:**
`Price = (Spot_Price * Spot_Ratio) + (Fixed_Clic_Price * Clic_Ratio) + Engie_Margin`

```python
def calculate_interval_cost(watts, p_spot, config):
    # Enedis 30min power (W) to energy (kWh)
    kwh = (watts * 0.5) / 1000
    
    # Weighting the Clic vs the Spot market
    clic_ratio = config['clic_ratio'] # e.g., 0.40 for 40% fixed
    p_clic = config['clic_fixed_rate']
    
    # Effective Energy Price
    p_effective = (p_spot * (1 - clic_ratio)) + (p_clic * clic_ratio)
    
    # Total cost for this interval including Engie's service fee
    return kwh * (p_effective + config['engie_margin'])

```

---

## 5. 2026 Regulatory & Tax Constants

To ensure the estimate matches your real Engie bill, you must include the following 2026 tax rates for professional profiles:

| Tax / Component | 2026 Rate (Estimated) | Note |
| --- | --- | --- |
| **Accise (TICFE)** | 0.02658 €/kWh | Updated Feb 1st, 2026 |
| **VAT (TVA)** | 20% | Standardized for all pro invoice lines |
| **CTA** | 15% (Rate) | Reduced to offset subscription hikes |

---

## 6. Implementation Checklist

1. **Authorization:** Run the OAuth2 flow once to get the initial `refresh_token`.
2. **Storage:** Store credentials in a secure `config.json` or `.env` file.
3. **Scheduling:** Run the calculation script daily (RTE publishes tomorrow's prices every day at 1:00 PM CET).
4. **Reporting:** Aggregate the 30-minute intervals into a monthly CSV for accounting.

```

```

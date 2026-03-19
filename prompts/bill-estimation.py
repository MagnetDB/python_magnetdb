import json
import requests
import os
from datetime import datetime, timedelta

class DynamicClicEstimator:
    def __init__(self, config_path='config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.tokens = self._load_tokens()

    def _load_tokens(self):
        if os.path.exists("tokens.json"):
            with open("tokens.json", "r") as f:
                return json.load(f)
        return None

    def refresh_enedis_token(self):
        """Refreshes Enedis access using the permanent refresh_token."""
        url = "https://ext.api.enedis.fr/oauth2/v3/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.tokens['refresh_token'],
            "client_id": self.config['api_credentials']['enedis']['client_id'],
            "client_secret": self.config['api_credentials']['enedis']['client_secret']
        }
        res = requests.post(url, data=payload)
        if res.status_code == 200:
            self.tokens.update(res.json())
            with open("tokens.json", "w") as f:
                json.dump(self.tokens, f)
            return True
        return False

    def get_market_prices(self):
        """Fetches hourly Day-Ahead prices from RTE."""
        # Use your RTE credentials to get a token first (per previous sketch)
        # This is a simplified fetcher for the demo
        print("Fetching RTE Market Prices...")
        # RTE returns €/MWh -> convert to €/kWh
        return {} # Mock: In production, return { "2026-03-10T14:00": 0.125 }

    def get_consumption(self, start_date, end_date):
        """Fetches load curve from Enedis."""
        url = "https://ext.api.enedis.fr/metering_data/v5/load_curve"
        headers = {"Authorization": f"Bearer {self.tokens['access_token']}"}
        params = {
            "usage_point_id": self.config['organization']['prm'],
            "start": start_date,
            "end": end_date
        }
        res = requests.get(url, headers=headers, params=params)
        if res.status_code == 401: # Token expired
            self.refresh_enedis_token()
            return self.get_consumption(start_date, end_date)
        return res.json().get('meter_reading', {}).get('interval_reading', [])

    def estimate(self, start_date, end_date):
        consumption = self.get_consumption(start_date, end_date)
        market_prices = self.get_market_prices()
        
        strategy = self.config['clic_strategy']
        taxes = self.config['taxes_and_fixed_costs_2026']
        
        energy_ht = 0
        total_kwh = 0

        for entry in consumption:
            # Enedis 30min Watts -> kWh
            kwh = (float(entry['value']) * 0.5) / 1000
            total_kwh += kwh
            
            # 2026 Spot price (fallback to 0.10 if not in RTE data)
            p_spot = market_prices.get(entry['date'], 0.10)
            
            # Dynamic Clic Formula: (Spot portion + Fixed portion) + Engie Margin
            p_dynamic = (p_spot * (1 - strategy['clic_ratio'])) + \
                         (strategy['clic_fixed_rate_kwh'] * strategy['clic_ratio'])
            
            energy_ht += kwh * (p_dynamic + strategy['engie_margin_kwh'])

        # --- Tax Calculations (2026 Rules) ---
        accise_total = total_kwh * taxes['accise_ticfe_kwh']
        fixed_costs = taxes['subscription_monthly_ht'] + taxes['cta_monthly_ht']
        
        # VAT (Everything at 20% in 2026 for Pro profiles)
        vat_total = (energy_ht + accise_total + fixed_costs) * 0.20
        total_ttc = energy_ht + accise_total + fixed_costs + vat_total

        return {
            "Period": f"{start_date} to {end_date}",
            "Consumption (kWh)": round(total_kwh, 2),
            "Energy Cost (HT)": round(energy_ht, 2),
            "Accise Tax (TICFE)": round(accise_total, 2),
            "Fixed Charges (Sub+CTA)": round(fixed_costs, 2),
            "VAT (20%)": round(vat_total, 2),
            "ESTIMATED TOTAL (TTC)": round(total_ttc, 2)
        }

if __name__ == "__main__":
    estimator = DynamicClicEstimator()
    report = estimator.estimate("2026-02-01", "2026-02-28")
    
    print(f"\n--- {estimator.config['organization']['contract_type']} Report ---")
    for k, v in report.items():
        print(f"{k:25}: {v}")

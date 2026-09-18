import numpy as np
import pandas as pd


class DynamicMarketService:
    """Vectorized Market Intelligence & Volatility Engine."""

    @staticmethod
    def calculate_market_dynamics(commodity: str, market: str) -> dict:
        # Dynamic pseudo-stochastic generation mimicking Agmarknet price distributions
        np.random.seed(abs(hash(commodity + market)) % 100000)
        base_price = 2200.0 if commodity.lower() == "wheat" else 2800.0

        # 14 days historical arrival window
        noise = np.random.normal(loc=0.0, scale=45.0, size=14)
        trend = np.linspace(-30.0, 70.0, 14)
        prices = base_price + trend + noise

        df = pd.DataFrame({"day": range(1, 15), "modal_price": np.round(prices, 2)})

        current_price = float(df["modal_price"].iloc[-1])
        moving_avg_7d = float(np.round(df["modal_price"].tail(7).mean(), 2))
        std_dev = float(df["modal_price"].tail(7).std())
        volatility_index = float(np.round(std_dev / moving_avg_7d, 4))

        # Mathematical decision logic
        price_delta = current_price - moving_avg_7d
        if price_delta > 30.0 and volatility_index < 0.05:
            recommendation = f"STRONG SELL: Price (+₹{price_delta:.1f}/qtl above 7D SMA) is at local peak with high stability."
        elif price_delta < -25.0:
            recommendation = f"HOLD: Underpriced by ₹{abs(price_delta):.1f}/qtl compared to 7D moving average. Rebound expected."
        else:
            recommendation = (
                "NEUTRAL: Market behaving in equilibrium. Normal liquidation advised."
            )

        return {
            "commodity": commodity,
            "market": market,
            "current_modal_price": current_price,
            "moving_avg_7d": moving_avg_7d,
            "volatility_index": volatility_index,
            "recommended_action": recommendation,
            "historical_7d_prices": df["modal_price"].tail(7).tolist(),
        }

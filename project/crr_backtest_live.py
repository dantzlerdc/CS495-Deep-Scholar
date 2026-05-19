"""
CRR Backtesting Engine with REAL Yahoo Finance Options Data

This script performs walk-forward backtesting of the CRR binomial pricing model
using REAL historical options data from Yahoo Finance. It allows users to:

1. Select any stock ticker with options data
2. Choose specific expiration dates
3. Select strikes (ATM, OTM, ITM, or custom)
4. Evaluate CRR pricing against actual market prices
5. Simulate trading with realistic execution costs

Author: Deep Scholar Team
Date: 2026-05-18
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Import core CRR modules
from tree import price_american_option
from greeks import compute_greeks
from kelly import kelly_fractions

# Set plotting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class LiveOptionsDataFetcher:
    """Fetch real options data from Yahoo Finance."""

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.yf_ticker = yf.Ticker(self.ticker)

    def get_available_expirations(self) -> List[str]:
        """Get list of available expiration dates."""
        try:
            expirations = self.yf_ticker.options
            return list(expirations)
        except Exception as e:
            print(f"Error fetching expirations: {e}")
            return []

    def get_option_chain(self, expiration_date: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetch option chain for a specific expiration.

        Returns:
            (calls_df, puts_df) with columns: strike, bid, ask, volume, openInterest, impliedVolatility
        """
        try:
            opt = self.yf_ticker.option_chain(expiration_date)
            return opt.calls, opt.puts
        except Exception as e:
            print(f"Error fetching option chain: {e}")
            return pd.DataFrame(), pd.DataFrame()

    def get_current_price(self) -> float:
        """Get current stock price."""
        try:
            return self.yf_ticker.history(period="1d")['Close'].iloc[-1]
        except Exception as e:
            print(f"Error fetching current price: {e}")
            return None

    def get_historical_prices(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch historical price data."""
        try:
            hist = self.yf_ticker.history(start=start_date, end=end_date)
            return hist
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return pd.DataFrame()

    def display_option_chain_summary(self, expiration_date: str, S: float):
        """Display a formatted summary of the option chain."""
        calls, puts = self.get_option_chain(expiration_date)

        if calls.empty or puts.empty:
            print("No options data available")
            return

        print(f"\n{'='*100}")
        print(f"OPTIONS CHAIN - {self.ticker} (Spot: ${S:.2f}) | Expiration: {expiration_date}")
        print(f"{'='*100}\n")

        # Filter for liquid options (volume > 0 or openInterest > 0)
        calls_liquid = calls[(calls['volume'] > 0) | (calls['openInterest'] > 0)]
        puts_liquid = puts[(puts['volume'] > 0) | (puts['openInterest'] > 0)]

        # Find ATM options
        atm_strike = calls_liquid.iloc[(calls_liquid['strike'] - S).abs().argsort()[:1]]['strike'].values[0]

        # Get nearby strikes
        nearby_strikes = sorted(calls_liquid['strike'].unique())
        atm_idx = nearby_strikes.index(atm_strike) if atm_strike in nearby_strikes else len(nearby_strikes)//2

        display_range = nearby_strikes[max(0, atm_idx-3):min(len(nearby_strikes), atm_idx+4)]

        print(f"{'Strike':<12} {'Call Bid':<12} {'Call Ask':<12} {'Call IV':<12} {'Put Bid':<12} {'Put Ask':<12} {'Put IV':<12} {'Moneyness':<12}")
        print("-" * 100)

        for strike in display_range:
            call_row = calls_liquid[calls_liquid['strike'] == strike]
            put_row = puts_liquid[puts_liquid['strike'] == strike]

            if not call_row.empty and not put_row.empty:
                moneyness = (S - strike) / strike * 100
                marker = " <-- ATM" if abs(moneyness) < 2 else ""

                print(f"${strike:<11.2f} "
                      f"${call_row['bid'].values[0]:<11.2f} "
                      f"${call_row['ask'].values[0]:<11.2f} "
                      f"{call_row['impliedVolatility'].values[0]*100:<11.1f}% "
                      f"${put_row['bid'].values[0]:<11.2f} "
                      f"${put_row['ask'].values[0]:<11.2f} "
                      f"{put_row['impliedVolatility'].values[0]*100:<11.1f}% "
                      f"{moneyness:>11.2f}%{marker}")

        print(f"\n{'='*100}\n")


class CRRLiveBacktester:
    """
    CRR Backtesting with real Yahoo Finance options data.
    """

    def __init__(
        self,
        ticker: str,
        initial_capital: float = 100000.0,
        min_edge: float = 0.02,
        transaction_cost: float = 0.005,  # 0.5% for options (realistic)
        kelly_fraction: float = 0.5,
        N_steps: int = 100,
        r: float = 0.053,
    ):
        self.ticker = ticker.upper()
        self.initial_capital = initial_capital
        self.min_edge = min_edge
        self.transaction_cost = transaction_cost
        self.kelly_fraction = kelly_fraction
        self.N_steps = N_steps
        self.r = r

        self.fetcher = LiveOptionsDataFetcher(ticker)

        # Results storage
        self.trades = []
        self.equity_history = []

    def calculate_realized_vol(self, prices: pd.Series, window: int = 30) -> float:
        """Calculate realized volatility from price series."""
        log_returns = np.log(prices / prices.shift(1)).dropna()
        rv = log_returns.tail(window).std() * np.sqrt(252)
        return float(rv)

    def get_mid_price(self, bid: float, ask: float) -> float:
        """Calculate mid price from bid-ask."""
        return (bid + ask) / 2.0

    def analyze_single_option(
        self,
        option_type: str,
        strike: float,
        expiration_date: str,
        S: float,
        rv: float,
        market_bid: float,
        market_ask: float,
        market_iv: float
    ) -> Dict:
        """
        Analyze a single option contract using CRR.

        Returns:
            Dictionary with pricing analysis
        """
        # Calculate time to expiration
        exp_dt = datetime.strptime(expiration_date, "%Y-%m-%d")
        today = datetime.now()
        T = (exp_dt - today).days / 365.0

        if T <= 0:
            return None

        # Market price (mid of bid-ask)
        V_market = self.get_mid_price(market_bid, market_ask)

        # CRR price with realized vol
        V_model_rv, _ = price_american_option(
            S, strike, self.r, rv, T, self.N_steps, option_type
        )

        # CRR price with implied vol (for validation)
        V_model_iv, _ = price_american_option(
            S, strike, self.r, market_iv, T, self.N_steps, option_type
        )

        # Calculate edges
        edge_rv = (V_model_rv - V_market) / V_market if V_market > 0 else 0
        edge_iv = (V_model_iv - V_market) / V_market if V_market > 0 else 0

        # Compute Greeks
        greeks = compute_greeks(S, strike, self.r, rv, T, self.N_steps, option_type)

        return {
            'option_type': option_type,
            'strike': strike,
            'T': T,
            'S': S,
            'rv': rv,
            'market_iv': market_iv,
            'market_bid': market_bid,
            'market_ask': market_ask,
            'V_market': V_market,
            'V_model_rv': V_model_rv,
            'V_model_iv': V_model_iv,
            'edge_rv': edge_rv,
            'edge_iv': edge_iv,
            'moneyness': (S - strike) / strike,
            'delta': greeks['delta'],
            'gamma': greeks['gamma'],
            'theta': greeks['theta'],
            'vega': greeks['vega'],
            'iv_rv_spread': market_iv - rv,
        }

    def analyze_full_chain(
        self,
        expiration_date: str,
        strikes_filter: str = 'liquid',  # 'all', 'liquid', 'atm', or list of strikes
        min_volume: int = 10
    ) -> pd.DataFrame:
        """
        Analyze entire option chain for mispricing opportunities.

        Args:
            expiration_date: Option expiration date
            strikes_filter: Which strikes to analyze
            min_volume: Minimum volume filter for liquidity

        Returns:
            DataFrame with analysis for all options
        """
        # Get current price
        S = self.fetcher.get_current_price()
        if S is None:
            print("Error: Could not fetch current price")
            return pd.DataFrame()

        # Get historical data for volatility
        hist = self.fetcher.get_historical_prices(
            start_date=(datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d")
        )

        if hist.empty:
            print("Error: Could not fetch historical data")
            return pd.DataFrame()

        rv = self.calculate_realized_vol(hist['Close'], window=30)

        print(f"\nCurrent Price: ${S:.2f}")
        print(f"30-Day Realized Vol: {rv*100:.2f}%")

        # Get option chain
        calls, puts = self.fetcher.get_option_chain(expiration_date)

        if calls.empty or puts.empty:
            print("Error: No options data available")
            return pd.DataFrame()

        # Filter for liquidity
        if strikes_filter == 'liquid':
            calls = calls[(calls['volume'] >= min_volume) | (calls['openInterest'] >= min_volume*5)]
            puts = puts[(puts['volume'] >= min_volume) | (puts['openInterest'] >= min_volume*5)]
        elif strikes_filter == 'atm':
            # Get ATM ± 10%
            lower = S * 0.90
            upper = S * 1.10
            calls = calls[(calls['strike'] >= lower) & (calls['strike'] <= upper)]
            puts = puts[(puts['strike'] >= lower) & (puts['strike'] <= upper)]

        # Analyze each option
        results = []

        print(f"\nAnalyzing {len(calls)} calls and {len(puts)} puts...")

        for _, row in calls.iterrows():
            analysis = self.analyze_single_option(
                'call', row['strike'], expiration_date, S, rv,
                row['bid'], row['ask'], row['impliedVolatility']
            )
            if analysis:
                analysis['volume'] = row['volume']
                analysis['openInterest'] = row['openInterest']
                results.append(analysis)

        for _, row in puts.iterrows():
            analysis = self.analyze_single_option(
                'put', row['strike'], expiration_date, S, rv,
                row['bid'], row['ask'], row['impliedVolatility']
            )
            if analysis:
                analysis['volume'] = row['volume']
                analysis['openInterest'] = row['openInterest']
                results.append(analysis)

        df = pd.DataFrame(results)

        if not df.empty:
            # Sort by absolute edge
            df['abs_edge_rv'] = df['edge_rv'].abs()
            df = df.sort_values('abs_edge_rv', ascending=False)

        return df

    def find_best_opportunities(
        self,
        expiration_date: str,
        top_n: int = 10,
        min_volume: int = 10
    ) -> pd.DataFrame:
        """Find top trading opportunities based on edge."""

        df = self.analyze_full_chain(expiration_date, strikes_filter='liquid', min_volume=min_volume)

        if df.empty:
            return df

        # Filter out deep OTM options with very low prices (likely illiquid/unreliable)
        df = df[df['V_market'] >= 1.00].copy()

        # Filter out options with unrealistic IVs
        df = df[(df['market_iv'] > 0.10) & (df['market_iv'] < 2.0)].copy()

        # Focus on options within reasonable moneyness range (-30% to +30%)
        df = df[(df['moneyness'] >= -0.30) & (df['moneyness'] <= 0.30)].copy()

        # Filter by minimum edge
        opportunities = df[df['abs_edge_rv'] >= self.min_edge].copy()

        # Determine action
        opportunities['action'] = opportunities['edge_rv'].apply(
            lambda x: 'BUY' if x > 0 else 'SELL'
        )

        # Kelly sizing
        def compute_position_size(row):
            p_win = 0.50 + row['edge_rv'] / 2.0
            p_win = np.clip(p_win, 0.01, 0.99)

            fracs = kelly_fractions(p_win, b=1.0)
            f_kelly = fracs['f_half'] if self.kelly_fraction == 0.5 else fracs['f_quarter']

            dollar_size = self.initial_capital * f_kelly
            contracts = int(dollar_size / (row['V_market'] * 100)) if row['V_market'] > 0 else 0

            return pd.Series({
                'p_win': p_win,
                'f_kelly': f_kelly,
                'dollar_size': dollar_size,
                'contracts': max(1, contracts)  # At least 1 contract
            })

        opportunities[['p_win', 'f_kelly', 'dollar_size', 'contracts']] = \
            opportunities.apply(compute_position_size, axis=1)

        # Calculate expected P&L
        opportunities['expected_pnl'] = opportunities['edge_rv'] * opportunities['V_market'] * opportunities['contracts'] * 100

        return opportunities.head(top_n)

    def display_opportunities(self, opps_df: pd.DataFrame):
        """Display trading opportunities in formatted table."""

        if opps_df.empty:
            print("\n⚠️  No opportunities found meeting criteria")
            return

        print(f"\n{'='*150}")
        print(f"TOP TRADING OPPORTUNITIES - {self.ticker}")
        print(f"{'='*150}\n")

        print(f"{'Type':<6} {'Strike':<10} {'Action':<8} {'Edge':<10} {'Model':<10} {'Market':<10} "
              f"{'Contracts':<12} {'$Size':<12} {'IV':<8} {'RV':<8} {'Volume':<10}")
        print("-" * 150)

        for _, row in opps_df.iterrows():
            # Handle NaN values gracefully
            volume = int(row['volume']) if pd.notna(row['volume']) else 0

            print(f"{row['option_type']:<6} "
                  f"${row['strike']:<9.2f} "
                  f"{row['action']:<8} "
                  f"{row['edge_rv']*100:>8.2f}% "
                  f"${row['V_model_rv']:<9.2f} "
                  f"${row['V_market']:<9.2f} "
                  f"{row['contracts']:<12} "
                  f"${row['dollar_size']:<11,.0f} "
                  f"{row['market_iv']*100:<7.1f}% "
                  f"{row['rv']*100:<7.1f}% "
                  f"{volume:<10}")

        print(f"\n{'='*150}\n")

        # Summary statistics
        total_capital_allocated = opps_df['dollar_size'].sum()
        total_expected_pnl = opps_df['expected_pnl'].sum()

        print(f"Summary:")
        print(f"  Total Opportunities: {len(opps_df)}")
        print(f"  Buy Signals: {len(opps_df[opps_df['action'] == 'BUY'])}")
        print(f"  Sell Signals: {len(opps_df[opps_df['action'] == 'SELL'])}")
        print(f"  Total Capital Allocated: ${total_capital_allocated:,.2f}")
        print(f"  Expected Total P&L: ${total_expected_pnl:,.2f}")
        print(f"  Portfolio Utilization: {total_capital_allocated/self.initial_capital*100:.1f}%")
        print()

    def plot_edge_analysis(self, df: pd.DataFrame, output_dir: str = "outputs"):
        """Create visualization of edge analysis."""

        if df.empty:
            return

        Path(output_dir).mkdir(exist_ok=True)

        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle(f'CRR Edge Analysis - {self.ticker}', fontsize=16, fontweight='bold')

        # 1. Edge vs Strike
        ax1 = axes[0, 0]
        calls = df[df['option_type'] == 'call']
        puts = df[df['option_type'] == 'put']

        if not calls.empty:
            ax1.scatter(calls['strike'], calls['edge_rv']*100, alpha=0.6, s=100, label='Calls', marker='o')
        if not puts.empty:
            ax1.scatter(puts['strike'], puts['edge_rv']*100, alpha=0.6, s=100, label='Puts', marker='^')

        ax1.axhline(0, color='black', linestyle='--', alpha=0.5)
        ax1.axhline(self.min_edge*100, color='green', linestyle='--', alpha=0.5, label='Min Edge Threshold')
        ax1.axhline(-self.min_edge*100, color='red', linestyle='--', alpha=0.5)
        ax1.set_xlabel('Strike Price ($)')
        ax1.set_ylabel('Edge (%)')
        ax1.set_title('Edge vs Strike')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # 2. Model vs Market Price
        ax2 = axes[0, 1]
        ax2.scatter(df['V_market'], df['V_model_rv'], alpha=0.6, s=50)
        max_price = max(df['V_market'].max(), df['V_model_rv'].max())
        ax2.plot([0, max_price], [0, max_price], 'r--', alpha=0.5, label='Perfect Agreement')
        ax2.set_xlabel('Market Price ($)')
        ax2.set_ylabel('CRR Model Price ($)')
        ax2.set_title('Model vs Market Prices')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # 3. IV vs RV Spread
        ax3 = axes[0, 2]
        ax3.scatter(df['strike'], df['iv_rv_spread']*100, alpha=0.6, s=50, c=df['edge_rv'], cmap='RdYlGn')
        ax3.axhline(0, color='black', linestyle='--', alpha=0.5)
        ax3.set_xlabel('Strike Price ($)')
        ax3.set_ylabel('IV - RV Spread (%)')
        ax3.set_title('Implied Vol Premium over Realized Vol')
        ax3.grid(True, alpha=0.3)

        # 4. Edge Distribution
        ax4 = axes[1, 0]
        ax4.hist(df['edge_rv']*100, bins=30, alpha=0.7, edgecolor='black')
        ax4.axvline(0, color='red', linestyle='--', linewidth=2)
        ax4.set_xlabel('Edge (%)')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Edge Distribution')
        ax4.grid(True, alpha=0.3)

        # 5. Volume vs Edge
        ax5 = axes[1, 1]
        scatter = ax5.scatter(df['volume'], df['edge_rv']*100, alpha=0.6, s=100,
                             c=df['openInterest'], cmap='viridis')
        ax5.set_xlabel('Volume')
        ax5.set_ylabel('Edge (%)')
        ax5.set_title('Trading Volume vs Edge')
        ax5.set_xscale('log')
        ax5.axhline(0, color='black', linestyle='--', alpha=0.5)
        plt.colorbar(scatter, ax=ax5, label='Open Interest')
        ax5.grid(True, alpha=0.3)

        # 6. Delta vs Edge
        ax6 = axes[1, 2]
        if not calls.empty:
            ax6.scatter(calls['delta'], calls['edge_rv']*100, alpha=0.6, s=100, label='Calls', marker='o')
        if not puts.empty:
            ax6.scatter(puts['delta'], puts['edge_rv']*100, alpha=0.6, s=100, label='Puts', marker='^')
        ax6.axhline(0, color='black', linestyle='--', alpha=0.5)
        ax6.set_xlabel('Delta')
        ax6.set_ylabel('Edge (%)')
        ax6.set_title('Delta vs Edge')
        ax6.legend()
        ax6.grid(True, alpha=0.3)

        plt.tight_layout()

        output_path = Path(output_dir) / f'{self.ticker}_edge_analysis.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved edge analysis plot to {output_path}")

        plt.show()


def interactive_menu():
    """Interactive menu for user to select stock and options."""

    print("\n" + "="*80)
    print("CRR OPTIONS BACKTESTER - Interactive Mode")
    print("="*80 + "\n")

    # Get ticker
    while True:
        ticker = input("Enter stock ticker (e.g., AAPL, TSLA, AMD): ").strip().upper()
        if ticker:
            break
        print("Please enter a valid ticker symbol")

    # Initialize fetcher
    fetcher = LiveOptionsDataFetcher(ticker)

    # Get current price
    S = fetcher.get_current_price()
    if S is None:
        print(f"Error: Could not fetch data for {ticker}")
        return None

    print(f"\n✓ {ticker} - Current Price: ${S:.2f}")

    # Get available expirations
    expirations = fetcher.get_available_expirations()
    if not expirations:
        print(f"Error: No options data available for {ticker}")
        return None

    print(f"\nAvailable Expirations ({len(expirations)} dates):")
    for i, exp in enumerate(expirations[:10], 1):  # Show first 10
        days_to_exp = (datetime.strptime(exp, "%Y-%m-%d") - datetime.now()).days
        print(f"  {i}. {exp} ({days_to_exp} days)")

    if len(expirations) > 10:
        print(f"  ... and {len(expirations)-10} more dates")

    # Select expiration
    while True:
        choice = input(f"\nSelect expiration (1-{min(10, len(expirations))}) or enter date (YYYY-MM-DD): ").strip()

        if choice.isdigit() and 1 <= int(choice) <= min(10, len(expirations)):
            expiration = expirations[int(choice)-1]
            break
        elif choice in expirations:
            expiration = choice
            break
        else:
            print("Invalid selection. Please try again.")

    print(f"\n✓ Selected expiration: {expiration}")

    # Display option chain
    fetcher.display_option_chain_summary(expiration, S)

    # Get backtest parameters
    print("\nBacktest Parameters:")

    capital = input("Initial capital (default: $100,000): ").strip()
    capital = float(capital) if capital else 100000.0

    min_edge = input("Minimum edge threshold % (default: 2%): ").strip()
    min_edge = float(min_edge)/100 if min_edge else 0.02

    kelly_choice = input("Kelly fraction (1=full, 2=half, 3=quarter, default: half): ").strip()
    kelly_map = {'1': 1.0, '2': 0.5, '3': 0.25}
    kelly_fraction = kelly_map.get(kelly_choice, 0.5)

    min_volume = input("Minimum volume filter (default: 10): ").strip()
    min_volume = int(min_volume) if min_volume else 10

    return {
        'ticker': ticker,
        'expiration': expiration,
        'capital': capital,
        'min_edge': min_edge,
        'kelly_fraction': kelly_fraction,
        'min_volume': min_volume
    }


def main():
    """Main execution function."""

    # Interactive mode
    params = interactive_menu()

    if params is None:
        print("\nExiting...")
        return

    # Initialize backtester
    backtester = CRRLiveBacktester(
        ticker=params['ticker'],
        initial_capital=params['capital'],
        min_edge=params['min_edge'],
        kelly_fraction=params['kelly_fraction']
    )

    print(f"\n{'='*80}")
    print("ANALYZING OPTIONS CHAIN WITH CRR MODEL")
    print(f"{'='*80}\n")

    # Find opportunities
    opportunities = backtester.find_best_opportunities(
        expiration_date=params['expiration'],
        top_n=20,
        min_volume=params['min_volume']
    )

    # Display results
    backtester.display_opportunities(opportunities)

    # Get full analysis for plotting
    full_analysis = backtester.analyze_full_chain(
        params['expiration'],
        strikes_filter='liquid',
        min_volume=params['min_volume']
    )

    # Plot
    if not full_analysis.empty:
        backtester.plot_edge_analysis(full_analysis)

        # Save to CSV
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)

        opportunities.to_csv(output_dir / f"{params['ticker']}_opportunities.csv", index=False)
        full_analysis.to_csv(output_dir / f"{params['ticker']}_full_analysis.csv", index=False)

        print(f"\n✓ Results saved to outputs/")
        print(f"  - {params['ticker']}_opportunities.csv")
        print(f"  - {params['ticker']}_full_analysis.csv")
        print(f"  - {params['ticker']}_edge_analysis.png")


if __name__ == "__main__":
    main()

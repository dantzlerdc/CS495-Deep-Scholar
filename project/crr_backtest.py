"""
CRR Backtesting Engine with Daily Performance Evaluation

This script performs walk-forward backtesting of the CRR binomial pricing model
using real historical data. It evaluates trading performance by:

1. Fetching historical options data and underlying prices
2. Computing CRR fair values daily with realized volatility
3. Identifying mispricing opportunities (edge detection)
4. Sizing positions using Kelly Criterion
5. Simulating trade execution with realistic costs
6. Computing comprehensive performance metrics
7. Generating detailed visualization plots

Performance Metrics:
- Total return, annualized return, Sharpe ratio
- Maximum drawdown, Calmar ratio
- Win rate, profit factor, average win/loss
- Greeks exposure over time

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
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Import core CRR modules
from tree import price_american_option
from greeks import compute_greeks
from kelly import kelly_fractions

# Set plotting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class CRRBacktester:
    """
    Walk-forward backtesting engine for CRR option pricing strategy.

    Attributes:
        ticker: Underlying stock symbol
        initial_capital: Starting portfolio value
        min_edge: Minimum edge threshold for trade entry (%)
        transaction_cost: Round-trip transaction cost (%)
        kelly_fraction: Kelly multiplier (0.5 = half-Kelly, 0.25 = quarter-Kelly)
        N_steps: Number of binomial tree steps
        r: Risk-free rate (annualized)
    """

    def __init__(
        self,
        ticker: str = "AMD",
        initial_capital: float = 100000.0,
        min_edge: float = 0.02,
        transaction_cost: float = 0.001,
        kelly_fraction: float = 0.5,
        N_steps: int = 100,
        r: float = 0.053,
    ):
        self.ticker = ticker
        self.initial_capital = initial_capital
        self.min_edge = min_edge
        self.transaction_cost = transaction_cost
        self.kelly_fraction = kelly_fraction
        self.N_steps = N_steps
        self.r = r

        # Results storage
        self.trades = []
        self.daily_equity = []
        self.daily_positions = []
        self.daily_greeks = []

    def fetch_historical_data(
        self,
        start_date: str,
        end_date: str,
        lookback_days: int = 30
    ) -> pd.DataFrame:
        """
        Fetch historical price data for the underlying asset.

        Args:
            start_date: Backtest start date (YYYY-MM-DD)
            end_date: Backtest end date (YYYY-MM-DD)
            lookback_days: Days before start_date to fetch for vol calculation

        Returns:
            DataFrame with columns: Date, Close, Returns, RV30
        """
        # Fetch extra data for initial volatility calculation
        lookback_start = (
            datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=lookback_days+60)
        ).strftime("%Y-%m-%d")

        print(f"Fetching {self.ticker} data from {lookback_start} to {end_date}...")
        ticker_obj = yf.Ticker(self.ticker)
        hist = ticker_obj.history(start=lookback_start, end=end_date)

        if hist.empty:
            raise ValueError(f"No data found for {self.ticker}")

        # Calculate log returns
        hist['Returns'] = np.log(hist['Close'] / hist['Close'].shift(1))

        # Calculate rolling 30-day realized volatility (annualized)
        hist['RV30'] = hist['Returns'].rolling(window=30).std() * np.sqrt(252)

        # Calculate rolling 60-day realized volatility
        hist['RV60'] = hist['Returns'].rolling(window=60).std() * np.sqrt(252)

        # Drop NaN values
        hist = hist.dropna()

        # Filter to backtest period
        hist = hist[hist.index >= start_date]

        print(f"Loaded {len(hist)} trading days")
        print(f"Date range: {hist.index[0].date()} to {hist.index[-1].date()}")
        print(f"Price range: ${hist['Close'].min():.2f} - ${hist['Close'].max():.2f}")

        return hist

    def generate_synthetic_option_chain(
        self,
        S: float,
        date: pd.Timestamp,
        expiry_days: int = 30
    ) -> pd.DataFrame:
        """
        Generate synthetic option chain with multiple strikes.

        In production, this would fetch real options data from a provider.
        For backtesting, we generate realistic strikes around current price.

        Args:
            S: Current stock price
            date: Current date
            expiry_days: Days to expiration

        Returns:
            DataFrame with option chain data
        """
        # Generate strikes: 90%, 95%, 100%, 105%, 110% of current price
        strikes = [S * mult for mult in [0.90, 0.95, 1.00, 1.05, 1.10]]

        T = expiry_days / 365.0
        expiry_date = date + pd.Timedelta(days=expiry_days)

        chain_data = []
        for K in strikes:
            for option_type in ['call', 'put']:
                # Estimate market IV using volatility smile (simplified)
                moneyness = S / K
                base_iv = 0.60  # Base IV for ATM

                # Volatility smile: OTM options have higher IV
                if option_type == 'call':
                    iv_adjustment = 0.05 * max(0, moneyness - 1.0)
                else:
                    iv_adjustment = 0.05 * max(0, 1.0 - moneyness)

                market_iv = base_iv + iv_adjustment + np.random.normal(0, 0.02)
                market_iv = max(0.20, min(1.20, market_iv))  # Clamp to realistic range

                # Price with market IV to get "market price"
                V_market, _ = price_american_option(
                    S, K, self.r, market_iv, T, self.N_steps, option_type
                )

                chain_data.append({
                    'date': date,
                    'expiry_date': expiry_date,
                    'option_type': option_type,
                    'K': K,
                    'S': S,
                    'T': T,
                    'market_iv': market_iv,
                    'V_market': V_market,
                    'moneyness': (S - K) / K,
                })

        return pd.DataFrame(chain_data)

    def compute_edge(
        self,
        S: float,
        K: float,
        r: float,
        sigma_model: float,
        T: float,
        option_type: str,
        V_market: float
    ) -> Tuple[float, float]:
        """
        Compute CRR model price and edge versus market.

        Args:
            S: Spot price
            K: Strike price
            r: Risk-free rate
            sigma_model: Model volatility (typically realized vol)
            T: Time to expiry (years)
            option_type: 'call' or 'put'
            V_market: Market price of option

        Returns:
            (V_model, edge) where edge = (V_model - V_market) / V_market
        """
        V_model, _ = price_american_option(
            S, K, r, sigma_model, T, self.N_steps, option_type
        )

        edge = (V_model - V_market) / V_market if V_market > 0 else 0.0

        return V_model, edge

    def edge_to_win_prob(self, edge: float, action: str) -> float:
        """
        Convert edge to win probability for Kelly sizing.

        This is a heuristic mapping. In production, use historical calibration.

        Args:
            edge: Relative mispricing (positive = model > market)
            action: 'buy' or 'sell'

        Returns:
            Estimated win probability [0.01, 0.99]
        """
        # For buy: positive edge means we think it's underpriced
        # For sell: negative edge means we think it's overpriced

        if action == 'buy':
            # Positive edge → higher win probability
            p_win = 0.50 + edge / 2.0
        else:  # sell
            # Negative edge → higher win probability for selling
            p_win = 0.50 - edge / 2.0

        return np.clip(p_win, 0.01, 0.99)

    def size_position(
        self,
        edge: float,
        action: str,
        capital: float,
        V_option: float
    ) -> float:
        """
        Compute position size using Kelly Criterion.

        Args:
            edge: Mispricing edge
            action: 'buy' or 'sell'
            capital: Available capital
            V_option: Option price

        Returns:
            Number of contracts to trade
        """
        p_win = self.edge_to_win_prob(edge, action)

        # Kelly formula: f* = (p*b - q) / b, where b=1 (even odds approximation)
        fracs = kelly_fractions(p_win, b=1.0)

        # Use fractional Kelly based on self.kelly_fraction
        if self.kelly_fraction == 0.5:
            f_kelly = fracs["f_half"]
        elif self.kelly_fraction == 0.25:
            f_kelly = fracs["f_quarter"]
        else:
            f_kelly = fracs["f_full"] * self.kelly_fraction

        # Convert to dollar position
        dollar_position = capital * f_kelly

        # Convert to number of contracts (1 contract = 100 shares typically)
        # For simplicity, trade in units of option price
        n_contracts = dollar_position / (V_option * 100) if V_option > 0 else 0

        return max(0, int(n_contracts))

    def run_backtest(
        self,
        start_date: str,
        end_date: str,
        expiry_days: int = 30,
        rebalance_days: int = 5
    ) -> pd.DataFrame:
        """
        Execute walk-forward backtest.

        Strategy:
        1. Every rebalance_days, scan option chain for mispricing
        2. Compute edge using CRR with realized volatility
        3. Enter trades with positive edge above min_edge threshold
        4. Exit at expiration or when edge reverses
        5. Track P&L daily including theta decay

        Args:
            start_date: Backtest start (YYYY-MM-DD)
            end_date: Backtest end (YYYY-MM-DD)
            expiry_days: Option expiry in days
            rebalance_days: Days between portfolio rebalancing

        Returns:
            DataFrame with daily performance metrics
        """
        print(f"\n{'='*80}")
        print(f"CRR BACKTEST: {self.ticker} from {start_date} to {end_date}")
        print(f"{'='*80}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        print(f"Min Edge Threshold: {self.min_edge*100:.1f}%")
        print(f"Kelly Fraction: {self.kelly_fraction}")
        print(f"Transaction Cost: {self.transaction_cost*100:.2f}%")
        print(f"CRR Steps: {self.N_steps}")
        print(f"Risk-Free Rate: {self.r*100:.1f}%")
        print(f"{'='*80}\n")

        # Fetch historical data
        hist_data = self.fetch_historical_data(start_date, end_date)

        # Initialize portfolio
        capital = self.initial_capital
        positions = []  # List of open positions

        # Daily loop
        rebalance_counter = 0

        for i, (date, row) in enumerate(hist_data.iterrows()):
            S = row['Close']
            rv30 = row['RV30']

            # Daily P&L from existing positions (mark-to-market + theta decay)
            daily_pnl = 0.0

            # Update existing positions
            updated_positions = []
            for pos in positions:
                # Calculate days to expiry
                days_to_expiry = (pos['expiry_date'] - date).days
                T_remaining = max(days_to_expiry / 365.0, 0.0001)

                # Mark to market
                if days_to_expiry <= 0:
                    # Option expired
                    if pos['option_type'] == 'call':
                        intrinsic = max(S - pos['K'], 0)
                    else:
                        intrinsic = max(pos['K'] - S, 0)

                    pnl = pos['n_contracts'] * 100 * (intrinsic - pos['entry_price'])
                    if pos['action'] == 'sell':
                        pnl = -pnl

                    daily_pnl += pnl

                    self.trades.append({
                        'entry_date': pos['entry_date'],
                        'exit_date': date,
                        'option_type': pos['option_type'],
                        'action': pos['action'],
                        'K': pos['K'],
                        'entry_price': pos['entry_price'],
                        'exit_price': intrinsic,
                        'n_contracts': pos['n_contracts'],
                        'pnl': pnl,
                        'exit_reason': 'expiration'
                    })
                else:
                    # Re-price option
                    V_current, _ = price_american_option(
                        S, pos['K'], self.r, rv30, T_remaining,
                        self.N_steps, pos['option_type']
                    )

                    pos['current_price'] = V_current

                    # Calculate unrealized P&L
                    unrealized_pnl = pos['n_contracts'] * 100 * (V_current - pos['entry_price'])
                    if pos['action'] == 'sell':
                        unrealized_pnl = -unrealized_pnl

                    pos['unrealized_pnl'] = unrealized_pnl

                    # Keep position open
                    updated_positions.append(pos)

            positions = updated_positions

            # Update capital
            capital += daily_pnl

            # Rebalancing logic
            if rebalance_counter % rebalance_days == 0 and i > 0:
                # Close existing positions (simplified: close all)
                for pos in positions:
                    pnl = pos['unrealized_pnl']
                    # Apply transaction costs
                    cost = abs(pnl) * self.transaction_cost
                    daily_pnl += pnl - cost
                    capital += pnl - cost

                    self.trades.append({
                        'entry_date': pos['entry_date'],
                        'exit_date': date,
                        'option_type': pos['option_type'],
                        'action': pos['action'],
                        'K': pos['K'],
                        'entry_price': pos['entry_price'],
                        'exit_price': pos['current_price'],
                        'n_contracts': pos['n_contracts'],
                        'pnl': pnl - cost,
                        'exit_reason': 'rebalance'
                    })

                positions = []

                # Scan for new opportunities
                chain = self.generate_synthetic_option_chain(S, date, expiry_days)

                opportunities = []
                for _, opt in chain.iterrows():
                    V_model, edge = self.compute_edge(
                        opt['S'], opt['K'], self.r, rv30,
                        opt['T'], opt['option_type'], opt['V_market']
                    )

                    # Determine action based on edge
                    if edge > self.min_edge:
                        # Model > Market → Buy (market is cheap)
                        action = 'buy'
                        opportunities.append({
                            'option_type': opt['option_type'],
                            'K': opt['K'],
                            'V_market': opt['V_market'],
                            'V_model': V_model,
                            'edge': edge,
                            'action': action,
                            'expiry_date': opt['expiry_date'],
                            'T': opt['T']
                        })
                    elif edge < -self.min_edge:
                        # Model < Market → Sell (market is expensive)
                        action = 'sell'
                        opportunities.append({
                            'option_type': opt['option_type'],
                            'K': opt['K'],
                            'V_market': opt['V_market'],
                            'V_model': V_model,
                            'edge': edge,
                            'action': action,
                            'expiry_date': opt['expiry_date'],
                            'T': opt['T']
                        })

                # Rank by absolute edge and take top opportunities
                if opportunities:
                    opps_df = pd.DataFrame(opportunities)
                    opps_df['abs_edge'] = opps_df['edge'].abs()
                    opps_df = opps_df.sort_values('abs_edge', ascending=False)

                    # Take top 3 opportunities (diversify)
                    top_opps = opps_df.head(3)

                    # Allocate capital equally among opportunities
                    capital_per_opp = capital / len(top_opps)

                    for _, opp in top_opps.iterrows():
                        n_contracts = self.size_position(
                            opp['edge'],
                            opp['action'],
                            capital_per_opp,
                            opp['V_market']
                        )

                        if n_contracts > 0:
                            # Enter position
                            entry_cost = n_contracts * 100 * opp['V_market']
                            transaction_fee = entry_cost * self.transaction_cost

                            positions.append({
                                'entry_date': date,
                                'option_type': opp['option_type'],
                                'action': opp['action'],
                                'K': opp['K'],
                                'entry_price': opp['V_market'],
                                'current_price': opp['V_market'],
                                'n_contracts': n_contracts,
                                'edge': opp['edge'],
                                'expiry_date': opp['expiry_date'],
                                'unrealized_pnl': 0.0
                            })

                            # Deduct transaction costs
                            capital -= transaction_fee

            rebalance_counter += 1

            # Record daily state
            total_unrealized = sum([p['unrealized_pnl'] for p in positions])
            equity = capital + total_unrealized

            self.daily_equity.append({
                'date': date,
                'capital': capital,
                'unrealized_pnl': total_unrealized,
                'equity': equity,
                'n_positions': len(positions),
                'S': S,
                'rv30': rv30
            })

        # Close any remaining positions at end
        for pos in positions:
            pnl = pos['unrealized_pnl']
            cost = abs(pnl) * self.transaction_cost

            self.trades.append({
                'entry_date': pos['entry_date'],
                'exit_date': hist_data.index[-1],
                'option_type': pos['option_type'],
                'action': pos['action'],
                'K': pos['K'],
                'entry_price': pos['entry_price'],
                'exit_price': pos['current_price'],
                'n_contracts': pos['n_contracts'],
                'pnl': pnl - cost,
                'exit_reason': 'end_of_backtest'
            })

        # Convert to DataFrames
        equity_df = pd.DataFrame(self.daily_equity)
        trades_df = pd.DataFrame(self.trades)

        print(f"\nBacktest Complete!")
        print(f"Total trades executed: {len(trades_df)}")
        print(f"Final equity: ${equity_df['equity'].iloc[-1]:,.2f}")

        return equity_df, trades_df

    def compute_performance_metrics(
        self,
        equity_df: pd.DataFrame,
        trades_df: pd.DataFrame
    ) -> Dict:
        """
        Compute comprehensive performance metrics.

        Returns:
            Dictionary with performance statistics
        """
        # Total return
        initial = self.initial_capital
        final = equity_df['equity'].iloc[-1]
        total_return = (final - initial) / initial

        # Annualized return
        days = len(equity_df)
        years = days / 252.0
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # Daily returns
        equity_df['returns'] = equity_df['equity'].pct_change()
        daily_returns = equity_df['returns'].dropna()

        # Sharpe ratio (assuming r_f from daily risk-free rate)
        daily_rf = self.r / 252.0
        excess_returns = daily_returns - daily_rf
        sharpe = np.sqrt(252) * excess_returns.mean() / excess_returns.std() if excess_returns.std() > 0 else 0

        # Maximum drawdown
        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        # Calmar ratio
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0

        # Trade statistics
        if len(trades_df) > 0:
            winning_trades = trades_df[trades_df['pnl'] > 0]
            losing_trades = trades_df[trades_df['pnl'] < 0]

            win_rate = len(winning_trades) / len(trades_df)
            avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
            avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0

            profit_factor = abs(winning_trades['pnl'].sum() / losing_trades['pnl'].sum()) if losing_trades['pnl'].sum() != 0 else np.inf

            total_pnl = trades_df['pnl'].sum()
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            profit_factor = 0
            total_pnl = 0

        metrics = {
            'initial_capital': initial,
            'final_equity': final,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'calmar_ratio': calmar,
            'total_trades': len(trades_df),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'total_pnl': total_pnl,
            'trading_days': days,
            'years': years
        }

        return metrics

    def print_performance_report(self, metrics: Dict):
        """Print formatted performance report."""
        print(f"\n{'='*80}")
        print(f"PERFORMANCE REPORT - {self.ticker}")
        print(f"{'='*80}")
        print(f"\nPortfolio Performance:")
        print(f"  Initial Capital:        ${metrics['initial_capital']:>15,.2f}")
        print(f"  Final Equity:           ${metrics['final_equity']:>15,.2f}")
        print(f"  Total Return:           {metrics['total_return']:>15.2%}")
        print(f"  Annualized Return:      {metrics['annual_return']:>15.2%}")

        print(f"\nRisk Metrics:")
        print(f"  Sharpe Ratio:           {metrics['sharpe_ratio']:>15.2f}")
        print(f"  Maximum Drawdown:       {metrics['max_drawdown']:>15.2%}")
        print(f"  Calmar Ratio:           {metrics['calmar_ratio']:>15.2f}")

        print(f"\nTrading Statistics:")
        print(f"  Total Trades:           {metrics['total_trades']:>15}")
        print(f"  Win Rate:               {metrics['win_rate']:>15.2%}")
        print(f"  Average Win:            ${metrics['avg_win']:>15,.2f}")
        print(f"  Average Loss:           ${metrics['avg_loss']:>15,.2f}")
        print(f"  Profit Factor:          {metrics['profit_factor']:>15.2f}")
        print(f"  Total P&L:              ${metrics['total_pnl']:>15,.2f}")

        print(f"\nBacktest Period:")
        print(f"  Trading Days:           {metrics['trading_days']:>15}")
        print(f"  Years:                  {metrics['years']:>15.2f}")
        print(f"{'='*80}\n")

    def plot_results(
        self,
        equity_df: pd.DataFrame,
        trades_df: pd.DataFrame,
        output_dir: str = "outputs"
    ):
        """Generate comprehensive visualization plots."""
        Path(output_dir).mkdir(exist_ok=True)

        # Set up the plot style
        plt.rcParams['figure.figsize'] = (16, 12)
        plt.rcParams['font.size'] = 10

        # Create 3x2 subplot layout
        fig, axes = plt.subplots(3, 2, figsize=(16, 12))
        fig.suptitle(f'CRR Backtest Results - {self.ticker}', fontsize=16, fontweight='bold')

        # 1. Equity Curve
        ax1 = axes[0, 0]
        ax1.plot(equity_df['date'], equity_df['equity'], linewidth=2, label='Portfolio Equity')
        ax1.axhline(self.initial_capital, color='red', linestyle='--', alpha=0.7, label='Initial Capital')
        ax1.fill_between(equity_df['date'], self.initial_capital, equity_df['equity'],
                          where=equity_df['equity'] >= self.initial_capital, alpha=0.3, color='green')
        ax1.fill_between(equity_df['date'], self.initial_capital, equity_df['equity'],
                          where=equity_df['equity'] < self.initial_capital, alpha=0.3, color='red')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Equity ($)')
        ax1.set_title('Portfolio Equity Curve')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)

        # 2. Drawdown
        ax2 = axes[0, 1]
        equity_df['returns'] = equity_df['equity'].pct_change()
        cumulative = (1 + equity_df['returns'].fillna(0)).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        ax2.fill_between(equity_df['date'], 0, drawdown * 100, alpha=0.6, color='red')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Drawdown (%)')
        ax2.set_title('Drawdown Over Time')
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)

        # 3. Underlying Price
        ax3 = axes[1, 0]
        ax3.plot(equity_df['date'], equity_df['S'], linewidth=2, color='blue')
        ax3.set_xlabel('Date')
        ax3.set_ylabel('Stock Price ($)')
        ax3.set_title(f'{self.ticker} Price History')
        ax3.grid(True, alpha=0.3)
        ax3.tick_params(axis='x', rotation=45)

        # 4. Realized Volatility
        ax4 = axes[1, 1]
        ax4.plot(equity_df['date'], equity_df['rv30'] * 100, linewidth=2, color='orange', label='RV30')
        ax4.set_xlabel('Date')
        ax4.set_ylabel('Volatility (%)')
        ax4.set_title('30-Day Realized Volatility')
        ax4.grid(True, alpha=0.3)
        ax4.legend()
        ax4.tick_params(axis='x', rotation=45)

        # 5. Win/Loss Distribution
        ax5 = axes[2, 0]
        if len(trades_df) > 0:
            wins = trades_df[trades_df['pnl'] > 0]['pnl']
            losses = trades_df[trades_df['pnl'] < 0]['pnl']

            ax5.hist(wins, bins=20, alpha=0.6, color='green', label=f'Wins (n={len(wins)})')
            ax5.hist(losses, bins=20, alpha=0.6, color='red', label=f'Losses (n={len(losses)})')
            ax5.axvline(0, color='black', linestyle='--', linewidth=2)
            ax5.set_xlabel('P&L ($)')
            ax5.set_ylabel('Frequency')
            ax5.set_title('Trade P&L Distribution')
            ax5.legend()
            ax5.grid(True, alpha=0.3)

        # 6. Cumulative P&L
        ax6 = axes[2, 1]
        if len(trades_df) > 0:
            trades_df_sorted = trades_df.sort_values('exit_date')
            trades_df_sorted['cumulative_pnl'] = trades_df_sorted['pnl'].cumsum()
            ax6.plot(trades_df_sorted['exit_date'], trades_df_sorted['cumulative_pnl'],
                     linewidth=2, marker='o', markersize=4, color='purple')
            ax6.axhline(0, color='black', linestyle='--', alpha=0.7)
            ax6.fill_between(trades_df_sorted['exit_date'], 0, trades_df_sorted['cumulative_pnl'],
                              where=trades_df_sorted['cumulative_pnl'] >= 0, alpha=0.3, color='green')
            ax6.fill_between(trades_df_sorted['exit_date'], 0, trades_df_sorted['cumulative_pnl'],
                              where=trades_df_sorted['cumulative_pnl'] < 0, alpha=0.3, color='red')
            ax6.set_xlabel('Date')
            ax6.set_ylabel('Cumulative P&L ($)')
            ax6.set_title('Cumulative Trade P&L')
            ax6.grid(True, alpha=0.3)
            ax6.tick_params(axis='x', rotation=45)

        plt.tight_layout()

        # Save figure
        output_path = Path(output_dir) / 'crr_backtest_results.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved plot to {output_path}")

        plt.show()

        # Additional plot: Monthly returns heatmap
        self.plot_monthly_returns(equity_df, output_dir)

    def plot_monthly_returns(self, equity_df: pd.DataFrame, output_dir: str):
        """Generate monthly returns heatmap."""
        equity_df = equity_df.copy()
        equity_df['returns'] = equity_df['equity'].pct_change()
        equity_df['year'] = equity_df['date'].dt.year
        equity_df['month'] = equity_df['date'].dt.month

        # Calculate monthly returns
        monthly = equity_df.groupby(['year', 'month'])['returns'].apply(
            lambda x: (1 + x).prod() - 1
        ).unstack(fill_value=0)

        if len(monthly) > 0:
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.heatmap(monthly * 100, annot=True, fmt='.2f', cmap='RdYlGn',
                        center=0, cbar_kws={'label': 'Return (%)'}, ax=ax)
            ax.set_xlabel('Month')
            ax.set_ylabel('Year')
            ax.set_title('Monthly Returns Heatmap (%)')

            output_path = Path(output_dir) / 'monthly_returns_heatmap.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Saved monthly returns heatmap to {output_path}")
            plt.show()


def main():
    """Main execution function."""

    # Initialize backtester
    backtester = CRRBacktester(
        ticker="AMD",
        initial_capital=100000.0,
        min_edge=0.02,          # 2% minimum edge
        transaction_cost=0.001,  # 0.1% transaction cost
        kelly_fraction=0.5,      # Half-Kelly sizing
        N_steps=100,
        r=0.053
    )

    # Run backtest (using recent data where we have actual prices)
    # Note: For realistic backtesting, you would need actual historical options data
    # This uses synthetic option chain generation as a demonstration

    start_date = "2024-01-01"
    end_date = "2024-12-31"

    equity_df, trades_df = backtester.run_backtest(
        start_date=start_date,
        end_date=end_date,
        expiry_days=30,
        rebalance_days=5
    )

    # Compute metrics
    metrics = backtester.compute_performance_metrics(equity_df, trades_df)

    # Print report
    backtester.print_performance_report(metrics)

    # Generate plots
    backtester.plot_results(equity_df, trades_df)

    # Save results to CSV
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    equity_df.to_csv(output_dir / "backtest_equity.csv", index=False)
    trades_df.to_csv(output_dir / "backtest_trades.csv", index=False)

    # Save metrics
    metrics_df = pd.DataFrame([metrics])
    metrics_df.to_csv(output_dir / "backtest_metrics.csv", index=False)

    print(f"\nResults saved to {output_dir}/")
    print("  - backtest_equity.csv")
    print("  - backtest_trades.csv")
    print("  - backtest_metrics.csv")
    print("  - crr_backtest_results.png")
    print("  - monthly_returns_heatmap.png")


if __name__ == "__main__":
    main()

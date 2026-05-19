"""
Quick test of live backtesting with real Yahoo Finance data
Non-interactive mode for demonstration
"""

from crr_backtest_live import CRRLiveBacktester, LiveOptionsDataFetcher
from datetime import datetime

def test_live_data():
    """Test with real options data."""

    # Test with AMD (or any ticker with options)
    ticker = "AMD"

    print(f"Testing with {ticker}...")

    # Initialize fetcher
    fetcher = LiveOptionsDataFetcher(ticker)

    # Get current price
    S = fetcher.get_current_price()
    print(f"Current {ticker} price: ${S:.2f}")

    # Get available expirations
    expirations = fetcher.get_available_expirations()
    print(f"\nAvailable expirations: {len(expirations)}")

    if not expirations:
        print("No options data available")
        return

    # Use the nearest expiration
    expiration = expirations[0]
    days_to_exp = (datetime.strptime(expiration, "%Y-%m-%d") - datetime.now()).days
    print(f"Using expiration: {expiration} ({days_to_exp} days)")

    # Display option chain
    fetcher.display_option_chain_summary(expiration, S)

    # Initialize backtester
    backtester = CRRLiveBacktester(
        ticker=ticker,
        initial_capital=100000.0,
        min_edge=0.02,
        kelly_fraction=0.5
    )

    print(f"\n{'='*80}")
    print("ANALYZING OPTIONS WITH CRR MODEL")
    print(f"{'='*80}\n")

    # Find opportunities
    opportunities = backtester.find_best_opportunities(
        expiration_date=expiration,
        top_n=10,
        min_volume=5  # Lower threshold for testing
    )

    # Display results
    backtester.display_opportunities(opportunities)

    # Get full analysis
    full_analysis = backtester.analyze_full_chain(
        expiration,
        strikes_filter='liquid',
        min_volume=5
    )

    # Plot
    if not full_analysis.empty:
        backtester.plot_edge_analysis(full_analysis)
        print("\n✓ Analysis complete!")
    else:
        print("\n⚠️  No liquid options found")

    return opportunities, full_analysis


if __name__ == "__main__":
    opportunities, analysis = test_live_data()

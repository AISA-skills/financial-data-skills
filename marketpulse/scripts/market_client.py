#!/usr/bin/env python3
"""
AIsa Market - AIsa API Client
Complete equity market data for autonomous agents.

Usage:
    python market_client.py stock prices --ticker <ticker> --start <date> --end <date> [--interval day|week|month] [--multiplier 1]
    python market_client.py stock news --ticker <ticker> [--count <n>]
    python market_client.py stock statements --ticker <ticker> --type <all|income|balance|cash> --period <annual|quarterly|ttm>
    python market_client.py stock segments --ticker <ticker> --period <annual|quarterly>
    python market_client.py stock metrics --ticker <ticker> [--historical --period <annual|quarterly|ttm>]
    python market_client.py stock analyst --ticker <ticker> [--period <annual|quarterly>]
    python market_client.py stock earnings --ticker <ticker>
    python market_client.py stock insider --ticker <ticker>
    python market_client.py stock ownership --ticker <ticker>
    python market_client.py stock filings --ticker <ticker> [--items --filing-type 10-K --year 2024]
    python market_client.py stock facts --ticker <ticker>
    python market_client.py stock rates [--bank <bank>] [--historical]
    python market_client.py stock screen --pe-max <n> --growth-min <n>
    python market_client.py stock line-items --tickers <AAPL,MSFT> --items <revenue,net_income> --period <annual|quarterly|ttm>
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
from typing import Any, Dict, List, Optional


def _resolve_aisa_api_key() -> str:
    """Resolve AISA_API_KEY from the environment, then from known credential files.

    os.environ is not always populated. The plugin / OpenClaw install form has no
    profile .env to inherit from, and hermes' sandboxed code-execution path
    strips variables whose name contains "KEY". `~/.aisa/credentials` is the
    cross-harness convention AgentSpec already documents for exactly this case
    (plugin-core/inject.ts: "scripts resolve these as: env var ->
    ~/.aisa/credentials").

    Order: env -> ~/.aisa/credentials
           -> $HERMES_HOME/profiles/$HERMES_PROFILE/.env (when HERMES_PROFILE is set)
           -> $HERMES_HOME/.env

    Under `hermes --profile X`, HERMES_HOME *is* the profile directory and
    HERMES_PROFILE is unset, so the last candidate resolves to that profile's own
    .env; the middle one covers harnesses that identify the profile by name
    instead. Only the running profile is ever read, never a sibling's, so a host
    with several profiles cannot hand back the wrong tenant's key.

    Returns "" when nothing is found; never raises on an unreadable or
    undecodable file.

    Kept byte-identical across the AIsa skills that need it —
    financial/marketpulse/scripts/market_client.py is the canonical copy; change
    it there first, then propagate.
    """
    key = os.environ.get("AISA_API_KEY", "").strip()
    if key:
        return key

    home = os.path.expanduser("~")
    hermes_home = os.environ.get("HERMES_HOME") or os.path.join(home, ".hermes")

    candidates = [os.path.join(home, ".aisa", "credentials")]
    profile = os.environ.get("HERMES_PROFILE", "").strip()
    if profile:
        candidates.append(os.path.join(hermes_home, "profiles", profile, ".env"))
    candidates.append(os.path.join(hermes_home, ".env"))

    for path in candidates:
        try:
            # utf-8-sig drops a BOM; errors="replace" keeps a mis-encoded file
            # from raising UnicodeDecodeError (a ValueError, not an OSError).
            with open(path, encoding="utf-8-sig", errors="replace") as handle:
                lines = handle.readlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            name, sep, value = line.partition("=")
            if not sep or name.strip() != "AISA_API_KEY":
                continue
            value = value.strip()
            if value[:1] in ("'", '"'):
                # A quoted value ends at its closing quote; whatever follows is
                # a trailing comment, not part of the secret. Checking "starts
                # and ends with a quote" instead would miss `KEY="v" # note`
                # and hand back the value with its quotes still attached.
                end = value.find(value[0], 1)
                value = value[1:end] if end != -1 else value[1:]
            else:
                for marker in (" #", "\t#"):
                    if marker in value:
                        value = value.split(marker, 1)[0]
                value = value.strip()
            # U+FFFD only appears where bytes failed to decode, so the value is
            # corrupt and cannot be a real key — keep looking rather than send
            # garbage as a bearer token.
            if value and "�" not in value:
                return value
    return ""


class MarketClient:
    """AIsa Market - Unified Market Data API Client."""

    BASE_URL = "https://api.aisa.one/apis/v1"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the client with an API key."""
        self.api_key = api_key or _resolve_aisa_api_key()
        if not self.api_key:
            raise ValueError(
                "AISA_API_KEY is required. Set the environment variable, add\n"
                "AISA_API_KEY=<key> to ~/.aisa/credentials, or pass it to the constructor."
            )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request to the AIsa API."""
        url = f"{self.BASE_URL}{endpoint}"

        if params:
            query_string = urllib.parse.urlencode(
                {k: v for k, v in params.items() if v is not None}
            )
            url = f"{url}?{query_string}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "AIsa-Market/1.0",
        }

        request_data = None
        if data:
            request_data = json.dumps(data).encode("utf-8")

        if method == "POST" and request_data is None:
            request_data = b"{}"

        req = urllib.request.Request(url, data=request_data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                return {"success": False, "error": {"code": str(e.code), "message": error_body}}
        except urllib.error.URLError as e:
            return {"success": False, "error": {"code": "NETWORK_ERROR", "message": str(e.reason)}}

    # ==================== Stock APIs ====================

    def stock_prices(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        interval: str = "day",
        interval_multiplier: int = 1,
    ) -> Dict[str, Any]:
        """Get historical stock prices."""
        return self._request("GET", "/financial/prices", params={
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "interval": interval,
            "interval_multiplier": interval_multiplier,
        })

    def company_news(self, ticker: str, limit: int = 10) -> Dict[str, Any]:
        """Get company news by ticker."""
        return self._request("GET", "/financial/news", params={
            "ticker": ticker,
            "limit": limit,
        })

    def statements_all(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        """Get all financial statements."""
        return self._request("GET", "/financial/financials", params={
            "ticker": ticker,
            "period": period,
        })

    def statements_income(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        """Get income statements."""
        return self._request("GET", "/financial/financials/income-statements", params={
            "ticker": ticker,
            "period": period,
        })

    def statements_balance(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        """Get balance sheets."""
        return self._request("GET", "/financial/financials/balance-sheets", params={
            "ticker": ticker,
            "period": period,
        })

    def statements_cash(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        """Get cash flow statements."""
        return self._request("GET", "/financial/financials/cash-flow-statements", params={
            "ticker": ticker,
            "period": period,
        })

    def segmented_revenues(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        """Get segmented revenues by business segment and geography."""
        return self._request("GET", "/financial/financials/segmented-revenues", params={
            "ticker": ticker,
            "period": period,
        })

    def metrics_snapshot(self, ticker: str) -> Dict[str, Any]:
        """Get real-time financial metrics snapshot."""
        return self._request("GET", "/financial/financial-metrics/snapshot", params={"ticker": ticker})

    def metrics_historical(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        """Get historical financial metrics."""
        return self._request("GET", "/financial/financial-metrics", params={
            "ticker": ticker,
            "period": period,
        })

    def analyst_eps(self, ticker: str, period: str = "annual") -> Dict[str, Any]:
        """Get earnings per share estimates."""
        return self._request("GET", "/financial/analyst-estimates", params={
            "ticker": ticker,
            "period": period,
        })

    def earnings_press_releases(self, ticker: str) -> Dict[str, Any]:
        """Get earnings press releases for a ticker."""
        return self._request("GET", "/financial/earnings/press-releases", params={"ticker": ticker})

    def insider_trades(self, ticker: str, limit: int = 10) -> Dict[str, Any]:
        """Get insider trades."""
        return self._request("GET", "/financial/insider-trades", params={
            "ticker": ticker,
            "limit": limit,
        })

    def institutional_ownership(self, ticker: str) -> Dict[str, Any]:
        """Get institutional ownership."""
        return self._request("GET", "/financial/institutional-ownership", params={"ticker": ticker})

    def sec_filings(self, ticker: str, filing_type: Optional[str] = None) -> Dict[str, Any]:
        """Get SEC filings."""
        params: Dict[str, Any] = {"ticker": ticker}
        if filing_type:
            params["filing_type"] = filing_type
        return self._request("GET", "/financial/filings", params=params)

    def sec_filing_items(self, ticker: str, filing_type: str, year: int) -> Dict[str, Any]:
        """Get SEC filing items (10-K or 10-Q)."""
        return self._request("GET", "/financial/filings/items", params={
            "ticker": ticker,
            "filing_type": filing_type,
            "year": year,
        })

    def company_facts(self, ticker: str) -> Dict[str, Any]:
        """Get company facts."""
        return self._request("GET", "/financial/company/facts", params={"ticker": ticker})

    def rates_snapshot(self) -> Dict[str, Any]:
        """Get current interest rates snapshot."""
        return self._request("GET", "/financial/macro/interest-rates/snapshot")

    def rates_historical(self, bank: str = "fed") -> Dict[str, Any]:
        """Get historical interest rates."""
        return self._request("GET", "/financial/macro/interest-rates", params={"bank": bank})

    def screen_stocks(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Screen for stocks matching criteria."""
        return self._request(
            "POST",
            "/financial/financials/search/screener",
            data={"filters": filters},
        )

    def search_line_items(
        self,
        tickers: List[str],
        line_items: List[str],
        period: str = "annual",
    ) -> Dict[str, Any]:
        """Search specific financial line items across tickers."""
        return self._request(
            "POST",
            "/financial/financials/search/line-items",
            data={
                "tickers": tickers,
                "line_items": line_items,
                "period": period,
            },
        )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AIsa Market - Complete equity market data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s stock prices --ticker AAPL --start 2025-01-01 --end 2025-01-31
    %(prog)s stock statements --ticker AAPL --type income --period annual
    %(prog)s stock segments --ticker AAPL --period annual
    %(prog)s stock earnings --ticker AAPL
    %(prog)s stock line-items --tickers AAPL,MSFT --items revenue,net_income --period annual
        """,
    )

    subparsers = parser.add_subparsers(dest="asset_type", help="Asset type")

    # ==================== Stock Commands ====================
    stock_parser = subparsers.add_parser("stock", help="Stock/Finance commands")
    stock_sub = stock_parser.add_subparsers(dest="command", help="Command")

    # prices
    prices = stock_sub.add_parser("prices", help="Get stock prices")
    prices.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    prices.add_argument("--start", "-s", required=True, help="Start date (YYYY-MM-DD)")
    prices.add_argument("--end", "-e", required=True, help="End date (YYYY-MM-DD)")
    prices.add_argument(
        "--interval", "-i", default="day",
        choices=["second", "minute", "day", "week", "month", "year"],
        help="Time interval (default: day)",
    )
    prices.add_argument("--multiplier", "-m", type=int, default=1,
                        help="Interval multiplier (default: 1)")

    # news
    news = stock_sub.add_parser("news", help="Get company news")
    news.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    news.add_argument("--count", "-c", type=int, default=10, help="Number of articles")

    # statements
    statements = stock_sub.add_parser("statements", help="Get financial statements")
    statements.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    statements.add_argument("--type", required=True,
                            choices=["all", "income", "balance", "cash"],
                            help="Statement type")
    statements.add_argument("--period", "-p", default="annual",
                            choices=["annual", "quarterly", "ttm"],
                            help="Reporting period (default: annual)")

    # segments
    segments = stock_sub.add_parser("segments", help="Get segmented revenues")
    segments.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    segments.add_argument("--period", "-p", default="annual",
                          choices=["annual", "quarterly"],
                          help="Reporting period (default: annual)")

    # metrics
    metrics = stock_sub.add_parser("metrics", help="Get financial metrics")
    metrics.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    metrics.add_argument("--historical", action="store_true", help="Get historical data")
    metrics.add_argument("--period", "-p", default="annual",
                         choices=["annual", "quarterly", "ttm"],
                         help="Period for historical metrics (default: annual)")

    # analyst
    analyst = stock_sub.add_parser("analyst", help="Get analyst estimates")
    analyst.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    analyst.add_argument("--period", "-p", choices=["annual", "quarterly"], default="annual")

    # earnings
    earnings = stock_sub.add_parser("earnings", help="Get earnings press releases")
    earnings.add_argument("--ticker", "-t", required=True, help="Stock ticker")

    # insider
    insider = stock_sub.add_parser("insider", help="Get insider trades")
    insider.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    insider.add_argument("--limit", "-l", type=int, default=10, help="Max trades to return")

    # ownership
    ownership = stock_sub.add_parser("ownership", help="Get institutional ownership")
    ownership.add_argument("--ticker", "-t", required=True, help="Stock ticker")

    # filings
    filings = stock_sub.add_parser("filings", help="Get SEC filings")
    filings.add_argument("--ticker", "-t", required=True, help="Stock ticker")
    filings.add_argument("--filing-type", help="Filing type (10-K, 10-Q, 8-K, 4, 144)")
    filings.add_argument("--items", action="store_true",
                         help="Fetch filing items instead of filings list (requires --filing-type and --year)")
    filings.add_argument("--year", type=int, help="Filing year (required with --items)")

    # facts
    facts = stock_sub.add_parser("facts", help="Get company facts")
    facts.add_argument("--ticker", "-t", required=True, help="Stock ticker")

    # rates
    rates = stock_sub.add_parser("rates", help="Get interest rates")
    rates.add_argument("--bank", "-b", default="fed", help="Central bank (e.g., fed)")
    rates.add_argument("--historical", action="store_true", help="Get historical data")

    # screen
    screen = stock_sub.add_parser("screen", help="Stock screener")
    screen.add_argument("--pe-max", type=float, help="Max P/E ratio")
    screen.add_argument("--pe-min", type=float, help="Min P/E ratio")
    screen.add_argument("--growth-min", type=float, help="Min revenue growth")
    screen.add_argument("--growth-max", type=float, help="Max revenue growth")

    # line-items
    line_items = stock_sub.add_parser("line-items", help="Search specific line items across tickers")
    line_items.add_argument("--tickers", required=True,
                            help="Comma-separated tickers (e.g., AAPL,MSFT)")
    line_items.add_argument("--items", required=True,
                            help="Comma-separated line items (e.g., revenue,net_income)")
    line_items.add_argument("--period", "-p", default="annual",
                            choices=["annual", "quarterly", "ttm"],
                            help="Period (default: annual)")

    args = parser.parse_args()

    if not args.asset_type:
        parser.print_help()
        sys.exit(1)

    if not args.command:
        stock_parser.print_help()
        sys.exit(1)

    try:
        client = MarketClient()
    except ValueError as e:
        print(json.dumps({"success": False, "error": {"code": "AUTH_ERROR", "message": str(e)}}))
        sys.exit(1)

    result = None

    if args.asset_type == "stock":
        if args.command == "prices":
            result = client.stock_prices(
                args.ticker, args.start, args.end, args.interval, args.multiplier
            )
        elif args.command == "news":
            result = client.company_news(args.ticker, args.count)
        elif args.command == "statements":
            if args.type == "all":
                result = client.statements_all(args.ticker, args.period)
            elif args.type == "income":
                result = client.statements_income(args.ticker, args.period)
            elif args.type == "balance":
                result = client.statements_balance(args.ticker, args.period)
            elif args.type == "cash":
                result = client.statements_cash(args.ticker, args.period)
        elif args.command == "segments":
            result = client.segmented_revenues(args.ticker, args.period)
        elif args.command == "metrics":
            if args.historical:
                result = client.metrics_historical(args.ticker, args.period)
            else:
                result = client.metrics_snapshot(args.ticker)
        elif args.command == "analyst":
            result = client.analyst_eps(args.ticker, args.period)
        elif args.command == "earnings":
            result = client.earnings_press_releases(args.ticker)
        elif args.command == "insider":
            result = client.insider_trades(args.ticker, args.limit)
        elif args.command == "ownership":
            result = client.institutional_ownership(args.ticker)
        elif args.command == "filings":
            if args.items:
                if not args.filing_type or not args.year:
                    print(json.dumps({
                        "success": False,
                        "error": {"code": "BAD_ARGS",
                                  "message": "--items requires --filing-type and --year"},
                    }))
                    sys.exit(1)
                result = client.sec_filing_items(args.ticker, args.filing_type, args.year)
            else:
                result = client.sec_filings(args.ticker, args.filing_type)
        elif args.command == "facts":
            result = client.company_facts(args.ticker)
        elif args.command == "rates":
            if args.historical:
                result = client.rates_historical(args.bank)
            else:
                result = client.rates_snapshot()
        elif args.command == "screen":
            filters: Dict[str, Any] = {}
            if args.pe_max or args.pe_min:
                filters["pe_ratio"] = {}
                if args.pe_max:
                    filters["pe_ratio"]["max"] = args.pe_max
                if args.pe_min:
                    filters["pe_ratio"]["min"] = args.pe_min
            if args.growth_max or args.growth_min:
                filters["revenue_growth"] = {}
                if args.growth_max:
                    filters["revenue_growth"]["max"] = args.growth_max
                if args.growth_min:
                    filters["revenue_growth"]["min"] = args.growth_min
            result = client.screen_stocks(filters)
        elif args.command == "line-items":
            tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
            items = [i.strip() for i in args.items.split(",") if i.strip()]
            result = client.search_line_items(tickers, items, args.period)

    if result:
        output = json.dumps(result, indent=2, ensure_ascii=False)
        try:
            print(output)
        except UnicodeEncodeError:
            print(json.dumps(result, indent=2, ensure_ascii=True))
        sys.exit(0 if result.get("success", True) else 1)


if __name__ == "__main__":
    main()

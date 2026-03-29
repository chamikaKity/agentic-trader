"""Market analysis agent: fetches OHLCV candles from Binance and computes indicators."""

import httpx
import pandas as pd

from agentic_trader.models.signal import IndicatorSet

_KLINES_URL = "https://api.binance.com/api/v3/klines"


def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=period - 1, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    return 100 - (100 / (1 + rs))


def _macd(
    close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    fast_ema = _ema(close, fast)
    slow_ema = _ema(close, slow)
    macd_line = fast_ema - slow_ema
    signal_line = _ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _bollinger(
    close: pd.Series, period: int = 20, std_dev: float = 2.0
) -> tuple[pd.Series, pd.Series]:
    sma = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    return upper, lower


def _atr(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.ewm(com=period - 1, adjust=False).mean()


async def fetch_indicators(symbol: str, interval: str = "1h") -> IndicatorSet:
    """Fetch 200 candles from Binance and return computed indicators."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            _KLINES_URL,
            params={"symbol": symbol, "interval": interval, "limit": 200},
        )
        response.raise_for_status()
        raw = response.json()

    df = pd.DataFrame(
        raw,
        columns=[
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "num_trades",
            "taker_buy_base",
            "taker_buy_quote",
            "ignore",
        ],
    )

    for col in ("open", "high", "low", "close", "volume"):
        df[col] = df[col].astype(float)

    # Validate OHLCV integrity
    invalid_rows = (df["high"] < df["low"]).sum()
    if invalid_rows > 0:
        raise ValueError(f"{invalid_rows} row(s) have high < low for {symbol}")

    # Forward-fill NaN gaps
    df = df.ffill()

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    rsi_series = _rsi(close)
    macd_line_s, signal_line_s, histogram_s = _macd(close)
    bb_upper_s, bb_lower_s = _bollinger(close)
    ema20_s = _ema(close, 20)
    ema50_s = _ema(close, 50)
    atr_s = _atr(high, low, close)
    volume_sma20_s = volume.rolling(20).mean()

    last = close.iloc[-1]
    bb_upper = float(bb_upper_s.iloc[-1])
    bb_lower = float(bb_lower_s.iloc[-1])

    if last > bb_upper:
        bb_position: str = "above"
    elif last < bb_lower:
        bb_position = "below"
    else:
        bb_position = "inside"

    return IndicatorSet(
        symbol=symbol,
        interval=interval,
        current_price=float(last),
        rsi=float(rsi_series.iloc[-1]),
        macd_histogram=float(histogram_s.iloc[-1]),
        macd_histogram_prev=float(histogram_s.iloc[-2]),
        macd_line=float(macd_line_s.iloc[-1]),
        signal_line=float(signal_line_s.iloc[-1]),
        bb_upper=bb_upper,
        bb_lower=bb_lower,
        bb_position=bb_position,  # type: ignore[arg-type]
        ema20=float(ema20_s.iloc[-1]),
        ema50=float(ema50_s.iloc[-1]),
        atr=float(atr_s.iloc[-1]),
        volume_sma20=float(volume_sma20_s.iloc[-1]),
    )

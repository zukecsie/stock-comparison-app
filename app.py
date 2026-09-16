import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 頁面配置
st.set_page_config(
    page_title="雙標的走勢與風險指標比較",
    page_icon="📈",
    layout="wide"
)

st.title("📊 股票與 ETF 綜合對比工具")
st.caption("支援美股與台股代碼，提供還原股價成長、回撤幅度、滾動波動率與量化風險指標對比。")

# 側邊欄設定
with st.sidebar:
    st.header("⚙️ 比較參數設定")
    
    col1, col2 = st.columns(2)
    with col1:
        ticker1_raw = st.text_input("標的一代碼", value="NTSX").strip().upper()
    with col2:
        ticker2_raw = st.text_input("標的二代碼", value="VTI").strip().upper()
        
    st.info("💡 **台股代碼**：直接輸入如 `2330`（自動辨識為 `2330.TW`），上櫃請輸入 `6488.TWO`。")

    period_mode = st.radio("時間範圍", ["快捷區間", "自訂日期"], horizontal=True)
    today = datetime.today().date()
    
    if period_mode == "快捷區間":
        timeframe = st.selectbox(
            "選擇區間",
            ["1 年 (1Y)", "3 年 (3Y)", "5 年 (5Y)", "10 年 (10Y)", "今年以來 (YTD)", "全部歷史 (MAX)"],
            index=2
        )
        if timeframe == "1 年 (1Y)":
            start_date = today - timedelta(days=365)
        elif timeframe == "3 年 (3Y)":
            start_date = today - timedelta(days=365 * 3)
        elif timeframe == "5 年 (5Y)":
            start_date = today - timedelta(days=365 * 5)
        elif timeframe == "10 年 (10Y)":
            start_date = today - timedelta(days=365 * 10)
        elif timeframe == "今年以來 (YTD)":
            start_date = datetime(today.year, 1, 1).date()
        else:
            start_date = datetime(1990, 1, 1).date()
        end_date = today
    else:
        start_date = st.date_input("開始日期", value=today - timedelta(days=365 * 5))
        end_date = st.date_input("結束日期", value=today)

    initial_investment = st.number_input("初始投資金額", min_value=1000, value=10000, step=1000)
    risk_free_rate = st.number_input("年化無風險利率 (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.1) / 100.0

def normalize_ticker(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if symbol.isdigit():
        return f"{symbol}.TW"
    return symbol

t1 = normalize_ticker(ticker1_raw)
t2 = normalize_ticker(ticker2_raw)

@st.cache_data(ttl=3600)
def fetch_stock_data(symbol: str, start: datetime.date, end: datetime.date):
    try:
        data = yf.download(symbol, start=start, end=end + timedelta(days=1), progress=False)
        if data.empty:
            return None, f"找不到代碼 {symbol} 的數據。"
        
        prices = data["Adj Close"] if "Adj Close" in data.columns else data.get("Close")
        if prices is None or prices.empty:
            return None, f"{symbol} 無法取得收盤價。"
            
        if isinstance(prices, pd.DataFrame):
            prices = prices.iloc[:, 0]
            
        return prices.dropna(), None
    except Exception as e:
        return None, f"載入 {symbol} 失敗: {str(e)}"

p1, err1 = fetch_stock_data(t1, start_date, end_date)
p2, err2 = fetch_stock_data(t2, start_date, end_date)

if err1:
    st.error(err1)
if err2:
    st.error(err2)

if p1 is not None and p2 is not None:
    combined = pd.DataFrame({t1: p1, t2: p2}).dropna()
    
    if len(combined) < 10:
        st.warning("兩者共同歷史交易天數不足，請調整時間範圍。")
        st.stop()

    returns = combined.pct_change().dropna()
    growth = (1 + returns).cumprod() * initial_investment
    first_row = pd.DataFrame([{t1: initial_investment, t2: initial_investment}], index=[combined.index[0]])
    growth = pd.concat([first_row, growth])

    cum_returns = (1 + returns).cumprod()
    peak = cum_returns.cummax()
    drawdowns = (cum_returns - peak) / peak

    trading_days = 252
    years = len(returns) / trading_days
    
    def calc_metrics(series_ret, series_cum, series_dd):
        total_ret = (series_cum.iloc[-1] / series_cum.iloc[0]) - 1
        cagr = (1 + total_ret) ** (1 / years) - 1 if years > 0 else 0
        vol = series_ret.std() * np.sqrt(trading_days)
        sharpe = (cagr - risk_free_rate) / vol if vol > 0 else 0
        
        neg_ret = series_ret[series_ret < 0]
        downside_std = neg_ret.std() * np.sqrt(trading_days)
        sortino = (cagr - risk_free_rate) / downside_std if downside_std > 0 else 0
        
        max_dd = series_dd.min()
        calmar = cagr / abs(max_dd) if max_dd != 0 else 0
        current_dd = series_dd.iloc[-1]
        
        return {
            "累積報酬率": f"{total_ret * 100:.2f}%",
            "年化複合報酬 (CAGR)": f"{cagr * 100:.2f}%",
            "年化波動率": f"{vol * 100:.2f}%",
            "夏普比率 (Sharpe)": f"{sharpe:.2f}",
            "索提諾比率 (Sortino)": f"{sortino:.2f}",
            "最大回撤 (Max Drawdown)": f"{max_dd * 100:.2f}%",
            "當前受創 (Current DD)": f"{current_dd * 100:.2f}%",
            "卡瑪比率 (Calmar)": f"{calmar:.2f}",
        }

    m1 = calc_metrics(returns[t1], cum_returns[t1], drawdowns[t1])
    m2 = calc_metrics(returns[t2], cum_returns[t2], drawdowns[t2])
    corr = returns[t1].corr(returns[t2])

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(label=f"{t1} 最終價值", value=f"${growth[t1].iloc[-1]:,.2f}", delta=m1["年化複合報酬 (CAGR)"] + " 年化")
    with c2:
        st.metric(label=f"{t2} 最終價值", value=f"${growth[t2].iloc[-1]:,.2f}", delta=m2["年化複合報酬 (CAGR)"] + " 年化")
    with c3:
        st.metric(label="相關係數 (Correlation)", value=f"{corr:.3f}")

    st.subheader("📈 資產累積成長對比")
    fig_growth = go.Figure()
    fig_growth.add_trace(go.Scatter(x=growth.index, y=growth[t1], mode='lines', name=t1, line=dict(width=2, color='#1f77b4')))
    fig_growth.add_trace(go.Scatter(x=growth.index, y=growth[t2], mode='lines', name=t2, line=dict(width=2, color='#ff7f0e')))
    fig_growth.update_layout(xaxis_title="日期", yaxis_title="資產價值 ($)", hovermode="x unified", template="plotly_white", height=450)
    st.plotly_chart(fig_growth, use_container_width=True)

    st.subheader("🌊 水下回撤幅度比較")
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(x=drawdowns.index, y=drawdowns[t1] * 100, mode='lines', name=t1, fill='tozeroy', line=dict(width=1.5, color='#1f77b4')))
    fig_dd.add_trace(go.Scatter(x=drawdowns.index, y=drawdowns[t2] * 100, mode='lines', name=t2, fill='tozeroy', line=dict(width=1.5, color='#ff7f0e')))
    fig_dd.update_layout(xaxis_title="日期", yaxis_title="回撤百分比 (%)", hovermode="x unified", template="plotly_white", height=380)
    st.plotly_chart(fig_dd, use_container_width=True)

    st.subheader("⚡ 滾動 60 日年化波動率")
    rolling_vol = returns.rolling(window=60).std() * np.sqrt(trading_days) * 100
    fig_vol = go.Figure()
    fig_vol.add_trace(go.Scatter(x=rolling_vol.index, y=rolling_vol[t1], mode='lines', name=t1, line=dict(width=1.8, color='#1f77b4')))
    fig_vol.add_trace(go.Scatter(x=rolling_vol.index, y=rolling_vol[t2], mode='lines', name=t2, line=dict(width=1.8, color='#ff7f0e')))
    fig_vol.update_layout(xaxis_title="日期", yaxis_title="波動率 (%)", hovermode="x unified", template="plotly_white", height=380)
    st.plotly_chart(fig_vol, use_container_width=True)

    st.subheader("📅 年度報酬對比")
    yearly_ret = combined.resample('YE').last().pct_change().dropna() * 100
    if not yearly_ret.empty:
        years_label = [d.strftime('%Y') for d in yearly_ret.index]
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=years_label, y=yearly_ret[t1], name=t1, marker_color='#1f77b4'))
        fig_bar.add_trace(go.Bar(x=years_label, y=yearly_ret[t2], name=t2, marker_color='#ff7f0e'))
        fig_bar.update_layout(barmode='group', xaxis_title="年份", yaxis_title="報酬率 (%)", hovermode="x unified", template="plotly_white", height=380)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📋 量化統計指標匯總")
    metrics_df = pd.DataFrame([m1, m2], index=[t1, t2]).T
    st.table(metrics_df)

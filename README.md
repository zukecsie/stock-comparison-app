# 股票與 ETF 綜合對比工具 (Stock Comparison Web App)

基於 Streamlit、Plotly 與 yfinance 開發的雙標的投資分析網站，功能對標 PortfoliosLab 的 Stock Comparison 工具。

## 功能特色
1. **支援美股與台股**：支援美股代碼（如 `NTSX`, `VTI`, `QQQ`, `AAPL`）與台股代碼（直接輸入 `2330` 自動轉 `2330.TW`，亦支援上櫃代碼如 `6488.TWO`）。
2. **資產累積成長對比（Performance Comparison）**：計算還原權息（Adj Close）之累積資產變化（預設 $10,000 起始資金）。
3. **水下回撤幅度比較（Drawdown Analysis）**：自歷史高點拉回百分比。
4. **滾動年化波動率（Rolling Volatility）**：滾動 60 日年化波動率走勢。
5. **歷年歷史報酬長條圖（Yearly Performance）**：逐年年度報酬並排比較。
6. **核心量化風險與報酬統計表**：CAGR、年化波動率、夏普比率 (Sharpe)、索提諾比率 (Sortino)、最大回撤 (Max Drawdown)、卡瑪比率 (Calmar)、兩者相關係數 (Correlation)。

## 本機快速啟動
```bash
# 1. 建立並啟動虛擬環境 (可選)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安裝套件
pip install -r requirements.txt

# 3. 啟動 Streamlit
streamlit run app.py
```

## 部署至 Streamlit Community Cloud
1. 在 GitHub 建立新的 Repository，將本資料夾所有檔案上傳。
2. 前往 https://share.streamlit.io/ 登入 GitHub 並點擊「Create app」。
3. 選擇該 Repository 與 `app.py`，點擊「Deploy」即可免費上線！

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- 頁面設定 ---
st.set_page_config(
    page_title="My Wealth Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 核心函數：抓取股價與匯率 ---
@st.cache_data(ttl=300) # 設定快取，避免每次切換頁面都重抓，5分鐘更新一次
def get_market_data(us_stocks, tw_stocks):
    data = []
    
    # 1. 抓取匯率 (USD to TWD)
    try:
        forex = yf.Ticker("TWD=X")
        # 為了保險，多抓幾天避免當下抓不到
        hist = forex.history(period="5d") 
        if not hist.empty:
            usd_rate = hist['Close'].iloc[-1]
        else:
            usd_rate = 32.0 # 預設值，避免掛掉
    except:
        usd_rate = 32.0

    # 2. 處理美股
    for stock in us_stocks:
        if stock["ticker"]:
            try:
                ticker = stock["ticker"].upper().strip()
                yf_stock = yf.Ticker(ticker)
                price = yf_stock.history(period="1d")['Close'].iloc[-1]
                
                market_value_usd = price * stock["qty"]
                market_value_twd = market_value_usd * usd_rate
                cost_twd = stock["cost_usd"] * stock["qty"] * usd_rate # 簡單估算成本
                
                data.append({
                    "Type": "美股",
                    "Ticker": ticker,
                    "Price (Orig)": price,
                    "Qty": stock["qty"],
                    "Market Value (TWD)": round(market_value_twd),
                    "Cost (TWD)": round(cost_twd),
                    "Profit (TWD)": round(market_value_twd - cost_twd),
                    "Return %": round(((market_value_twd - cost_twd) / cost_twd) * 100, 2) if cost_twd > 0 else 0
                })
            except:
                st.error(f"找不到美股代號: {stock['ticker']}")

    # 3. 處理台股
    for stock in tw_stocks:
        if stock["ticker"]:
            try:
                ticker_code = str(stock["ticker"]).strip()
                if ".TW" not in ticker_code and ".TWO" not in ticker_code:
                    ticker_code += ".TW"
                
                yf_stock = yf.Ticker(ticker_code)
                price = yf_stock.history(period="1d")['Close'].iloc[-1]
                
                market_value_twd = price * stock["qty"]
                cost_twd = stock["cost_twd"] * stock["qty"]
                
                data.append({
                    "Type": "台股",
                    "Ticker": ticker_code.replace(".TW", ""),
                    "Price (Orig)": price,
                    "Qty": stock["qty"],
                    "Market Value (TWD)": round(market_value_twd),
                    "Cost (TWD)": round(cost_twd),
                    "Profit (TWD)": round(market_value_twd - cost_twd),
                    "Return %": round(((market_value_twd - cost_twd) / cost_twd) * 100, 2) if cost_twd > 0 else 0
                })
            except:
                st.error(f"找不到台股代號: {stock['ticker']}")

    return pd.DataFrame(data), usd_rate

# --- Session State 初始化 (讓資料在切換頁面時不會不見) ---
if 'bank_cash' not in st.session_state:
    st.session_state['bank_cash'] = 100000
if 'crypto_total' not in st.session_state:
    st.session_state['crypto_total'] = 50000
if 'us_portfolio' not in st.session_state:
    st.session_state['us_portfolio'] = pd.DataFrame(
        [{"ticker": "AAPL", "qty": 10, "cost_usd": 150}, 
         {"ticker": "NVDA", "qty": 5, "cost_usd": 400}]
    )
if 'tw_portfolio' not in st.session_state:
    st.session_state['tw_portfolio'] = pd.DataFrame(
        [{"ticker": "2330", "qty": 1000, "cost_twd": 500},
         {"ticker": "0050", "qty": 500, "cost_twd": 120}]
    )

# --- 側邊欄導航 ---
st.sidebar.title("💎 資產管家")
page = st.sidebar.radio("前往頁面", ["📝 資料輸入", "📊 資產儀表板"])
st.sidebar.markdown("---")
st.sidebar.info("資料儲存於暫存記憶體，重新整理網頁會重置為預設值。")

# ================= 頁面 1: 資料輸入 =================
if page == "📝 資料輸入":
    st.title("📝 資產資料輸入")
    st.write("請在下方表格直接編輯您的持股，系統會自動儲存。")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🏦 現金與加密貨幣")
        st.session_state['bank_cash'] = st.number_input(
            "銀行現金餘額 (TWD)", 
            value=st.session_state['bank_cash'], 
            step=1000
        )
        st.session_state['crypto_total'] = st.number_input(
            "幣圈資產總值 (TWD估值)", 
            value=st.session_state['crypto_total'], 
            step=1000
        )

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🇺🇸 美股配置 (US Stock)")
        st.caption("請輸入代號、股數、美金成本")
        # 使用 data_editor 讓使用者可以像 Excel 一樣增刪修改
        st.session_state['us_portfolio'] = st.data_editor(
            st.session_state['us_portfolio'], 
            num_rows="dynamic",
            column_config={
                "ticker": "代號 (如 AAPL)",
                "qty": st.column_config.NumberColumn("股數", min_value=0),
                "cost_usd": st.column_config.NumberColumn("成本 (USD)", min_value=0, format="$%.2f")
            }
        )

    with c2:
        st.subheader("🇹🇼 台股配置 (TW Stock)")
        st.caption("請輸入代號 (如 2330)、股數、台幣成本")
        st.session_state['tw_portfolio'] = st.data_editor(
            st.session_state['tw_portfolio'], 
            num_rows="dynamic", 
            column_config={
                "ticker": "代號 (如 2330)",
                "qty": st.column_config.NumberColumn("股數", min_value=0),
                "cost_twd": st.column_config.NumberColumn("成本 (TWD)", min_value=0, format="$%d")
            }
        )
    
    if st.button("確認儲存並前往儀表板"):
        st.toast("資料已更新！請切換至儀表板查看。", icon="✅")

# ================= 頁面 2: 資產儀表板 =================
elif page == "📊 資產儀表板":
    st.title("📊 我的資產全覽")
    
    with st.spinner('正在連線 Yahoo Finance 抓取最新股價...'):
        # 整理資料格式給函數
        us_inputs = st.session_state['us_portfolio'].to_dict('records')
        tw_inputs = st.session_state['tw_portfolio'].to_dict('records')
        
        df_stocks, usd_rate = get_market_data(us_inputs, tw_inputs)
        
        # 計算總資產
        stock_total = df_stocks['Market Value (TWD)'].sum() if not df_stocks.empty else 0
        cash_total = st.session_state['bank_cash']
        crypto_total = st.session_state['crypto_total']
        net_worth = stock_total + cash_total + crypto_total
        
        # 顯示大指標
        st.markdown("### 💰 總淨值 (Net Worth)")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("總資產 (TWD)", f"${net_worth:,.0f}")
        col_m2.metric("即時匯率 (USD/TWD)", f"{usd_rate:.2f}")
        
        # 計算整體股票損益
        if not df_stocks.empty:
            total_profit = df_stocks['Profit (TWD)'].sum()
            total_cost = df_stocks['Cost (TWD)'].sum()
            total_return_pct = (total_profit / total_cost * 100) if total_cost > 0 else 0
            col_m3.metric("股票總損益", f"${total_profit:,.0f}", f"{total_return_pct:.2f}%")
        
        st.markdown("---")

        # 圖表區
        c_chart1, c_chart2 = st.columns(2)
        
        with c_chart1:
            st.subheader("資產類別分佈")
            # 準備圓餅圖資料
            asset_data = pd.DataFrame({
                "Category": ["現金", "加密貨幣", "美股", "台股"],
                "Value": [
                    cash_total, 
                    crypto_total, 
                    df_stocks[df_stocks['Type']=='美股']['Market Value (TWD)'].sum() if not df_stocks.empty else 0,
                    df_stocks[df_stocks['Type']=='台股']['Market Value (TWD)'].sum() if not df_stocks.empty else 0
                ]
            })
            asset_data = asset_data[asset_data['Value'] > 0] # 只顯示有錢的項目
            fig_pie = px.pie(asset_data, values='Value', names='Category', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)

        with c_chart2:
            st.subheader("持股佔比 (股票部位)")
            if not df_stocks.empty:
                fig_stock = px.sunburst(df_stocks, path=['Type', 'Ticker'], values='Market Value (TWD)', color='Return %', color_continuous_scale='RdYlGn')
                st.plotly_chart(fig_stock, use_container_width=True)
            else:
                st.info("尚無股票資料")

        # 詳細表格區
        st.subheader("📋 持股詳細清單")
        if not df_stocks.empty:
            # 美化表格顯示
            st.dataframe(
                df_stocks.style.format({
                    "Price (Orig)": "{:.2f}",
                    "Market Value (TWD)": "{:,.0f}",
                    "Cost (TWD)": "{:,.0f}",
                    "Profit (TWD)": "{:,.0f}",
                    "Return %": "{:.2f}%"
                }).background_gradient(subset=["Return %"], cmap="RdYlGn", vmin=-20, vmax=20),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning("請回到『資料輸入』頁面新增持股")

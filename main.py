import streamlit as st

st.title("🎉 恭喜！環境架設成功！")
st.header("看來不是程式寫太爛，是剛剛 yfinance 抓資料卡住了 😂")

st.write("既然這裡能顯示，代表你的雲端主機是活著的。")
st.write("我們可以開始一步一步把功能加回來了。")

# 放個慶祝特效
if st.button('點我慶祝一下'):
    st.balloons()

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# 데이터 저장 파일 설정
DB_FILE = "4m_data_log.csv"

if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["일시", "라인", "4M구분", "변동내용", "작업자"])
    df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")

st.set_page_config(page_title="현장 4M 관리", layout="wide")

# QR코드 스캔 시 주소 뒤에 ?line=Line-A 처럼 붙는 값을 읽어옵니다.
query_params = st.query_params
qr_line = query_params.get("line", "")

st.sidebar.title("🏭 사내 4M 관리 시스템")
menu = st.sidebar.radio("메뉴", ["📱 현장 변동점 등록", "🖥️ PC 실시간 대시보드"])

if menu == "📱 현장 변동점 등록":
    st.header("📱 4M 변동점 현장 입력")

    with st.form(key="input_form", clear_on_submit=True):
        lines_list = ["Line-A", "Line-B", "Line-C", "Line-D"]
        default_idx = lines_list.index(qr_line) if qr_line in lines_list else 0

        selected_line = st.selectbox("📍 변동 발생 라인", lines_list, index=default_idx)
        m_category = st.radio("🔍 4M 구분", ["Man (작업자)", "Machine (설비)", "Material (원재료)", "Method (작업방법)"],
                              horizontal=True)
        change_detail = st.text_area("📝 변동 내용 상세")
        worker_name = st.text_input("👤 입력자(작업자)")

        submit = st.form_submit_button(label="🚀 변동사항 등록")

        if submit:
            if not change_detail or not worker_name:
                st.error("⚠️ 모든 내용을 입력해주세요.")
            else:
                df_log = pd.read_csv(DB_FILE)
                new_row = pd.DataFrame([{
                    "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "라인": selected_line,
                    "4M구분": m_category.split(" ")[0],
                    "변동내용": change_detail,
                    "작업자": worker_name
                }])
                df_log = pd.concat([df_log, new_row], ignore_index=True)
                df_log.to_csv(DB_FILE, index=False, encoding="utf-8-sig")
                st.success(f"✅ [{selected_line}] 등록 완료!")

elif menu == "🖥️ PC 실시간 대시보드":
    st.header("🖥️ 4M 변동점 실시간 대시보드")
    df_log = pd.read_csv(DB_FILE)

    if df_log.empty:
        st.info("등록된 데이터가 없습니다.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 라인별 발생 건수")
            fig1 = px.bar(df_log["라인"].value_counts().reset_index(), x="라인", y="count", color="라인")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            st.subheader("🍕 4M 항목별 분포")
            fig2 = px.pie(df_log["4M구분"].value_counts().reset_index(), values="count", names="4M구분", hole=0.3)
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 전체 변동 이력 (최신순)")
        st.dataframe(df_log.iloc[::-1], use_container_width=True)
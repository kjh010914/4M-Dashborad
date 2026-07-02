import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, timezone
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="현장 4M 관리", layout="wide")

# 🌟 한국 시간(KST) 설정 (스트림릿 클라우드 서버 시간 차이 9시간 보정)
KST = timezone(timedelta(hours=9))

# --- 1. 구글 스프레드시트 연결 ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    df = conn.read(worksheet="4M-Dashboard", ttl=0)
    df = df.dropna(how="all") 
    return df

# --- 3. 기본 세팅 ---
query_params = st.query_params
qr_line = query_params.get("line", "전체")
lines_list = ["Line-A", "Line-B", "Line-C", "Line-D"]

st.sidebar.title("🏭 사내 4M 관리 시스템")
menu = st.sidebar.radio("메뉴", ["📱 현장 변동점 등록", "🖥️ PC 실시간 대시보드", "✏️ 등록 데이터 수정/삭제"])

# --- 4. 현장 변동점 등록 화면 ---
if menu == "📱 현장 변동점 등록":
    st.header("📱 4M 변동점 현장 입력")
    
    with st.form(key="input_form", clear_on_submit=True):
        col_date, col_time = st.columns(2)
        with col_date:
            selected_date = st.date_input("📅 발생 일자", value=datetime.now(KST).date())
        with col_time:
            selected_time = st.time_input("⏰ 발생 시간", value=datetime.now(KST).time())
            
        st.markdown("---")
        
        default_idx = lines_list.index(qr_line) if qr_line in lines_list else 0
        selected_line = st.selectbox("📍 변동 발생 라인", lines_list, index=default_idx)
        m_category = st.radio("🔍 4M 구분", ["Man (작업자)", "Machine (설비)", "Material (원재료/부품)", "Method (작업방법)"], horizontal=True)
        
        change_detail = st.text_area("📝 변동 내용 상세")
        quality_issue = st.text_area("⚠️ 품질 내역")
        
        st.markdown("---")
        st.markdown("👤 **등록자 정보**")
        col_dept, col_name = st.columns(2)
        with col_dept:
            department = st.text_input("🏢 부서", placeholder="예: 생산팀")
        with col_name:
            worker_name = st.text_input("🧑‍💼 담당자 성명", placeholder="예: 홍길동")
        
        st.markdown("---")
        action_taken = st.text_area("🛠️ 조치 내용")
        validity_check = st.radio("✅ 유효성 점검 결과", ["점검 전", "양호 (문제없음)", "불량 (개선필요)"], horizontal=True)
        
        submit = st.form_submit_button(label="🚀 변동사항 등록")
        
        if submit:
            if not change_detail or not department or not worker_name:
                st.error("⚠️ 변동 내용과 등록자 정보(부서, 성명)를 모두 작성해주세요.")
            else:
                df_log = load_data()
                custom_datetime = f"{selected_date} {selected_time.strftime('%H:%M:%S')}"
                
                new_row = pd.DataFrame([{
                    "일시": custom_datetime,
                    "라인": selected_line,
                    "4M구분": m_category.split(" ")[0],
                    "변동내용": change_detail,
                    "조치내용": action_taken,
                    "부서": department,
                    "담당자": worker_name,
                    "품질내역": quality_issue,
                    "유효성점검": validity_check.split(" ")[0]
                }])
                df_log = pd.concat([df_log, new_row], ignore_index=True)
                
                conn.update(worksheet="4M-Dashboard", data=df_log)
                st.success(f"✅ [{selected_line}] 구글 시트에 완벽하게 등록되었습니다!")

# --- 5. PC 실시간 대시보드 화면 ---
elif menu == "🖥️ PC 실시간 대시보드":
    st.header("🖥️ 4M 변동점 실시간 대시보드")
    
    df_log = load_data()
    
    if df_log.empty or len(df_log) == 0:
        st.info("등록된 데이터가 없습니다.")
    else:
        df_log['일시'] = pd.to_datetime(df_log['일시'])
        
        st.subheader("🔍 데이터 필터링")
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            start_date = st.date_input("📅 시작일", value=datetime.now(KST).date() - timedelta(days=7))
            end_date = st.date_input("📅 종료일", value=datetime.now(KST).date())
        with col_f2:
            filter_default = qr_line if qr_line in lines_list else "전체"
            filter_line = st.selectbox("📍 라인 선택", ["전체"] + lines_list, index=(["전체"] + lines_list).index(filter_default))
        with col_f3:
            filter_4m = st.selectbox("🔍 4M 구분", ["전체", "Man", "Machine", "Material", "Method"])

        filtered_df = df_log.copy()
        filtered_df = filtered_df[(filtered_df['일시'].dt.date >= start_date) & (filtered_df['일시'].dt.date <= end_date)]
        
        if filter_line != "전체":
            filtered_df = filtered_df[filtered_df['라인'] == filter_line]
        if filter_4m != "전체":
            filtered_df = filtered_df[filtered_df['4M구분'] == filter_4m]

        st.markdown("---")
        
        if filtered_df.empty:
            st.warning("선택하신 조건에 맞는 데이터가 없습니다.")
        else:
            st.metric("조건부 총 발생 건수", f"{len(filtered_df)} 건")
            col1, col2 = st.columns(2)
            with col1:
                fig1 = px.bar(filtered_df["라인"].value_counts().reset_index(), x="라인", y="count", color="라인")
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                fig2 = px.pie(filtered_df["4M구분"].value_counts().reset_index(), values="count", names="4M구분", hole=0.3)
                st.plotly_chart(fig2, use_container_width=True)
            
            st.subheader("📋 변동 이력 상세내역 (최신순)")
            
            display_df = filtered_df.copy()
            display_df['일시'] = display_df['일시'].dt.strftime("%Y-%m-%d %H:%M:%S")
            
            
            st.dataframe(display_df.iloc[::-1], use_container_width=True)
            
            st.download_button(
                label="📥 현재 데이터 엑셀(CSV) 다운로드",
                data=display_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"4M_Data_Google_{datetime.now(KST).strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

# --- 6. 데이터 수정 및 삭제 화면 ---
elif menu == "✏️ 등록 데이터 수정/삭제":
    st.header("✏️ 등록 데이터 수정 및 삭제")
    admin_password = st.text_input("🔒 관리자 비밀번호를 입력하세요 ", type="password")
    
    if admin_password == "0701":
        df_log = load_data()
        if df_log.empty or len(df_log) == 0:
            st.warning("수정할 데이터가 없습니다.")
        else:
            edited_df = st.data_editor(df_log, num_rows="dynamic", use_container_width=True)
            if st.button("💾 수정한 내용을 구글 시트에 저장하기"):
                conn.update(worksheet="4M-Dashboard", data=edited_df)
                st.success("✅ 구글 스프레드시트에 성공적으로 덮어쓰기 완료되었습니다!")
    elif admin_password != "":
        st.error("❌ 비밀번호가 틀렸습니다.")

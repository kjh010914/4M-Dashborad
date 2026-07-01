import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

# --- 1. 데이터 저장 파일 설정 (항목 추가됨) ---
DB_FILE = "4m_data_log.csv"
COLUMNS = ["일시", "라인", "4M구분", "변동내용", "작업자", "품질내역", "유효성점검"]

if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=COLUMNS)
    df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")

st.set_page_config(page_title="현장 4M 관리", layout="wide")

# --- 2. QR코드 파라미터 (자동 라인 선택) ---
query_params = st.query_params
qr_line = query_params.get("line", "전체")
lines_list = ["Line-A", "Line-B", "Line-C", "Line-D"]

st.sidebar.title("🏭 사내 4M 관리 시스템")
menu = st.sidebar.radio("메뉴", ["📱 현장 변동점 등록", "🖥️ PC 실시간 대시보드", "✏️ 등록 데이터 수정/삭제"])
# --- 3. 현장 변동점 등록 화면 ---
if menu == "📱 현장 변동점 등록":
    st.header("📱 4M 변동점 현장 입력")

    with st.form(key="input_form", clear_on_submit=True):
        default_idx = lines_list.index(qr_line) if qr_line in lines_list else 0

        selected_line = st.selectbox("📍 변동 발생 라인", lines_list, index=default_idx)
        m_category = st.radio("🔍 4M 구분", ["Man (작업자)", "Machine (설비)", "Material (원재료)", "Method (작업방법)"],
                              horizontal=True)
        change_detail = st.text_area("📝 변동 내용 상세")
        worker_name = st.text_input("👤 입력자(작업자)")

        # 새로 추가된 항목
        st.markdown("---")
        quality_issue = st.text_area("⚠️ 품질 내역 (예: 불량 발생 여부, 조치사항 등)")
        validity_check = st.radio("✅ 유효성 점검 결과", ["점검 전", "양호 (문제없음)", "불량 (개선필요)"], horizontal=True)

        submit = st.form_submit_button(label="🚀 변동사항 등록")

        if submit:
            if not change_detail or not worker_name:
                st.error("⚠️ 변동 내용과 입력자를 모두 작성해주세요.")
            else:
                df_log = pd.read_csv(DB_FILE)
                new_row = pd.DataFrame([{
                    "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "라인": selected_line,
                    "4M구분": m_category.split(" ")[0],
                    "변동내용": change_detail,
                    "작업자": worker_name,
                    "품질내역": quality_issue,
                    "유효성점검": validity_check.split(" ")[0]  # '양호', '불량' 등 앞 글자만 저장
                }])
                df_log = pd.concat([df_log, new_row], ignore_index=True)
                df_log.to_csv(DB_FILE, index=False, encoding="utf-8-sig")
                st.success(f"✅ [{selected_line}] 등록 완료!")

# --- 4. PC 실시간 대시보드 화면 ---
elif menu == "🖥️ PC 실시간 대시보드":
    st.header("🖥️ 4M 변동점 실시간 대시보드")
    df_log = pd.read_csv(DB_FILE)

    if df_log.empty:
        st.info("등록된 데이터가 없습니다.")
    else:
        # 데이터의 '일시' 문자를 날짜(datetime) 형태로 변환
        df_log['일시'] = pd.to_datetime(df_log['일시'])

        # --- 검색 및 필터링 기능 ---
        st.subheader("🔍 데이터 필터링")
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            # 기본 조회 기간: 7일 전 ~ 오늘
            start_date = st.date_input("📅 시작일", value=datetime.today() - timedelta(days=7))
            end_date = st.date_input("📅 종료일", value=datetime.today())

        with col_f2:
            # QR로 들어왔으면 해당 라인이 기본값으로, 아니면 '전체'
            filter_default = qr_line if qr_line in lines_list else "전체"
            filter_line = st.selectbox("📍 라인 선택", ["전체"] + lines_list,
                                       index=(["전체"] + lines_list).index(filter_default))

        with col_f3:
            filter_4m = st.selectbox("🔍 4M 구분", ["전체", "Man", "Machine", "Material", "Method"])

        # 필터 적용
        filtered_df = df_log.copy()
        # 1. 날짜 필터
        filtered_df = filtered_df[(filtered_df['일시'].dt.date >= start_date) & (filtered_df['일시'].dt.date <= end_date)]
        # 2. 라인 필터
        if filter_line != "전체":
            filtered_df = filtered_df[filtered_df['라인'] == filter_line]
        # 3. 4M 필터
        if filter_4m != "전체":
            filtered_df = filtered_df[filtered_df['4M구분'] == filter_4m]

        st.markdown("---")

        # 필터링된 결과가 없을 경우
        if filtered_df.empty:
            st.warning("선택하신 조건에 맞는 데이터가 없습니다.")
        else:
            # 상단 요약 지표
            st.metric("조건부 총 발생 건수", f"{len(filtered_df)} 건")

            # 차트 (필터링된 데이터 반영)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 라인별 발생 건수")
                fig1 = px.bar(filtered_df["라인"].value_counts().reset_index(), x="라인", y="count", color="라인")
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                st.subheader("🍕 4M 항목별 분포")
                fig2 = px.pie(filtered_df["4M구분"].value_counts().reset_index(), values="count", names="4M구분", hole=0.3)
                st.plotly_chart(fig2, use_container_width=True)

            # 표 (필터링된 데이터 최신순)
            st.subheader("📋 변동 이력 상세내역 (최신순)")

            # 날짜를 다시 보기 좋은 문자로 변환
            display_df = filtered_df.copy()
            display_df['일시'] = display_df['일시'].dt.strftime("%Y-%m-%d %H:%M:%S")

            st.dataframe(display_df.iloc[::-1], use_container_width=True)

# --- 5. 데이터 수정 및 삭제 화면 ---
elif menu == "✏️ 등록 데이터 수정/삭제":
    st.header("✏️ 등록 데이터 수정 및 삭제")
    st.info("💡 수정: 표의 칸을 더블클릭하여 내용을 수정하세요.\n\n💡 삭제: 지우고 싶은 줄의 맨 왼쪽 빈칸을 체크한 뒤, 표 우측 상단의 휴지통 아이콘을 누르세요.")
    
    # 구글 시트에서 최신 데이터 로드
    df_log = load_data()
    
    if df_log.empty or len(df_log) == 0:
        st.warning("수정할 데이터가 없습니다.")
    else:
        # 데이터 에디터 띄우기 (num_rows="dynamic"으로 설정하여 삭제 허용)
        edited_df = st.data_editor(df_log, num_rows="dynamic", use_container_width=True)
        
        # 저장 버튼
        if st.button("💾 수정한 내용을 구글 시트에 최종 덮어쓰기"):
            with st.spinner("구글 스프레드시트 업데이트 중..."):
                conn.update(worksheet="Sheet1", data=edited_df)
            st.success("✅ 구글 스프레드시트에 성공적으로 덮어쓰기 완료되었습니다!")

import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(
    page_title="열화상 타일 정밀 충진율 분석 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS (가독성 및 UI 최적화)
st.markdown("""
    <style>
        html, body, [class*="css"] { font-size: 1.2rem !important; }
        .stApp { background-color: #f8fafc; color: #0f172a; }
        .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; max-width: 95% !important; }
        .title-card {
            background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
            padding: 1.5rem 2rem;
            border-radius: 14px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
            margin-bottom: 1.5rem;
        }
        .title-card h1 { color: #ffffff !important; font-size: 2.2rem !important; font-weight: 800 !important; margin: 0 !important; }
        .title-card p { color: #dbeafe !important; font-size: 1.15rem !important; margin-top: 0.5rem !important; }
        .sub-instruction {
            background-color: #ffffff;
            padding: 1rem 1.2rem;
            border-radius: 10px;
            border-left: 6px solid #2563eb;
            font-weight: 700;
            color: #1e293b;
            font-size: 1.3rem !important;
            margin-bottom: 1.2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .stButton>button {
            font-size: 1.2rem !important;
            font-weight: 700 !important;
            padding: 0.7rem 1.5rem !important;
            border-radius: 8px !important;
        }
        h5 {
            font-size: 1.4rem !important;
            font-weight: 700 !important;
            color: #1e293b !important;
            margin-bottom: 0.8rem !important;
        }
        h3, .stSubheader { font-size: 1.6rem !important; font-weight: 800 !important; }
        [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e2e8f0 !important; }
        [data-testid="column"] { background: #ffffff; padding: 1.2rem; border-radius: 12px; border: 1px solid #cbd5e1; }
    </style>
""", unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []
if "pts" not in st.session_state:
    st.session_state.pts = []
if "coord_key" not in st.session_state:
    st.session_state.coord_key = 0
if "last_coord" not in st.session_state:
    st.session_state.last_coord = None

st.markdown("""
    <div class="title-card">
        <h1>🔥 열화상 타일 정밀 충진율 분석 시스템</h1>
        <p>아바쿠스 시뮬레이션 기반 모델 적용 · 4점 ROI 자동 보정 및 정밀 이진화 분석 솔루션</p>
    </div>
""", unsafe_allow_html=True)

st.sidebar.header("📁 이미지 업로드")
uploaded_file = st.sidebar.file_uploader("열화상 사진 선택", type=["jpg", "jpeg", "png", "bmp"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    full_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if full_img is None:
        st.error("❌ 이미지를 불러올 수 없습니다.")
    else:
        orig_img = full_img
        img_h, img_w = orig_img.shape[:2]
        
        st.markdown('<div class="sub-instruction">📌 <b>타일 모서리 4개 순서대로 클릭 후 [분석 실행] 버튼을 누르세요</b> (1.좌상 ➔ 2.우상 ➔ 3.우하 ➔ 4.좌하)</div>', unsafe_allow_html=True)
        
        MAX_W = 400
        if img_w > MAX_W:
            canvas_w = MAX_W
            canvas_h = int(img_h * (MAX_W / img_w))
        else:
            canvas_w = img_w
            canvas_h = img_h
        
        bg_img_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(bg_img_rgb).resize((canvas_w, canvas_h))
        
        draw_img = np.array(pil_image).copy()
        for i, p in enumerate(st.session_state.pts):
            cv2.circle(draw_img, (p[0], p[1]), 8, (255, 255, 255), -1)
            cv2.circle(draw_img, (p[0], p[1]), 6, (239, 68, 68), -1)
            cv2.putText(draw_img, str(i+1), (p[0]+12, p[1]+6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            cv2.putText(draw_img, str(i+1), (p[0]+12, p[1]+6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.markdown("##### 1. 타일 영역 지정 (4점)")
            coord_val = streamlit_image_coordinates(
                Image.fromarray(draw_img),
                key=f"coord_input_{st.session_state.coord_key}"
            )

            if coord_val is not None and coord_val != st.session_state.last_coord:
                st.session_state.last_coord = coord_val
                new_pt = [coord_val["x"], coord_val["y"]]
                if len(st.session_state.pts) < 4:
                    st.session_state.pts.append(new_pt)
                    st.rerun()

            st.write(f"📍 선택된 좌표: **{len(st.session_state.pts)} / 4** 개")
            
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if st.button("🔄 리셋", use_container_width=True):
                    st.session_state.pts = []
                    st.session_state.last_coord = None
                    st.session_state.coord_key += 1
                    st.rerun()
            with b_col2:
                run_clicked = st.button("🚀 분석 실행", type="primary", use_container_width=True, disabled=(len(st.session_state.pts) != 4))

        if run_clicked and len(st.session_state.pts) == 4:
            clicked_pts = []
            x_scale = img_w / canvas_w
            y_scale = img_h / canvas_h
            for pt in st.session_state.pts:
                clicked_pts.append([int(pt[0] * x_scale), int(pt[1] * y_scale)])

            # 원근 보정 (Perspective Warp)
            src_pts = np.float32(clicked_pts)
            TARGET_W, TARGET_H = 600, 300
            dst_pts = np.float32([[0, 0], [TARGET_W, 0], [TARGET_W, TARGET_H], [0, TARGET_H]])
            
            matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped_img = cv2.warpPerspective(orig_img, matrix, (TARGET_W, TARGET_H))
            warped_rgb = cv2.cvtColor(warped_img, cv2.COLOR_BGR2RGB)
            
            # HSV 색공간 변환을 통한 정밀 이진화 및 마스크 추출
            hsv = cv2.cvtColor(warped_img, cv2.COLOR_BGR2HSV)
            
            # 1. 초록색 영역 (완전 충진 - 100%) - 범위 미세 확장으로 고충진 타일 손실 방지
            mask_green = cv2.inRange(hsv, np.array([22, 12, 12]), np.array([98, 255, 255]))

            # 2. 노란색 + 주황색 영역 (부분 충진 - 가중치를 50%로 최적화 조정)
            mask_yellow_orange = cv2.inRange(hsv, np.array([8, 15, 15]), np.array([25, 255, 255]))

            # 3. 빨강-주황 경계 천이 영역 (미세 가중치 - 20%)
            mask_boundary = cv2.inRange(hsv, np.array([3, 15, 15]), np.array([7, 255, 255]))

            # 우선순위에 따른 마스크 중복 제거
            mask_yellow_orange = cv2.bitwise_and(mask_yellow_orange, cv2.bitwise_not(mask_green))
            mask_boundary = cv2.bitwise_and(mask_boundary, cv2.bitwise_not(cv2.bitwise_or(mask_green, mask_yellow_orange)))

            # 모폴로지 연산으로 노이즈 정제
            kernel = np.ones((2, 2), np.uint8)
            mask_green = cv2.morphologyEx(mask_green, cv2.MORPH_OPEN, kernel)
            mask_yellow_orange = cv2.morphologyEx(mask_yellow_orange, cv2.MORPH_OPEN, kernel)
            mask_boundary = cv2.morphologyEx(mask_boundary, cv2.MORPH_OPEN, kernel)

            # 자잘한 노이즈 필터링 (최소 크기 10픽셀 이상)
            for m in [mask_yellow_orange, mask_boundary]:
                num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(m)
                filtered_m = np.zeros_like(m)
                for i in range(1, num_labels):
                    if stats[i, cv2.CC_STAT_AREA] >= 10:
                        filtered_m[labels == i] = 255
                m[:] = filtered_m[:]

            # 진단 결과 그레이스케일 마스크 시각화 생성 (노랑·주황은 128 중간 회색으로 표현)
            display_mask_gray = np.zeros((TARGET_H, TARGET_W), dtype=np.uint8)
            display_mask_gray[mask_boundary == 255]     = 50   # 경계 천이 영역 (20%)
            display_mask_gray[mask_yellow_orange == 255] = 128  # 노랑·주황 부분 충진 (50%)
            display_mask_gray[mask_green == 255]        = 255  # 초록색 완전 충진 (100%)

            # 픽셀 수 및 비율 계산
            green_pixels = np.sum(mask_green == 255)
            yellow_orange_pixels = np.sum(mask_yellow_orange == 255)
            boundary_pixels = np.sum(mask_boundary == 255)
            total_pixels = TARGET_W * TARGET_H

            green_pct = (green_pixels / total_pixels) * 100.0
            yellow_orange_pct = (yellow_orange_pixels / total_pixels) * 100.0
            boundary_pct = (boundary_pixels / total_pixels) * 100.0

            # 최종 가중치 반영 충진율 산출 (노랑·주황 50%, 경계 20%)
            final_ratio = min(green_pct + (yellow_orange_pct * 0.50) + (boundary_pct * 0.20), 100.0)

            with col2:
                st.markdown("##### 2. 정면 보정 이미지")
                st.image(warped_rgb, use_container_width=True)
            
            with col3:
                st.markdown("##### 3. 진단 마스크 (Grayscale)")
                st.image(display_mask_gray, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if final_ratio >= 80.0:
                st.success(f"🎉 **[기준 80% 만족 (합격)]** 최종 가중 충진율: {final_ratio:.2f}%")
            else:
                st.error(f"🚨 **[기준 80% 미달 (불합격)]** 최종 가중 충진율: {final_ratio:.2f}%")
                st.markdown("""
                **[현장 조치 지침]**
                * **공사 중:** 재시공 필요, 타일 즉시 철거 후 개량압착공법으로 재시공
                * **공사 완료 후:** 보강 필요, 줄눈 타공 후 에폭시 수지 고압 주입 보강
                """)

            saved_title = uploaded_file.name
            now = datetime.now()
            new_record = {
                "사진 이름": saved_title,
                "날짜시간": now.strftime("%Y-%m-%d %H:%M:%S"),
                "최종 충진율": f"{final_ratio:.2f}%",
                "warped_img": warped_rgb,
                "mask_img": display_mask_gray
            }
            
            if not st.session_state.history or st.session_state.history[0].get("날짜시간") != new_record["날짜시간"]:
                st.session_state.history.insert(0, new_record)

        else:
            with col2:
                st.markdown("##### 2. 정면 보정 이미지")
                st.info("좌측 이미지에서 4개의 모서리를 모두 터치해주세요.")
            with col3:
                st.markdown("##### 3. 진단 마스크 (Grayscale)")
                st.info("분석 대기 중")

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📋 **분석 이력 기록 및 이미지 진화 과정 확인**", expanded=False):
            if st.session_state.history:
                df_display = pd.DataFrame([{k: v for k, v in item.items() if k not in ["warped_img", "mask_img"]} for item in st.session_state.history])
                st.dataframe(df_display, use_container_width=True)
                
                st.markdown("🔍 **이력별 상세 보기 (보정 이미지 및 마스크 비교)**")
                selected_idx = st.selectbox(
                    "확인할 분석 이력 선택", 
                    range(len(st.session_state.history)), 
                    format_func=lambda i: f"[{st.session_state.history[i]['날짜시간']}]: {st.session_state.history[i]['사진 이름']} ({st.session_state.history[i]['최종 충진율']})"
                )
                
                if selected_idx is not None:
                    rec = st.session_state.history[selected_idx]
                    h_col1, h_col2 = st.columns(2)
                    with h_col1:
                        st.text("당시 보정된 원본 이미지")
                        st.image(rec["warped_img"], use_container_width=True)
                    with h_col2:
                        st.text("당시 생성된 진단 마스크")
                        st.image(rec["mask_img"], use_container_width=True)
                
                col_exp1, col_exp2 = st.columns([1, 1])
                with col_exp1:
                    csv_data = df_display.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("💾 CSV 다운로드", data=csv_data, file_name="tile_history.csv", mime="text/csv", use_container_width=True)
                with col_exp2:
                    if st.button("🧹 이력 초기화", use_container_width=True):
                        st.session_state.history = []
                        st.session_state.pts = []
                        st.session_state.last_coord = None
                        st.session_state.coord_key += 1
                        st.rerun()
            else:
                st.caption("저장된 이력이 없습니다.")

else:
    st.session_state.pts = []
    st.session_state.last_coord = None
    st.info("👈 사이드바에서 열화상 사진을 업로드하세요.")

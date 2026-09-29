import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

# 페이지 레이아웃 및 브라우저 탭 설정
st.set_page_config(
    page_title="열화상 타일 정밀 충진율 분석 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS 스타일링
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

st.markdown("""
    <div class="title-card">
        <h1>🔥 열화상 타일 정밀 충진율 분석 시스템</h1>
        <p>열화상 HSV 채널 가중 분석(초록 100%, 노랑 40%) 및 충진율 진단 솔루션</p>
    </div>
""", unsafe_allow_html=True)

st.sidebar.header("📁 이미지 파일 선택")
uploaded_file = st.sidebar.file_uploader("열화상 사진 선택", type=["jpg", "jpeg", "png", "bmp"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    full_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if full_img is None:
        st.error("❌ 이미지를 불러올 수 없습니다.")
    else:
        full_h, full_w = full_img.shape[:2]
        if full_h > full_w:
            orig_img = full_img[0:int(full_h * 0.33), :]
        else:
            orig_img = full_img
            
        img_h, img_w = orig_img.shape[:2]
        
        # 📌 안내 문구
        st.markdown('<div class="sub-instruction">📌 <b>RGB 타일 영역 4개 모서리 클릭:</b> 1.좌상 ➔ 2.우상 ➔ 3.우하 ➔ 4.좌하</div>', unsafe_allow_html=True)
        
        # 📌 기존보다 캔버스 크기를 크게 확장 (360px -> 520px)
        canvas_w = 520
        canvas_h = int(img_h * (canvas_w / img_w))
        
        bg_img_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(bg_img_rgb).resize((canvas_w, canvas_h))
        
        draw_img = np.array(pil_image).copy()
        for i, p in enumerate(st.session_state.pts):
            cv2.circle(draw_img, (p[0], p[1]), 8, (255, 255, 255), -1)
            cv2.circle(draw_img, (p[0], p[1]), 6, (239, 68, 68), -1)
            cv2.putText(draw_img, str(i+1), (p[0]+12, p[1]+6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
            cv2.putText(draw_img, str(i+1), (p[0]+12, p[1]+6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)

        # 📌 화면 전체 폭을 높게 활용하기 위해 3개 컬럼의 비율을 크게 설정
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.markdown("##### 1. RGB 타일 (영역 지정)")
            value = streamlit_image_coordinates(
                Image.fromarray(draw_img),
                key=f"mobile_coord_{st.session_state.coord_key}"
            )

            if value is not None:
                point = [value["x"], value["y"]]
                if len(st.session_state.pts) < 4 and point not in st.session_state.pts:
                    st.session_state.pts.append(point)
                    st.rerun()

            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                st.write(f"📍 좌표 선택: **{len(st.session_state.pts)} / 4**")
                if st.button("🔄 리셋", use_container_width=True):
                    st.session_state.pts = []
                    st.session_state.coord_key += 1
                    st.rerun()
                    
            with col_btn2:
                run_btn = st.button("🚀 분석 실행", disabled=(len(st.session_state.pts) != 4), type="primary", use_container_width=True)

        if run_btn and len(st.session_state.pts) == 4:
            clicked_pts = []
            x_scale = img_w / canvas_w
            y_scale = img_h / canvas_h
            for pt in st.session_state.pts:
                clicked_pts.append([int(pt[0] * x_scale), int(pt[1] * y_scale)])

            src_pts = np.float32(clicked_pts)
            TARGET_W, TARGET_H = 600, 300
            dst_pts = np.float32([[0, 0], [TARGET_W, 0], [TARGET_W, TARGET_H], [0, TARGET_H]])
            
            matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped_img = cv2.warpPerspective(orig_img, matrix, (TARGET_W, TARGET_H))
            warped_rgb = cv2.cvtColor(warped_img, cv2.COLOR_BGR2RGB)
            
            # 📌 가중치 방식 색상 영역 추출 (초록 1.0, 노랑 0.4)
            hsv = cv2.cvtColor(warped_img, cv2.COLOR_BGR2HSV)
            
            lower_green = np.array([36, 40, 40])
            upper_green = np.array([85, 255, 255])
            mask_green = cv2.inRange(hsv, lower_green, upper_green)
            
            lower_yellow = np.array([24, 40, 40])
            upper_yellow = np.array([35, 255, 255])
            mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
            
            display_mask = np.zeros((TARGET_H, TARGET_W), dtype=np.uint8)
            display_mask[mask_green == 255] = 255
            display_mask[mask_yellow == 255] = 180
            display_mask_bgr = cv2.cvtColor(display_mask, cv2.COLOR_GRAY2BGR)

            green_pixels = np.sum(mask_green == 255)
            yellow_pixels = np.sum(mask_yellow == 255)
            total_pixels = TARGET_W * TARGET_H

            weighted_filled_pixels = (green_pixels * 1.0) + (yellow_pixels * 0.4)
            final_ratio = (weighted_filled_pixels / total_pixels) * 100.0

            with col2:
                st.markdown("##### 2. 정면 보정")
                st.image(warped_rgb, use_container_width=True)
            
            with col3:
                st.markdown("##### 3. 진단 마스크 (BW)")
                st.image(display_mask_bgr, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            green_pct = (green_pixels / total_pixels) * 100
            yellow_pct = (yellow_pixels / total_pixels) * 100
            st.info(f"🟢 완전 충진(초록): **{green_pct:.2f}%** | 🟡 일부 충진(노랑): **{yellow_pct:.2f}%** (가중치 40% 적용)")

            if final_ratio >= 80.0:
                st.success(f"🎉 **[기준 80% 만족 (합격)]** 최종 가중 충진율: **{final_ratio:.2f}%**")
            else:
                st.error(f"🚨 **[기준 80% 미달 (불합격)]** 최종 가중 충진율: **{final_ratio:.2f}%**")

            now = datetime.now()
            new_record = {
                "사진 이름": uploaded_file.name,
                "시간": now.strftime("%H:%M:%S"),
                "완전 충진(초록)": f"{green_pct:.1f}%",
                "일부 충진(노랑)": f"{yellow_pct:.1f}%",
                "최종 충진율": f"{final_ratio:.2f}%"
            }
            
            if not st.session_state.history or st.session_state.history[0]["시간"] != new_record["시간"]:
                st.session_state.history.insert(0, new_record)

        else:
            with col2:
                st.markdown("##### 2. 정면 보정")
                st.info("4곳 터치 후 분석 버튼 클릭")
            with col3:
                st.markdown("##### 3. 진단 마스크")
                st.info("분석 대기 중")

        # =========================================================
        # 📌 [수정] 평소에는 닫혀있고 필요할 때 열어보는 접이식 이력 창 (st.expander)
        # =========================================================
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📋 **분석 이력 기록 열기 / 닫기**", expanded=False):
            if st.session_state.history:
                df = pd.DataFrame(st.session_state.history)
                st.dataframe(df, use_container_width=True)
                
                col_exp1, col_exp2 = st.columns([1, 1])
                with col_exp1:
                    csv_data = df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("💾 CSV 다운로드", data=csv_data, file_name="tile_history.csv", mime="text/csv", use_container_width=True)
                with col_exp2:
                    if st.button("🧹 이력 초기화", use_container_width=True):
                        st.session_state.history = []
                        st.session_state.pts = []
                        st.session_state.coord_key += 1
                        st.rerun()
            else:
                st.caption("저장된 이력이 없습니다.")

else:
    st.session_state.pts = []
    st.info("👈 사이드바에서 열화상 사진을 업로드하세요.")

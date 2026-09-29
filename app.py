import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(
    page_title="열화상 타일 빛 번짐 보정 자동 충진율 분석 시스템",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
    <style>
        html, body, [class*="css"] { font-size: 1.2rem !important; }
        .stApp { background-color: #f8fafc; color: #0f172a; }
        .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; max-width: 95% !important; }
        .title-card {
            background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%);
            padding: 1.5rem 2rem;
            border-radius: 14px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
            margin-bottom: 1.5rem;
        }
        .title-card h1 { color: #ffffff !important; font-size: 2.2rem !important; font-weight: 800 !important; margin: 0 !important; }
        .title-card p { color: #93c5fd !important; font-size: 1.15rem !important; margin-top: 0.5rem !important; }
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
        <h1>📊 빛 번짐(포화) 보정 열화상 타일 충진율 분석 시스템</h1>
        <p>Otsu 적응형 이진화 + 흰색 포화 영역(최고온도 지점) 자동 감지 융합</p>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 📌 사이드바 옵션
# ---------------------------------------------------------
st.sidebar.header("📁 이미지 및 빛 번짐 보정 설정")
uploaded_file = st.sidebar.file_uploader("열화상 사진 선택", type=["jpg", "jpeg", "png", "bmp"])

st.sidebar.markdown("---")
st.sidebar.header("☀️ 빛 번짐(흰색 영역) 보정 옵션")
fix_glare = st.sidebar.checkbox("빛 번짐/흰색 포화 영역 자동 포함", value=True)
white_thresh = st.sidebar.slider("흰색 포화 감지 기준 (RGB 명도)", 200, 255, 235)

st.sidebar.caption("💡 **원리:** 열화상 촬영 시 빛 반사나 최고 온도로 인해 흰색으로 번진 영역을 '가장 뜨거운 충진 영역'으로 판별하여 분석 결과에 100% 반영합니다.")

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    full_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if full_img is None:
        st.error("❌ 이미지를 불러올 수 없습니다.")
    else:
        orig_img = full_img
        img_h, img_w = orig_img.shape[:2]
        
        st.markdown('<div class="sub-instruction">📌 <b>RGB 타일 영역 4개 모서리 클릭:</b> 1.좌상 ➔ 2.우상 ➔ 3.우하 ➔ 4.좌하</div>', unsafe_allow_html=True)
        
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
                run_btn = st.button("🚀 자동 분석 실행", disabled=(len(st.session_state.pts) != 4), type="primary", use_container_width=True)

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
            
            # --- 1. 대비 선명화 (CLAHE 적용) ---
            gray_img = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced_gray = clahe.apply(gray_img)
            blurred = cv2.GaussianBlur(enhanced_gray, (5, 5), 0)
            
            # --- 2. Otsu 적응형 이진화 ---
            otsu_thresh, binary_mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # --- 3. 빛 번짐 / 흰색 포화 영역 보정 (White Glare Mask) ---
            if fix_glare:
                # RGB 모든 채널이 설정값 이상으로 매우 높은 영역 (흰색 포화 지점)
                white_mask = cv2.inRange(warped_rgb, 
                                         np.array([white_thresh, white_thresh, white_thresh]), 
                                         np.array([255, 255, 255]))
                
                # Otsu 이진화 마스크와 흰색 포화 마스크를 합성(OR 연산)
                combined_mask = cv2.bitwise_or(binary_mask, white_mask)
            else:
                combined_mask = binary_mask

            # --- 4. 노이즈 및 자잘한 구멍 메우기 (Morphological Closing) ---
            kernel = np.ones((5, 5), np.uint8)
            # MORPH_CLOSE: 팽창 후 침식을 수행하여 내부의 자잘한 미충진/빛번짐 구멍을 메움
            final_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
            final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, kernel)

            # 비율 계산
            filled_pixels = np.sum(final_mask == 255)
            total_pixels = TARGET_W * TARGET_H
            final_ratio = (filled_pixels / total_pixels) * 100.0

            # 마스크 시각화
            display_mask_bgr = cv2.cvtColor(final_mask, cv2.COLOR_GRAY2BGR)

            with col2:
                st.markdown("##### 2. 정면 보정")
                st.image(warped_rgb, use_container_width=True)
            
            with col3:
                st.markdown("##### 3. 보정 진단 마스크")
                st.image(display_mask_bgr, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            st.info(f"🤖 **[자동 연산 정보]:** Otsu 경계값: {otsu_thresh:.1f} | 빛 번짐 보정: {'적용됨' if fix_glare else '미적용'}")

            if final_ratio >= 80.0:
                st.success(f"🎉 **[기준 80% 만족 (합격)]** 보정 후 충진율: **{final_ratio:.2f}%**")
            else:
                st.error(f"🚨 **[기준 80% 미달 (불합격)]** 보정 후 충진율: **{final_ratio:.2f}%**")

            now = datetime.now()
            new_record = {
                "사진 이름": uploaded_file.name,
                "시간": now.strftime("%H:%M:%S"),
                "빛번짐 보정": "적용" if fix_glare else "미적용",
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

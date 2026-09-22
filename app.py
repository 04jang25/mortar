import streamlit as st
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from PIL import Image
from streamlit_drawable_canvas import st_canvas

st.set_page_config(
    page_title="LH 열화상 타일 정밀 충진율 분석 시스템",
    layout="wide",
    initial_sidebar_state="collapsed" # 모바일 화면 확보를 위해 사이드바 기본 접음
)

if "history" not in st.session_state:
    st.session_state.history = []

st.title("🔥 LH 기준 열화상 타일 정밀 충진율 분석 시스템 v1.0")
st.markdown("---")

st.sidebar.header("📁 이미지 파일 선택")
uploaded_file = st.sidebar.file_uploader("열화상 사진을 선택하세요", type=["jpg", "jpeg", "png", "bmp"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    orig_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if orig_img is None:
        st.error("❌ 이미지를 불러올 수 없습니다.")
    else:
        img_h, img_w = orig_img.shape[:2]
        
        # 모바일 환경 대응: 모바일 화면 폭에 맞춘 가상 캔버스 크기
        canvas_w = 340
        canvas_h = int(img_h * (canvas_w / img_w))
        
        bg_img_rgb = cv2.cvtColor(orig_img, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(bg_img_rgb)
        
        st.subheader("📌 [1단계] 이미지에서 모서리 4곳을 터치(클릭)하세요")
        st.info("순서: 1.좌상(TL) ➔ 2.우상(TR) ➔ 3.우하(BR) ➔ 4.좌하(BL)")
        
        # 캔버스 배치
        canvas_result = st_canvas(
            fill_color="rgba(239, 68, 68, 0.8)",
            stroke_width=3,
            stroke_color="#ef4444",
            background_image=pil_image,
            update_streamlit=True,
            height=canvas_h,
            width=canvas_w,
            drawing_mode="point",
            point_display_radius=10, # 모바일 터치 인식을 위해 손가락 크기에 맞춰 점 크기 확대
            display_toolbar=False,
            key="canvas_tile_mobile",
        )

        # 클릭/터치 좌표 수집
        clicked_pts = []
        if canvas_result.json_data is not None and "objects" in canvas_result.json_data:
            for obj in canvas_result.json_data["objects"]:
                x_scale = img_w / canvas_w
                y_scale = img_h / canvas_h
                orig_x = int(obj["left"] * x_scale)
                orig_y = int(obj["top"] * y_scale)
                clicked_pts.append([orig_x, orig_y])

        st.caption(f"📍 현재 선택된 모서리 좌표 수: **{len(clicked_pts)} / 4 개**")

        # 4개 선택 완료 시 버튼 활성화
        run_btn = st.button("🚀 충진율 정밀 분석 실행", disabled=(len(clicked_pts) != 4), use_container_width=True)
        
        if len(clicked_pts) != 4:
            st.warning("⚠️ 모서리 4곳을 터치해야 분석 버튼이 활성화됩니다. (초과 선택 시 페이지를 새로고침 해주세요)")

        # 분석 실행
        if run_btn and len(clicked_pts) == 4:
            src_pts = np.float32(clicked_pts)
            TARGET_W, TARGET_H = 600, 300
            dst_pts = np.float32([[0, 0], [TARGET_W, 0], [TARGET_W, TARGET_H], [0, TARGET_H]])
            
            matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped_img = cv2.warpPerspective(orig_img, matrix, (TARGET_W, TARGET_H))
            
            blurred = cv2.GaussianBlur(warped_img, (5, 5), 0)
            hsv_warped = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
            
            lower_red1 = np.array([0, 50, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([145, 50, 50])
            upper_red2 = np.array([180, 255, 255])
            mask_red = cv2.inRange(hsv_warped, lower_red1, upper_red1) | cv2.inRange(hsv_warped, lower_red2, upper_red2)
            
            lower_white = np.array([0, 0, 200])
            upper_white = np.array([180, 80, 255])
            mask_white = cv2.inRange(hsv_warped, lower_white, upper_white)
            
            mask_full = cv2.bitwise_or(mask_red, mask_white)
            
            lower_yellow = np.array([11, 50, 100])
            upper_yellow = np.array([35, 255, 255])
            mask_partial = cv2.inRange(hsv_warped, lower_yellow, upper_yellow)
            
            kernel = np.ones((5, 5), np.uint8)
            mask_full = cv2.morphologyEx(mask_full, cv2.MORPH_CLOSE, kernel)
            mask_partial = cv2.morphologyEx(mask_partial, cv2.MORPH_CLOSE, kernel)
            
            total_pixels = TARGET_W * TARGET_H
            full_pixels = np.sum(mask_full == 255)
            partial_pixels = np.sum(mask_partial == 255)
            
            WEIGHT_FULL = 1.0
            WEIGHT_PARTIAL = 0.45
            weighted_filled_pixels = (full_pixels * WEIGHT_FULL) + (partial_pixels * WEIGHT_PARTIAL)
            final_ratio = (weighted_filled_pixels / total_pixels) * 100
            
            display_mask = np.ones_like(warped_img) * 255
            display_mask[mask_partial == 255] = [0, 255, 255]
            display_mask[mask_full == 255] = [0, 0, 255]
            
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.markdown("**2. 투시 보정 정면 타일**")
                st.image(cv2.cvtColor(warped_img, cv2.COLOR_BGR2RGB), use_container_width=True)
            
            with col_res2:
                st.markdown("**3. 충진 진단 분석 마스크**")
                st.image(cv2.cvtColor(display_mask, cv2.COLOR_BGR2RGB), use_container_width=True)

            st.markdown("---")
            
            if final_ratio >= 80.0:
                st.success(f"🎉 **[LH 시방 기준 만족 (합격)]** 최종 산출 충진율: **{final_ratio:.2f}%**")
                st.caption("• LH 표준 시방 요구조건(충진율 80% 이상)을 충족합니다. 별도의 보강 조치가 필요하지 않습니다.")
            else:
                st.error(f"🚨 **[LH 시방 기준 미달 (불합격)]** 최종 산출 충진율: **{final_ratio:.2f}%**")
                st.markdown("""
                ### ⚠️ LH 미달시 단계별 현장 조치 지침
                1. **공사 중 (시공 진행 단계):**
                   - 미충진 부위 타일 **즉시 철거 후 전면 재시공** 실시
                   - 바탕면 이물질 제거 및 **개량압착공법(타일 뒷면+바탕면 양면 도포)** 적용
                2. **공사 완료 후 (완공/검수 단계):**
                   - 줄눈 타공 후 **에폭시/주입용 에폭시 수지 고압 주입 보강공법** 적용
                """)

            now = datetime.now()
            new_record = {
                "사진 이름": uploaded_file.name,
                "날짜": now.strftime("%Y-%m-%d"),
                "시간": now.strftime("%H:%M:%S"),
                "충진율(%)": f"{final_ratio:.2f}%"
            }
            
            if not st.session_state.history or st.session_state.history[0]["사진 이름"] != uploaded_file.name:
                st.session_state.history.insert(0, new_record)

        st.markdown("---")
        st.subheader("📋 누적 분석 이력 목록")
        if st.session_state.history:
            df = pd.DataFrame(st.session_state.history)
            st.dataframe(df, use_container_width=True)
            
            csv_data = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="💾 CSV 내보내기",
                data=csv_data,
                file_name="tile_analysis_history.csv",
                mime="text/csv",
                use_container_width=True
            )
            if st.button("🧹 이력 초기화", use_container_width=True):
                st.session_state.history = []
                st.rerun()
        else:
            st.write("아직 기록된 분석 이력이 없습니다.")

else:
    st.info("👈 왼쪽 상단 메뉴(>]를 눌러 사이드바에서 열화상 사진을 업로드해 주세요.")

# main.py
import streamlit as st
import pandas as pd

# Import các module đã được module hóa
from config import HARCODED_GDRIVE_URL, RECOMMENDATION_SHEET, PRICE_SHEET
from src.data_loader import load_data_from_gdrive
from src.analyzer import process_stock_data, calculate_win_rate_summary
from src.ui import setup_sidebar, display_results_html as display_results

def main():
    """
    Hàm chính điều phối toàn bộ ứng dụng Streamlit.
    """
    # --- Cấu hình trang ---
    st.set_page_config(layout="wide", page_title="Bộ lọc Cổ phiếu")
    
    
    # --- Sidebar để lấy tùy chọn của người dùng ---
    period_offset, period_label = setup_sidebar()

    # --- Quy trình chính ---
    if not HARCODED_GDRIVE_URL or HARCODED_GDRIVE_URL == "YOUR_GOOGLE_DRIVE_LINK_HERE":
        st.info("Chào mừng! Vui lòng chỉnh sửa file config.py và thêm link Google Drive vào biến 'HARCODED_GDRIVE_URL' để bắt đầu.")
        return

    with st.spinner("Đang tải và xử lý dữ liệu..."):
        try:
            # 1. Tải dữ liệu
            df_rec, df_price = load_data_from_gdrive(HARCODED_GDRIVE_URL, RECOMMENDATION_SHEET, PRICE_SHEET)

            if df_rec.empty or df_price.empty:
                st.warning("Không thể tải dữ liệu hoặc file không hợp lệ. Vui lòng kiểm tra lại link và định dạng file.")
                return
            
            # 2. Xử lý và phân tích
            df1, df2, df3, df4 = process_stock_data(df_rec, df_price, period_offset, period_label)
            
            results = {
                "Out_sang_MarketPerform": df1,
                "MarketPerform_sang_Out": df2,
                "Khuyen_nghi_BUY": df3,
                "Khuyen_nghi_UnderPerform": df4
            }
            
            # 3. Tính toán Win Rate
            summary_df = calculate_win_rate_summary(results)

            # 4. Hiển thị kết quả
            display_results(results, summary_df, period_label)

        except Exception as e:
            st.error(f"Một lỗi không mong muốn đã xảy ra: {e}")

if __name__ == "__main__":
    main()
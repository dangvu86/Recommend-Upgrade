# src/data_loader.py
import pandas as pd
import re
import streamlit as st
from typing import Tuple, Optional

def convert_gdrive_link(gdrive_url: str) -> Optional[str]:
    """
    Chuyển đổi link chia sẻ Google Drive (file hoặc sheet) thành link tải trực tiếp.
    
    Args:
        gdrive_url (str): Link Google Drive.

    Returns:
        Optional[str]: Link tải trực tiếp hoặc None nếu link không hợp lệ.
    """
    # Regex cho link Google Sheets
    sheet_match = re.search(r'/spreadsheets/d/([a-zA-Z0-9_-]+)', gdrive_url)
    if sheet_match:
        sheet_id = sheet_match.group(1)
        return f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx'

    # Regex cho link Google Drive (file Excel)
    file_match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', gdrive_url)
    if file_match:
        file_id = file_match.group(1)
        return f'https://drive.google.com/uc?export=download&id={file_id}'
        
    return None

@st.cache_data
def load_data_from_gdrive(gdrive_url: str, rec_sheet: str, price_sheet: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Tải dữ liệu từ file Excel trên Google Drive.

    Args:
        gdrive_url (str): Link Google Drive đã được hardcode.
        rec_sheet (str): Tên sheet chứa dữ liệu khuyến nghị.
        price_sheet (str): Tên sheet chứa dữ liệu giá.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Hai DataFrame chứa dữ liệu khuyến nghị và giá.
    
    Raises:
        FileNotFoundError: Nếu không tìm thấy các sheet cần thiết trong file Excel.
        Exception: Cho các lỗi khác khi tải hoặc đọc file.
    """
    download_url = convert_gdrive_link(gdrive_url)
    if not download_url:
        raise ValueError("Link Google Drive không hợp lệ. Vui lòng kiểm tra lại link trong file config.py.")

    try:
        xls = pd.ExcelFile(download_url, engine='openpyxl')
        
        if rec_sheet not in xls.sheet_names or price_sheet not in xls.sheet_names:
            raise FileNotFoundError(f"Lỗi: File Excel phải chứa cả hai sheet tên là '{rec_sheet}' và '{price_sheet}'.")
        
        df_rec = pd.read_excel(xls, sheet_name=rec_sheet, header=1, index_col=0)
        df_price = pd.read_excel(xls, sheet_name=price_sheet)
        
        return df_rec, df_price
    except Exception as e:
        st.error(f"Đã xảy ra lỗi khi tải hoặc xử lý file: {e}")
        st.error("Vui lòng đảm bảo link của bạn được chia sẻ ở chế độ 'Bất kỳ ai có đường liên kết'.")
        return pd.DataFrame(), pd.DataFrame()
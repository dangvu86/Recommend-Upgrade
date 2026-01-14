# src/ui_html.py
import streamlit as st
import pandas as pd
from pandas.tseries.offsets import DateOffset
from typing import Tuple, Dict
from src.utils import to_excel
import base64
import streamlit.components.v1 as components # Import component HTML
import datetime # Thêm thư viện datetime

# Hàm setup_sidebar và create_download_link_html giữ nguyên như cũ
def setup_sidebar() -> Tuple[DateOffset, str]:
    """
    Cài đặt và hiển thị các widget trong sidebar, bao gồm cả tùy chọn tùy chỉnh ngày.
    """
    st.sidebar.header("⚙️ Tùy chọn Phân tích")

    period_options = {
        '3 tháng': (DateOffset(months=3), '3T'),
        '6 tháng': (DateOffset(months=6), '6T'),
        '1 năm': (DateOffset(months=12), '1Y')
    }

    # Mặc định vẫn là '6 tháng'
    selected_period = st.sidebar.selectbox(
        "Chọn khoảng thời gian tính hiệu suất:",
        options=list(period_options.keys()),
        index=1
    )

    period_offset, period_label = period_options[selected_period]

    # Thêm chú thích về cách xác định Win Rate
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Cách Xác Định Win Rate")
    st.sidebar.markdown("""
    **Nguyên tắc chung:**
    - Winrate = (Số lần dự đoán đúng / Tổng số khuyến nghị) × 100%
    - So sánh hiệu suất cổ phiếu với chỉ số VNINDEX

    **Chi tiết từng cột:**

    📉 **OUTPERFORM → MARKET-PERFORM**
    - Đếm % số lần cổ phiếu **UNDERPERFORM** VNINDEX
    - Winrate cao = Quyết định hạ khuyến nghị chính xác

    🚀 **MARKET-PERFORM → OUTPERFORM**
    - Đếm % số lần cổ phiếu **OUTPERFORM** VNINDEX
    - Winrate cao = Quyết định nâng khuyến nghị chính xác

    ✅ **Khuyến nghị BUY**
    - Đếm % số lần cổ phiếu **OUTPERFORM** VNINDEX
    - Winrate cao = Khuyến nghị mua chính xác

    ⚠️ **Khuyến nghị UNDER-PERFORM**
    - Đếm % số lần cổ phiếu **UNDERPERFORM** VNINDEX
    - Winrate cao = Khuyến nghị underperform chính xác
    """)

    return period_offset, period_label

def create_download_link_html(df_dict: dict, filename: str, link_text: str) -> str:
    excel_data = to_excel(df_dict)
    b64 = base64.b64encode(excel_data).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" class="download-button">{link_text}</a>'


def display_results_html(results: Dict[str, pd.DataFrame], summary_df: pd.DataFrame, period_label: str):
    """
    Hiển thị kết quả phân tích với bảng Win Rate header 2 tầng và styling đẹp.
    """
    
    # --- Styling functions ---
    def style_rating(val):
        color = ''
        if val == 'Outperform': color = '#D4EDDA'
        elif val == 'Underperform': color = '#F8D7DA'
        return f'background-color: {color}'

    def style_win_rate_cell(val):
        """Style cho ô win rate (tô màu theo % > 50 hoặc < 50)"""
        if isinstance(val, str) and '%' in val:
            try:
                num_val = float(val.split('%')[0].strip())
                if num_val > 50: return 'background-color: #D4EDDA; color: #155724;'
                elif num_val < 50: return 'background-color: #F8D7DA; color: #721c24;'
            except: pass
        return ''

    def style_alpha_cell(val):
        """Style cho ô alpha (tô màu theo dấu + hoặc -)"""
        if isinstance(val, str):
            if val.startswith('+'): return 'background-color: #D4EDDA; color: #155724;'
            elif val.startswith('-'): return 'background-color: #F8D7DA; color: #721c24;'
        return ''

    # --- Tạo HTML cho bảng Win Rate với header 2 tầng ---
    def create_summary_table_html(df: pd.DataFrame) -> str:
        if df.empty:
            return "<p>Không có đủ dữ liệu để tạo bảng thống kê.</p>"
        
        # Lấy thông tin cột
        if isinstance(df.columns, pd.MultiIndex):
            level0 = df.columns.get_level_values(0).unique().tolist()
            if 'Năm' in level0:
                level0.remove('Năm')
        else:
            # Fallback nếu không phải MultiIndex
            return df.to_html(index=False)
        
        # Màu sắc cho từng loại khuyến nghị
        colors = {
            'Out → MP': ('#e74c3c', '#fadbd8'),  # Đỏ
            'MP → Out': ('#27ae60', '#d5f5e3'),  # Xanh lá
            'BUY': ('#3498db', '#d6eaf8'),        # Xanh dương
            'UNDER': ('#f39c12', '#fdebd0')       # Cam
        }
        
        html = '''
        <table class="summary-table">
            <thead>
                <tr class="header-row-1">
                    <th rowspan="2" class="year-header" style="text-align: center;">NĂM</th>
        '''
        
        # Header row 1: Tên loại khuyến nghị
        for cat in level0:
            bg_color, _ = colors.get(cat, ('#6c757d', '#e9ecef'))
            html += f'<th colspan="2" style="background: {bg_color}; color: white; text-align: center;">{cat}</th>'
        
        html += '</tr><tr class="header-row-2">'
        
        # Header row 2: WinRate | Avg Alpha
        for cat in level0:
            _, light_color = colors.get(cat, ('#6c757d', '#e9ecef'))
            html += f'<th style="background: {light_color}; text-align: center;">WinRate</th>'
            html += f'<th style="background: {light_color}; text-align: center;">Avg Alpha</th>'
        
        html += '</tr></thead><tbody>'
        
        # Data rows
        for idx, row in df.iterrows():
            is_total = row.iloc[0] == 'Total'
            row_class = 'total-row' if is_total else ''
            html += f'<tr class="{row_class}">'
            
            # Cột Năm
            year_val = row.iloc[0]
            html += f'<td class="year-cell">{year_val}</td>'
            
            # Các cột dữ liệu
            col_idx = 1
            for cat in level0:
                winrate_val = row.iloc[col_idx] if col_idx < len(row) else '—'
                alpha_val = row.iloc[col_idx + 1] if col_idx + 1 < len(row) else '—'
                
                # Style cho WinRate
                wr_style = style_win_rate_cell(winrate_val)
                html += f'<td style="{wr_style}">{winrate_val}</td>'
                
                # Style cho Alpha
                alpha_style = style_alpha_cell(alpha_val)
                html += f'<td style="{alpha_style}">{alpha_val}</td>'
                
                col_idx += 2
            
            html += '</tr>'
        
        html += '</tbody></table>'
        return html

    # Tạo HTML cho bảng summary
    summary_html = create_summary_table_html(summary_df)

    results_html = {}
    for name, df in results.items():
        if not df.empty:
            numeric_cols = [col for col in df.columns if 'Hiệu suất' in col or 'vs VNINDEX' in col]
            styler = df.style.map(style_rating, subset=['Rating'])
            styler.set_properties(**{'text-align': 'right'}, subset=numeric_cols)
            results_html[name] = styler.hide(axis="index").to_html(embed_css=True)
        else:
            results_html[name] = f"<p>Không có dữ liệu cho mục này.</p>"
            
    dfs_for_export = {"Thong_ke_Win_Rate": summary_df, **results}
    download_filename = f"ket_qua_loc_co_phieu_{period_label}.xlsx"
    download_button_html = create_download_link_html(dfs_for_export, download_filename, "📁 Tải file Excel")


    # --- Mã HTML và CSS ---
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        .container {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            width: 100%;
        }}
        h3, h4 {{
            color: #0d3b66;
            border-bottom: 2px solid #f4d35e;
            padding-bottom: 5px;
            margin-top: 25px;
        }}
        h4 > a {{
            text-decoration: none;
            color: inherit;
        }}
        .grid-container {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}
        .grid-item {{
            width: 100%;
        }}
        .table-container {{
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.75em;
            table-layout: fixed; /* Giúp CSS width hoạt động ổn định */
        }}
        th, td {{
            padding: 6px 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
            word-wrap: break-word; /* Chống vỡ layout nếu nội dung quá dài */
        }}
        th {{
            background-color: #f2f2f2;
            position: sticky;
            top: 0;
        }}
        .winrate-table table th, .winrate-table table td {{
            text-align: right;
        }}
        .winrate-table table th:first-child, .winrate-table table td:first-child {{
            text-align: left;
        }}
        .download-button {{ /* ... */ }}

        /* === STYLING CHO BẢNG WIN RATE HEADER 2 TẦNG === */
        .summary-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 0.85em;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }}
        
        .summary-table th {{
            padding: 12px 10px;
            text-align: center;
            font-weight: 600;
            border: none;
            position: sticky;
        }}
        
        .summary-table .header-row-1 th {{
            font-size: 1.1em;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}
        
        .summary-table .header-row-2 th {{
            font-size: 0.85em;
            font-weight: 500;
            color: #333;
        }}
        
        .summary-table .year-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            vertical-align: middle;
        }}
        
        .summary-table td {{
            padding: 10px 12px;
            text-align: center;
            border-bottom: 1px solid #eee;
            transition: background-color 0.2s ease;
        }}
        
        .summary-table tbody tr:hover {{
            background-color: #f8f9fa;
        }}
        
        .summary-table .year-cell {{
            font-weight: 700;
            background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
            color: #4a4a4a;
        }}
        
        .summary-table .total-row {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        }}
        
        .summary-table .total-row td {{
            color: white;
            font-weight: 700;
            border-bottom: none;
        }}
        
        .summary-table .total-row .year-cell {{
            background: linear-gradient(135deg, #1a252f 0%, #2c3e50 100%);
            color: #f8f9fa;
        }}

        .download-section {{
            margin-top: 30px;
            padding-top: 15px;
            border-top: 1px solid #ccc;
        }}

        /* === CSS ĐỂ TÙY CHỈNH ĐỘ RỘNG CỘT CHI TIẾT === */
        .table-container th:nth-child(1), .table-container td:nth-child(1) {{ width: 13%; }} /* Cổ phiếu */
        .table-container th:nth-child(2), .table-container td:nth-child(2) {{ width: 18%; }} /* Ngày */
        .table-container th:nth-child(3), .table-container td:nth-child(3) {{ width: 15%; }} /* Hiệu suất CP */
        .table-container th:nth-child(4), .table-container td:nth-child(4) {{ width: 15%; }} /* Hiệu suất VNINDEX */
        .table-container th:nth-child(5), .table-container td:nth-child(5) {{ width: 15%; }} /* vs VNINDEX */
        .table-container th:nth-child(6), .table-container td:nth-child(6) {{ width: 20%; }} /* Rating */

    </style>
    </head>
    <body>
    <div class="container">
        <h3>📊 Win Rate</h3>
        <div class="winrate-table">
            {summary_html}
        </div>

        
        <div class="grid-container">
            <div class="grid-item">
                <h4>📉 OUTPERFORM to MARKET-PERFORM</h4>
                <div class="table-container">{results_html["Out_sang_MarketPerform"]}</div>
            </div>
            <div class="grid-item">
                <h4>🚀 MARKET-PERFORM to OUTPERFORM</h4>
                <div class="table-container">{results_html["MarketPerform_sang_Out"]}</div>
            </div>
            <div class="grid-item">
                <h4>✅ Khuyến nghị BUY</h4>
                <div class="table-container">{results_html["Khuyen_nghi_BUY"]}</div>
            </div>
            <div class="grid-item">
                <h4>⚠️ Khuyến nghị UNDER-PERFORM</h4>
                <div class="table-container">{results_html["Khuyen_nghi_UnderPerform"]}</div>
            </div>
        </div>
        
        <div class="download-section">
            <h3>📥 Tải xuống kết quả</h3>
            {download_button_html}
        </div>
    </div>
    </body>
    </html>
    """

    # --- Lệnh hiển thị (không đổi) ---
    components.html(html_template, height=1800)
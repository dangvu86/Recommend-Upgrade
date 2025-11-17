# Recommend-Upgrade - Hệ thống Phân tích Khuyến nghị Cổ phiếu

## Tổng quan dự án

Ứng dụng Streamlit phân tích hiệu suất của các khuyến nghị cổ phiếu so với chỉ số VNINDEX, tính toán tỷ lệ thành công (win rate) của các khuyến nghị đầu tư.

## Cấu trúc dự án

```
Recommend-Upgrade-main/
├── main.py                 # File chính, điều phối ứng dụng Streamlit
├── config.py               # Cấu hình: Google Drive URL, tên sheets
├── requirements.txt        # Dependencies
├── .env                    # Biến môi trường
└── src/
    ├── data_loader.py      # Tải dữ liệu từ Google Drive
    ├── analyzer.py         # Logic phân tích và tính toán hiệu suất
    ├── ui.py              # Giao diện người dùng (sidebar, display)
    └── utils.py           # Tiện ích (export Excel)
```

## Luồng hoạt động chính

1. **Tải dữ liệu** (`data_loader.py`):
   - Đọc file Excel từ Google Drive
   - 2 sheets: Khuyến nghị (Recommendation) và Giá (Price)

2. **Xử lý dữ liệu** (`analyzer.py`):
   - Phát hiện thay đổi khuyến nghị (OUTPERFORM ↔ MARKET-PERFORM)
   - Phát hiện khuyến nghị BUY và UNDER-PERFORM
   - Tính hiệu suất cổ phiếu vs VNINDEX theo khoảng thời gian

3. **Tính Win Rate** (`analyzer.py`):
   - Phân loại theo năm
   - Tính tỷ lệ dự đoán đúng

4. **Hiển thị kết quả** (`ui.py`):
   - Bảng thống kê Win Rate
   - 4 bảng chi tiết khuyến nghị
   - Xuất file Excel

## Cách tính hiệu suất

### Ngày bắt đầu tính
- **OUTPERFORM ↔ MARKET-PERFORM**: Ngày thay đổi khuyến nghị
- **BUY & UNDER-PERFORM**: Ngày phát hành khuyến nghị

### Công thức
```python
# Ngày kết thúc = Ngày bắt đầu + Khoảng thời gian (3T/6T/1Y)
stock_performance = (end_price / start_price) - 1
vnindex_performance = (end_price_vnindex / start_price_vnindex) - 1
vs_vnindex = stock_performance - vnindex_performance

# Rating
if vs_vnindex > 0: "Outperform"
if vs_vnindex < 0: "Underperform"
```

### Lấy giá
- **Giá bắt đầu**: Giá gần nhất SAU hoặc BẰNG ngày bắt đầu
- **Giá kết thúc**: Giá gần nhất TRƯỚC hoặc BẰNG ngày kết thúc

## Cách tính Win Rate

### 4 loại khuyến nghị được phân tích

| Loại | Tính Win Rate | Ý nghĩa |
|------|---------------|---------|
| **Out_sang_MarketPerform** | % Underperform | Hạ khuyến nghị → Cổ phiếu thực sự underperform = Đúng |
| **MarketPerform_sang_Out** | % Outperform | Nâng khuyến nghị → Cổ phiếu thực sự outperform = Đúng |
| **Khuyen_nghi_BUY** | % Outperform | Khuyến nghị mua → Cổ phiếu outperform = Đúng |
| **Khuyen_nghi_UnderPerform** | % Underperform | Khuyến nghị underperform → Cổ phiếu thực sự underperform = Đúng |

### Công thức
```python
# Với Out_sang_MarketPerform & Khuyen_nghi_UnderPerform
target_rating = 'Underperform'
winrate = (số lần Underperform / tổng số khuyến nghị) × 100%

# Với MarketPerform_sang_Out & Khuyen_nghi_BUY
target_rating = 'Outperform'
winrate = (số lần Outperform / tổng số khuyến nghị) × 100%
```

### Hiển thị
- Win rate theo từng năm
- Win rate tổng (Total)
- Format: `"75.00% (3/4)"` = 3 đúng / 4 tổng số

## Files quan trọng

### `src/analyzer.py`
- `add_performance_cols()`: Tính hiệu suất cho từng khuyến nghị
- `process_stock_data()`: Xử lý dữ liệu, phát hiện thay đổi khuyến nghị
- `calculate_win_rate_summary()`: Tính bảng thống kê win rate

### `src/ui.py`
- `setup_sidebar()`: Cấu hình sidebar (chọn thời gian, chú thích)
- `display_results_html()`: Hiển thị kết quả dưới dạng HTML/CSS

### `config.py`
- `HARCODED_GDRIVE_URL`: Link Google Drive chứa file Excel
- `RECOMMENDATION_SHEET`: Tên sheet khuyến nghị
- `PRICE_SHEET`: Tên sheet giá
- `VNINDEX_TICKER`: Mã chỉ số VNINDEX

## Cài đặt và chạy

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình Google Drive URL trong config.py
# Đảm bảo file được share "Anyone with the link"

# Chạy ứng dụng
streamlit run main.py
```

## Tùy chọn phân tích

Sidebar cung cấp:
- **3 tháng**: Tính hiệu suất sau 3 tháng kể từ ngày khuyến nghị
- **6 tháng** (mặc định): Tính hiệu suất sau 6 tháng
- **1 năm**: Tính hiệu suất sau 1 năm

## Xuất dữ liệu

Ứng dụng cho phép tải xuống file Excel chứa:
- Bảng thống kê Win Rate
- 4 bảng chi tiết khuyến nghị với đầy đủ thông tin hiệu suất

## Lưu ý kỹ thuật

1. **Caching**: Dữ liệu từ Google Drive được cache (`@st.cache_data`) để tăng tốc độ
2. **Format ngày**: Các cột ngày được format thành `'%Y-%m-%d'` trước khi hiển thị
3. **Xử lý missing data**: Nếu không tìm thấy giá cho ngày cụ thể, hệ thống tìm giá gần nhất
4. **Streamlit rerun**: Khi thay đổi khoảng thời gian, ứng dụng tự động tính lại hiệu suất

## Phân tích dữ liệu

### Sheet Khuyến nghị (Recommendation)
- Index: Ngày
- Columns: Mã cổ phiếu
- Values: Khuyến nghị (OUTPERFORM, MARKET-PERFORM, BUY, UNDER-PERFORM)

### Sheet Giá (Price)
- Columns: Date, Stock, Price
- Format: Long format (mỗi dòng = 1 mã + 1 ngày + 1 giá)

## Changelog

### Version hiện tại
- ✅ Tính Win Rate dựa trên logic khác nhau cho từng loại khuyến nghị
- ✅ Chú thích chi tiết trong sidebar về cách tính Win Rate
- ✅ Bỏ option "Tùy chỉnh" khỏi selectbox thời gian
- ✅ Hiển thị kết quả dưới dạng HTML với styling đẹp
- ✅ Xuất Excel với nhiều sheets

## Liên hệ & Hỗ trợ

Nếu có vấn đề hoặc cần hỗ trợ, vui lòng kiểm tra:
1. Google Drive URL có đúng và được share công khai
2. File Excel có đủ 2 sheets với tên đúng
3. Format dữ liệu trong sheets đúng chuẩn

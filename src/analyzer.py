# src/analyzer.py
import pandas as pd
from pandas.tseries.offsets import DateOffset
import streamlit as st
from typing import Tuple, Dict, Any
from config import VNINDEX_TICKER

def add_performance_cols(df: pd.DataFrame, prices_pivot: pd.DataFrame, date_col_name: str, period_offset: DateOffset, period_label: str) -> pd.DataFrame:
    """
    Thêm các cột hiệu suất và rating vào DataFrame dựa trên khoảng thời gian được chọn.

    Args:
        df (pd.DataFrame): DataFrame kết quả cần thêm cột.
        prices_pivot (pd.DataFrame): DataFrame giá đã được pivot.
        date_col_name (str): Tên cột chứa ngày bắt đầu tính hiệu suất.
        period_offset (DateOffset): Khoảng thời gian để tính toán (vd: DateOffset(months=6)).
        period_label (str): Nhãn cho khoảng thời gian (vd: '6T').

    Returns:
        pd.DataFrame: DataFrame đã được thêm các cột hiệu suất.
    """
    if df.empty or prices_pivot.empty:
        df[f'Hiệu suất CP ({period_label})'] = 'N/A'
        df[f'Hiệu suất VNINDEX ({period_label})'] = 'N/A'
        df[f'vs VNINDEX ({period_label})'] = 'N/A'
        df['Rating'] = 'N/A'
        return df

    stock_perfs, vnindex_perfs, vs_vnindex_perfs, ratings = [], [], [], []

    for _, row in df.iterrows():
        stock = row['Cổ phiếu']
        start_date = pd.to_datetime(row[date_col_name])
        end_date = start_date + period_offset

        try:
            if stock not in prices_pivot.columns or VNINDEX_TICKER not in prices_pivot.columns:
                raise KeyError(f"Không tìm thấy mã {stock} hoặc {VNINDEX_TICKER} trong dữ liệu giá.")

            # Lấy giá gần nhất SAU ngày bắt đầu
            start_prices_slice = prices_pivot.loc[start_date:].dropna(subset=[stock, VNINDEX_TICKER])
            if start_prices_slice.empty: raise IndexError("Ngày bắt đầu nằm ngoài phạm vi.")
            
            start_price_stock = start_prices_slice[stock].iloc[0]
            start_price_vnindex = start_prices_slice[VNINDEX_TICKER].iloc[0]

            # Lấy giá gần nhất TRƯỚC hoặc BẰNG ngày kết thúc
            end_prices_slice = prices_pivot.loc[:end_date].dropna(subset=[stock, VNINDEX_TICKER])
            if end_prices_slice.empty: raise IndexError("Ngày kết thúc nằm ngoài phạm vi.")
                
            end_price_stock = end_prices_slice[stock].iloc[-1]
            end_price_vnindex = end_prices_slice[VNINDEX_TICKER].iloc[-1]

            stock_perf_num = (end_price_stock / start_price_stock) - 1
            vnindex_perf_num = (end_price_vnindex / start_price_vnindex) - 1
            vs_vnindex_perf_num = stock_perf_num - vnindex_perf_num
            
            stock_perfs.append(f"{stock_perf_num:.2%}")
            vnindex_perfs.append(f"{vnindex_perf_num:.2%}")
            vs_vnindex_perfs.append(f"{vs_vnindex_perf_num:.2%}")

            if vs_vnindex_perf_num > 0:
                ratings.append('Outperform')
            elif vs_vnindex_perf_num < 0:
                ratings.append('Underperform')
            else: 
                ratings.append('N/A')

        except (KeyError, IndexError, ValueError):
            stock_perfs.append('N/A')
            vnindex_perfs.append('N/A')
            vs_vnindex_perfs.append('N/A')
            ratings.append('N/A')

    df[f'Hiệu suất CP ({period_label})'] = stock_perfs
    df[f'Hiệu suất VNINDEX ({period_label})'] = vnindex_perfs
    df[f'vs VNINDEX ({period_label})'] = vs_vnindex_perfs
    df['Rating'] = ratings
    return df

def process_stock_data(df_rec: pd.DataFrame, df_price: pd.DataFrame, period_offset: DateOffset, period_label: str) -> Tuple[pd.DataFrame, ...]:
    """
    Xử lý, làm sạch và phân tích dữ liệu cổ phiếu.
    """
    # 1. Làm sạch dữ liệu khuyến nghị
    df_rec.dropna(axis=1, how='all', inplace=True)
    df_rec = df_rec.loc[:, ~df_rec.columns.str.contains('^Unnamed')]
    df_rec.index = pd.to_datetime(df_rec.index, errors='coerce')
    df_rec.dropna(axis=0, how='all', inplace=True)
    df_rec = df_rec[df_rec.index.notna()]
    df_rec.sort_index(inplace=True)

    if df_rec.empty:
        st.warning("Không tìm thấy dữ liệu ngày tháng hợp lệ trong sheet khuyến nghị.")
        return tuple(pd.DataFrame() for _ in range(4))
    
    # 2. Chuẩn bị dữ liệu giá
    prices_pivot = pd.DataFrame()
    if not df_price.empty:
        df_price['Date'] = pd.to_datetime(df_price['Date'], errors='coerce')
        df_price.dropna(subset=['Date'], inplace=True)
        prices_pivot = df_price.pivot_table(index='Date', columns='Stock', values='Price', aggfunc='first')
        prices_pivot.sort_index(inplace=True)

    # 3. Phân tích sự thay đổi trạng thái
    df_filled = df_rec.ffill()
    df_shifted = df_filled.shift(1)

    cond1 = (df_filled == 'MARKET-PERFORM') & (df_shifted == 'OUTPERFORM')
    cond2 = (df_filled == 'OUTPERFORM') & (df_shifted == 'MARKET-PERFORM')

    list1_data = [{'Cổ phiếu': stock, 'Ngày thay đổi': date} for stock in cond1.columns for date in cond1.index[cond1[stock]]]
    list2_data = [{'Cổ phiếu': stock, 'Ngày thay đổi': date} for stock in cond2.columns for date in cond2.index[cond2[stock]]]
    buy_data = [{'Cổ phiếu': stock, 'Ngày khuyến nghị': date} for stock in df_rec.columns for date in df_rec.index[df_rec[stock] == 'BUY']]
    under_data = [{'Cổ phiếu': stock, 'Ngày khuyến nghị': date} for stock in df_rec.columns for date in df_rec.index[df_rec[stock] == 'UNDER-PERFORM']]

    df_list1 = pd.DataFrame(list1_data).sort_values(by='Ngày thay đổi', ascending=False)
    df_list2 = pd.DataFrame(list2_data).sort_values(by='Ngày thay đổi', ascending=False)
    df_list3 = pd.DataFrame(buy_data).sort_values(by='Ngày khuyến nghị', ascending=False)
    df_list4 = pd.DataFrame(under_data).sort_values(by='Ngày khuyến nghị', ascending=False)

    # **THAY ĐỔI MỚI: ĐỊNH DẠNG LẠI CỘT NGÀY**
    if not df_list1.empty:
        df_list1['Ngày thay đổi'] = pd.to_datetime(df_list1['Ngày thay đổi']).dt.strftime('%Y-%m-%d')
    if not df_list2.empty:
        df_list2['Ngày thay đổi'] = pd.to_datetime(df_list2['Ngày thay đổi']).dt.strftime('%Y-%m-%d')
    if not df_list3.empty:
        df_list3['Ngày khuyến nghị'] = pd.to_datetime(df_list3['Ngày khuyến nghị']).dt.strftime('%Y-%m-%d')
    if not df_list4.empty:
        df_list4['Ngày khuyến nghị'] = pd.to_datetime(df_list4['Ngày khuyến nghị']).dt.strftime('%Y-%m-%d')


    # 4. Thêm cột hiệu suất cho từng bảng
    df_list1 = add_performance_cols(df_list1, prices_pivot, 'Ngày thay đổi', period_offset, period_label)
    df_list2 = add_performance_cols(df_list2, prices_pivot, 'Ngày thay đổi', period_offset, period_label)
    df_list3 = add_performance_cols(df_list3, prices_pivot, 'Ngày khuyến nghị', period_offset, period_label)
    df_list4 = add_performance_cols(df_list4, prices_pivot, 'Ngày khuyến nghị', period_offset, period_label)

    return df_list1, df_list2, df_list3, df_list4

def _parse_percentage(val: str) -> float:
    """
    Parse giá trị phần trăm từ string sang float.
    Ví dụ: "-3.25%" -> -0.0325, "5.80%" -> 0.058
    """
    try:
        if isinstance(val, str) and '%' in val:
            return float(val.replace('%', '').strip()) / 100
        return float('nan')
    except (ValueError, TypeError):
        return float('nan')


def calculate_win_rate_summary(data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Tạo bảng thống kê Win Rate và Avg Alpha theo năm từ các DataFrame kết quả.
    Trả về DataFrame với MultiIndex columns để hiển thị header 2 tầng.

    Args:
        data_dict (Dict[str, pd.DataFrame]): Từ điển chứa các DataFrame kết quả.

    Returns:
        pd.DataFrame: Bảng thống kê Win Rate kèm Avg Alpha với header 2 tầng.
    """
    all_years = set()
    dfs_copy = {}
    
    # Tên hiển thị ngắn gọn hơn
    display_names = {
        'Out_sang_MarketPerform': 'Out → MP',
        'MarketPerform_sang_Out': 'MP → Out', 
        'Khuyen_nghi_BUY': 'BUY',
        'Khuyen_nghi_UnderPerform': 'UNDER'
    }
    
    # Chuẩn bị dữ liệu và thu thập tất cả các năm có dữ liệu
    for name, df in data_dict.items():
        df_copy = df.copy()
        date_col = next((col for col in df_copy.columns if 'Ngày' in col), None)
        if date_col and not df_copy.empty:
            df_copy['Year'] = pd.to_datetime(df_copy[date_col]).dt.year
            all_years.update(df_copy['Year'].unique())
        dfs_copy[name] = (df_copy, date_col)

    if not all_years:
        return pd.DataFrame()

    years = sorted(list(all_years))
    
    # Tạo cấu trúc dữ liệu cho MultiIndex columns
    summary_data = {}

    for name, (df, date_col) in dfs_copy.items():
        display_name = display_names.get(name, name)
        win_rates = []
        alphas = []
        
        if not df.empty and 'Rating' in df.columns:
            df_filtered = df[df['Rating'] != 'N/A'].copy()
            
            # Tìm cột vs VNINDEX
            vs_vnindex_col = next((col for col in df_filtered.columns if 'vs VNINDEX' in col), None)
            
            # Parse giá trị Alpha từ string sang số
            if vs_vnindex_col:
                df_filtered['Alpha_Numeric'] = df_filtered[vs_vnindex_col].apply(_parse_percentage)

            # Xác định target rating
            target_rating = 'Underperform' if name in ['Out_sang_MarketPerform', 'Khuyen_nghi_UnderPerform'] else 'Outperform'

            for year in years:
                year_df = df_filtered[df_filtered['Year'] == year]
                total = len(year_df)
                if total > 0:
                    wins = len(year_df[year_df['Rating'] == target_rating])
                    rate = wins / total
                    win_rates.append(f"{rate:.0%} ({wins}/{total})")
                    
                    # Tính Avg Alpha
                    if vs_vnindex_col and 'Alpha_Numeric' in year_df.columns:
                        avg_alpha = year_df['Alpha_Numeric'].mean()
                        if not pd.isna(avg_alpha):
                            alphas.append(f"{avg_alpha:+.1%}")
                        else:
                            alphas.append('—')
                    else:
                        alphas.append('—')
                else:
                    win_rates.append('—')
                    alphas.append('—')

            # Tính tổng cộng
            total_all_time = len(df_filtered)
            if total_all_time > 0:
                wins_all_time = len(df_filtered[df_filtered['Rating'] == target_rating])
                total_rate = wins_all_time / total_all_time
                win_rates.append(f"{total_rate:.0%} ({wins_all_time}/{total_all_time})")
                
                if vs_vnindex_col and 'Alpha_Numeric' in df_filtered.columns:
                    avg_alpha_total = df_filtered['Alpha_Numeric'].mean()
                    if not pd.isna(avg_alpha_total):
                        alphas.append(f"{avg_alpha_total:+.1%}")
                    else:
                        alphas.append('—')
                else:
                    alphas.append('—')
            else:
                win_rates.append('—')
                alphas.append('—')
                
            summary_data[(display_name, 'WinRate')] = win_rates
            summary_data[(display_name, 'Alpha')] = alphas
        else:
            summary_data[(display_name, 'WinRate')] = ['—'] * (len(years) + 1)
            summary_data[(display_name, 'Alpha')] = ['—'] * (len(years) + 1)

    # Tạo DataFrame với MultiIndex columns
    summary_df = pd.DataFrame(summary_data, index=[str(y) for y in years] + ['Total'])
    summary_df.columns = pd.MultiIndex.from_tuples(summary_df.columns)
    summary_df.index.name = 'Năm'
    
    return summary_df.reset_index()
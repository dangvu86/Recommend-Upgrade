# src/utils.py
import io
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

def to_excel(dfs_dict: dict) -> bytes:
    """
    Chuyển đổi một từ điển chứa các DataFrame thành một file Excel trong bộ nhớ.
    Mỗi cặp key-value trong từ điển sẽ tương ứng với một sheet trong file Excel.

    Args:
        dfs_dict (dict): Từ điển với key là tên sheet và value là DataFrame.

    Returns:
        bytes: Dữ liệu file Excel dưới dạng bytes.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in dfs_dict.items():
            # Nếu df là một đối tượng Styler của pandas, ta cần lấy dữ liệu gốc
            df_to_write = df.data.copy() if hasattr(df, 'data') else df.copy()
            
            # Xử lý MultiIndex columns - flatten thành single level
            if isinstance(df_to_write.columns, pd.MultiIndex):
                df_to_write.columns = [f"{col[0]}_{col[1]}" if col[1] else col[0] for col in df_to_write.columns]
            
            # Xử lý các cột datetime để không bị ảnh hưởng bởi múi giờ khi ghi ra Excel
            for col in df_to_write.columns:
                if is_datetime64_any_dtype(df_to_write[col]):
                    df_to_write[col] = df_to_write[col].dt.tz_localize(None)

            df_to_write.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Tự động điều chỉnh độ rộng cột
            for column in df_to_write:
                column_length = max(df_to_write[column].astype(str).map(len).max(), len(column))
                col_idx = df_to_write.columns.get_loc(column)
                writer.sheets[sheet_name].set_column(col_idx, col_idx, column_length + 1)
                
    processed_data = output.getvalue()
    return processed_data
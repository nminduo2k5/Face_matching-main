import os
import pandas as pd
import requests
from urllib.parse import urlparse

def download_public_google_sheet_to_csv(sheet_url="https://docs.google.com/spreadsheets/d/1XU31AREaDxK2Gn_ikELCT2nKahDlZm6sXcXtP3V0XzI/edit?pli=1&gid=1743251291#gid=1743251291", 
                                        csv_file_path="output.csv"):
    """
    Download a public Google Sheet as a CSV file.
    
    Parameters:
    - sheet_url: str, URL of the public Google Sheet (default provided).
    - csv_file_path: str, path where the CSV file will be saved (default: "output.csv").
    """
    csv_url = sheet_url.replace('/edit?pli=1&gid=', '/gviz/tq?tqx=out:csv&gid=')
    df = pd.read_csv(csv_url)
    df.to_csv(csv_file_path, index=False)
    print(f"Downloaded CSV file: {csv_file_path}")
    return df

def convert_google_drive_link(link):
    """
    Chuyển đổi link Google Drive để tải về trực tiếp hoặc nhận diện thư mục.

    Parameters:
    - link: str, Google Drive link.

    Returns:
    - Tuple(str, bool), direct download link (or original link) và flag để chỉ ra nếu đó là thư mục.
    """
    if not isinstance(link, str):
        print(f"Giá trị không hợp lệ: {link}")
        return "", False

    try:
        if "drive.google.com" in link:
            # Xử lý link file Google Drive
            if '/file/d/' in link:
                file_id = link.split('/file/d/')[1].split('/')[0]
                return f"https://drive.google.com/uc?export=download&id={file_id}", False
            # Xử lý link thư mục Google Drive
            elif '/folders/' in link or 'drive/folders/' in link:
                return link, True  # Đây là thư mục
        return link, False
    except IndexError:
        print(f"Lỗi xử lý liên kết: {link}")
        return link, False

def download_images_from_csv(df, 
                             employee_code_column='MÃ NHÂN VIÊN', 
                             link_column='Link ảnh chấm công'):
    """
    Tạo thư mục theo mã nhân viên và tải ảnh từ liên kết "LINK ĐỒNG BỘ".
    
    Parameters:
    - df: DataFrame, dữ liệu CSV đã được tải về.
    - employee_code_column: str, tên cột chứa mã nhân viên (default: 'MÃ NHÂN VIÊN').
    - link_column: str, tên cột chứa link ảnh (default: 'Link ảnh chấm công').
    """
    # Các loại file ảnh được hỗ trợ
    valid_image_formats = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/heif', 'image/heic', 'image/webp']
    
    successful_downloads = 0  # Biến đếm số mã nhân viên tải thành công

    for index, row in df.iterrows():
        employee_code = row[employee_code_column]
        link = row[link_column]
        
        # Chuyển đổi link Google Drive nếu cần
        direct_link, is_folder = convert_google_drive_link(link)

        if is_folder:
            print(f"{employee_code} là thư mục: {direct_link}")
        else:
            if pd.notna(direct_link):  # Kiểm tra nếu link không phải NaN
                try:
                    response = requests.get(direct_link)
                    content_type = response.headers.get('Content-Type', '')

                    # Kiểm tra xem content type có nằm trong danh sách các định dạng ảnh hợp lệ không
                    if response.status_code == 200 and content_type in valid_image_formats:
                        # Lấy đuôi file từ content-type
                        file_extension = content_type.split('/')[1]  # Ví dụ: 'image/jpeg' -> 'jpeg'
                        
                        folder_path = os.path.join('./faces/', str(employee_code))
                        if not os.path.exists(folder_path):
                            os.makedirs(folder_path)

                        image_path = os.path.join(folder_path, f"{employee_code}.{file_extension}")
                        with open(image_path, 'wb') as f:
                            f.write(response.content)
                        print(f"Đã tải ảnh cho nhân viên {employee_code} với đuôi {file_extension}")
                        successful_downloads += 1  # Tăng biến đếm lên 1
                    else:
                        print(f"Lỗi khi tải ảnh từ {link}, không phải định dạng ảnh hợp lệ.")
                except Exception as e:
                    print(f"Lỗi: {e}")

    # Hiển thị số mã nhân viên đã tải thành công
    print(f"Tổng số mã nhân viên tải thành công: {successful_downloads}")

# Ví dụ sử dụng với các giá trị mặc định
# df = download_public_google_sheet_to_csv()
download_images_from_csv(download_public_google_sheet_to_csv())


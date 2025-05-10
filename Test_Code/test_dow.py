# import os
# import pandas as pd
# import requests

# # Đường dẫn tới file CSV
# csv_file_path = './data_image_sheet/ẢNH NHÂN SỰ DH - Trang tính1 (1).csv'

# # Tên thư mục cha
# base_dir = 'faces'

# # Đọc file CSV
# df = pd.read_csv(csv_file_path)

# # Hàm chuyển đổi link Google Drive sang link tải trực tiếp
# def convert_drive_url(drive_url):
#     if isinstance(drive_url, str) and '/d/' in drive_url:
#         try:
#             file_id = drive_url.split('/d/')[1].split('/')[0]
#             return f'https://drive.google.com/uc?export=download&id={file_id}'
#         except IndexError:
#             return None
#     else:
#         return None

# # Tạo thư mục nếu chưa tồn tại
# def create_directory(directory):
#     if not os.path.exists(directory):
#         os.makedirs(directory)

# # Tải ảnh và lưu vào thư mục tương ứng với đuôi file chính xác
# def download_image(url, save_dir, ma_nhan_vien):
#     try:
#         response = requests.get(url, stream=True)
#         if response.status_code == 200:
#             # Lấy loại file từ Content-Type header
#             content_type = response.headers.get('Content-Type')
            
#             # Xác định phần đuôi file từ Content-Type
#             if 'image/jpeg' in content_type:
#                 extension = '.jpg'
#             elif 'image/png' in content_type:
#                 extension = '.png'
#             elif 'image/heic' in content_type or 'heif' in content_type:
#                 extension = '.heic'
#                 print(ma_nhan_vien + "duooi anh k dung .HIEC")
#             else:
#                 extension = '.jpg'  # Mặc định là .jpg nếu không xác định được

#             # Đường dẫn lưu ảnh
#             save_path = os.path.join(save_dir, f"{ma_nhan_vien}{extension}")
            
#             # Lưu ảnh
#             with open(save_path, 'wb') as out_file:
#                 out_file.write(response.content)
#             return True  # Thành công
#         else:
#             return f"Lỗi {response.status_code}"
#     except Exception as e:
#         return str(e)

# # Tạo thư mục 'faces' nếu chưa tồn tại
# create_directory(base_dir)

# # Biến đếm thành công và lỗi
# success_count = 0
# error_count = 0
# error_log = []

# # Lặp qua từng dòng trong file CSV
# for index, row in df.iterrows():
#     ma_nhan_vien = row['Mã NV']
#     link_anh = row['Link ảnh']
    
#     # Chuyển đổi link Google Drive
#     download_url = convert_drive_url(link_anh)
    
#     if download_url:
#         # Tạo thư mục cho mã nhân viên bên trong thư mục 'faces'
#         employee_dir = os.path.join(base_dir, ma_nhan_vien)
#         create_directory(employee_dir)
        
#         # Tải ảnh và xử lý kết quả
#         result = download_image(download_url, employee_dir, ma_nhan_vien)
#         if result == True:
#             success_count += 1
#         else:
#             error_count += 1
#             error_log.append(f"{ma_nhan_vien} - {result}")
#     else:
#         error_count += 1
#         error_log.append(f"{ma_nhan_vien} - Lỗi: Link không hợp lệ hoặc rỗng")

# # Thông báo tổng kết
# print(f"Quá trình tải ảnh hoàn thành!")
# print(f"Ảnh tải thành công: {success_count}")
# print(f"Ảnh bị lỗi: {error_count}")

# # Hiển thị chi tiết lỗi nếu có
# if error_log:
#     print("\nChi tiết các lỗi:")
#     for error in error_log:
#         print(error)


import os
import pandas as pd
import requests

# Chuyển đổi link Google Sheets thành link CSV
sheet_id = '1J4RjzSExm8ugz9OKioK0fuYBuQCvFTqfNNPol0qONrk'
csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'

# Đọc dữ liệu từ link CSV
df = pd.read_csv(csv_url)

# Tên thư mục cha
base_dir = 'faces'

# Hàm chuyển đổi link Google Drive sang link tải trực tiếp
def convert_drive_url(drive_url):
    if isinstance(drive_url, str) and '/d/' in drive_url:
        try:
            file_id = drive_url.split('/d/')[1].split('/')[0]
            return f'https://drive.google.com/uc?export=download&id={file_id}'
        except IndexError:
            return None
    else:
        return None

# Tạo thư mục nếu chưa tồn tại
def create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Tải ảnh và lưu vào thư mục tương ứng với đuôi file chính xác
def download_image(url, save_dir, ma_nhan_vien):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            # Lấy loại file từ Content-Type header
            content_type = response.headers.get('Content-Type')
            
            # Xác định phần đuôi file từ Content-Type
            if 'image/jpeg' in content_type:
                extension = '.jpg'
            elif 'image/png' in content_type:
                extension = '.png'
            elif 'image/heic' in content_type or 'heif' in content_type:
                extension = '.heic'
                print(ma_nhan_vien + " đuôi ảnh không đúng: .HIEC")
            else:
                extension = '.jpg'  # Mặc định là .jpg nếu không xác định được

            # Đường dẫn lưu ảnh
            save_path = os.path.join(save_dir, f"{ma_nhan_vien}{extension}")
            
            # Lưu ảnh
            with open(save_path, 'wb') as out_file:
                out_file.write(response.content)
            return True  # Thành công
        else:
            return f"Lỗi {response.status_code}"
    except Exception as e:
        return str(e)

# Tạo thư mục 'faces' nếu chưa tồn tại
create_directory(base_dir)

# Biến đếm thành công và lỗi
success_count = 0
error_count = 0
error_log = []

# Lặp qua từng dòng trong file CSV
for index, row in df.iterrows():
    ma_nhan_vien = row['Mã NV']
    link_anh = row['Link ảnh']
    
    # Chuyển đổi link Google Drive
    download_url = convert_drive_url(link_anh)
    
    if download_url:
        # Tạo thư mục cho mã nhân viên bên trong thư mục 'faces'
        employee_dir = os.path.join(base_dir, ma_nhan_vien)
        create_directory(employee_dir)
        
        # Tải ảnh và xử lý kết quả
        result = download_image(download_url, employee_dir, ma_nhan_vien)
        if result == True:
            success_count += 1
        else:
            error_count += 1
            error_log.append(f"{ma_nhan_vien} - {result}")
    else:
        error_count += 1
        error_log.append(f"{ma_nhan_vien} - Lỗi: Link không hợp lệ hoặc rỗng")

# Thông báo tổng kết
print(f"Quá trình tải ảnh hoàn thành!")
print(f"Ảnh tải thành công: {success_count}")
print(f"Ảnh bị lỗi: {error_count}")

# Hiển thị chi tiết lỗi nếu có
if error_log:
    print("\nChi tiết các lỗi:")
    for error in error_log:
        print(error)

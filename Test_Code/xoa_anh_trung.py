import os

def xoa_anh_trung_thu_muc_con(thu_muc_goc):
    # Duyệt qua các thư mục con
    for thu_muc_con in os.listdir(thu_muc_goc):
        duong_dan_thu_muc_con = os.path.join(thu_muc_goc, thu_muc_con)
        if os.path.isdir(duong_dan_thu_muc_con):
            # Lấy danh sách tất cả các ảnh trong thư mục con
            danh_sach_anh = {}
            
            # Duyệt qua các file trong thư mục con
            for file in os.listdir(duong_dan_thu_muc_con):
                ten_file, duoi_file = os.path.splitext(file)
                
                # Nếu tên file đã có trong danh sách, tức là đã có ảnh trùng tên
                if ten_file in danh_sach_anh:
                    # Xóa ảnh theo đuôi tùy ý (ở đây ta sẽ giữ ảnh đầu tiên)
                    duong_dan_file_xoa = os.path.join(duong_dan_thu_muc_con, file)
                    print(f"Xóa ảnh: {duong_dan_file_xoa}")
                    os.remove(duong_dan_file_xoa)
                else:
                    # Nếu chưa có tên file, thêm vào danh sách
                    danh_sach_anh[ten_file] = duoi_file

# Thư mục gốc chứa các thư mục con
thu_muc_goc = "faces"

xoa_anh_trung_thu_muc_con(thu_muc_goc)

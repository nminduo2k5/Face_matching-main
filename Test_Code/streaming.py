import cv2
import os
import random
import torch
from load_model import load_model
from c.cConst import Const
from service.processing import build_targets
from service.frame_processor import frame_processor
from utils.utils import count_directories_and_files

var = Const()
var.source = "video.mp4"  # Đường dẫn đến file MP4
var.output_path = "output.mp4"  # Đường dẫn lưu video sau khi xử lý

def process_video():
    """Xử lý video và hiển thị kết quả."""
    # Tải mô hình và tạo danh sách mục tiêu
    detector, recognizer = load_model()
    targets = build_targets(detector, recognizer, var.faces_dir)
    colors = {name: (random.randint(0, 256), random.randint(0, 256), random.randint(0, 256)) for _, name in targets}

    # Mở video nguồn
    cap = cv2.VideoCapture(var.source)
    if not cap.isOpened():
        raise Exception(f"Không thể mở video: {var.source}")

    # Lấy thông tin về kích thước và FPS của video
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Tạo đối tượng VideoWriter để lưu video đã xử lý
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Định dạng mã hóa
    out = cv2.VideoWriter(var.output_path, fourcc, fps, (width, height))

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Kết thúc video.")
            break

        if frame_count % var.max_frame == 0:
            try:
                # Xử lý frame và nhận diện khuôn mặt
                frame, recognized_names = frame_processor(
                    frame, detector, recognizer, targets, colors, var
                )

                # In ra terminal các tên đã nhận diện
                if recognized_names:
                    print("Nhận diện:", ", ".join(recognized_names))
            except Exception as e:
                print("Lỗi khi xử lý frame:", str(e))

        # Hiển thị frame đã xử lý
        cv2.imshow('Video', frame)

        # Ghi frame vào file output
        out.write(frame)

        # Nhấn 'q' để thoát
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Thoát chương trình.")
            break

        frame_count += 1
        if frame_count > 1000:
            frame_count = 0

    # Giải phóng tài nguyên
    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    process_video()

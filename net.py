import cv2
import numpy as np
import onnxruntime as rt
import time

# 1. Cấu hình session options để tối ưu hóa mô hình ONNX
sess_options = rt.SessionOptions()
sess_options.graph_optimization_level = rt.GraphOptimizationLevel.ORT_ENABLE_ALL
sess_options.intra_op_num_threads = 4  # Điều chỉnh số luồng theo tài nguyên máy của bạn

# 2. Khởi tạo ONNX Runtime session với TensorRTExecutionProvider nếu có
model_path = r'C:\Users\duong\OneDrive_duong\Desktop\Face_Matching-main\weights\RealESRGAN_x4plus.onnx'

# Thử dùng TensorRTExecutionProvider trước, nếu không thì dùng CUDAExecutionProvider
providers = ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']
try:
    sess = rt.InferenceSession(model_path, sess_options=sess_options, providers=providers)
    print("Using providers:", sess.get_providers())
except Exception as e:
    print("TensorRTExecutionProvider không khả dụng, sử dụng CUDAExecutionProvider.")
    sess = rt.InferenceSession(model_path, sess_options=sess_options, providers=['CUDAExecutionProvider'])
    print("Using providers:", sess.get_providers())

print("Loaded model.")

# 3. Load ảnh đầu vào và tiền xử lý
input_path = r'C:\Users\duong\OneDrive_duong\Desktop\Face_Matching-main\query\duong.jpg'
in_image = cv2.imread(input_path, cv2.IMREAD_COLOR)
if in_image is None:
    raise ValueError(f"Không thể load ảnh từ {input_path}!")
print("Loaded input image.")

# Chuyển từ BGR sang RGB, chuyển về float và scale về [0, 1]
in_image_rgb = cv2.cvtColor(in_image, cv2.COLOR_BGR2RGB)
in_image_rgb = in_image_rgb.astype(np.float32) / 255.0

# Chuyển ảnh từ định dạng HWC sang CHW và thêm batch dimension
in_tensor = np.transpose(in_image_rgb, (2, 0, 1))  # (3, H, W)
in_tensor = np.expand_dims(in_tensor, axis=0)         # (1, 3, H, W)

# 4. Suy luận với ONNX Runtime
input_name = sess.get_inputs()[0].name
output_name = sess.get_outputs()[0].name

start_time = time.time()
out_tensor = sess.run([output_name], {input_name: in_tensor})[0]
elapsed_time = time.time() - start_time
print(f"Inference time: {elapsed_time:.4f} seconds")

# 5. Hậu xử lý: chuyển kết quả về dạng ảnh
# Giả sử đầu ra có shape (1, 3, H_out, W_out)
out_tensor = np.squeeze(out_tensor, axis=0)  # (3, H_out, W_out)
out_tensor = np.clip(out_tensor, 0, 1) * 255.0
out_tensor = out_tensor.astype(np.uint8)
# Chuyển từ CHW sang HWC
out_image_rgb = np.transpose(out_tensor, (1, 2, 0))
# Chuyển từ RGB sang BGR (để lưu với cv2)
out_image = cv2.cvtColor(out_image_rgb, cv2.COLOR_RGB2BGR)

output_path = './net/output.jpg'
cv2.imwrite(output_path, out_image)
print(f"Output image saved as '{output_path}'.")

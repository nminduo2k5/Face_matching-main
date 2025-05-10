from PIL import Image
import torchvision.transforms as transforms
import onnxruntime
import numpy as np
# Đọc ảnh
img = Image.open(r"C:\Users\duong\OneDrive_duong\Desktop\Face_Matching-main\query\duong.jpg")

# Thay đổi kích thước ảnh về 224x224
resize = transforms.Resize([224, 224])
img = resize(img)

# Chuyển đổi ảnh sang chế độ RGB nếu ảnh ở chế độ RGBA
if img.mode == 'RGBA':
    img = img.convert('RGB')

# Chuyển đổi ảnh thành tensor
to_tensor = transforms.ToTensor()
img_tensor = to_tensor(img)
img_tensor = img_tensor.unsqueeze(0)  # Thêm chiều batch


ort_session = onnxruntime.InferenceSession(r"C:\Users\duong\OneDrive_duong\Desktop\Face_Matching-main\weights\RealESRGAN_x4plus.onnx", providers=["CPUExecutionProvider"])
# Thực hiện suy luận
ort_inputs = {ort_session.get_inputs()[0].name: img_tensor.numpy()}
ort_outs = ort_session.run(None, ort_inputs)

# Lấy đầu ra từ kết quả suy luận
img_out = ort_outs[0]

# Chuyển đổi đầu ra từ numpy array sang Image
img_out = np.squeeze(img_out)  # Loại bỏ chiều batch
img_out = np.transpose(img_out, (1, 2, 0))  # Chuyển đổi từ (C, H, W) sang (H, W, C)
img_out = np.clip(img_out * 255.0, 0, 255).astype(np.uint8)  # Chuyển đổi về giá trị pixel

# Tạo đối tượng Image từ numpy array
img_out = Image.fromarray(img_out)

# Lưu ảnh kết quả
img_out.save("./net/super_resolved_image.jpg")
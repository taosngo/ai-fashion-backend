# ==============================================================================
#  BACKEND CHO ỨNG DỤNG AI FASHION STUDIO
#  Ngôn ngữ: Python
#  Framework: FastAPI
# ==============================================================================

# --- Bước 1: Cài đặt các thư viện cần thiết ---
# Mở terminal (dòng lệnh) và chạy lệnh sau:
# pip install "fastapi[all]" google-cloud-aiplatform python-multipart

# --- Bước 2: Import thư viện ---
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.cloud.aiplatform as aiplatform
import base64
import os

# --- Bước 3: Cấu hình dự án ---
# LƯU Ý: Lập trình viên sẽ cần thay thế các giá trị này.
# Bạn cần cung cấp cho họ file .json đã tải về.
PROJECT_ID = "[DÁN-PROJECT-ID-CỦA-BẠN-VÀO-ĐÂY]"
LOCATION = "us-central1"  # Thường là khu vực này cho các model tạo ảnh
SERVICE_ACCOUNT_FILE = "service_account_key.json" # Đổi tên file .json của bạn thành tên này và để cùng thư mục

# Thiết lập biến môi trường để xác thực với Google Cloud
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE

# --- Bước 4: Khởi tạo ứng dụng FastAPI ---
app = FastAPI(title="AI Fashion Studio Backend")

# Cấu hình CORS để cho phép Frontend từ Vercel có thể gọi API này
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong sản phẩm thực tế, nên giới hạn lại chỉ domain của Vercel
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# --- Bước 5: Khởi tạo kết nối tới Google AI Platform ---
try:
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    print("Kết nối tới Google Cloud AI Platform thành công!")
except Exception as e:
    print(f"LỖI: Không kết nối được tới Google Cloud. Hãy kiểm tra lại PROJECT_ID và file key. Lỗi: {e}")

# --- Bước 6: Định nghĩa Endpoint chính để tạo ảnh ---
@app.post("/api/generate-image")
async def generate_image_endpoint(style: str, product_image: UploadFile = File(...)):
    """
    Nhận ảnh sản phẩm và một 'style' (phong cách), sau đó trả về ảnh đã được AI tạo ra.
    """
    # Đọc nội dung file ảnh người dùng tải lên
    image_bytes = await product_image.read()
    
    # Mã hóa ảnh sang dạng base64 để gửi đi
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    # Chọn câu lệnh (prompt) dựa trên style người dùng chọn
    if style == "studio":
        prompt = "a professional photo of a fashion model wearing this. full body shot in a clean, bright studio with a plain white background. e-commerce, hyperrealistic, high detail."
    elif style == "street":
        prompt = "a candid lifestyle photo of a fashion model wearing this on a beautiful street in Ho Chi Minh City. sunny day, blurred background, looking natural and happy."
    else:
        # Báo lỗi nếu style không hợp lệ
        raise HTTPException(status_code=400, detail="Phong cách không hợp lệ. Vui lòng chọn 'studio' hoặc 'street'.")

    # Gửi yêu cầu tới model tạo ảnh của Google (Imagen)
    try:
        model = aiplatform.ImageGenerationModel.from_pretrained("imagegeneration@005")
        
        response = model.generate_images(
            prompt=prompt,
            base_image=image_bytes,
            number_of_images=1,
            # Các thông số khác có thể thêm ở đây
        )
        
        # Lấy ảnh kết quả trả về và mã hóa lại sang base64 để gửi về frontend
        generated_image_bytes = response.images[0]._image_bytes
        generated_image_b64 = base64.b64encode(generated_image_bytes).decode("utf-8")

        print("Tạo ảnh thành công!")
        return {"generated_image_base64": generated_image_b64}

    except Exception as e:
        print(f"LỖI: Quá trình gọi AI thất bại. Lỗi: {e}")
        raise HTTPException(status_code=500, detail=f"Có lỗi xảy ra khi gọi AI: {e}")

# --- Bước 7: Chạy server (dành cho lập trình viên) ---
# Để chạy file này, mở terminal và gõ:
# uvicorn main:app --host 0.0.0.0 --port 8000
"""
摄像头工具函数
"""
import cv2
import numpy as np
from PIL import Image
import io
import base64

class CameraCapture:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None
    
    def initialize(self):
        """初始化摄像头"""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                return False
            # 设置分辨率
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            return True
        except Exception as e:
            print(f"摄像头初始化失败: {e}")
            return False
    
    def capture_frame(self):
        """捕获一帧图像"""
        if self.cap is None or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if ret:
            # 转换BGR到RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return frame_rgb
        return None
    
    def capture_image(self):
        """捕获图像并转换为PIL Image"""
        frame = self.capture_frame()
        if frame is not None:
            return Image.fromarray(frame)
        return None
    
    def release(self):
        """释放摄像头资源"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
    
    def image_to_base64(self, image):
        """将PIL Image转换为base64字符串"""
        if image is None:
            return None
        
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    
    def save_image(self, image, filepath):
        """保存图像到文件"""
        if image is not None:
            image.save(filepath)
            return True
        return False


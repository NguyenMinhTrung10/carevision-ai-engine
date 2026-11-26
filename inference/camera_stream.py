import threading
import time
import cv2


class CameraStream:
    """Đọc camera ở thread riêng, luôn giữ frame MỚI NHẤT, tự kết nối lại khi mất mạng."""

    def __init__(self, source):
        self.source = int(source) if str(source).isdigit() else source
        self.frame = None
        self.running = True
        self.connected = False
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        while self.running:
            cap = cv2.VideoCapture(self.source)
            self.connected = cap.isOpened()
            while self.running and cap.isOpened():
                ok, frame = cap.read()
                if not ok:
                    break
                self.frame = frame
            cap.release()
            self.connected = False
            time.sleep(2)  # thử lại sau 2 giây

    def read(self):
        return self.frame

    def stop(self):
        self.running = False

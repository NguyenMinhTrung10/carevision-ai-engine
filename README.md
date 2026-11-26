# carevision-ai-engine
Prototype V1: camera/video -> YOLO pose -> luật té ngã -> event -> backend.

## Chạy
    pip install -r requirements.txt
    python -m tests.test_event_detector   # test logic, không cần camera
    cp .env.example .env                  # CAMERA_SOURCE: 0 | file.mp4 | rtsp://...
    python main.py                        # pipeline chính
    uvicorn api.main:app --port 8001      # /health

## Cấu trúc
datasets/ configs/ models/ training/ evaluation/ inference/ gateway/ api/ deployment/ tests/
Không đưa video bệnh nhân hay dữ liệu cá nhân lên GitHub công khai.

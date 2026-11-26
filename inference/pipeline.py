import os
import time
import uuid
from datetime import datetime, timezone

import cv2
from dotenv import load_dotenv
from ultralytics import YOLO

from inference.camera_stream import CameraStream
from gateway.event_publisher import EventPublisher
from inference.event_detector import FallDetector

load_dotenv()
SOURCE = os.getenv("CAMERA_SOURCE", "0")
CAMERA_ID = os.getenv("CAMERA_ID", "CAM-001")
ROOM_ID = os.getenv("ROOM_ID", "ROOM-101")
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/events")
DEVICE_ID = os.getenv("DEVICE_ID")
DEVICE_TOKEN = os.getenv("DEVICE_TOKEN", "")
TARGET_FPS = 8
os.makedirs("snapshots", exist_ok=True)


def run():
    if not DEVICE_TOKEN:
        raise SystemExit("Thiếu DEVICE_TOKEN trong .env (xem: python -m gateway.register --help)")
    model = YOLO("yolo11n-pose.pt")
    cam = CameraStream(SOURCE)
    detector = FallDetector()
    publisher = EventPublisher(API_URL, DEVICE_TOKEN)
    last_flush = 0.0

    while True:
        frame = cam.read()
        if frame is None:
            time.sleep(0.05)
            continue
        t = time.time()
        res = model(frame, verbose=False)[0]
        annotated = res.plot()

        # lấy người có khung bao lớn nhất (demo 1 người)
        if res.keypoints is not None and len(res.boxes) > 0:
            i = int(res.boxes.xywh[:, 2:].prod(dim=1).argmax())
            kpts = res.keypoints.xy[i].cpu().numpy()
            conf = res.keypoints.conf[i].cpu().numpy()
            bbox = res.boxes.xyxy[i].cpu().numpy()
            ev = detector.update(kpts, conf, bbox, t)
            if ev:
                event_id = f"EVT-{uuid.uuid4().hex[:8]}"
                snap = f"snapshots/{event_id}.jpg"
                cv2.imwrite(snap, annotated)
                publisher.publish({
                    "event_id": event_id,
                    "device_id": DEVICE_ID,
                    "camera_id": CAMERA_ID,
                    "room_id": ROOM_ID,
                    "event_type": ev["event_type"],
                    "severity": ev["severity"],
                    "confidence": ev["score"],  # điểm heuristic, chưa hiệu chỉnh
                    "model": {"name": "fall_rule", "version": "0.1.0"},
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                    "evidence": {"snapshot_path": snap},
                })
                cv2.putText(annotated, "FALL DETECTED", (30, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)

        if t - last_flush > 10:
            publisher.flush_queue()
            last_flush = t

        cv2.imshow("CareVision", annotated)
        if cv2.waitKey(1) == ord("q"):
            break
        time.sleep(max(0, 1 / TARGET_FPS - (time.time() - t)))

    cam.stop()
    cv2.destroyAllWindows()

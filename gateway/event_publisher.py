import json
import os

import requests

QUEUE_FILE = "event_queue.jsonl"


class EventPublisher:
    """Gửi event (+ ảnh bằng chứng) về backend bằng token riêng của thiết bị.
    Lỗi mạng hoặc backend lỗi tạm thời -> lưu hàng đợi cục bộ và gửi lại sau.
    Lỗi 4xx (sai token, payload sai) cũng vào hàng đợi để không mất sự kiện, nhưng sẽ in cảnh báo rõ ràng."""

    def __init__(self, api_url, device_token, timeout=5):
        self.api_url = api_url.rstrip("/")  # vd http://localhost:8000/api/v1/events
        self.headers = {"X-Device-Token": device_token}
        self.timeout = timeout

    def _post(self, event):
        r = requests.post(self.api_url, json=event, headers=self.headers, timeout=self.timeout)
        r.raise_for_status()
        self._upload_snapshot(event)

    def _upload_snapshot(self, event):
        path = (event.get("evidence") or {}).get("snapshot_path")
        if not path or not os.path.exists(path):
            return
        try:
            with open(path, "rb") as f:
                r = requests.post(
                    f"{self.api_url}/{event['event_id']}/snapshot",
                    files={"file": (os.path.basename(path), f, "image/jpeg")},
                    headers=self.headers,
                    timeout=self.timeout,
                )
            r.raise_for_status()
        except requests.RequestException as e:
            print("[event] snapshot upload failed:", e)

    def publish(self, event):
        try:
            self._post(event)
            print("[event] sent", event["event_id"])
        except requests.RequestException as e:
            print("[event] offline/rejected, queued:", e)
            with open(QUEUE_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")

    def flush_queue(self):
        if not os.path.exists(QUEUE_FILE):
            return
        with open(QUEUE_FILE, encoding="utf-8") as f:
            events = [json.loads(line) for line in f if line.strip()]
        remaining = []
        for ev in events:
            try:
                self._post(ev)
            except requests.RequestException:
                remaining.append(ev)
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            for ev in remaining:
                f.write(json.dumps(ev) + "\n")

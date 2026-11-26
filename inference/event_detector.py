"""Phát hiện té ngã bằng luật trên keypoints COCO-17 (YOLO pose).

Logic: (1) hông rơi nhanh -> (2) thân nằm ngang -> (3) nằm yên >= lying_sec => fall_detected.
Lưu ý: 'score' là điểm heuristic, KHÔNG phải xác suất. Cần đo precision/recall trên dữ liệu thật.
"""
import math
from collections import deque

L_SH, R_SH, L_HIP, R_HIP = 5, 6, 11, 12


def _mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


class FallDetector:
    def __init__(self, drop_speed=0.6, angle_deg=55, aspect=1.1,
                 lying_sec=2.0, drop_memory_sec=2.0, cooldown_sec=30, min_conf=0.3):
        self.drop_speed = drop_speed          # chiều cao người / giây
        self.angle_deg = angle_deg            # góc thân so với phương thẳng đứng
        self.aspect = aspect                  # rộng/cao khung bao khi nằm
        self.lying_sec = lying_sec
        self.drop_memory_sec = drop_memory_sec
        self.cooldown_sec = cooldown_sec
        self.min_conf = min_conf
        self.hist = deque()                   # (t, hip_y, bbox_h)
        self.last_drop_t = -1e9
        self.lying_since = None
        self.last_event_t = -1e9
        self.max_speed = 0.0

    def update(self, kpts, conf, bbox, t):
        """kpts: (17,2), conf: (17,), bbox: (x1,y1,x2,y2), t: giây. Trả về dict event hoặc None."""
        mc = self.min_conf
        sh_ok = conf[L_SH] > mc and conf[R_SH] > mc
        hip_ok = conf[L_HIP] > mc and conf[R_HIP] > mc
        x1, y1, x2, y2 = bbox
        w, h = x2 - x1, max(y2 - y1, 1.0)
        aspect = w / h

        hip = _mid(kpts[L_HIP], kpts[R_HIP]) if hip_ok else None
        if hip:
            self.hist.append((t, hip[1], h))
        while self.hist and t - self.hist[0][0] > 3.0:
            self.hist.popleft()

        angle = None
        if sh_ok and hip_ok:
            sh = _mid(kpts[L_SH], kpts[R_SH])
            angle = math.degrees(math.atan2(abs(hip[0] - sh[0]), abs(hip[1] - sh[1]) + 1e-6))

        lying = aspect > self.aspect or (angle is not None and angle > self.angle_deg)

        # tốc độ rơi của hông trong ~0.5 giây gần nhất (cú ngã thật diễn ra rất nhanh)
        if hip and len(self.hist) >= 2:
            ref_h = max(x[2] for x in self.hist)
            old = next(x for x in self.hist if t - x[0] <= 0.5)
            dt = t - old[0]
            if dt > 0.2:
                speed = (hip[1] - old[1]) / ref_h / dt
                if speed > self.drop_speed:
                    self.last_drop_t = t
                    self.max_speed = max(self.max_speed, speed)

        if not lying:
            self.lying_since = None
        elif self.lying_since is None and t - self.last_drop_t <= self.drop_memory_sec:
            self.lying_since = t

        if (self.lying_since is not None
                and t - self.lying_since >= self.lying_sec
                and t - self.last_event_t >= self.cooldown_sec):
            self.last_event_t = t
            self.lying_since = None
            score = min(1.0, 0.5 + 0.3 * min(self.max_speed / (2 * self.drop_speed), 1.0)
                        + 0.2 * (1.0 if aspect > self.aspect else 0.5))
            self.max_speed = 0.0
            return {"event_type": "fall_detected", "severity": "critical",
                    "score": round(score, 2), "occurred_at": t}
        return None

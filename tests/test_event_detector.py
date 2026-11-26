"""Test giả lập bằng keypoints tổng hợp (không cần camera/model)."""
import numpy as np
from inference.event_detector import FallDetector


def pose(sh, hip, bbox):
    k = np.zeros((17, 2))
    k[5], k[6] = (sh[0] - 10, sh[1]), (sh[0] + 10, sh[1])
    k[11], k[12] = (hip[0] - 10, hip[1]), (hip[0] + 10, hip[1])
    return k, np.ones(17), np.array(bbox, float)


def run(frames, fps=10):
    d, events = FallDetector(), []
    for i, (k, c, b) in enumerate(frames):
        ev = d.update(k, c, b, i / fps)
        if ev:
            events.append((i / fps, ev))
    return events


standing = [pose((110, 100), (110, 200), (80, 60, 140, 340))] * 20
fall = [pose((110 + 14 * i, 100 + 44 * i), (110, 200 + 26 * i), (60, 60 + 46 * i, 140 + 24 * i, 340))
        for i in range(1, 6)]
lying = [pose((190, 320), (110, 330), (60, 290, 260, 350))] * 40

# 1) ngã thật -> phải có đúng 1 event
assert len(run(standing + fall + lying)) == 1, "ngã thật phải báo"
# 2) nằm xuống CHẬM (không có cú rơi nhanh) -> không báo
slow = [pose((110 + 2 * i, 100 + 4.4 * i), (110, 200 + 2.6 * i), (80 - 2 * i, 60 + 4.6 * i, 140 + 2 * i, 340))
        for i in range(1, 51)]
assert len(run(standing + slow + lying)) == 0, "nằm chậm không được báo"
# 3) chỉ đứng -> không báo
assert len(run(standing * 3)) == 0
print("OK: 3/3 test qua")

"""Đăng ký Edge Box với backend bằng mã dùng một lần do Admin tạo.

    python -m gateway.register --api http://localhost:8000 --device-id EDGE-HCM-001 --code ABCDE12345

In ra DEVICE_TOKEN: dán vào .env của AI Engine. Token chỉ hiện một lần.
"""
import argparse
import sys

import requests


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--api", required=True, help="vd http://localhost:8000")
    p.add_argument("--device-id", required=True)
    p.add_argument("--code", required=True)
    p.add_argument("--firmware", default="0.1.0")
    a = p.parse_args()

    r = requests.post(
        a.api.rstrip("/") + "/api/v1/devices/register",
        json={"device_id": a.device_id, "registration_code": a.code, "firmware_version": a.firmware},
        timeout=10,
    )
    if r.status_code != 200:
        print(f"Đăng ký thất bại ({r.status_code}): mã sai, đã dùng hoặc hết hạn.")
        sys.exit(1)
    d = r.json()
    print("Đăng ký thành công. Thêm vào .env của AI Engine:\n")
    print(f"DEVICE_ID={d['device_id']}")
    print(f"DEVICE_TOKEN={d['device_token']}")


if __name__ == "__main__":
    main()

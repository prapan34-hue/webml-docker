"""
Web frontend service (Flask)
- แสดงฟอร์มให้ผู้ใช้กรอกข้อมูลดอกไอริส
- ส่งไปทำนายที่ ML API โดยอ้างด้วย "ชื่อ service" (http://ml-api:8000) ผ่าน Docker network
- แสดงผลทำนาย + ประวัติการทำนายล่าสุด (ดึงผ่าน ML API ซึ่งอ่านจาก PostgreSQL)
"""
import os
import requests
from flask import Flask, render_template, request

# อ้างถึง ML API ด้วยชื่อ service ไม่ใช่ localhost/IP
ML_API_URL = os.getenv("ML_API_URL", "http://ml-api:8000")

app = Flask(__name__)

FIELDS = ["sepal_length", "sepal_width", "petal_length", "petal_width"]


@app.get("/health")
def health():
    """ใช้โดย Docker healthcheck"""
    return {"status": "ok"}


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        try:
            payload = {f: float(request.form.get(f, "")) for f in FIELDS}
            resp = requests.post(f"{ML_API_URL}/predict", json=payload, timeout=10)
            resp.raise_for_status()
            result = resp.json()
        except ValueError:
            error = "กรุณากรอกค่าตัวเลขให้ครบทุกช่อง"
        except requests.RequestException as err:
            error = f"เชื่อมต่อ ML API ไม่สำเร็จ: {err}"

    # ดึงประวัติล่าสุด (ผ่าน ML API -> PostgreSQL)
    try:
        history = requests.get(f"{ML_API_URL}/history", timeout=10).json().get("items", [])
    except requests.RequestException:
        history = []

    return render_template(
        "index.html",
        result=result,
        error=error,
        history=history,
        ml_api_url=ML_API_URL,
    )


if __name__ == "__main__":
    # ใช้เฉพาะตอนพัฒนา; ใน production รันด้วย gunicorn (ดู Dockerfile)
    app.run(host="0.0.0.0", port=5000, debug=True)

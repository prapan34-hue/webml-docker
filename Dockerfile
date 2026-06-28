# ---- ML API service: FastAPI + scikit-learn ----
FROM python:3.11-slim

# กัน Python เขียน .pyc และให้ log ออกทันที
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_PATH=/app/artifacts/model.joblib

WORKDIR /app

# ติดตั้ง dependencies ก่อน (ใช้ layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกซอร์สโค้ด
COPY app ./app

# โฟลเดอร์เก็บโมเดลที่เทรนแล้ว
RUN mkdir -p /app/artifacts

EXPOSE 8000

# รันด้วย uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

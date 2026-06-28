"""
ML API service (FastAPI)
- รับฟีเจอร์ดอกไอริส -> ทำนาย species ด้วยโมเดล -> บันทึกลง PostgreSQL
- เปิด endpoint /health สำหรับ healthcheck, /predict สำหรับทำนาย, /history สำหรับดูประวัติ
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import db
from app.model import get_model, predict as run_predict


class IrisInput(BaseModel):
    sepal_length: float = Field(..., ge=0, le=20, examples=[5.1])
    sepal_width: float = Field(..., ge=0, le=20, examples=[3.5])
    petal_length: float = Field(..., ge=0, le=20, examples=[1.4])
    petal_width: float = Field(..., ge=0, le=20, examples=[0.2])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ตอน start: รอ DB พร้อม -> สร้างตาราง -> โหลด/เทรนโมเดล
    db.wait_for_db()
    db.init_db()
    app.state.model = get_model()
    print("[ml-api] startup complete", flush=True)
    yield


app = FastAPI(title="Iris ML Inference API", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    """ใช้โดย Docker healthcheck"""
    return {"status": "ok"}


@app.post("/predict")
def predict(data: IrisInput):
    try:
        result = run_predict(app.state.model, data.model_dump())
        db.save_prediction(data.model_dump(), result["species"], result["probability"])
        return result
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(err))


@app.get("/history")
def history(limit: int = 10):
    return {"items": db.fetch_history(limit)}

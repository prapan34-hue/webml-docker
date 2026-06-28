"""
โมดูลโมเดล Machine Learning
- เทรนโมเดลจำแนกพันธุ์ดอกไอริส (Iris) ด้วย scikit-learn
- บันทึก/โหลดโมเดลจากไฟล์ .joblib เพื่อไม่ต้องเทรนใหม่ทุกครั้ง
"""
import os
import joblib
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = os.getenv("MODEL_PATH", "/app/artifacts/model.joblib")

# ลำดับชื่อคลาส (species) ตรงกับ target ของชุดข้อมูล Iris
CLASSES = ["setosa", "versicolor", "virginica"]

# ลำดับฟีเจอร์ที่โมเดลคาดหวัง (หน่วยเป็นเซนติเมตร)
FEATURE_ORDER = ["sepal_length", "sepal_width", "petal_length", "petal_width"]


def train_and_save() -> RandomForestClassifier:
    """เทรนโมเดลจากชุดข้อมูล Iris แล้วบันทึกลงดิสก์"""
    data = load_iris()
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(data.data, data.target)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(clf, MODEL_PATH)
    return clf


def get_model() -> RandomForestClassifier:
    """โหลดโมเดลถ้ามีอยู่แล้ว ไม่งั้นเทรนใหม่"""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return train_and_save()


def predict(model: RandomForestClassifier, features: dict) -> dict:
    """รับ dict ฟีเจอร์ คืนผลทำนาย species + ความน่าจะเป็น"""
    row = [[float(features[name]) for name in FEATURE_ORDER]]
    pred_idx = int(model.predict(row)[0])
    proba = float(max(model.predict_proba(row)[0]))
    return {"species": CLASSES[pred_idx], "probability": round(proba, 4)}

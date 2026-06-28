# 🌸 Web-ML Demo — ระบบทำนายพันธุ์ดอกไอริสด้วย Docker Compose

โปรเจกต์ตัวอย่าง "ระบบบริการที่ซับซ้อน" ที่ประกอบด้วย **3 containers** ทำงานร่วมกันจริงผ่าน
Docker network เดียวกัน เหมาะสำหรับวิชา Machine Learning / Independent Study

| Service | เทคโนโลยี | หน้าที่ | พอร์ต (host) |
|---------|-----------|---------|--------------|
| `web` | Flask + gunicorn | รับ-แสดงผลกับผู้ใช้ (ฟอร์มเว็บ) | `8080` |
| `ml-api` | FastAPI + scikit-learn | ทำนายผลด้วยโมเดล ML (Random Forest) | `8000` |
| `db` | PostgreSQL 16 | เก็บประวัติการทำนาย (ข้อมูลคงอยู่) | ภายในเท่านั้น |

> **เหตุผลการเลือกเทคโนโลยี**
> - **Flask** สำหรับ frontend เพราะเบา เขียนฟอร์ม HTML ได้ตรงไปตรงมา เหมาะกับ demo
> - **FastAPI** สำหรับ ML API เพราะเร็ว มี data validation ในตัว (Pydantic) และทำเอกสาร API อัตโนมัติที่ `/docs`
> - **PostgreSQL** เพราะเป็นฐานข้อมูลมาตรฐานระดับ production รองรับ JSONB เก็บฟีเจอร์ได้สะดวก

---

## 🏗️ สถาปัตยกรรมและการไหลของข้อมูล

```
                       Docker network: app-net
  ┌─────────────┐        ┌──────────────┐        ┌──────────────┐
  │    web      │        │   ml-api     │        │     db       │
  │  (Flask)    │            │ (FastAPI)    │        │ (PostgreSQL) │
  │  :5000      │            │  :8000       │        │  :5432       │
  └─────┬───────┘        └──────┬───────┘        └──────┬───────┘
        │                       │                       │
   host :8080             host :8000              (internal only)
        │                       │                       │
   ผู้ใช้เปิดเบราว์เซอร์          │                       │
        │  1. กรอกฟอร์ม          │                       │
        ├──── POST /predict ───▶│                       │
        │   http://ml-api:8000  │ 2. โมเดลทำนาย species  │
        │                       ├──── INSERT ─────────▶│ 3. บันทึกผล
        │◀──── {species,prob} ──┤                       │
        │                       │                       │
        │  4. GET /history ────▶│──── SELECT ─────────▶│
        │◀──── ประวัติล่าสุด ────┤◀──────────────────────┤
        ▼
   แสดงผล + ตารางประวัติ
```

**จุดสำคัญ:** ทุก service อ้างถึงกันด้วย **ชื่อ service** (`ml-api`, `db`) ไม่ใช่ IP หรือ `localhost`
เช่น `web` เรียก `http://ml-api:8000` และ `ml-api` ต่อ DB ที่ host `db` — Docker DNS แปลงชื่อให้เอง

---

## 📁 โครงสร้างโฟลเดอร์

```
webml-docker/
├── docker-compose.yml          # รวมทุก service: network, volume, healthcheck, depends_on
├── .env.example                # ตัวอย่างตัวแปรลับ (คัดลอกเป็น .env)
├── .env                        # ค่าจริง (อยู่ใน .gitignore ไม่ commit)
├── .gitignore
├── README.md
├── ml-api/                     # ── ML inference service ──
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .dockerignore
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI: /health /predict /history
│       ├── model.py            # เทรน/โหลดโมเดล + ทำนาย
│       └── db.py               # เชื่อมต่อ PostgreSQL, save/fetch
└── web/                        # ── Frontend service ──
    ├── Dockerfile
    ├── requirements.txt
    ├── .dockerignore
    ├── app.py                  # Flask: ฟอร์ม + เรียก ml-api
    └── templates/
        └── index.html
```

---

## 🚀 วิธี Build & Run

### 1. เตรียมไฟล์ตัวแปรลับ
```bash
cd webml-docker
cp .env.example .env
# (แก้รหัสผ่านใน .env ตามต้องการ)
```

### 2. สั่ง build และรันทั้งระบบ
```bash
docker compose up --build
```
รันเบื้องหลัง (detached):
```bash
docker compose up --build -d
```

### 3. ลำดับการ start (คุมด้วย depends_on + healthcheck)
```
db (รอจน pg_isready ผ่าน)  →  ml-api (รอจน /health = 200)  →  web
```

---

## 🔍 ตรวจสอบสถานะและ Log

```bash
# ดูสถานะทุก service + ผลลัพธ์ healthcheck (ควรเห็น (healthy))
docker compose ps

# ดู log รวมทุก service
docker compose logs -f

# ดู log เฉพาะ service
docker compose logs -f ml-api
docker compose logs -f web
docker compose logs -f db
```
ตัวอย่างผลลัพธ์ `docker compose ps` ที่คาดหวัง:
```
NAME           SERVICE   STATUS                 PORTS
webml-db       db        Up (healthy)
webml-ml-api   ml-api    Up (healthy)           0.0.0.0:8000->8000/tcp
webml-web      web       Up (healthy)           0.0.0.0:8080->5000/tcp
```

---

## ✅ วิธีทดสอบ (พิสูจน์ว่า ≥2 container ทำงานร่วมกัน)

### ทดสอบที่ 1 — เปิดเบราว์เซอร์ (web → ml-api → db)
เปิด **http://localhost:8080** กรอกค่าแล้วกด "ทำนาย"
ผลลัพธ์ที่ได้และตารางประวัติด้านล่าง พิสูจน์ว่า `web` คุยกับ `ml-api` และ `ml-api` เขียน/อ่าน `db`

### ทดสอบที่ 2 — ยิง ML API ตรง ๆ ด้วย curl
```bash
# health check
curl http://localhost:8000/health
# -> {"status":"ok"}

# ทำนาย (ตัวอย่างค่าของ setosa)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sepal_length":5.1,"sepal_width":3.5,"petal_length":1.4,"petal_width":0.2}'
# -> {"species":"setosa","probability":1.0}

# ดูประวัติที่อ่านจาก PostgreSQL
curl http://localhost:8000/history
```

### ทดสอบที่ 3 — พิสูจน์การสื่อสารข้าม container "จากภายใน" (ชื่อ service)
สั่งจาก container `web` ให้เรียก `ml-api` ด้วยชื่อ service โดยตรง:
```bash
docker compose exec web python -c \
 "import requests; print(requests.get('http://ml-api:8000/health').json())"
# -> {'status': 'ok'}
```

### ทดสอบที่ 4 — ยืนยันว่าข้อมูลถูกบันทึกลง PostgreSQL จริง
```bash
docker compose exec db psql -U mluser -d mlpredictions \
  -c "SELECT id, species, probability, created_at FROM predictions ORDER BY id DESC LIMIT 5;"
```

> เอกสาร API อัตโนมัติของ FastAPI: **http://localhost:8000/docs**

---

## 🧹 การหยุดและล้างระบบ

```bash
docker compose down           # หยุดและลบ container/network (เก็บ volume ข้อมูลไว้)
docker compose down -v        # ลบ volume ข้อมูล PostgreSQL ด้วย (เริ่มใหม่หมด)
```

---

## 🧠 หมายเหตุด้านความปลอดภัย / การออกแบบ
- รหัสผ่าน DB อ่านจาก `.env` ผ่าน environment variables — **ไม่ hardcode** ในโค้ดหรือ compose
- `db` ไม่เปิดพอร์ตออก host (เข้าถึงได้เฉพาะภายใน network `app-net`) เพื่อความปลอดภัย
- ข้อมูลใน PostgreSQL เก็บใน named volume `pgdata` จึงคงอยู่แม้ลบ container
- `ml-api` รอ `db` healthy และ `web` รอ `ml-api` healthy ป้องกัน race condition ตอน start

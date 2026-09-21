"""
main.py
========
PENTING — PERBAIKAN BUG CSS TIDAK TER-LOAD dari versi sebelumnya:
StaticFiles(directory="static") dan Jinja2Templates(directory="templates")
sebelumnya memakai path RELATIF, yang resolusinya tergantung dari
directory tempat `uvicorn` dijalankan. Kalau dijalankan dari folder lain,
FastAPI 404 di semua asset, JS, dan CSS -> HTML tampil tanpa styling
(persis bug yang kamu laporkan).

Perbaikannya: semua path dibangun dari BASE_DIR = lokasi file main.py
ini sendiri, jadi selalu benar berapa pun current working directory saat
`uvicorn main:app` dijalankan.

TAHAP INI HANYA: FORM -> VALIDATION -> EXISTING PREPROCESSING -> BASE_PREDICTORS.
Tidak ada model, training, atau endpoint prediksi (lihat routes/input.py).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routes.input import router as input_router
from routes.predict import router as predict_router
from preprocessing.mappings import (
    GENDER_MAPPING, EDUCATION_MAPPING, SCHOOL_STATUS_MAPPING, MARITAL_STATUS_MAPPING,
    EMPLOYMENT_STATUS_MAPPING, SECTOR_MAPPING, HOUSE_MAPPING, FLOOR_MAPPING, WALL_MAPPING,
    ROOF_MAPPING, WATER_MAPPING, LIGHTING_MAPPING, EPOWER_MAPPING, COOKING_FUEL_MAPPING,
    TOILET_MAPPING, SEPTIC_MAPPING, ASSET_MAPPING,
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="Skripsi Proxy Means Test (PMT) — Input & Preprocessing")

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app.include_router(input_router)
app.include_router(predict_router)

FORM_MAPPINGS = {
    "gender": GENDER_MAPPING,
    "education": EDUCATION_MAPPING,
    "school_status": SCHOOL_STATUS_MAPPING,
    "marital_status": MARITAL_STATUS_MAPPING,
    "employment_status": EMPLOYMENT_STATUS_MAPPING,
    "sector": SECTOR_MAPPING,
    "house_type": HOUSE_MAPPING,
    "floor_type": FLOOR_MAPPING,
    "wall_type": WALL_MAPPING,
    "roof_type": ROOF_MAPPING,
    "water_source": WATER_MAPPING,
    "lighting_source": LIGHTING_MAPPING,
    "electric_power": EPOWER_MAPPING,
    "cooking_fuel": COOKING_FUEL_MAPPING,
    "toilet_type": TOILET_MAPPING,
    "septic_type": SEPTIC_MAPPING,
    "assets": ASSET_MAPPING,
}

# Kode kabupaten/kota (Jawa Tengah + DIY) -> nama, dipakai dropdown wilayah.
# region hanya diteruskan apa adanya oleh backend (bukan bagian BASE_PREDICTORS).
KAB_NAMES = {
    3301: "Cilacap", 3302: "Banyumas", 3303: "Purbalingga", 3304: "Banjarnegara",
    3305: "Kebumen", 3306: "Purworejo", 3307: "Wonosobo", 3308: "Magelang",
    3309: "Boyolali", 3310: "Klaten", 3311: "Sukoharjo", 3312: "Wonogiri",
    3313: "Karanganyar", 3314: "Sragen", 3315: "Grobogan", 3316: "Blora",
    3317: "Rembang", 3318: "Pati", 3319: "Kudus", 3320: "Jepara",
    3321: "Demak", 3322: "Semarang", 3323: "Temanggung", 3324: "Kendal",
    3325: "Batang", 3326: "Pekalongan", 3327: "Pemalang", 3328: "Tegal",
    3329: "Brebes", 3371: "Kota Magelang", 3372: "Kota Surakarta",
    3373: "Kota Salatiga", 3374: "Kota Semarang", 3375: "Kota Pekalongan",
    3376: "Kota Tegal", 3401: "Kulon Progo", 3402: "Bantul",
    3403: "Gunungkidul", 3404: "Sleman", 3471: "Kota Yogyakarta",
}
KAB_OPTIONS = sorted(({"value": k, "label": v} for k, v in KAB_NAMES.items()), key=lambda x: x["label"])


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request}
    )


@app.get("/cerita", response_class=HTMLResponse)
def cerita_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="cerita.html",
        context={"request": request}
    )


@app.get("/prediksi", response_class=HTMLResponse)
def input_page(request: Request):
    return templates.TemplateResponse(
    request=request,
    name="input.html",
    context={
        "request": request,
        "kab_options": KAB_OPTIONS,
        "opts": FORM_MAPPINGS
    }
)

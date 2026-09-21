"""
routes/predict.py
===================
POST /api/predict — TIPIS, sesuai pola route existing (routes/input.py):
    request -> validation -> existing preprocessing -> prediction service -> response

TIDAK ada logika preprocessing atau model kedua di sini.
"""

from __future__ import annotations

from fastapi import APIRouter
from pathlib import Path

import logging
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from schemas.input_schema import HouseholdInput
from preprocessing.validator import validate_household, ValidationError
from preprocessing.transformer import transform_household_input, compute_h_krt_female
from services.model_loader import ModelNotFoundError, ModelLoadError
from services.prediction_service import predict_single_stage, predict_two_stage, FeatureContractError

logger = logging.getLogger("pmt.routes.predict")
router = APIRouter(prefix="/api", tags=["prediksi"])

# Model mana yang ditandai "Digunakan sebagai estimasi akhir" di UI hasil.
# Dibuat sebagai konfigurasi eksplisit (bukan hardcode di template/JS)
# supaya gampang diubah kalau konfigurasi penelitian berbeda dari asumsi
# ini. [PERLU KONFIRMASI] saya set "two_stage" mengikuti reference UI yang
# kamu kirim (badge ada di kartu Two-Stage) — konfirmasi apakah itu memang
# model final penelitianmu.
FINAL_MODEL: Literal["single_stage", "two_stage"] = "two_stage"


class PredictRequest(HouseholdInput):
    model: Literal["single_stage", "two_stage"] = "two_stage"


def _format_rupiah(value: float) -> str:
    return "Rp " + f"{round(value):,}".replace(",", ".")


@router.post("/predict")
def predict(payload: PredictRequest):
    if payload.region is None:
        raise HTTPException(status_code=400, detail="Kabupaten/kota (region) wajib dipilih untuk menjalankan estimasi.")
    kode_kab = payload.region

    logger.info("[predict] mulai kode_kab=%s model=%s", kode_kab, payload.model)

    try:
        validate_household(payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        features = transform_household_input(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Terdapat masalah dalam memproses data. {e}")

    logger.info("[predict] BASE_PREDICTORS shape=(1, %d)", len(features))

    try:
        if payload.model == "single_stage":
            result = predict_single_stage(features, kode_kab)
            response = {
                "success": True,
                "kode_kab": kode_kab,
                "model": "single_stage_xgb",
                "y_pred": round(result["y_pred"]),
                "y_pred_raw": result["y_pred_raw"],
                "y_pred_formatted": _format_rupiah(result["y_pred"]),
                "p_rentan": None,
                "debug": result["debug"],
            }
        else:
            result = predict_two_stage(features, kode_kab)
            response = {
                "success": True,
                "kode_kab": kode_kab,
                "model": "two_stage_logreg_xgb",
                "y_pred": round(result["y_pred"]),
                "y_pred_raw": result["y_pred_raw"],
                "y_pred_formatted": _format_rupiah(result["y_pred"]),
                "p_rentan": round(result["p_rentan"], 4),
                "p_rentan_pct": round(result["p_rentan"] * 100, 1),
                "debug": result["debug"],
            }
    except ModelNotFoundError as e:
        logger.warning("[predict] model tidak ditemukan: %s", e)
        raise HTTPException(status_code=503, detail="Model untuk kabupaten/kota yang dipilih belum tersedia.") from e
    except ModelLoadError as e:
        logger.error("[predict] gagal load artifact: %s", e)
        raise HTTPException(status_code=500, detail="Terjadi masalah saat memuat model. Silakan coba kembali.") from e
    except FeatureContractError as e:
        logger.error("[predict] feature contract mismatch: %s", e)
        raise HTTPException(status_code=500, detail="Data belum dapat diproses karena konfigurasi model tidak sesuai.") from e
    except Exception as e:
        logger.exception("[predict] error tak terduga")
        raise HTTPException(status_code=500, detail="Terjadi masalah saat menghitung estimasi. Silakan coba kembali.") from e

    response["h_krt_female"] = compute_h_krt_female(payload)
    response["n_features"] = len(features)
    logger.info("[predict] selesai kode_kab=%s model=%s y_pred=%s p_rentan=%s", kode_kab, payload.model, response["y_pred"], response.get("p_rentan"))
    return response


@router.post("/predict/compare")
def predict_compare(payload: HouseholdInput):
    """Jalankan single-stage DAN two-stage sekaligus (untuk result page yang
    menampilkan kartu perbandingan seperti reference UI kamu)."""
    if payload.region is None:
        raise HTTPException(status_code=400, detail="Kabupaten/kota (region) wajib dipilih untuk menjalankan estimasi.")
    kode_kab = payload.region

    try:
        validate_household(payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        features = transform_household_input(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Terdapat masalah dalam memproses data. {e}")

    errors = {}
    single_result = two_result = None

    try:
        single_result = predict_single_stage(features, kode_kab)
    except (ModelNotFoundError, ModelLoadError, FeatureContractError) as e:
        errors["single_stage"] = str(e)

    try:
        two_result = predict_two_stage(features, kode_kab)
    except (ModelNotFoundError, ModelLoadError, FeatureContractError) as e:
        errors["two_stage"] = str(e)

    if single_result is None and two_result is None:
        raise HTTPException(status_code=503, detail="Model untuk kabupaten/kota yang dipilih belum tersedia.")

    return {
        "success": True,
        "kode_kab": kode_kab,
        "final_model": FINAL_MODEL,
        "single_stage": (
            {
                "y_pred": round(single_result["y_pred"]),
                "y_pred_formatted": _format_rupiah(single_result["y_pred"]),
                "debug": single_result["debug"],
            }
            if single_result else {"error": errors.get("single_stage")}
        ),
        "two_stage": (
            {
                "y_pred": round(two_result["y_pred"]),
                "y_pred_formatted": _format_rupiah(two_result["y_pred"]),
                "p_rentan": round(two_result["p_rentan"], 4),
                "p_rentan_pct": round(two_result["p_rentan"] * 100, 1),
                "debug": two_result["debug"],
            }
            if two_result else {"error": errors.get("two_stage")}
        ),
    }

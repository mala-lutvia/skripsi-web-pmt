"""
routes/input.py
================
Endpoint preprocessing. TIPIS: hanya menerima input, memanggil validator,
memanggil transformer, mengembalikan feature vector. Tidak ada logika
preprocessing di sini.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from schemas.input_schema import HouseholdInput
from preprocessing.constants import BASE_PREDICTORS
from preprocessing.validator import validate_household, ValidationError
from preprocessing.transformer import transform_household_input, compute_h_krt_female
from preprocessing.mappings import PERLU_KONFIRMASI_FIELDS

router = APIRouter(prefix="/api", tags=["preprocessing"])


@router.post("/preprocess")
def preprocess(payload: HouseholdInput):
    """Menerima data rumah tangga + anggota, mengembalikan feature vector
    97 kolom. TIDAK memanggil model / melakukan prediksi."""
    try:
        validate_household(payload)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        features = transform_household_input(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": True,
        "n_features": len(features),
        "features": features,
        "region": payload.region,
        "h_krt_female": compute_h_krt_female(payload),
        "perlu_konfirmasi": PERLU_KONFIRMASI_FIELDS,
    }


@router.get("/preprocess/schema-info")
def schema_info():
    return {
        "base_predictors": BASE_PREDICTORS,
        "n_features": len(BASE_PREDICTORS),
        "perlu_konfirmasi": PERLU_KONFIRMASI_FIELDS,
    }

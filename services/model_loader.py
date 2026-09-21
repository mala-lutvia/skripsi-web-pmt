"""
services/model_loader.py
==========================
Bertugas HANYA: menentukan path artifact -> load pkl -> cache -> kembalikan
object model. TIDAK melakukan preprocessing, feature engineering, atau
transformasi target apa pun (itu tugas services/prediction_service.py).

Pola nama file di bawah diambil PERSIS dari screenshot folder yang kamu
kirim (bukan tebakan):

    output_stage1_logreg_raw/models/logreg_{kode_kab}_raw.pkl
    output_two_stage_logreg_xgb_raw/models/xgb_two_stage_{kode_kab}_timedef.pkl
    output_single_stage_xgb_timedef/models/xgb_single_{kode_kab}_timedef.pkl

============================================================================
CATATAN JUJUR — INI BELUM DIVALIDASI TERHADAP FILE ASLI:
Saya belum punya file .pkl asli kamu di sandbox ini (cuma lihat nama file
lewat screenshot). Jadi baris `pickle.load()` di bawah SUDAH BENAR secara
mekanisme (sudah diuji dengan artifact sklearn dummy, lihat
tests/test_model_loader.py), TAPI saya belum bisa membuktikan bahwa isi
pkl asli kamu (object apa yang tersimpan di dalamnya, apakah predict_proba
tersedia, dst) benar-benar cocok dengan asumsi di sini. Begitu kamu upload
file aslinya (atau taruh di folder yang sesuai lalu jalankan lokal),
loader ini akan langsung memberi tahu lewat error yang jelas kalau ada
yang tidak cocok -- bukan diam-diam salah.
============================================================================
"""

from __future__ import annotations

import logging
import joblib
from pathlib import Path
from typing import Any

logger = logging.getLogger("pmt.model_loader")

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIRS = {
    "stage1": BASE_DIR / "output_stage1_logreg_raw" / "models",
    "two_stage": BASE_DIR / "output_two_stage_logreg_xgb_raw" / "models",
    "single_stage": BASE_DIR / "output_single_stage_xgb_timedef" / "models",
}

FILENAME_PATTERNS = {
    "stage1": "logreg_{kab}_raw.pkl",
    "two_stage": "xgb_two_stage_{kab}_timedef.pkl",
    "single_stage": "xgb_single_{kab}_timedef.pkl",
}

_CACHE: dict[tuple[str, int], Any] = {}


class ModelNotFoundError(FileNotFoundError):
    """Artifact untuk kombinasi (model_type, kode_kab) tidak ditemukan."""


class ModelLoadError(RuntimeError):
    """File ditemukan tapi gagal di-unpickle / rusak."""


def resolve_model_path(model_type: str, kode_kab: int) -> Path:
    if model_type not in MODEL_DIRS:
        raise ValueError(f"model_type tidak dikenali: {model_type} (harus salah satu dari {list(MODEL_DIRS)})")
    filename = FILENAME_PATTERNS[model_type].format(kab=kode_kab)
    return MODEL_DIRS[model_type] / filename


def load_model(model_type: str, kode_kab: int, use_cache: bool = True) -> Any:
    """Load satu artifact model (lazy, di-cache in-memory setelah load pertama)."""
    cache_key = (model_type, kode_kab)
    if use_cache and cache_key in _CACHE:
        logger.info("[model_loader] cache hit type=%s kab=%s", model_type, kode_kab)
        return _CACHE[cache_key]

    path = resolve_model_path(model_type, kode_kab)
    logger.info("[model_loader] mencari path=%s exists=%s", path, path.exists())

    if not path.exists():
        raise ModelNotFoundError(
            f"Model '{model_type}' untuk kabupaten/kota kode={kode_kab} tidak ditemukan. "
            f"Path yang dicari: {path} "
            f"dengan nama persis '{FILENAME_PATTERNS[model_type].format(kab=kode_kab)}'."
        )

    try:
        with open(path, "rb") as f:
            obj = joblib.load(f)
    except Exception as e:
        raise ModelLoadError(f"Gagal memuat artifact di {path}: {type(e).__name__}: {e}") from e

    logger.info("[model_loader] berhasil load type=%s kab=%s object_type=%s", model_type, kode_kab, type(obj))
    if use_cache:
        _CACHE[cache_key] = obj
    return obj


def inspect_artifact(obj: Any) -> dict:
    """Introspeksi ringan sebuah artifact yang sudah di-load — dipakai untuk
    debug endpoint dan untuk resolve feature order (lihat prediction_service.py).
    TIDAK menebak apa pun; hanya melaporkan atribut yang benar-benar ada."""
    info = {"python_type": f"{type(obj).__module__}.{type(obj).__name__}"}

    if isinstance(obj, dict):
        info["is_dict"] = True
        info["dict_keys"] = list(obj.keys())
        return info

    info["is_dict"] = False
    info["has_predict"] = hasattr(obj, "predict")
    info["has_predict_proba"] = hasattr(obj, "predict_proba")

    # sklearn wrapper (XGBRegressor/XGBClassifier, LogisticRegression, dst)
    if hasattr(obj, "n_features_in_"):
        info["n_features_in_"] = int(obj.n_features_in_)
    if hasattr(obj, "feature_names_in_"):
        info["feature_names_in_"] = list(obj.feature_names_in_)

    # XGBoost sklearn API menyimpan nama kolom training di booster, kalau
    # dilatih dengan pandas DataFrame
    try:
        booster = obj.get_booster() if hasattr(obj, "get_booster") else None
        if booster is not None and booster.feature_names:
            info["booster_feature_names"] = list(booster.feature_names)
    except Exception:
        pass

    return info


def clear_cache() -> None:
    _CACHE.clear()

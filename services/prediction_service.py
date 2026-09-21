"""
services/prediction_service.py
================================
Tugas: BASE_PREDICTORS (+ p_rentan untuk stage 2) -> model -> output.
TIDAK melakukan preprocessing / feature engineering apa pun -- itu tugas
preprocessing/transformer.py yang sudah ada dan TIDAK disentuh di sini.

============================================================================
DUA ASUMSI YANG BELUM BISA DIVERIFIKASI TANPA FILE ARTIFACT ASLI — dibuat
SEJELAS MUNGKIN dan MUDAH DIUBAH, bukan ditebak lalu disembunyikan:

1. URUTAN KOLOM STAGE 2 (BASE_PREDICTORS + p_rentan)
   Kalau artifact XGBoost-nya sklearn API dan dilatih dengan pandas
   DataFrame, `get_booster().feature_names` MENYIMPAN urutan asli training
   -- kode di bawah SELALU cek ini dulu dan pakai urutan itu kalau ada.
   Fallback (kalau info itu tidak ada di artifact): BASE_PREDICTORS lalu
   `p_rentan` di kolom terakhir (STAGE2_P_RENTAN_POSITION = "last").

2. TARGET TRANSFORMATION
   susenas_preprocess.py (skrip training yang kamu lampirkan sebelumnya)
   menghitung `lpcexp = np.log1p(pcexp)` sebagai salah satu kolom, yang
   MENGINDIKASIKAN kemungkinan target model adalah log1p(pengeluaran) --
   tapi ini BUKAN bukti langsung model di-fit ke `lpcexp` (bisa saja
   fit ke `pcexp` mentah). TARGET_IS_LOG1P di bawah default True dengan
   asumsi ini, tapi endpoint /api/predict SELALU mengembalikan y_pred_raw
   (sebelum inverse transform) di response supaya kamu bisa cocokkan
   sendiri dengan angka di report_xgb_single_2025_timedef.csv /
   master_xgb_single_2025_timedef.csv milikmu. Kalau ternyata salah,
   tinggal ubah TARGET_IS_LOG1P jadi False di file ini.
============================================================================
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from preprocessing.constants import BASE_PREDICTORS
from services.model_loader import load_model, inspect_artifact

logger = logging.getLogger("pmt.prediction_service")

TARGET_IS_LOG1P = True  # lihat catatan di atas — ubah di sini kalau perlu
STAGE2_P_RENTAN_POSITION = "last"  # dipakai hanya kalau feature order tidak bisa dibaca dari artifact


class FeatureContractError(ValueError):
    """Jumlah/nama fitur yang dikirim ke model tidak cocok dengan artifact."""


def _to_dataframe(features: dict, columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame([{c: features[c] for c in columns}])[columns]


def _resolve_feature_order(model, fallback: list[str]) -> tuple[list[str], str]:
    """Coba baca urutan fitur training LANGSUNG dari artifact. Kembalikan
    (urutan_kolom, sumber) supaya bisa dilaporkan di debug output -- source
    of truth = artifact kalau tersedia, bukan tebakan kita."""
    info = inspect_artifact(model)
    if info.get("booster_feature_names"):
        return info["booster_feature_names"], "booster.feature_names (dari artifact)"
    if info.get("feature_names_in_"):
        return info["feature_names_in_"], "feature_names_in_ (dari artifact)"
    return fallback, "fallback (BASE_PREDICTORS urutan konfigurasi, TIDAK terbaca dari artifact)"


def _check_feature_count(model, X: pd.DataFrame, model_label: str) -> None:
    info = inspect_artifact(model)
    expected = info.get("n_features_in_")
    if expected is not None and expected != X.shape[1]:
        raise FeatureContractError(
            f"{model_label} feature mismatch: artifact mengharapkan {expected} fitur, "
            f"tapi input yang dikirim ada {X.shape[1]} fitur. Kolom yang dikirim: "
            f"{list(X.columns)}"
        )


def _inverse_transform_target(y_raw: float) -> float:
    return float(np.expm1(y_raw)) if TARGET_IS_LOG1P else float(y_raw)


def predict_single_stage(features: dict, kode_kab: int) -> dict:
    model = load_model("single_stage", kode_kab)
    single_info = inspect_artifact(model)

    order, source = _resolve_feature_order(model, BASE_PREDICTORS)
    missing = [c for c in order if c not in features]
    if missing:
        raise FeatureContractError(f"Fitur yang dibutuhkan model single-stage tapi tidak ada di BASE_PREDICTORS: {missing}")
    X = _to_dataframe(features, order)
    _check_feature_count(model, X, "Single-stage")

    y_raw = float(np.asarray(model.predict(X))[0])
    y_pred = _inverse_transform_target(y_raw)

    logger.info("[predict] single_stage kab=%s shape=%s y_raw=%s y_pred=%s", kode_kab, X.shape, y_raw, y_pred)

    return {
        "y_pred_raw": y_raw,
        "y_pred": y_pred,
        "debug": {
            "kode_kab": kode_kab,
            "model": "single_stage_xgb",
            "feature_order_source": source,
            "input_shape": list(X.shape),
            "artifact_info": single_info,
        },
    }


def predict_two_stage(features: dict, kode_kab: int) -> dict:
    stage1 = load_model("stage1", kode_kab)
    stage1_info = inspect_artifact(stage1)
    if not stage1_info.get("has_predict_proba"):
        raise FeatureContractError(
            f"Artifact Stage 1 untuk kab={kode_kab} tidak punya predict_proba() "
            f"(python_type={stage1_info.get('python_type')}). Tidak bisa menghasilkan "
            f"p_rentan kontinu sesuai kontrak Two-Stage tanpa ini -- cek ulang artifact."
        )
    order1, source1 = _resolve_feature_order(stage1, BASE_PREDICTORS)
    X1 = _to_dataframe(features, order1)
    _check_feature_count(stage1, X1, "Stage 1")
    proba = np.asarray(stage1.predict_proba(X1))
    p_rentan = float(proba[0, 1] if proba.ndim == 2 and proba.shape[1] > 1 else proba[0])

    stage2 = load_model("two_stage", kode_kab)
    stage2_info = inspect_artifact(stage2)
    fallback_order2 = (
        BASE_PREDICTORS + ["p_rentan"] if STAGE2_P_RENTAN_POSITION == "last" else ["p_rentan"] + BASE_PREDICTORS
    )
    order2, source2 = _resolve_feature_order(stage2, fallback_order2)

    features_with_p = dict(features)
    features_with_p["p_rentan"] = p_rentan
    missing2 = [c for c in order2 if c not in features_with_p]
    if missing2:
        raise FeatureContractError(
            f"Fitur yang dibutuhkan model Stage 2 tapi tidak tersedia: {missing2}. "
            f"Urutan yang dicoba (source={source2}): {order2}"
        )
    X2 = _to_dataframe(features_with_p, order2)
    _check_feature_count(stage2, X2, "Stage 2")

    y_raw = float(np.asarray(stage2.predict(X2))[0])
    y_pred = _inverse_transform_target(y_raw)

    logger.info(
        "[predict] two_stage kab=%s stage1_shape=%s p_rentan=%s stage2_shape=%s y_raw=%s y_pred=%s",
        kode_kab, X1.shape, p_rentan, X2.shape, y_raw, y_pred,
    )

    return {
        "p_rentan": p_rentan,
        "y_pred_raw": y_raw,
        "y_pred": y_pred,
        "debug": {
            "kode_kab": kode_kab,
            "model": "two_stage_logreg_xgb",
            "stage1_feature_order_source": source1,
            "stage2_feature_order_source": source2,
            "stage1_input_shape": list(X1.shape),
            "stage2_input_shape": list(X2.shape),
            "stage1_artifact_info": stage1_info,
            "stage2_artifact_info": stage2_info,
        },
    }

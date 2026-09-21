"""
preprocessing/transformer.py
==============================
transform_household_input(): mengubah HouseholdInput (sudah lolos
validate_household) menjadi feature vector dict, key & urutan = BASE_PREDICTORS.

TIDAK ADA standardisasi/scaling/PCA/feature engineering tambahan.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from . import constants as c
from .mappings import age_to_bucket
from schemas.input_schema import HouseholdInput


def _zero_vector() -> Dict[str, float]:
    return {col: 0 for col in c.BASE_PREDICTORS}


def transform_household_input(data: HouseholdInput) -> Dict[str, float]:
    row = _zero_vector()
    n = data.household_count
    row["h_hhcount"] = n

    edu_counts = {k: 0 for k in c.EDU_LIST}

    for m in data.members:
        row[m.gender] += 1
        row[age_to_bucket(m.age)] += 1
        edu_counts[m.education] += 1
        row[m.school_status] += 1
        row[m.marital_status] += 1

        if m.employment_status is not None and m.employment_sector is not None:
            suffix = c.STAT_CODE_TO_SUFFIX[m.employment_status]
            bucket = f"h_sec{m.employment_sector}_stat{suffix}"
            if bucket not in row:
                raise ValueError(f"Kombinasi sektor/status kerja menghasilkan bucket tidak dikenal: {bucket}")
            row[bucket] += 1

    # Pendidikan: WAJIB proporsi
    for edu_col, count in edu_counts.items():
        row[edu_col] = count / n if n else 0

    # Rumah tangga: one-hot (satu kali)
    h = data.housing
    row[h.house_type] = 1
    row[h.floor_type] = 1
    row[h.wall_type] = 1
    row[h.roof_type] = 1
    row[h.water_source] = 1
    row[h.lighting_source] = 1
    row[h.electric_power] = 1
    row[h.cooking_fuel] = 1
    row[h.toilet_type] = 1
    row[h.septic_type] = 1

    # Aset
    for aset in data.assets.owned:
        row[aset] = 1

    # Luas lantai -> log1p
    row["h_lnluaslantai"] = float(np.log1p(h.floor_area)) if h.floor_area > 0 else 0.0

    # Jumlah keluarga (field rumah tangga, terpisah dari h_hhcount)
    row["h_nfamily"] = h.family_count

    # Validasi akhir: tidak ada kolom hilang/lebih, tidak ada NaN
    missing = [col for col in c.BASE_PREDICTORS if col not in row]
    if missing:
        raise ValueError(f"Feature vector kekurangan kolom: {missing}")
    extra = [col for col in row if col not in c.BASE_PREDICTORS]
    if extra:
        raise ValueError(f"Feature vector punya kolom di luar BASE_PREDICTORS: {extra}")
    nan_cols = [col for col, val in row.items() if val is None or (isinstance(val, float) and np.isnan(val))]
    if nan_cols:
        raise ValueError(f"Feature vector mengandung NaN pada kolom: {nan_cols}")

    return {col: row[col] for col in c.BASE_PREDICTORS}


def compute_h_krt_female(data: HouseholdInput) -> int:
    """h_krt_female: info tambahan hasil preprocessing asli, BUKAN bagian
    BASE_PREDICTORS — dihitung dari anggota yang is_head=True."""
    head = next((m for m in data.members if m.is_head), None)
    if head is None:
        return 0
    return 1 if head.gender == "h_nfemale" else 0

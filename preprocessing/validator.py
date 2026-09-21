"""
preprocessing/validator.py
===========================
Validasi lintas-field, dipanggil SEBELUM transformer.py. Tidak dicampur
dengan HTML — bisa dipanggil langsung dari Python (lihat tests/).
"""

from __future__ import annotations

from schemas.input_schema import HouseholdInput


class ValidationError(Exception):
    """Dipakai routes/input.py untuk balas 400 dengan pesan jelas."""


def validate_household(data: HouseholdInput) -> None:
    errors: list[str] = []

    # 1. h_hhcount > 0
    if data.household_count < 1:
        errors.append("household_count harus lebih dari 0")

    # 2. jumlah anggota yang diinput = h_hhcount
    if len(data.members) != data.household_count:
        errors.append(
            f"household_count={data.household_count} tapi data anggota yang "
            f"dikirim ada {len(data.members)} — jumlah kartu Anggota yang "
            f"diisi user harus sama dengan jumlah anggota yang dipilih di awal."
        )

    # 3. tepat 1 kepala rumah tangga
    n_head = sum(1 for m in data.members if m.is_head)
    if n_head == 0:
        errors.append("Belum ada anggota yang ditandai sebagai kepala rumah tangga.")
    elif n_head > 1:
        errors.append(f"Ada {n_head} anggota yang ditandai kepala rumah tangga, harus tepat 1.")

    # 4-8: karena tiap anggota wajib mengisi gender/umur/pendidikan/status
    # sekolah/status kawin (required field di HouseholdMember), otomatis
    # tercapai kalau butir 2 lolos. Tetap dicek eksplisit di sini.
    if data.members:
        n = len(data.members)
        checks = {
            "jenis kelamin": sum(1 for m in data.members if m.gender),
            "umur": sum(1 for m in data.members if m.age is not None),
            "pendidikan": sum(1 for m in data.members if m.education),
            "status sekolah": sum(1 for m in data.members if m.school_status),
            "status perkawinan": sum(1 for m in data.members if m.marital_status),
        }
        for label, count in checks.items():
            if count != n:
                errors.append(f"Data {label} tidak lengkap untuk semua anggota ({count}/{n}).")

    # Kombinasi status kerja + sektor: harus sama-sama terisi atau kosong
    for i, m in enumerate(data.members, start=1):
        if (m.employment_status is None) != (m.employment_sector is None):
            errors.append(
                f"Anggota {i}: status pekerjaan dan sektor pekerjaan harus "
                f"sama-sama diisi, atau sama-sama kosong (tidak bekerja)."
            )

    # 9. luas lantai >= 0 (sudah dijamin pydantic, dicek ulang)
    if data.housing.floor_area < 0:
        errors.append("Luas lantai tidak boleh negatif.")

    # 10. jumlah keluarga >= 1 (sudah dijamin pydantic, dicek ulang)
    if data.housing.family_count < 1:
        errors.append("Jumlah keluarga harus minimal 1.")

    if errors:
        raise ValidationError(" | ".join(errors))

"""
mappings.py
===========
Semua pemetaan label manusiawi <-> kode internal h_*, dipisah per kategori
sesuai permintaan (GENDER_MAPPING, AGE_MAPPING, dst) supaya bisa diaudit.

Kalau definisi label TIDAK ADA secara eksplisit di skrip training atau di
instruksi Mala, labelnya ditandai literal "[PERLU KONFIRMASI ...]" alih-alih
ditebak. Field itu tetap fungsional (kode internalnya benar), hanya
teksnya placeholder — JANGAN ditampilkan ke user produksi sebelum
dikonfirmasi. Lihat PERLU_KONFIRMASI_FIELDS di bawah.
"""

from __future__ import annotations

PERLU_KONFIRMASI_FIELDS: list[str] = []


def _flag(name: str) -> None:
    if name not in PERLU_KONFIRMASI_FIELDS:
        PERLU_KONFIRMASI_FIELDS.append(name)


GENDER_MAPPING = [
    {"value": "h_nmale", "label": "Laki-laki"},
    {"value": "h_nfemale", "label": "Perempuan"},
]


def age_to_bucket(age: int) -> str:
    """AGE_MAPPING sebagai fungsi (rentang, bukan dropdown) — sesuai
    training age_cat: <=4, <=19, <=64, >64."""
    if age <= 4:
        return "h_nage04"
    if age <= 19:
        return "h_nage519"
    if age <= 64:
        return "h_nage2064"
    return "h_nage65up"


AGE_MAPPING = {
    "h_nage04": "0-4 tahun",
    "h_nage519": "5-19 tahun",
    "h_nage2064": "20-64 tahun",
    "h_nage65up": "65 tahun ke atas",
}

EDUCATION_MAPPING = [
    {"value": "h_notgrad", "label": "Tidak tamat SD"},
    {"value": "h_ngrad_sd", "label": "SD"},
    {"value": "h_ngrad_smp", "label": "SMP"},
    {"value": "h_ngrad_sma", "label": "SMA"},
    {"value": "h_ngrad_d", "label": "Diploma"},
    {"value": "h_ngrad_s", "label": "Sarjana"},
]

SCHOOL_STATUS_MAPPING = [
    {"value": "h_neverschool", "label": "Tidak/belum pernah sekolah"},
    {"value": "h_stillschool", "label": "Masih sekolah"},
    {"value": "h_notschool", "label": "Tidak bersekolah lagi"},
]

MARITAL_STATUS_MAPPING = [
    {"value": "h_notmarried", "label": "Belum kawin"},
    {"value": "h_married", "label": "Kawin"},
    {"value": "h_divorced", "label": "Cerai hidup"},
    {"value": "h_widowed", "label": "Cerai mati"},
]


_flag("status_pekerjaan")
EMPLOYMENT_STATUS_MAPPING = [
    {"value": 0, "label": "Tidak bekerja"},
    {"value": 1, "label": "Berusaha sendiri"},
    {"value": 2, "label": "Berusaha dibantu buruh tidak tetap/pekerja keluarga/tidak dibayar"},
    {"value": 3, "label": "Berusaha dibantu buruh tetap dan dibayar"},
    {"value": 4, "label": "Buruh/karyawan/pegawai"},
    {"value": 5, "label": "Pekerja bebas"},
    {"value": 6, "label": "Pekerja keluarga atau tidak dibayar"},
]


_flag("sektor_pekerjaan")
SECTOR_MAPPING = [
    {"value": 1, "label": "Pertanian/Hortikultura/Perkebunan/Perikanan/Peternakan/Kehutanan"},
    {"value": 2, "label": "Pertambangan dan Penggalian/Industri Pengolahan/Pengadaan listrik, gas, uap, dan udara dingin/Konstruksi"},
    {"value": 3, "label": "Pengelolaan air, limbah, sampah, dan aktivitas remediasi/Perdagangan, Pengangkutan, dan Lainnya"},
]


_flag("jenis_rumah")
HOUSE_MAPPING = [
    {"value": "h_house1", "label": "Milik Sendiri"},
    {"value": "h_house2", "label": "Bebas Sewa/Lainnya"},
    {"value": "h_house3", "label": "Kontrak/Sewa"},
    {"value": "h_house4", "label": "Dinas"},
]


FLOOR_MAPPING = [
    {"value": "h_floor1", "label": "Marmer/Granit/Keramik/Parket/Vinil/Karpet", "color": "#A8D5BA"},
    {"value": "h_floor2", "label": "Ubin/Tegel/Teraso", "color": "#F9E07F"},
    {"value": "h_floor3", "label": "Kayu/Papan/Semen/Bata Merah", "color": "#F4A96A"},
    {"value": "h_floor4", "label": "Lainnya", "color": "#E8877A"},
]

WALL_MAPPING = [
    {"value": "h_wall1", "label": "Tembok", "color": "#A8D5BA"},
    {"value": "h_wall2", "label": "Plesteran/Kawat/Kayu/Papan", "color": "#F9E07F"},
    {"value": "h_wall3", "label": "Anyaman Bambu/Bambu", "color": "#F4A96A"},
    {"value": "h_wall4", "label": "Lainnya", "color": "#E8877A"},
]

ROOF_MAPPING = [
    {"value": "h_roof1", "label": "Beton", "color": "#A8D5BA"},
    {"value": "h_roof2", "label": "Genteng", "color": "#F9E07F"},
    {"value": "h_roof3", "label": "Seng/Asbes/Bambu/Kayu", "color": "#F4A96A"},
    {"value": "h_roof4", "label": "Lainnya", "color": "#E8877A"},
]

WATER_MAPPING = [
    {"value": "h_dwater1", "label": "Kemasan Bermerek"},
    {"value": "h_dwater2", "label": "Isi Ulang/Leding"},
    {"value": "h_dwater3", "label": "Sumur Bor/Mata Air Terlindung"},
    {"value": "h_dwater4", "label": "Mata Air Tak Terlindung"},
    {"value": "h_dwater5", "label": "Lainnya"},
]

LIGHTING_MAPPING = [
    {"value": "h_lighting1", "label": "Listrik PLN"},
    {"value": "h_lighting2", "label": "Listrik Non-PLN"},
    {"value": "h_lighting3", "label": "Bukan Listrik"},
]

EPOWER_MAPPING = [
    {"value": "h_epower1", "label": "450 VA"},
    {"value": "h_epower2", "label": "900 VA"},
    {"value": "h_epower3", "label": "> 1300 VA"},
]

COOKING_FUEL_MAPPING = [
    {"value": "h_cookingfuel1", "label": "Listrik"},
    {"value": "h_cookingfuel2", "label": "LPG 12 kg"},
    {"value": "h_cookingfuel3", "label": "LPG < 12 kg/Biogas"},
    {"value": "h_cookingfuel4", "label": "Lainnya"},
    {"value": "h_cookingfuel5", "label": "Tidak Memasak"},
]


_flag("jenis_toilet (label kategori 2 vs 4 identik)")
TOILET_MAPPING = [
    {"value": "h_toiltype1", "label": "Ada, digunakan hanya ART sendiri & Leher Angsa"},
    {"value": "h_toiltype2", "label": "Ada, digunakan bersama / MCK Komunal & Leher Angsa"},
    {"value": "h_toiltype3", "label": "Ada, di MCK Umum & Leher Angsa"},
    {"value": "h_toiltype4", "label": "Ada, digunakan hanya ART sendiri & Plengsengan dengan Tutup"},
    {"value": "h_toiltype5", "label": "Ada, digunakan bersama / MCK Komunal & Tutup"},
    {"value": "h_toiltype6", "label": "Ada, di MCK Umum & Plengsengan dengan Tutup"},
]

_flag("jenis_septic")
SEPTIC_MAPPING = [
    {"value": "h_septic1", "label": "Ada, digunakan hanya ART sendiri & Tangki Septik"},
    {"value": "h_septic2", "label": "Ada, digunakan bersama / MCK Komunal & Tangki Septik"},
    {"value": "h_septic3", "label": "Ada, di MCK umum & Tangki Septik"},
    {"value": "h_septic4", "label": "Ada, digunakan hanya ART sendiri & IPAL"},
    {"value": "h_septic5", "label": "Ada, digunakan bersama / MCK Komunal & IPAL"},
]

_flag("aset_internet (ada di training, tidak ada di BASE_PREDICTORS)")
ASSET_MAPPING = [
    {"value": "h_asset_lpg5kg", "label": "LPG ≥ 5,5 kg"},
    {"value": "h_asset_fridge", "label": "Kulkas"},
    {"value": "h_asset_ac", "label": "AC"},
    {"value": "h_asset_wheater", "label": "Water heater"},
    {"value": "h_asset_phone", "label": "Telepon"},
    {"value": "h_asset_computer", "label": "Komputer/Laptop"},
    {"value": "h_asset_jewelry", "label": "Perhiasan"},
    {"value": "h_asset_motorcycle", "label": "Sepeda motor"},
    {"value": "h_asset_boat", "label": "Perahu"},
    {"value": "h_asset_motorboat", "label": "Motorboat"},
    {"value": "h_asset_car", "label": "Mobil"},
    {"value": "h_asset_tv", "label": "TV"},
    {"value": "h_asset_smartphone", "label": "Smartphone"},
    {"value": "h_asset_land", "label": "Tanah"},
]

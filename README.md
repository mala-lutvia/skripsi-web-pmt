# Skripsi PMT — Input & Preprocessing (Website Terintegrasi)

Melanjutkan project existing (bukan project baru). Preprocessing existing
(`preprocessing/` — constants/mappings/validator/transformer) TIDAK diganti
dari sesi sebelumnya, hanya disesuaikan nama field schema (lihat bagian C).
Fokus tahap ini: **FORM → VALIDATION → EXISTING PREPROCESSING → BASE_PREDICTORS → STOP.**
Tidak ada model, training, Stage 1/2, atau endpoint prediksi.

## Menjalankan

```bash
pip install -r requirements.txt
python -m pytest preprocessing/tests/ tests/ -v   # 43/43 harus hijau
uvicorn main:app --reload
```
Buka `http://127.0.0.1:8000`.

---

## A. PROJECT

**Struktur existing yang dipertahankan:** `preprocessing/` sebagai satu-satunya
sumber kebenaran transformasi (constants, mappings, validator, transformer),
dipisah dari layer web (`routes/`, `schemas/`, `templates/`, `static/`) — persis
pola yang sudah dibangun sesi sebelumnya.

**File yang diubah:**
- `preprocessing/__init__.py` — disederhanakan (hanya re-export `BASE_PREDICTORS`).
  **Alasan:** versi sebelumnya re-export `validate_household`/`transform_household_input`
  di level package, tapi modul itu meng-import `schemas.input_schema`, yang
  gantian meng-import `preprocessing.constants` → circular import (app CRASH
  saat startup, ketemu saat smoke-test `uvicorn` sungguhan). Sekarang setiap
  route meng-import langsung dari submodule (`from preprocessing.validator import ...`),
  bukan dari `preprocessing/__init__.py`.
- `preprocessing/validator.py`, `preprocessing/transformer.py` — field internal
  disesuaikan ke kontrak schema baru (`is_head`, `gender`, `age`, dst — lihat
  bagian C), logika aggregation/transformasi TIDAK diubah.

**File yang dibuat baru:** `main.py`, `routes/input.py`, `schemas/input_schema.py`,
`templates/index.html`, `templates/input.html`, `static/css/style.css`,
`static/js/form.js`, `static/assets/*.png` (lihat bagian E), `tests/test_preprocessing.py`.

**Tidak ada preprocessing kedua.** Semua route memanggil fungsi yang sama
di `preprocessing/transformer.py` dan `preprocessing/validator.py`.

---

## B. PREPROCESSING

- **Fungsi yang dipanggil:** `preprocessing.validator.validate_household()` →
  `preprocessing.transformer.transform_household_input()`.
- **Jumlah BASE_PREDICTORS:** 97 (dites di `test_seluruh_base_predictors_tersedia`
  dan `test_urutan_dan_nama_fitur_sama_base_predictors`).
- **Feature order:** sama persis urutan `BASE_PREDICTORS` di `preprocessing/constants.py`.
- **Perubahan terhadap preprocessing existing:** hanya nama field input
  (`jenis_kelamin`→`gender`, dst — 100% mekanis, LIHAT TABEL DI BAGIAN C).
  Logika aggregation, proporsi pendidikan, one-hot, dan `log1p(luas lantai)`
  **tidak diubah**.

### Tabel mapping raw input → preprocessing → output feature

| UI Question | Raw Field (JSON) | Existing Preprocessing | Output Feature |
|---|---|---|---|
| Kepala rumah tangga? | `members[i].is_head` | tepat 1 True (validator.py) | `h_krt_female` (info tambahan, bukan BASE_PREDICTORS) |
| Jenis kelamin | `members[i].gender` | hitung per kategori (absolut) | `h_nmale`, `h_nfemale` |
| Umur | `members[i].age` | `age_to_bucket()` (0-4/5-19/20-64/65+) | `h_nage04`...`h_nage65up` |
| Pendidikan terakhir | `members[i].education` | hitung lalu dibagi `h_hhcount` (**proporsi**) | `h_ngrad_sd`...`h_notgrad` |
| Status sekolah | `members[i].school_status` | hitung per kategori (absolut) | `h_neverschool`, `h_stillschool`, `h_notschool` |
| Status perkawinan | `members[i].marital_status` | hitung per kategori (absolut) | `h_notmarried`...`h_widowed` |
| Status bekerja + Sektor | `members[i].employment_status` + `.employment_sector` | `STAT_CODE_TO_SUFFIX` → gabung jadi `h_sec{sektor}_stat{suffix}` | `h_sec1_stat1`...`h_sec3_stat6` (18 kolom) |
| Kabupaten/kota | `region` | **diteruskan apa adanya**, TIDAK diproses (bukan bagian BASE_PREDICTORS) | — |
| Luas lantai | `housing.floor_area` | `np.log1p(x)`, 0 kalau x=0 | `h_lnluaslantai` |
| Jumlah keluarga | `housing.family_count` | absolut | `h_nfamily` |
| Jenis rumah / lantai / dinding / atap / air / penerangan / listrik / bahan bakar / toilet / septic | `housing.house_type`, `.floor_type`, dst | one-hot (pilihan=1, lainnya=0) | `h_house1-4`, `h_floor1-4`, dst |
| Aset yang dimiliki | `assets.owned` (list) | 1 kalau ada di list, 0 kalau tidak | `h_asset_lpg5kg`...`h_asset_land` |

---

## C. FORM — daftar pertanyaan final

1. Kabupaten/kota (`region`)
2. Jumlah anggota rumah tangga (stepper, dinamis)
3. **Per anggota** (kartu berulang, pertanyaan identik): Kepala rumah tangga?,
   Jenis kelamin, Umur, Pendidikan terakhir, Status sekolah, Status perkawinan,
   Status bekerja, Sektor pekerjaan (muncul kondisional kalau bekerja)
4. Luas lantai, Jumlah keluarga, Jenis rumah, Jenis lantai, Jenis dinding,
   Jenis atap, Sumber air minum, Sumber penerangan, Daya listrik,
   Bahan bakar memasak, Jenis toilet, Septic tank
5. Aset rumah tangga (checkbox, 14 item)

Daftar ini diambil dari raw input yang benar-benar dipakai `preprocessing/transformer.py`
— tidak ada field yang ditambahkan hanya karena "biasanya dipakai PMT".

**Catatan kontrak data:** frontend TIDAK mengirim `h_nmale=1` dsb — value
yang dikirim untuk field seperti `gender` memang memakai string kode
internal (`"h_nmale"`/`"h_nfemale"`) sebagai *identifier* enum yang stabil
(dipilih lewat radio button berlabel manusiawi "Laki-laki"/"Perempuan"),
BUKAN pengisian angka fitur h_* secara manual — backend tetap yang
melakukan seluruh **agregasi** (hitung per kategori, proporsi, one-hot,
gabungan sektor×status). Tidak ada `maleCount++` atau sejenisnya di JS.

---

## D. DYNAMIC MEMBER

- Tombol `+`/`−` mengubah jumlah kartu anggota; data yang sudah diisi
  disimpan di objek `memberData` di `form.js` supaya tidak hilang saat
  jumlah berubah (dan minta konfirmasi kalau mau menghapus kartu yang
  sudah terisi).
- "Kepala rumah tangga?" diimplementasikan sebagai **radio button lintas
  kartu** (`name="head_selector"`) — otomatis menjamin tepat 1 terpilih
  di sisi UI; backend tetap memvalidasi ulang (`validate_household`)
  supaya aman meski request tidak lewat form ini.
- Saat submit, JS merakit `members[]` dari seluruh kartu dan mengirim
  sebagai JSON ke `/api/preprocess` — backend yang mengagregasi.

---

## E. VISUAL ASSETS (bukan aset kepemilikan rumah tangga)

| File | Sumber | Dipakai di |
|---|---|---|
| `static/assets/logo.png` | **File asli** yang kamu upload (logo Politeknik Statistika STIS) | Navbar |
| `static/assets/background.png`, `asset_building.png` | **File asli** yang kamu upload (foto gedung STIS dengan overlay navy) | Hero background & section "Kondisi tempat tinggal" |
| `static/assets/asset_family.png` | **Temporary** (dibuat lokal, ikon 3 orang) | Section Anggota rumah tangga, kartu "Komposisi keluarga" |
| `static/assets/asset_education.png` | **Temporary** | Kartu "Pendidikan" |
| `static/assets/asset_infrastructure.png` | **Temporary** | Kartu "Infrastruktur" |
| `static/assets/asset_water.png` | **Temporary** | (disiapkan, belum dipasang di section spesifik — lihat catatan di bawah) |
| `static/assets/asset_lighting.png` | **Temporary** | (disiapkan) |
| `static/assets/asset_cooking.png` | **Temporary** | (disiapkan) |
| `static/assets/asset_toilet.png` | **Temporary** | (disiapkan) |
| `static/assets/asset_household_assets.png` | **Temporary** | Section Aset rumah tangga |

Semua file "Temporary" dibuat dengan PIL (bentuk geometris sederhana,
warna navy/oranye sesuai palet), disimpan sebagai file PNG lokal
sungguhan di `static/assets/` — **bukan URL eksternal, bukan broken
image**. Filename sudah stabil sesuai permintaan; kamu tinggal
menimpa file yang sama untuk mengganti dengan desain final, tanpa
perlu mengubah HTML/CSS.

**Catatan jujur:** `asset_water.png`, `asset_lighting.png`, `asset_cooking.png`,
`asset_toilet.png` sudah dibuat dan bisa diakses (`/static/assets/...`, sudah
dites 200 OK), tapi belum saya pasang sebagai ikon di masing-masing field
kondisi tempat tinggal di `templates/input.html` (section itu masih pakai
teks label saja tanpa ikon per-field) — supaya section itu tidak jadi
terlalu ramai untuk satu grid form. Bilang kalau kamu mau saya tambahkan.

---

## F. STATIC FILE TEST

Dites dengan request HTTP sungguhan (`TestClient`, DAN `uvicorn` yang benar-benar
dijalankan dari `/tmp` — direktori yang tidak ada hubungannya dengan project,
persis skenario yang menyebabkan bug CSS-tidak-load sebelumnya):

```
GET /                              -> 200
GET /prediksi                      -> 200
GET /static/css/style.css          -> 200 (content-type: text/css)
GET /static/js/form.js             -> 200
GET /static/assets/logo.png        -> 200 (content-type: image/*)
GET /static/assets/asset_building.png -> 200
GET /static/assets/asset_family.png   -> 200
```

CSS: **PASS**
JS: **PASS**
Assets: **PASS** (11/11 file, lihat `tests/test_preprocessing.py::TestStaticFilesBenarBenarTerServe`)
API: **PASS**

**Akar masalah bug sebelumnya** (sudah diperbaiki): `StaticFiles(directory="static")`
dan `Jinja2Templates(directory="templates")` memakai path relatif terhadap
current working directory saat `uvicorn` dijalankan. Sekarang `main.py` memakai
`BASE_DIR = Path(__file__).resolve().parent` sehingga path selalu benar,
berapa pun folder tempat kamu menjalankan `uvicorn main:app`.

---

## G. END-TO-END TEST

```
Form (JSON) -> POST /api/preprocess -> Pydantic (schemas/input_schema.py)
-> preprocessing.validator.validate_household()
-> preprocessing.transformer.transform_household_input()
-> feature_vector (97 kolom)
```

**PASS** — 43/43 test hijau (`python -m pytest preprocessing/tests/ tests/ -v`),
termasuk skenario 3-anggota persis contoh di instruksi kamu (bagian AK/37):
`h_hhcount=3, h_nmale=1, h_nfemale=2, h_nage519=1, h_nage2064=2,
h_ngrad_sd=1/3, h_ngrad_sma=2/3, h_krt_female=0`. Juga dites: request
gagal 400 kalau jumlah anggota tidak cocok, kalau 0 atau 2 KRT, dan kalau
ada kategori tidak valid.

---

## H. RESPONSIVE TEST

CSS memakai `grid-template-columns` yang collapse ke 1 kolom di bawah 760px
(`@media (max-width: 760px)` di `static/css/style.css`) untuk form fields,
material grid, dan stat cards; navbar link disembunyikan di mobile. **Belum
saya uji dengan browser sungguhan** (sandbox ini tidak punya akses install
browser headless untuk screenshot) — jadi status ini saya laporkan sebagai
**BELUM DITES SECARA VISUAL**, bukan PASS. Tolong cek langsung di HP/tablet
kamu setelah dijalankan; struktur CSS-nya sudah disiapkan tapi saya tidak
mau bilang "sudah responsive" tanpa benar-benar melihatnya.

---

## Yang TIDAK dikerjakan (sesuai instruksi "STOP setelah BASE_PREDICTORS")

`routes/predict.py` dan folder model dari sesi sebelumnya **sengaja
dihapus** dari project ini — instruksi terbaru eksplisit melarang
`predict()`/`predict_proba()`/Stage 1/Stage 2 di tahap ini. Kalau nanti
lanjut ke integrasi model, itu jadi tahap terpisah berikutnya.

## PERLU_KONFIRMASI (belum berubah dari sesi sebelumnya)

Field berikut fungsional tapi labelnya masih placeholder karena skrip
training tidak menyertakan definisi teks eksplisit — lihat komentar
`[PERLU KONFIRMASI]` di `preprocessing/mappings.py`:
status pekerjaan (kode 1-8), nama sektor per grup, jenis rumah
(`h_house1-4`), jenis septic tank, dan label `h_toiltype2` vs `h_toiltype4`
yang identik teksnya ("Ada & Tutup").

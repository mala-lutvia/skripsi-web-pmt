"""
tests/test_preprocessing.py
============================
Test END-TO-END sungguhan: JSON request -> FastAPI route (/api/preprocess)
-> Pydantic validation -> existing preprocessing -> feature vector.
TIDAK bypass ke transformer.py langsung dengan dict buatan (itu ada di
preprocessing/tests/test_transformer.py sebagai unit test terpisah).

Juga menguji static file benar-benar ter-serve (CSS/JS/asset), dan
GET /, GET /prediksi merender HTML dengan status 200.
"""

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _payload_3_anggota():
    """Contoh persis dari instruksi bagian 37: 3 anggota household."""
    return {
        "region": 3471,
        "household_count": 3,
        "members": [
            {
                "is_head": True, "gender": "h_nmale", "age": 45,
                "education": "h_ngrad_sma", "school_status": "h_notschool",
                "marital_status": "h_married", "employment_status": 1, "employment_sector": 1,
            },
            {
                "is_head": False, "gender": "h_nfemale", "age": 40,
                "education": "h_ngrad_sma", "school_status": "h_notschool",
                "marital_status": "h_married", "employment_status": None, "employment_sector": None,
            },
            {
                "is_head": False, "gender": "h_nfemale", "age": 10,
                "education": "h_ngrad_sd", "school_status": "h_stillschool",
                "marital_status": "h_notmarried", "employment_status": None, "employment_sector": None,
            },
        ],
        "housing": {
            "floor_area": 60, "family_count": 3, "house_type": "h_house1",
            "floor_type": "h_floor1", "wall_type": "h_wall1", "roof_type": "h_roof2",
            "water_source": "h_dwater2", "lighting_source": "h_lighting1",
            "electric_power": "h_epower3", "cooking_fuel": "h_cookingfuel2",
            "toilet_type": "h_toiltype1", "septic_type": "h_septic1",
        },
        "assets": {"owned": ["h_asset_fridge", "h_asset_tv", "h_asset_motorcycle"]},
    }


class TestEndToEndPreprocess:
    def test_request_masuk_dan_berhasil_200(self):
        res = client.post("/api/preprocess", json=_payload_3_anggota())
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True

    def test_jumlah_fitur_97(self):
        res = client.post("/api/preprocess", json=_payload_3_anggota())
        data = res.json()
        assert data["n_features"] == 97
        assert len(data["features"]) == 97

    def test_urutan_dan_nama_fitur_sama_base_predictors(self):
        from preprocessing.constants import BASE_PREDICTORS
        res = client.post("/api/preprocess", json=_payload_3_anggota())
        data = res.json()
        assert list(data["features"].keys()) == BASE_PREDICTORS

    def test_hasil_agregasi_gender_dan_umur_sesuai_contoh_instruksi(self):
        res = client.post("/api/preprocess", json=_payload_3_anggota())
        f = res.json()["features"]
        assert f["h_hhcount"] == 3
        assert f["h_nmale"] == 1
        assert f["h_nfemale"] == 2
        assert f["h_nage04"] == 0
        assert f["h_nage519"] == 1
        assert f["h_nage2064"] == 2
        assert f["h_nage65up"] == 0

    def test_pendidikan_proporsi(self):
        res = client.post("/api/preprocess", json=_payload_3_anggota())
        f = res.json()["features"]
        assert f["h_ngrad_sd"] == pytest.approx(1 / 3)
        assert f["h_ngrad_sma"] == pytest.approx(2 / 3)

    def test_krt_female_perempuan_karena_krt_lakilaki(self):
        res = client.post("/api/preprocess", json=_payload_3_anggota())
        data = res.json()
        assert data["h_krt_female"] == 0  # KRT di contoh ini laki-laki

    def test_tidak_ada_model_prediction_di_response(self):
        res = client.post("/api/preprocess", json=_payload_3_anggota())
        data = res.json()
        assert "prediction" not in data
        assert "p_rentan" not in data
        assert "predict" not in str(data.keys())

    def test_jumlah_anggota_tidak_sesuai_gagal_400(self):
        payload = _payload_3_anggota()
        payload["household_count"] = 4  # tidak sesuai jumlah members (3)
        res = client.post("/api/preprocess", json=payload)
        assert res.status_code == 400

    def test_dua_krt_gagal_400(self):
        payload = _payload_3_anggota()
        payload["members"][1]["is_head"] = True  # sekarang ada 2 KRT
        res = client.post("/api/preprocess", json=payload)
        assert res.status_code == 400

    def test_nol_krt_gagal_400(self):
        payload = _payload_3_anggota()
        payload["members"][0]["is_head"] = False  # sekarang 0 KRT
        res = client.post("/api/preprocess", json=payload)
        assert res.status_code == 400

    def test_kategori_tidak_valid_gagal_422_atau_400(self):
        payload = _payload_3_anggota()
        payload["housing"]["floor_type"] = "h_floor99"  # kategori tidak ada
        res = client.post("/api/preprocess", json=payload)
        assert res.status_code in (400, 422)


class TestHalamanHTML:
    def test_get_landing_page_200(self):
        res = client.get("/")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]

    def test_get_input_page_200(self):
        res = client.get("/prediksi")
        assert res.status_code == 200
        assert "text/html" in res.headers["content-type"]
        assert "Estimasi kesejahteraan rumah tangga" in res.text


class TestStaticFilesBenarBenarTerServe:
    """Ini yang membuktikan bug CSS-tidak-load sebelumnya sudah tidak
    terjadi lagi -- request nyata ke /static/..., bukan asumsi path benar."""

    def test_css_ter_serve(self):
        res = client.get("/static/css/style.css")
        assert res.status_code == 200
        assert "text/css" in res.headers["content-type"]
        assert len(res.text) > 100

    def test_js_ter_serve(self):
        res = client.get("/static/js/form.js")
        assert res.status_code == 200
        assert len(res.text) > 100

    @pytest.mark.parametrize("filename", [
        "logo.png", "background.png", "asset_building.png", "asset_family.png",
        "asset_education.png", "asset_infrastructure.png", "asset_water.png",
        "asset_lighting.png", "asset_cooking.png", "asset_toilet.png",
        "asset_household_assets.png",
    ])
    def test_semua_asset_ter_serve(self, filename):
        res = client.get(f"/static/assets/{filename}")
        assert res.status_code == 200, f"{filename} tidak ditemukan / 404"
        assert res.headers["content-type"].startswith("image/")

    def test_input_html_mereferensikan_css_lewat_url_for(self):
        res = client.get("/prediksi")
        assert "/static/css/style.css" in res.text
        assert "/static/js/form.js" in res.text

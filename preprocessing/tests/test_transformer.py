"""
preprocessing/tests/test_transformer.py
Unit test murni Python (tanpa FastAPI) untuk transformer & validator,
supaya preprocessing engine bisa diuji independen dari web layer.
Untuk test END-TO-END lewat endpoint sungguhan, lihat tests/test_preprocessing.py.
"""

import pytest

from preprocessing.constants import BASE_PREDICTORS
from preprocessing.transformer import transform_household_input, compute_h_krt_female
from preprocessing.validator import validate_household, ValidationError
from schemas.input_schema import HouseholdInput, HouseholdMember, HousingInput, AssetInput


def _housing(**overrides):
    base = dict(
        floor_area=45.0, family_count=1, house_type="h_house1", floor_type="h_floor1",
        wall_type="h_wall1", roof_type="h_roof1", water_source="h_dwater1",
        lighting_source="h_lighting1", electric_power="h_epower1",
        cooking_fuel="h_cookingfuel1", toilet_type="h_toiltype1", septic_type="h_septic1",
    )
    base.update(overrides)
    return HousingInput(**base)


def _member(**overrides):
    base = dict(
        is_head=False, gender="h_nmale", age=30, education="h_ngrad_sma",
        school_status="h_notschool", marital_status="h_married",
        employment_status=None, employment_sector=None,
    )
    base.update(overrides)
    return HouseholdMember(**base)


def test_satu_anggota():
    data = HouseholdInput(
        household_count=1, members=[_member(is_head=True)],
        housing=_housing(), assets=AssetInput(owned=[]),
    )
    vec = transform_household_input(data)
    assert vec["h_hhcount"] == 1
    assert list(vec.keys()) == BASE_PREDICTORS


def test_tiga_anggota_contoh_instruksi():
    """Persis contoh transformasi di instruksi bagian AK."""
    data = HouseholdInput(
        household_count=3,
        members=[
            _member(is_head=True, gender="h_nmale", age=45, education="h_ngrad_sma",
                    school_status="h_notschool", marital_status="h_married",
                    employment_status=1, employment_sector=1),
            _member(is_head=False, gender="h_nfemale", age=40, education="h_ngrad_sma",
                    school_status="h_notschool", marital_status="h_married"),
            _member(is_head=False, gender="h_nfemale", age=10, education="h_ngrad_sd",
                    school_status="h_stillschool", marital_status="h_notmarried"),
        ],
        housing=_housing(family_count=3),
        assets=AssetInput(owned=[]),
    )
    vec = transform_household_input(data)
    assert vec["h_hhcount"] == 3
    assert vec["h_nmale"] == 1
    assert vec["h_nfemale"] == 2
    assert vec["h_nage04"] == 0
    assert vec["h_nage519"] == 1
    assert vec["h_nage2064"] == 2
    assert vec["h_nage65up"] == 0
    assert vec["h_ngrad_sd"] == pytest.approx(1 / 3)
    assert vec["h_ngrad_sma"] == pytest.approx(2 / 3)
    assert vec["h_stillschool"] == 1
    assert vec["h_notschool"] == 2
    assert vec["h_notmarried"] == 1
    assert vec["h_married"] == 2
    assert vec["h_sec1_stat1"] == 1
    assert compute_h_krt_female(data) == 0  # KRT laki-laki


def test_gender_aggregation():
    data = HouseholdInput(
        household_count=3,
        members=[_member(gender="h_nmale", is_head=True), _member(gender="h_nfemale"), _member(gender="h_nfemale")],
        housing=_housing(family_count=3), assets=AssetInput(owned=[]),
    )
    vec = transform_household_input(data)
    assert vec["h_nmale"] == 1
    assert vec["h_nfemale"] == 2


def test_umur_aggregation():
    data = HouseholdInput(
        household_count=4,
        members=[_member(age=4, is_head=True), _member(age=19), _member(age=64), _member(age=65)],
        housing=_housing(family_count=4), assets=AssetInput(owned=[]),
    )
    vec = transform_household_input(data)
    assert vec["h_nage04"] == 1
    assert vec["h_nage519"] == 1
    assert vec["h_nage2064"] == 1
    assert vec["h_nage65up"] == 1


def test_pendidikan_proporsi():
    data = HouseholdInput(
        household_count=4,
        members=[
            _member(education="h_ngrad_sd", is_head=True), _member(education="h_ngrad_smp"),
            _member(education="h_ngrad_sma"), _member(education="h_ngrad_sma"),
        ],
        housing=_housing(family_count=4), assets=AssetInput(owned=[]),
    )
    vec = transform_household_input(data)
    assert vec["h_ngrad_sd"] == pytest.approx(0.25)
    assert vec["h_ngrad_smp"] == pytest.approx(0.25)
    assert vec["h_ngrad_sma"] == pytest.approx(0.50)


def test_status_sekolah():
    data = HouseholdInput(
        household_count=3,
        members=[_member(school_status="h_stillschool", is_head=True), _member(school_status="h_notschool"), _member(school_status="h_neverschool")],
        housing=_housing(family_count=3), assets=AssetInput(owned=[]),
    )
    vec = transform_household_input(data)
    assert vec["h_stillschool"] == 1
    assert vec["h_notschool"] == 1
    assert vec["h_neverschool"] == 1


def test_status_perkawinan():
    data = HouseholdInput(
        household_count=4,
        members=[
            _member(marital_status="h_notmarried", is_head=True), _member(marital_status="h_married"),
            _member(marital_status="h_divorced"), _member(marital_status="h_widowed"),
        ],
        housing=_housing(family_count=4), assets=AssetInput(owned=[]),
    )
    vec = transform_household_input(data)
    assert vec["h_notmarried"] == 1 and vec["h_married"] == 1
    assert vec["h_divorced"] == 1 and vec["h_widowed"] == 1


def test_tepat_satu_krt_valid():
    data = HouseholdInput(
        household_count=2, members=[_member(is_head=True), _member(is_head=False)],
        housing=_housing(family_count=2), assets=AssetInput(owned=[]),
    )
    validate_household(data)  # tidak raise


def test_nol_krt_invalid():
    data = HouseholdInput(
        household_count=2, members=[_member(is_head=False), _member(is_head=False)],
        housing=_housing(family_count=2), assets=AssetInput(owned=[]),
    )
    with pytest.raises(ValidationError):
        validate_household(data)


def test_dua_krt_invalid():
    data = HouseholdInput(
        household_count=2, members=[_member(is_head=True), _member(is_head=True)],
        housing=_housing(family_count=2), assets=AssetInput(owned=[]),
    )
    with pytest.raises(ValidationError):
        validate_household(data)


def test_asset_one_hot():
    data = HouseholdInput(
        household_count=1, members=[_member(is_head=True)],
        housing=_housing(), assets=AssetInput(owned=["h_asset_tv", "h_asset_fridge"]),
    )
    vec = transform_household_input(data)
    assert vec["h_asset_tv"] == 1 and vec["h_asset_fridge"] == 1
    others = [k for k in vec if k.startswith("h_asset_") and k not in ("h_asset_tv", "h_asset_fridge")]
    assert all(vec[k] == 0 for k in others)


def test_material_rumah_one_hot():
    data = HouseholdInput(
        household_count=1, members=[_member(is_head=True)],
        housing=_housing(floor_type="h_floor3", wall_type="h_wall2", roof_type="h_roof4"),
        assets=AssetInput(owned=[]),
    )
    vec = transform_household_input(data)
    assert vec["h_floor3"] == 1 and vec["h_floor1"] == 0
    assert vec["h_wall2"] == 1
    assert vec["h_roof4"] == 1


def test_seluruh_base_predictors_tersedia():
    data = HouseholdInput(
        household_count=1, members=[_member(is_head=True)],
        housing=_housing(), assets=AssetInput(owned=[]),
    )
    vec = transform_household_input(data)
    assert list(vec.keys()) == BASE_PREDICTORS
    assert len(vec) == 97


def test_luas_lantai_log1p():
    import numpy as np
    data = HouseholdInput(
        household_count=1, members=[_member(is_head=True)],
        housing=_housing(floor_area=60), assets=AssetInput(owned=[]),
    )
    vec = transform_household_input(data)
    assert vec["h_lnluaslantai"] == pytest.approx(np.log1p(60))


def test_luas_lantai_nol():
    data = HouseholdInput(
        household_count=1, members=[_member(is_head=True)],
        housing=_housing(floor_area=0), assets=AssetInput(owned=[]),
    )
    vec = transform_household_input(data)
    assert vec["h_lnluaslantai"] == 0


def test_invalid_household_count():
    data = HouseholdInput(
        household_count=3, members=[_member(is_head=True), _member()],  # cuma 2, bukan 3
        housing=_housing(family_count=3), assets=AssetInput(owned=[]),
    )
    with pytest.raises(ValidationError):
        validate_household(data)

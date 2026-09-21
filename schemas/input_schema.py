"""
schemas/input_schema.py
========================
Struktur input sesuai konsep yang diminta:

    HouseholdInput
    |- region (kode_kab)
    |- household_count (h_hhcount)
    |- members[] (HouseholdMember)
    |- housing (HousingInput)
    `- assets (AssetInput)

    HouseholdMember
    |- is_head
    |- gender
    |- age
    |- education
    |- school_status
    |- marital_status
    |- employment_status
    `- employment_sector
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from preprocessing import constants as c


class HouseholdMember(BaseModel):
    is_head: bool = Field(..., description="Tepat satu anggota harus True (divalidasi di validator.py)")
    gender: str = Field(..., description="'h_nmale' atau 'h_nfemale'")
    age: int = Field(..., ge=0, le=120)
    education: str
    school_status: str
    marital_status: str
    employment_status: Optional[int] = Field(None, description="kode 1-8, None jika tidak bekerja")
    employment_sector: Optional[int] = Field(None, description="1/2/3, wajib jika employment_status terisi")

    @field_validator("gender")
    @classmethod
    def _v_gender(cls, v):
        if v not in c.GENDER_LIST:
            raise ValueError(f"gender tidak dikenali: {v}")
        return v

    @field_validator("education")
    @classmethod
    def _v_edu(cls, v):
        if v not in c.EDU_LIST:
            raise ValueError(f"education tidak dikenali: {v}")
        return v

    @field_validator("school_status")
    @classmethod
    def _v_school(cls, v):
        if v not in c.SCHOOL_LIST:
            raise ValueError(f"school_status tidak dikenali: {v}")
        return v

    @field_validator("marital_status")
    @classmethod
    def _v_marital(cls, v):
        if v not in c.MARRIAGE_LIST:
            raise ValueError(f"marital_status tidak dikenali: {v}")
        return v

    @field_validator("employment_status")
    @classmethod
    def _v_emp_status(cls, v):
        if v is not None and v not in c.STAT_CODE_TO_SUFFIX:
            raise ValueError(f"employment_status harus salah satu dari {sorted(c.STAT_CODE_TO_SUFFIX)} atau null")
        return v

    @field_validator("employment_sector")
    @classmethod
    def _v_sector(cls, v):
        if v is not None and v not in (1, 2, 3):
            raise ValueError("employment_sector harus 1, 2, atau 3")
        return v


class HousingInput(BaseModel):
    floor_area: float = Field(..., ge=0, description="m^2 -> h_lnluaslantai = log1p(floor_area)")
    family_count: int = Field(..., ge=1, description="-> h_nfamily")
    house_type: str
    floor_type: str
    wall_type: str
    roof_type: str
    water_source: str
    lighting_source: str
    electric_power: str
    cooking_fuel: str
    toilet_type: str
    septic_type: str

    @field_validator("house_type")
    @classmethod
    def _v_house(cls, v):
        if v not in c.HOUSE_LIST:
            raise ValueError(f"house_type tidak dikenali: {v}")
        return v

    @field_validator("floor_type")
    @classmethod
    def _v_floor(cls, v):
        if v not in c.FLOOR_LIST:
            raise ValueError(f"floor_type tidak dikenali: {v}")
        return v

    @field_validator("wall_type")
    @classmethod
    def _v_wall(cls, v):
        if v not in c.WALL_LIST:
            raise ValueError(f"wall_type tidak dikenali: {v}")
        return v

    @field_validator("roof_type")
    @classmethod
    def _v_roof(cls, v):
        if v not in c.ROOF_LIST:
            raise ValueError(f"roof_type tidak dikenali: {v}")
        return v

    @field_validator("water_source")
    @classmethod
    def _v_water(cls, v):
        if v not in c.WATER_LIST:
            raise ValueError(f"water_source tidak dikenali: {v}")
        return v

    @field_validator("lighting_source")
    @classmethod
    def _v_light(cls, v):
        if v not in c.LIGHTING_LIST:
            raise ValueError(f"lighting_source tidak dikenali: {v}")
        return v

    @field_validator("electric_power")
    @classmethod
    def _v_power(cls, v):
        if v not in c.EPOWER_LIST:
            raise ValueError(f"electric_power tidak dikenali: {v}")
        return v

    @field_validator("cooking_fuel")
    @classmethod
    def _v_fuel(cls, v):
        if v not in c.COOKINGFUEL_LIST:
            raise ValueError(f"cooking_fuel tidak dikenali: {v}")
        return v

    @field_validator("toilet_type")
    @classmethod
    def _v_toilet(cls, v):
        if v not in c.TOILTYPE_LIST:
            raise ValueError(f"toilet_type tidak dikenali: {v}")
        return v

    @field_validator("septic_type")
    @classmethod
    def _v_septic(cls, v):
        if v not in c.SEPTIC_LIST:
            raise ValueError(f"septic_type tidak dikenali: {v}")
        return v


class AssetInput(BaseModel):
    owned: List[str] = Field(default_factory=list, description="list value dari ASSET_MAPPING yang dimiliki")

    @field_validator("owned")
    @classmethod
    def _v_owned(cls, v):
        invalid = set(v) - set(c.ASSET_LIST)
        if invalid:
            raise ValueError(f"Aset tidak dikenali: {sorted(invalid)}")
        return v


class HouseholdInput(BaseModel):
    region: Optional[int] = Field(None, description="kode_kab dari dropdown wilayah, diteruskan apa adanya")
    household_count: int = Field(..., ge=1, description="-> h_hhcount, HARUS sama dengan len(members)")
    members: List[HouseholdMember]
    housing: HousingInput
    assets: AssetInput

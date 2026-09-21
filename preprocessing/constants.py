"""
constants.py — daftar kolom final (BASE_PREDICTORS) & daftar kategori
internal (h_*). Murni data, tidak ada logika. Sama dengan tahap
preprocessing-engine sebelumnya (tidak diubah).
"""

from __future__ import annotations

BASE_PREDICTORS: list[str] = [
    'h_hhcount', 'h_nmale', 'h_nfemale', 'h_nage04', 'h_nage519', 'h_nage2064', 'h_nage65up',
    'h_ngrad_sd', 'h_ngrad_smp', 'h_ngrad_sma', 'h_ngrad_d', 'h_ngrad_s', 'h_notgrad',
    'h_sec1_stat1', 'h_sec1_stat2', 'h_sec1_stat3', 'h_sec1_stat4', 'h_sec1_stat5', 'h_sec1_stat6',
    'h_sec2_stat1', 'h_sec2_stat2', 'h_sec2_stat3', 'h_sec2_stat4', 'h_sec2_stat5', 'h_sec2_stat6',
    'h_sec3_stat1', 'h_sec3_stat2', 'h_sec3_stat3', 'h_sec3_stat4', 'h_sec3_stat5', 'h_sec3_stat6',
    'h_neverschool', 'h_stillschool', 'h_notschool',
    'h_house1', 'h_house2', 'h_house3', 'h_house4',
    'h_floor1', 'h_floor2', 'h_floor3', 'h_floor4',
    'h_wall1', 'h_wall2', 'h_wall3', 'h_wall4',
    'h_roof1', 'h_roof2', 'h_roof3', 'h_roof4',
    'h_dwater1', 'h_dwater2', 'h_dwater3', 'h_dwater4', 'h_dwater5',
    'h_lighting1', 'h_lighting2', 'h_lighting3',
    'h_epower1', 'h_epower2', 'h_epower3',
    'h_cookingfuel1', 'h_cookingfuel2', 'h_cookingfuel3', 'h_cookingfuel4', 'h_cookingfuel5',
    'h_toiltype1', 'h_toiltype2', 'h_toiltype3', 'h_toiltype4', 'h_toiltype5', 'h_toiltype6',
    'h_septic1', 'h_septic2', 'h_septic3', 'h_septic4', 'h_septic5',
    'h_asset_lpg5kg', 'h_asset_fridge', 'h_asset_ac', 'h_asset_wheater', 'h_asset_phone', 'h_asset_computer',
    'h_asset_jewelry', 'h_asset_motorcycle', 'h_asset_boat', 'h_asset_motorboat', 'h_asset_car', 'h_asset_tv',
    'h_asset_smartphone', 'h_asset_land',
    'h_lnluaslantai', 'h_nfamily',
    'h_notmarried', 'h_married', 'h_divorced', 'h_widowed',
]
assert len(BASE_PREDICTORS) == 97

GENDER_LIST = ['h_nmale', 'h_nfemale']
AGE_BUCKETS = ['h_nage04', 'h_nage519', 'h_nage2064', 'h_nage65up']
EDU_LIST = ['h_ngrad_sd', 'h_ngrad_smp', 'h_ngrad_sma', 'h_ngrad_d', 'h_ngrad_s', 'h_notgrad']
SCHOOL_LIST = ['h_neverschool', 'h_stillschool', 'h_notschool']
MARRIAGE_LIST = ['h_notmarried', 'h_married', 'h_divorced', 'h_widowed']
SEC_LIST = [f'h_sec{s}_stat{st}' for s in (1, 2, 3) for st in range(1, 7)]

# Kode status pekerjaan mentah (1-8) -> suffix bucket h_secX_statY, PERSIS
# dari logika training (process_block()):
#   stat==1->Y1 | stat==2->Y2 | stat==3->Y3 | stat in[4,5]->Y4
#   stat in[6,7]->Y5 | stat==8->Y6
STAT_CODE_TO_SUFFIX = {1: 1, 2: 2, 3: 3, 4: 4, 5: 4, 6: 5, 7: 5, 8: 6}

HOUSE_LIST = ['h_house1', 'h_house2', 'h_house3', 'h_house4']
FLOOR_LIST = ['h_floor1', 'h_floor2', 'h_floor3', 'h_floor4']
WALL_LIST = ['h_wall1', 'h_wall2', 'h_wall3', 'h_wall4']
ROOF_LIST = ['h_roof1', 'h_roof2', 'h_roof3', 'h_roof4']
WATER_LIST = ['h_dwater1', 'h_dwater2', 'h_dwater3', 'h_dwater4', 'h_dwater5']
LIGHTING_LIST = ['h_lighting1', 'h_lighting2', 'h_lighting3']
EPOWER_LIST = ['h_epower1', 'h_epower2', 'h_epower3']
COOKINGFUEL_LIST = ['h_cookingfuel1', 'h_cookingfuel2', 'h_cookingfuel3', 'h_cookingfuel4', 'h_cookingfuel5']
TOILTYPE_LIST = [f'h_toiltype{i}' for i in range(1, 7)]
SEPTIC_LIST = [f'h_septic{i}' for i in range(1, 6)]

# h_asset_internet ADA di skrip training tapi TIDAK ADA di BASE_PREDICTORS
# yang dilampirkan -> sengaja tidak dimasukkan ke ASSET_LIST (lihat mappings.py
# untuk catatan PERLU_KONFIRMASI karena pesan terbaru menyebut "Internet"
# sebagai salah satu opsi UI aset).
ASSET_LIST = [
    'h_asset_lpg5kg', 'h_asset_fridge', 'h_asset_ac', 'h_asset_wheater', 'h_asset_phone',
    'h_asset_computer', 'h_asset_jewelry', 'h_asset_motorcycle', 'h_asset_boat',
    'h_asset_motorboat', 'h_asset_car', 'h_asset_tv', 'h_asset_smartphone', 'h_asset_land',
]

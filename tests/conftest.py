import pytest

from pathlib import Path


@pytest.fixture
def asset_path():
    return Path('tests/assets')


@pytest.fixture
def ifc_family_house(asset_path: Path):
    return asset_path.joinpath('ifc/FamilyHouse_AC13.ifc')


@pytest.fixture
def ifc_small_office(asset_path: Path):
    return asset_path.joinpath('ifc/SmallOffice_d_IFC2x3.ifc')

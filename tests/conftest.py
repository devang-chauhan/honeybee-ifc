import pytest

from pathlib import Path
from tempfile import TemporaryDirectory

from honeybee.model import Model as HBModel
from honeybee_ifc.model import Model


@pytest.fixture(scope='session')
def asset_path():
    return Path('tests/assets')


@pytest.fixture(scope='session')
def small_office_name():
    return 'SmallOffice_d_IFC2x3'


@pytest.fixture(scope='session')
def ifc_small_office(asset_path: Path, small_office_name):
    return asset_path.joinpath(f'ifc/{small_office_name}.ifc')


@pytest.fixture(scope='session')
def tmp_path_hbjson():
    d = TemporaryDirectory()
    yield Path(d.name)
    d.cleanup()


@pytest.fixture(scope='session')
def converted_small_office(tmp_path_hbjson: Path, ifc_small_office: Path):
    m = Model(ifc_small_office).to_hbjson(tmp_path_hbjson)
    assert Path(m).name == ifc_small_office.stem + '.hbjson'
    yield m


@pytest.fixture(scope='session')
def office_model(converted_small_office: Path):
    return HBModel.from_hbjson(converted_small_office)


@pytest.fixture(scope='session')
def verified_office_model():
    return HBModel.from_hbjson('tests/assets/hbjsons/SmallOffice_d_IFC2x3.hbjson')


"""Testing center point locations and the volume of close gapped zones."""

import pytest
import pathlib
import os
import shutil
from honeybee_ifc.to_hbjson import export_close_gapped_zones, extract_elements, get_ifc_settings
from honeybee.model import Model


# Tests for Small office IFC
file_2 = pathlib.Path('tests/assets/ifc/SmallOffice_d_IFC2x3.ifc')
verified_model = Model.from_hbjson(pathlib.Path(
    'tests/assets/hbjsons/SmallOffice_d_IFC2x3_gap_closed_zones.hbjson'))


@pytest.fixture
def model():
    """Returning the Honeybee model that will be used in multiple unit tests."""
    return Model.from_hbjson(pathlib.Path(
        'tests/assets/temp_gap_closed_zones/SmallOffice_d_IFC2x3_gap_closed_zones.hbjson'))


def test_convert_to_hbjson():
    """Convert IFC to HBJSONs to a temp folder."""
    temp_folder = r'tests/assets/temp_gap_closed_zones'

    if os.path.isdir(temp_folder):
        shutil.rmtree(temp_folder)
    os.mkdir(temp_folder)

    spaces = extract_elements(file_2, get_ifc_settings())[0]
    hbjson2 = export_close_gapped_zones(file_2, spaces, get_ifc_settings(), temp_folder)
    assert isinstance(hbjson2, Model)


def test_center_points(model):
    """Make sure the center point of the generated zones match the zones in the verified model."""
    for i, room in enumerate(model.rooms):
        assert room.center.distance_to_point(verified_model.rooms[i].center) <= 0.01


def test_volumes(model):
    """Make sure the volumes of the generated zones match the zones in the verified model."""
    for i, room in enumerate(model.rooms):
        assert room.volume == verified_model.rooms[i].volume


def test_remove_temp():
    """Remove the temp folder."""
    temp_folder = r'tests/assets/temp_gap_closed_zones'

    if os.path.isdir(temp_folder):
        shutil.rmtree(temp_folder)

    assert not os.path.isdir(temp_folder)

"""Verify assets and write files to be used by unit tests in other modules."""

import shutil
import os
import pathlib
from honeybee_ifc.model import Model
from honeybee.model import Model as HBModel
import pytest

# file_1 = pathlib.Path('tests/assets/ifc/FamilyHouse_AC13.ifc')
# file_2 = pathlib.Path('tests/assets/ifc/SmallOffice_d_IFC2x3.ifc')


# def test_assets():
#     """Test that the files in assets remain."""
#     assert file_1.stem == 'FamilyHouse_AC13'
#     assert file_2.stem == 'SmallOffice_d_IFC2x3'

def test_convert_to_hbjson(tmp_path: pathlib.Path,
                           ifc_family_house: pathlib.Path,
                           ifc_small_office: pathlib.Path):
    """Convert IFC to HBJSONs to a temp folder."""
    # NOTE: This test takes the longest to run.

    temp_folder = tmp_path.joinpath('hbjson')

    hbjson_1 = Model(ifc_family_house).to_hbjson(target_folder=temp_folder)
    hbjson_2 = Model(ifc_small_office).to_hbjson(target_folder=temp_folder)

    assert pathlib.Path(hbjson_1).name == ifc_family_house.stem + '.hbjson'
    assert pathlib.Path(hbjson_2).name == ifc_small_office.stem + '.hbjson'

"""Verify assets and write files to be used by unit tests in other modules."""

import shutil
import os
import pathlib
from honeybee_ifc.to_hbjson import export_model, extract_elements, get_ifc_settings
from honeybee.model import Model

file_1 = pathlib.Path('tests/assets/ifc/FamilyHouse_AC13.ifc')
file_2 = pathlib.Path('tests/assets/ifc/SmallOffice_d_IFC2x3.ifc')


def test_assets():
    """Test that the files in assets remain."""
    assert file_1.stem == 'FamilyHouse_AC13'
    assert file_2.stem == 'SmallOffice_d_IFC2x3'


def test_convert_to_hbjson():
    """Convert IFC to HBJSONs to a temp folder."""
    # NOTE: This test takes the longest to run.

    temp_folder = r'tests/assets/temp'

    if os.path.isdir(temp_folder):
        shutil.rmtree(temp_folder)
    os.mkdir(temp_folder)

    spaces_1, windows_1, doors_1, slabs_1 = extract_elements(file_1, get_ifc_settings())
    hbjson1 = export_model(file_1, spaces_1, windows_1, doors_1, slabs_1, temp_folder)

    spaces_2, windows_2, doors_2, slabs_2 = extract_elements(file_2, get_ifc_settings())
    hbjson2 = export_model(file_2, spaces_2, windows_2, doors_2, slabs_2, temp_folder)

    assert isinstance(hbjson1, Model)
    assert isinstance(hbjson2, Model)

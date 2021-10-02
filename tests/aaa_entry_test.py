"""This module create a temp folder and converts IFC files in assets to HBJSONs for
 other tests to use."""

import shutil
import os
import pathlib
from honeybee_ifc.export import export_hbjson

from honeybee.model import Model

file_1 = pathlib.Path('tests/assets/ifc/FamilyHouse_AC13.ifc')
file_2 = pathlib.Path('tests/assets/ifc/SmallOffice_d_IFC2x3.ifc')


def test_assets():
    """Test that the files in assets remain."""
    assert file_1.stem == 'FamilyHouse_AC13'
    assert file_2.stem == 'SmallOffice_d_IFC2x3'


def test_convert_to_hbjson():
    """Convert IFC to HBJSONs to a temp folder."""
    temp_folder = r'tests/assets/temp'

    if os.path.isdir(temp_folder):
        shutil.rmtree(temp_folder)
    os.mkdir(temp_folder)

    hbjson1 = export_hbjson(file_1, temp_folder)
    hbjson2 = export_hbjson(file_2, temp_folder)

    assert isinstance(hbjson1, Model)
    assert isinstance(hbjson2, Model)

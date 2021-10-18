"""Testing center point locations and normals for doors in HBJSONs exported from
two IFC file."""

import shutil
import os
import pathlib
from honeybee_ifc.to_hbjson import export_model, extract_elements, get_ifc_settings
from honeybee.model import Model

file_1 = pathlib.Path('tests/assets/ifc/FamilyHouse_AC13.ifc')
file_2 = pathlib.Path('tests/assets/ifc/SmallOffice_d_IFC2x3.ifc')

house_model_verified = Model.from_hbjson(pathlib.Path(
    'tests/assets/hbjsons/FamilyHouse_AC13.hbjson'))

office_model_verified = Model.from_hbjson(pathlib.Path(
    'tests/assets/hbjsons/SmallOffice_d_IFC2x3.hbjson'))


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

    spaces_1, windows_1, doors_1, slabs_1 = extract_elements(file_1, get_ifc_settings())
    hbjson1 = export_model(file_1, spaces_1, windows_1, doors_1, slabs_1, temp_folder)

    spaces_2, windows_2, doors_2, slabs_2 = extract_elements(file_2, get_ifc_settings())
    hbjson2 = export_model(file_2, spaces_2, windows_2, doors_2, slabs_2, temp_folder)

    assert isinstance(hbjson1, Model)
    assert isinstance(hbjson2, Model)


def test_number_of_doors_house():
    """Test the number of doors."""

    house_model = Model.from_hbjson(pathlib.Path(
        'tests/assets/temp/FamilyHouse_AC13.hbjson'))

    assert len(house_model.doors) == 21


def test_center_points_house():
    """Make sure the center point location matches the expected location"""

    house_model = Model.from_hbjson(pathlib.Path(
        'tests/assets/temp/FamilyHouse_AC13.hbjson'))

    verified_center_points = [
        door.geometry.center for door in house_model_verified.doors]

    assert len(house_model.doors) == len(verified_center_points)

    for count, door in enumerate(house_model.doors):
        center = door.geometry.center
        expected_center = verified_center_points[count]
        assert center.distance_to_point(expected_center) <= 0.01


def test_normals_house():
    """Meke sure the normal of doors matches expected normals."""

    house_model = Model.from_hbjson(pathlib.Path(
        'tests/assets/temp/FamilyHouse_AC13.hbjson'))

    verified_normals = [
        door.geometry.normal for door in house_model_verified.doors]

    assert len(house_model.doors) == len(verified_normals)

    for count, door in enumerate(house_model.doors):
        normal = door.geometry.normal.normalize()
        vec = verified_normals[count]
        assert normal.angle(vec) <= 0.01


def test_number_of_doors_office():
    """Test the number of doors."""

    office_model = Model.from_hbjson(pathlib.Path(
        'tests/assets/temp/SmallOffice_d_IFC2x3.hbjson'))

    assert len(office_model.doors) == 33


def test_center_points_office():
    """Make sure the center point location matches the expected location"""

    office_model = Model.from_hbjson(pathlib.Path(
        'tests/assets/temp/SmallOffice_d_IFC2x3.hbjson'))

    verified_center_points = [
        door.geometry.center for door in office_model_verified.doors]

    assert len(office_model.doors) == len(verified_center_points)

    for count, door in enumerate(office_model.doors):
        center = door.geometry.center
        expected_center = verified_center_points[count]
        assert center.distance_to_point(expected_center) < 0.01


def center_normals_office():
    """Meke sure the normal of doors matches expected normals."""

    office_model = Model.from_hbjson(pathlib.Path(
        'tests/assets/temp/SmallOffice_d_IFC2x3.hbjson'))

    verified_normals = [
        door.geometry.normal for door in office_model_verified.doors]

    assert len(office_model.doors) == len(verified_normals)

    for count, door in enumerate(office_model.doors):
        normal = door.geometry.normal.normalize()
        vec = verified_normals[count]
        assert normal.angle(vec) <= 0.01


def test_remove_temp():
    """Remove the temp folder."""
    temp_folder = r'tests/assets/temp'

    if os.path.isdir(temp_folder):
        shutil.rmtree(temp_folder)

    assert not os.path.isdir(temp_folder)

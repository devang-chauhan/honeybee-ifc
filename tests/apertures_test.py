"""Testing center point locations and normals for apertures in HBJSONs exported from
two IFC file."""
import shutil
import os
import pathlib
from honeybee_ifc.to_hbjson import export_model, extract_elements, get_ifc_settings
from honeybee.model import Model

file_1 = pathlib.Path('tests/assets/ifc/FamilyHouse_AC13.ifc')
file_2 = pathlib.Path('tests/assets/ifc/SmallOffice_d_IFC2x3.ifc')

verified_house_model = Model.from_hbjson(pathlib.Path(
    'tests/assets/hbjsons/FamilyHouse_AC13.hbjson'))
verified_office_model = Model.from_hbjson(pathlib.Path(
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


def test_number_of_apertures_house():
    """Test the number of apertures."""

    house_model = Model.from_hbjson(pathlib.Path(
        'tests/assets/temp/FamilyHouse_AC13.hbjson'))

    assert len(house_model.apertures) == 31


def test_center_points_house():
    """Make sure the center point location matches the expected location"""

    house_model = Model.from_hbjson(pathlib.Path(
        'tests/assets/temp/FamilyHouse_AC13.hbjson'))

    verified_center_points = [
        aperture.geometry.center for aperture in verified_house_model.apertures]

    assert len(house_model.apertures) == len(verified_center_points)

    for count, aperture in enumerate(house_model.apertures):
        center = aperture.geometry.center
        expected_center = verified_center_points[count]
        assert center.distance_to_point(expected_center) <= 0.01


def test_normals_house():
    """Meke sure the normal of apertures matches expected normals."""

    house_model = Model.from_hbjson(pathlib.Path(
        'tests/assets/temp/FamilyHouse_AC13.hbjson'))

    verified_normals = [
        aperture.geometry.normal for aperture in verified_house_model.apertures]

    assert len(house_model.apertures) == len(verified_normals)

    for count, aperture in enumerate(house_model.apertures):
        normal = aperture.geometry.normal.normalize()
        vec = verified_normals[count]
        normal = aperture.geometry.normal.normalize()
        assert normal.angle(vec) <= 0.01


def test_number_of_apertures_office():
    """Test the number of apertures."""

    offie_model = Model.from_hbjson(pathlib.Path(
        'tests/assets/temp/SmallOffice_d_IFC2x3.hbjson'))

    assert len(offie_model.apertures) == 80


def test_center_points_office():
    """Make sure the center point location matches the expected location"""

    offie_model = Model.from_hbjson(pathlib.Path(
        'tests/assets/temp/SmallOffice_d_IFC2x3.hbjson'))

    verified_center_points = [
        aperture.geometry.center for aperture in verified_office_model.apertures]

    assert len(offie_model.apertures) == len(verified_center_points)

    for count, aperture in enumerate(offie_model.apertures):
        center = aperture.geometry.center
        expected_center = verified_center_points[count]
        # Some of the apertures have more than one near by spaces(zones) and therefore,
        # the location of the apertue is decided by randomly choosing the wall of the
        # either of the nearby space. Therefore, the validation distance here is 0.2
        # which close to the wall thickness.
        assert center.distance_to_point(expected_center) < 0.2


def center_normals_office():
    """Make sure the normal of apertures matches expected normals."""

    offie_model = Model.from_hbjson(pathlib.Path(
        'tests/assets/temp/SmallOffice_d_IFC2x3.hbjson'))

    verified_normals = [
        aperture.geometry.normal for aperture in verified_office_model.apertures]

    assert len(offie_model.apertures) == len(verified_normals)

    for count, aperture in enumerate(offie_model.apertures):
        normal = aperture.geometry.normal.normalize()
        vec = verified_normals[count]
        assert normal.angle(vec) <= 0.01


def test_remove_temp():
    """Remove the temp folder."""
    temp_folder = r'tests/assets/temp'

    if os.path.isdir(temp_folder):
        shutil.rmtree(temp_folder)

    assert not os.path.isdir(temp_folder)

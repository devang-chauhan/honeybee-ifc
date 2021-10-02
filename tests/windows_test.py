"""Testing center point locations and normals for apertures in HBJSONs exported from
two IFC file."""

import pathlib
from honeybee_ifc.export import export_hbjson
from honeybee.model import Model
from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D

# Tests for Family House IFC
hb_model_house = Model.from_hbjson(pathlib.Path(
    'tests/assets/temp/FamilyHouse_AC13.hbjson'))
verified_hb_model_house = Model.from_hbjson(pathlib.Path(
    'tests/assets/hbjsons/FamilyHouse_AC13.hbjson'))


def test_number_of_apertures_house():
    """Test the number of apertures."""
    assert len(hb_model_house.apertures) == 31


def test_center_points_house():
    """Make sure the center point location matches the expected location"""
    verified_center_points = [
        aperture.geometry.center for aperture in verified_hb_model_house.apertures]

    assert len(hb_model_house.apertures) == len(verified_center_points)

    for count, aperture in enumerate(hb_model_house.apertures):
        center = aperture.geometry.center
        expected_center = verified_center_points[count]
        assert center.distance_to_point(expected_center) <= 0.01


def test_normals_house():
    """Meke sure the normal of apertures matches expected normals."""

    verified_normals = [
        aperture.geometry.normal for aperture in verified_hb_model_house.apertures]

    assert len(hb_model_house.apertures) == len(verified_normals)

    for count, aperture in enumerate(hb_model_house.apertures):
        normal = aperture.geometry.normal.normalize()
        vec = verified_normals[count]
        normal = aperture.geometry.normal.normalize()
        assert normal.angle(vec) <= 0.01


# Tests for Small office IFC
hb_model_office = Model.from_hbjson(pathlib.Path(
    'tests/assets/temp/SmallOffice_d_IFC2x3.hbjson'))
verified_hb_model_office = Model.from_hbjson(pathlib.Path(
    'tests/assets/hbjsons/SmallOffice_d_IFC2x3.hbjson'))


def test_number_of_apertures_office():
    """Test the number of apertures."""
    assert len(hb_model_office.apertures) == 80


def test_center_points_office():
    """Make sure the center point location matches the expected location"""
    verified_center_points = [
        aperture.geometry.center for aperture in verified_hb_model_office.apertures]

    assert len(hb_model_office.apertures) == len(verified_center_points)

    for count, aperture in enumerate(hb_model_office.apertures):
        center = aperture.geometry.center
        expected_center = verified_center_points[count]
        # Some of the apertures have more than one near by spaces(zones) and therefore,
        # the location of the apertue is decided by randomly choosing the wall of the
        # either of the nearby space. Therefore, the validation distance here is 0.2
        # which close to the wall thickness.
        assert center.distance_to_point(expected_center) < 0.2


def center_normals_office():
    """Meke sure the normal of apertures matches expected normals."""

    verified_normals = [
        aperture.geometry.normal for aperture in verified_hb_model_office.apertures]

    assert len(hb_model_office.apertures) == len(verified_normals)

    for count, aperture in enumerate(hb_model_office.apertures):
        normal = aperture.geometry.normal.normalize()
        vec = verified_normals[count]
        assert normal.angle(vec) <= 0.01

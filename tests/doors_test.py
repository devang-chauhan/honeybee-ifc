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


def test_number_of_doors_house():
    """Test the number of doors."""
    assert len(hb_model_house.doors) == 21


def test_center_points_house():
    """Make sure the center point location matches the expected location"""
    verified_center_points = [
        door.geometry.center for door in verified_hb_model_house.doors]

    assert len(hb_model_house.doors) == len(verified_center_points)

    for count, door in enumerate(hb_model_house.doors):
        center = door.geometry.center
        expected_center = verified_center_points[count]
        assert center.distance_to_point(expected_center) <= 0.01


def test_normals_house():
    """Meke sure the normal of doors matches expected normals."""

    verified_normals = [
        door.geometry.normal for door in verified_hb_model_house.doors]

    assert len(hb_model_house.doors) == len(verified_normals)

    for count, door in enumerate(hb_model_house.doors):
        normal = door.geometry.normal.normalize()
        vec = verified_normals[count]
        assert normal.angle(vec) <= 0.01


# Tests for Small office IFC
hb_model_office = Model.from_hbjson(pathlib.Path(
    'tests/assets/temp/SmallOffice_d_IFC2x3.hbjson'))
verified_hb_model_office = Model.from_hbjson(pathlib.Path(
    'tests/assets/hbjsons/SmallOffice_d_IFC2x3.hbjson'))


def test_number_of_doors_office():
    """Test the number of doors."""
    assert len(hb_model_office.doors) == 33


def test_center_points_office():
    """Make sure the center point location matches the expected location"""
    verified_center_points = [
        door.geometry.center for door in verified_hb_model_office.doors]

    assert len(hb_model_office.doors) == len(verified_center_points)

    for count, door in enumerate(hb_model_office.doors):
        center = door.geometry.center
        expected_center = verified_center_points[count]
        assert center.distance_to_point(expected_center) < 0.01


def center_normals_office():
    """Meke sure the normal of doors matches expected normals."""

    verified_normals = [
        door.geometry.normal for door in verified_hb_model_office.doors]

    assert len(hb_model_office.doors) == len(verified_normals)

    for count, door in enumerate(hb_model_office.doors):
        normal = door.geometry.normal.normalize()
        vec = verified_normals[count]
        assert normal.angle(vec) <= 0.01

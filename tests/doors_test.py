"""Testing center point locations and normals for doors in HBJSONs exported from
two IFC file."""

import pytest
import pathlib
from honeybee.model import Model


house_model_verified = Model.from_hbjson(pathlib.Path(
    'tests/assets/hbjsons/FamilyHouse_AC13.hbjson'))
office_model_verified = Model.from_hbjson(pathlib.Path(
    'tests/assets/hbjsons/SmallOffice_d_IFC2x3.hbjson'))


def test_number_of_doors_house(house_model):
    """Test the number of doors."""

    assert len(house_model.doors) == 21


def test_center_points_house(house_model):
    """Make sure the center point location matches the expected location"""

    verified_center_points = [
        door.geometry.center for door in house_model_verified.doors]

    assert len(house_model.doors) == len(verified_center_points)

    for count, door in enumerate(house_model.doors):
        center = door.geometry.center
        expected_center = verified_center_points[count]
        assert center.distance_to_point(expected_center) <= 0.01


def test_normals_house(house_model):
    """Meke sure the normal of doors matches expected normals."""

    verified_normals = [
        door.geometry.normal for door in house_model_verified.doors]

    assert len(house_model.doors) == len(verified_normals)

    for count, door in enumerate(house_model.doors):
        normal = door.geometry.normal.normalize()
        vec = verified_normals[count]
        assert normal.angle(vec) <= 0.01


def test_number_of_doors_office(office_model):
    """Test the number of doors."""

    assert len(office_model.doors) == 33


def test_center_points_office(office_model):
    """Make sure the center point location matches the expected location"""

    verified_center_points = [
        door.geometry.center for door in office_model_verified.doors]

    assert len(office_model.doors) == len(verified_center_points)

    for count, door in enumerate(office_model.doors):
        center = door.geometry.center
        expected_center = verified_center_points[count]
        assert center.distance_to_point(expected_center) < 0.01


def center_normals_office(office_model):
    """Meke sure the normal of doors matches expected normals."""

    verified_normals = [
        door.geometry.normal for door in office_model_verified.doors]

    assert len(office_model.doors) == len(verified_normals)

    for count, door in enumerate(office_model.doors):
        normal = door.geometry.normal.normalize()
        vec = verified_normals[count]
        assert normal.angle(vec) <= 0.01

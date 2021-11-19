"""Testing center point locations and normals for apertures in HBJSONs exported from
two IFC file."""

import pytest


def test_number_of_apertures(office_model):
    assert len(office_model.apertures) == 80


def test_number_of_doors(office_model):
    assert len(office_model.doors) == 33


def test_number_of_shades(office_model):
    assert len(office_model.shades) == 36


def test_number_of_faces(office_model):
    assert len(office_model.faces) == 3299


def test_number_of_grids(office_model):
    assert len(office_model.properties.radiance.sensor_grids) == 29


def test_aperture_center_normal(office_model, verified_office_model):
    """Make sure the center point location & normal matches the verified model."""

    verified_center_points = [
        aperture.geometry.center for aperture in verified_office_model.apertures]

    verified_normals = [
        aperture.geometry.normal for aperture in verified_office_model.apertures]

    for count, aperture in enumerate(office_model.apertures):
        center = aperture.geometry.center
        expected_center = verified_center_points[count]
        assert center.distance_to_point(expected_center) < 0.01

        normal = aperture.geometry.normal.normalize()
        vec = verified_normals[count]
        assert normal.angle(vec) <= 0.01


def test_door_center_normal(office_model, verified_office_model):
    """Make sure the center point location & normal matches the verified model."""

    verified_center_points = [
        door.geometry.center for door in verified_office_model.doors]

    verified_normals = [
        door.geometry.normal for door in verified_office_model.doors]

    for count, door in enumerate(office_model.doors):
        center = door.geometry.center
        expected_center = verified_center_points[count]
        assert center.distance_to_point(expected_center) < 0.01

        normal = door.geometry.normal.normalize()
        vec = verified_normals[count]
        assert normal.angle(vec) <= 0.01

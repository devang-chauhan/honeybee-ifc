"""Testing center point locations and normals for apertures in HBJSONs exported from
two IFC file."""

import pytest
import pathlib
from honeybee.model import Model


verified_house_model = Model.from_hbjson(pathlib.Path(
    'tests/assets/hbjsons/FamilyHouse_AC13.hbjson'))
verified_office_model = Model.from_hbjson(pathlib.Path(
    'tests/assets/hbjsons/SmallOffice_d_IFC2x3.hbjson'))


def test_number_of_apertures_house(house_model):
    """Test the number of apertures."""

    assert len(house_model.apertures) == 31


def test_center_points_house(house_model):
    """Make sure the center point location matches the expected location"""

    verified_center_points = [
        aperture.geometry.center for aperture in verified_house_model.apertures]

    assert len(house_model.apertures) == len(verified_center_points)

    for count, aperture in enumerate(house_model.apertures):
        center = aperture.geometry.center
        expected_center = verified_center_points[count]
        assert center.distance_to_point(expected_center) <= 0.01


def test_normals_house(house_model):
    """Meke sure the normal of apertures matches expected normals."""

    verified_normals = [
        aperture.geometry.normal for aperture in verified_house_model.apertures]

    assert len(house_model.apertures) == len(verified_normals)

    for count, aperture in enumerate(house_model.apertures):
        normal = aperture.geometry.normal.normalize()
        vec = verified_normals[count]
        normal = aperture.geometry.normal.normalize()
        assert normal.angle(vec) <= 0.01


def test_number_of_apertures_office(office_model):
    """Test the number of apertures."""

    assert len(office_model.apertures) == 80


def test_center_points_office(office_model):
    """Make sure the center point location matches the expected location"""

    verified_center_points = [
        aperture.geometry.center for aperture in verified_office_model.apertures]

    assert len(office_model.apertures) == len(verified_center_points)

    for count, aperture in enumerate(office_model.apertures):
        center = aperture.geometry.center
        expected_center = verified_center_points[count]
        # Some of the apertures have more than one near by spaces(zones) and therefore,
        # the location of the apertue is decided by randomly choosing the wall of the
        # either of the nearby space. Therefore, the validation distance here is 0.2
        # which close to the wall thickness.
        assert center.distance_to_point(expected_center) < 0.2


def center_normals_office(office_model):
    """Make sure the normal of apertures matches expected normals."""

    verified_normals = [
        aperture.geometry.normal for aperture in verified_office_model.apertures]

    assert len(office_model.apertures) == len(verified_normals)

    for count, aperture in enumerate(office_model.apertures):
        normal = aperture.geometry.normal.normalize()
        vec = verified_normals[count]
        assert normal.angle(vec) <= 0.01

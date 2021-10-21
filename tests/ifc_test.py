"""Unit tests to validate ifc export."""

import pytest
import os
import shutil
import pathlib
import ifcopenshell

from typing import List, Tuple

from honeybee.model import Model
from ladybug_geometry.geometry3d import Point3D

from honeybee_ifc.ifc import ElementType, Ifc
from honeybee_ifc.to_hbjson import extract_elements, get_ifc_settings
from honeybee_ifc.geometry import get_face3d, get_polyface3d


@pytest.fixture
def ifc_file() -> ifcopenshell.file:
    hbjson = r"tests\assets\hbjsons\from lbt\small_office.hbjson"
    # honeybee model
    model = Model.from_hbjson(hbjson)
    # helper function

    def point3d_to_tuple(points: Tuple[Point3D]) -> List[Tuple]:
        return [(point.x, point.y, point.z) for point in points]

    # Ifc object
    ifc_file = Ifc()
    for aperture in model.apertures:
        points = point3d_to_tuple(aperture.vertices)
        ifc_file.add_ifc_elements(ElementType.window, [points])

    for door in model.doors:
        points = point3d_to_tuple(door.vertices)
        ifc_file.add_ifc_elements(ElementType.door, [points])

    for shade in model.orphaned_shades:
        points = point3d_to_tuple(shade.vertices)
        ifc_file.add_ifc_elements(ElementType.slab, [points])

    for room in model.rooms:
        points_list = [point3d_to_tuple(face.vertices) for face in room.faces]
        ifc_file.add_ifc_elements(ElementType.space, points_list)

    return ifc_file


@pytest.fixture
def test_ifc_writing(ifc_file):
    """Test if the ifc file is being written to the target folder."""
    temp_folder = r'tests/assets/temp'

    if os.path.isdir(temp_folder):
        shutil.rmtree(temp_folder)
    os.mkdir(temp_folder)

    ifc_path = ifc_file.write_ifc(temp_folder)

    assert os.path.isfile(ifc_path)
    assert pathlib.Path(ifc_path).stem == 'model'
    assert pathlib.Path(ifc_path).suffix == '.ifc'


@pytest.fixture
def elements():
    # generates ifc and elements extracted from the ifc file
    ifc_path = r'tests/assets/temp/model.ifc'
    spaces, windows, doors, slabs = extract_elements(
        ifc_file_path=ifc_path, settings=get_ifc_settings())
    return spaces, windows, doors, slabs


@pytest.fixture
def valid_elements():
    # validated ifc and elements extracted from the ifc file
    valid_ifc_path = r"tests\assets\ifc\from honeybee-ifc\small office.ifc"
    spaces, windows, doors, slabs = extract_elements(
        ifc_file_path=valid_ifc_path, settings=get_ifc_settings())
    return spaces, windows, doors, slabs


def test_elements(test_ifc_writing, elements, valid_elements):
    """Test if the number of elements in the generated file match the number
    of elements in the validated file."""
    spaces, windows, doors, slabs = elements
    spaces_val, windows_val, doors_val, slabs_val = valid_elements
    assert len(spaces) == len(spaces_val)
    assert len(windows) == len(windows_val)
    assert len(doors) == len(doors_val)
    assert len(slabs) == len(slabs_val)


def test_space_centers(test_ifc_writing, elements, valid_elements):
    """Test if the centroid of IfcSpace elements match the centroid of the
    validated IfcSpace elements."""
    spaces = elements[0]
    spaces_val = valid_elements[0]

    for count, space in enumerate(spaces):
        polyface = get_polyface3d(space, get_ifc_settings())
        polyface_val = get_polyface3d(spaces_val[count], get_ifc_settings())
        assert polyface.center.distance_to_point(polyface_val.center) <= 0.01


def test_window_centers(test_ifc_writing, elements, valid_elements):
    """Test if the centroid of IfcWindow elements match the centroid of the
    validated IfcWindow elements."""
    windows = elements[1]
    windows_val = valid_elements[1]

    for count, window in enumerate(windows):
        face = get_face3d(window, get_ifc_settings())
        face_val = get_face3d(windows_val[count], get_ifc_settings())
        assert face.center.distance_to_point(face_val.center) <= 0.01


def test_door_centers(test_ifc_writing, elements, valid_elements):
    """Test if the centroid of IfcDoor elements match the centroid of the
    validated IfcDoor elements."""
    doors = elements[2]
    doors_val = valid_elements[2]

    for count, door in enumerate(doors):
        face = get_face3d(door, get_ifc_settings())
        face_val = get_face3d(doors_val[count], get_ifc_settings())
        assert face.center.distance_to_point(face_val.center) <= 0.01


def test_slab_centers(test_ifc_writing, elements, valid_elements):
    """Test if the centroid of IfcSlab elements match the centroid of the
    validated IfcSlab elements."""
    slabs = elements[3]
    slabs_val = valid_elements[3]

    for count, slab in enumerate(slabs):
        face = get_face3d(slab, get_ifc_settings())
        face_val = get_face3d(slabs_val[count], get_ifc_settings())
        assert face.center.distance_to_point(face_val.center) <= 0.01

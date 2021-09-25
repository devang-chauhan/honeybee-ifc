"""This is a module for debugging only. The module has functions to experiment
on single objects. Once these functions work, they are migrated to other modules where
the functions work on lists of objects."""

from honeybee.shade import Shade
from honeybee.aperture import Aperture
from honeybee.room import Room
from honeybee.typing import clean_and_id_string

from ladybug_geometry.geometry3d import LineSegment3D

import ifcopenshell
from ifcopenshell.util.unit import calculate_unit_scale
from ifcopenshell.entity_instance import entity_instance as Element
from ifcopenshell.file import file as File
from ladybug_geometry.geometry3d.ray import Ray3D


# relative import
from geometry import get_window_face3d, get_polyface3d
from children import get_opening, get_back_face_center_location


def get_projected_window_and_space(guid: str, ifc_file: File, settings):
    element = ifc_file.by_guid(guid)
    opening_element = get_opening(element)
    hb_shades = [Shade(clean_and_id_string('Shade'), face)
                 for face in get_polyface3d(opening_element, settings).faces]
    simplified_face = get_window_face3d(get_polyface3d(element, settings))

    length_unit_factor = calculate_unit_scale(ifc_file)
    search_radius = 0.5
    # setup BVH tree
    tree_settings = ifcopenshell.geom.settings()
    tree_settings.set(tree_settings.DISABLE_TRIANGULATION, True)
    tree_settings.set(tree_settings.DISABLE_OPENING_SUBTRACTIONS, True)
    it = ifcopenshell.geom.iterator(tree_settings, ifc_file, include=("IfcSpace",))
    t = ifcopenshell.geom.tree()
    t.add_iterator(it)

    # Get element location
    element = opening_element
    m4 = ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement)
    # This is the mid-point of the lowest edge of the font face of the opening element
    location = tuple(map(float, m4[0:3, 3] * length_unit_factor))
    back_face_center_location = get_back_face_center_location(
        element, location, settings)

    # search tree
    near_by_spaces = t.select(back_face_center_location, extend=search_radius)
    polyfaces = [get_polyface3d(space, settings) for space in near_by_spaces]
    hb_rooms = [Room.from_polyface3d(clean_and_id_string(
        'Room'), polyface) for polyface in polyfaces]

    # Getting projcted window face
    print("Nearest ifc spaces", near_by_spaces)
    polyface = polyfaces[0]
    window_face = simplified_face
    nearest_face = sorted([
        face for face in polyface.faces],
        key=lambda x: x.plane.closest_point(window_face.center).distance_to_point(window_face.center))[0]

    # check if the nearest face is above or below the window face
    if window_face.plane.is_point_above(nearest_face.center):
        window_face = window_face.flip()

    # first method to project aperture
    plane = nearest_face.plane
    closest_point = plane.closest_point(window_face.center)
    line = LineSegment3D.from_end_points(window_face.center, closest_point)
    moved_face = window_face.move(line.v)

    if moved_face.plane.is_coplanar(plane):
        pass
    else:
        # second method to project aperture
        print("Window non coplanar")
        magnitude = nearest_face.plane.distance_to_point(window_face.center)
        print("Window normal", window_face.normal)
        vector = window_face.normal.reverse().normalize() * magnitude

        print("vector", vector)
        moved_face = window_face.move(vector)
        print(window_face.center, moved_face.center)

    hb_apertures = [Aperture(clean_and_id_string('Aperture'), moved_face)]

    return hb_apertures, hb_shades, hb_rooms

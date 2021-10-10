"""This is a module for debugging only. The module has functions to experiment
on single objects. Once these functions work, they are migrated to other modules where
the functions work on lists of objects."""

from honeybee.shade import Shade
from honeybee.aperture import Aperture
from honeybee.door import Door
from honeybee.room import Room
from honeybee.typing import clean_and_id_string

from ladybug_geometry.geometry3d import LineSegment3D

import ifcopenshell
from ifcopenshell.util.unit import calculate_unit_scale
from ifcopenshell.entity_instance import entity_instance as Element
from ifcopenshell.file import file as File
from ladybug_geometry.geometry3d.ray import Ray3D


# relative import
from .geometry import get_window_face3d, get_door_face3d, get_polyface3d, get_moved_face
from .apertures import get_opening, get_front_face_center_location


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
    back_face_center_location = get_front_face_center_location(
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
    parallel_faces = [
        face for face in polyface.faces if not window_face.plane.intersect_plane(face.plane)]
    nearest_face = sorted([
        face for face in parallel_faces],
        key=lambda x: x.plane.closest_point(window_face.center).distance_to_point(window_face.center))[0]

    # check if the nearest face is above or below the window face
    if window_face.plane.is_point_above(nearest_face.center):
        window_face = window_face.flip()

    print(nearest_face.center, nearest_face.plane)
    # first method to project aperture
    plane = nearest_face.plane
    closest_point = plane.closest_point(window_face.center)
    line = LineSegment3D.from_end_points(window_face.center, closest_point)
    moved_face = window_face.move(line.v)

    # second method to project aperture
    if not moved_face.plane.is_coplanar(plane):
        print("Window not coplanar")
        magnitude = nearest_face.plane.distance_to_point(window_face.center)
        vector = window_face.normal.reverse().normalize() * magnitude
        moved_face = window_face.move(vector)

    hb_apertures = [Aperture(clean_and_id_string('Aperture'), moved_face)]

    return hb_apertures, hb_shades, hb_rooms


def get_projected_door_and_space(guid: str, ifc_file: File, settings):
    element = ifc_file.by_guid(guid)
    opening_element = get_opening(element)
    hb_shades = [Shade(clean_and_id_string('Shade'), face)
                 for face in get_polyface3d(opening_element, settings).faces]
    simplified_face = get_door_face3d(get_polyface3d(
        element, settings), get_polyface3d(opening_element, settings))

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
    back_face_center_location = get_front_face_center_location(
        element, location, settings)

    # search tree
    near_by_spaces = t.select(back_face_center_location, extend=search_radius)

    door_face = simplified_face

    if len(near_by_spaces) == 1:
        polyfaces = [get_polyface3d(near_by_spaces[0], settings)]
        nearest_faces = sorted([face for face in polyfaces[0].faces],
                               key=lambda x: x.plane.closest_point(door_face.center).distance_to_point(door_face.center))
        for face in nearest_faces:
            line = LineSegment3D.from_end_points(
                door_face.center, face.plane.closest_point(door_face.center))
            if face.intersect_line_ray(Ray3D(door_face.center, line.v)):
                nearest_face = face
                break
    elif len(near_by_spaces) == 2:
        polyfaces = [get_polyface3d(space, settings) for space in near_by_spaces]
        # find nearby polyface with the larger nearest face.
        nearest_faces = []
        for polyface in polyfaces:
            nearest_faces.append(
                sorted([face for face in polyface.faces],
                       key=lambda x: x.plane.closest_point(door_face.center).distance_to_point(door_face.center))[0])
        nearest_face = sorted(nearest_faces, key=lambda x: x.area)[-1]
    else:
        print(f'Door {element} did not export')

    hb_rooms = [Room.from_polyface3d(clean_and_id_string(
        'Room'), polyface) for polyface in polyfaces]
    moved_face = get_moved_face(door_face, nearest_face)
    # Getting projcted window face
    print("Nearest ifc spaces", near_by_spaces)

    hb_doors = [Door(clean_and_id_string('Door'), moved_face)]

    return hb_doors, hb_shades, hb_rooms

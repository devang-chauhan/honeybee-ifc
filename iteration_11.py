
# Honeybee imports
from honeybee.door import Door
from honeybee.shade import Shade
from honeybee.face import Face
from honeybee.facetype import face_types
from honeybee.aperture import Aperture
from honeybee.room import Room
from honeybee.model import Model
from honeybee.typing import clean_and_id_string

# Ladybug imports
from ladybug_geometry.geometry3d import Face3D, Point3D, Polyface3D, LineSegment3D,\
    Plane, Polyline3D, polyface

# ifcOpenShell imports
import ifcopenshell
import multiprocessing
from ifcopenshell import geom
from ifcopenshell.util.element import get_container
from ifcopenshell.util.placement import get_local_placement
from ifcopenshell.util.unit import calculate_unit_scale
from ifcopenshell.entity_instance import entity_instance as Element
from ifcopenshell.file import file as File

# FreeCAD imports
# While we're not using it. Without importing FreeCAD, the Part module won't work
import FreeCAD
import Part

# Python imports
import random
import pathlib
from enum import Enum
from typing import List, Tuple


# measuring time
import time
from datetime import timedelta


file_1 = pathlib.Path("D:\simulation\ifc\FamilyHouse_AC13.ifc")
file_2 = pathlib.Path("D:\simulation\ifc\SmallOffice_d_IFC2x3.ifc")
file_path = file_1
file_name = file_path.stem
ifc_file = ifcopenshell.open(file_path)


def get_ifc_settings() -> ifcopenshell.geom.settings:
    """Get ifc geometry settings."""
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.USE_BREP_DATA, True)
    return settings


def distance_to_closest_point_on_plane(point: Point3D, plane: Plane) -> float:
    """Get the distance from a point to a point on a plane."""
    cp = plane.closest_point(point)
    return cp.distance_to_point(point)


def get_door_face3d(polyface: Polyface3D) -> Face3D:
    """Get a simplified Face3D to represent door from a Polyface3D."""
    face3ds = polyface.faces
    # sort faces based on area
    area_sorted_faces = sorted(
        face3ds, key=lambda x: x.area, reverse=True)

    # first face is with the largest area
    largest_area = area_sorted_faces[0].area

    # Get the number of faces with the largest area
    faces_with_largest_area = [
        face.area for face in area_sorted_faces].count(largest_area)

    # Select faces with the largest area
    if faces_with_largest_area < 4:
        faces_to_use = [face for face in area_sorted_faces if face.area > 0.01]
    else:
        faces_to_use = area_sorted_faces[:faces_with_largest_area]

    # Get the plane of the first selected face
    selected_plane = faces_to_use[0].plane

    # Select the faces with the same plane
    selected_faces = [
        face for face in faces_to_use
        if distance_to_closest_point_on_plane(face.center, selected_plane) < 0.01]

    # Merge faces
    polyface = Polyface3D.from_faces(selected_faces, 0.01)
    lines = list(polyface.naked_edges)
    polylines = Polyline3D.join_segments(lines, 0.01)
    face3d = Face3D(boundary=polylines[0].vertices)

    return face3d


def get_window_face3d(polyface: Polyface3D) -> Face3D:
    """Get a simplified Face3D to represent apertue from a Polyface3D."""
    face3ds = polyface.faces
    # sort faces based on area
    area_sorted_faces = sorted(
        face3ds, key=lambda x: x.area, reverse=True)
    return area_sorted_faces[0]


def get_shape(element: Element, settings: ifcopenshell.geom.settings) -> Part.Shape:
    """Convert ifc element to a basic FreeCAD shape"""
    shape = geom.create_shape(settings, element)
    occ_shape = shape.geometry.brep_data

    with open("brep_data", "w") as file:
        file.write(occ_shape)

    fc_shape = Part.Shape()
    fc_shape.importBrepFromString(occ_shape)
    return fc_shape


def get_face3d_from_shape(face: Part.Shape.Faces) -> Face3D:
    """Get a Face3D from a FreeCAD shape object."""
    edges = face.Edges

    lines = [LineSegment3D.from_end_points(
        Point3D(edge.Vertexes[0].X, edge.Vertexes[0].Y, edge.Vertexes[0].Z),
        Point3D(edge.Vertexes[1].X, edge.Vertexes[1].Y, edge.Vertexes[1].Z))
        for edge in edges]
    polylines = Polyline3D.join_segments(lines, 0.01)
    face3d = Face3D(boundary=polylines[0].vertices)

    return face3d


def get_face3ds_from_shape(shape: Part.Shape) -> List[Face3D]:
    face3ds = [get_face3d_from_shape(face) for face in shape.Faces]
    return face3ds


def get_polyface3d(element: Element, settings: ifcopenshell.geom.settings) -> Polyface3D:
    """Get a polyface3d from an ifc element."""
    part_shape = get_shape(element, settings)
    face3ds = get_face3ds_from_shape(part_shape)
    polyface3d = Polyface3D.from_faces(face3ds, tolerance=0.01)
    # if the Polyface is solid return it or return a new Polyface with all faces flipped
    if polyface3d.is_solid:
        return polyface3d
    else:
        polyface3d = polyface3d.from_faces(
            [face.flip() for face in face3ds], tolerance=0.01)
        return polyface3d


def extract_elements(ifc_file: File,
                     settings: ifcopenshell.geom.settings) -> Tuple[
                         List[Element], List[Element], List[Element], List[Element]]:
    """Extract elements from an IFC file."""
    spaces, windows, doors, slabs = [], [], [], []

    elements = ('IfcSpace', 'IfcWindow', 'IfcDoor', 'IfcSlab')

    iterator = ifcopenshell.geom.iterator(
        settings, ifc_file, multiprocessing.cpu_count(), include=elements)

    if iterator.initialize():
        while iterator.next():
            shape = iterator.get()
            element = ifc_file.by_guid(shape.guid)

            if element.is_a() == 'IfcSpace':
                spaces.append(element)

            elif element.is_a() == 'IfcWindow':
                windows.append(element)

            elif element.is_a() == 'IfcDoor':
                doors.append(element)

            elif element.is_a() == 'IfcSlab':
                slabs.append(element)

    return spaces, windows, doors, slabs


def get_opening(element: Element) -> Element:
    """Get an IfcOpeningElement for a IfcDoor or an IfcWindow element."""
    return element.FillsVoids[0].RelatingOpeningElement


def get_back_face_center_location(
        element: Element, location: Tuple[float, float, float],
        settings: ifcopenshell.geom.settings) -> Tuple[float, float, float]:

    point3d = Point3D(location[0], location[1], location[2])
    polyface3d = get_polyface3d(element, settings)
    largest_faces = sorted([face for face in polyface3d.faces],
                           key=lambda x: x.area, reverse=True)[:2]
    back_face = sorted([face for face in largest_faces], key=lambda x: x.plane.closest_point(
        point3d).distance_to_point(point3d), reverse=True)[0]
    return back_face.center.x, back_face.center.y, back_face.center.z


def get_nearest_spaces(ifc: File, elements: List[Element],
                       settings: ifcopenshell.geom.settings,
                       search_radius: float = 0.5) -> List[List[Polyface3D]]:
    """Get Polyfaces of nearest IfcSpaces from a list of ifc opening elements.

    Returns a list of lists of Polyface3Ds for each IfcOpeningElement.
    """
    length_unit_factor = calculate_unit_scale(ifc)

    # setup BVH tree
    tree_settings = ifcopenshell.geom.settings()
    tree_settings.set(tree_settings.DISABLE_TRIANGULATION, True)
    tree_settings.set(tree_settings.DISABLE_OPENING_SUBTRACTIONS, True)
    it = ifcopenshell.geom.iterator(tree_settings, ifc, include=("IfcSpace",))
    t = ifcopenshell.geom.tree()
    t.add_iterator(it)

    near_by_spaces = []
    # Get element location
    for element in elements:
        m4 = ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement)
        # This is the mid-point of the lowest edge of the font face of the opening element
        location = tuple(map(float, m4[0:3, 3] * length_unit_factor))
        back_face_center_location = get_back_face_center_location(
            element, location, settings)

        # search tree
        ifc_spaces = t.select(back_face_center_location, extend=search_radius)
        print("IfcSpaces", ifc_spaces, '\n')
        ifc_spaces = [get_polyface3d(space, settings) for space in ifc_spaces]
        near_by_spaces.append(ifc_spaces)

    return near_by_spaces


def get_simplified_faces_and_opening_elements(
        elements: List[Element],
        settings: ifcopenshell.geom.settings) -> Tuple[List[Element], List[Face3D]]:
    """Get openings elements and simplified faces for IfcDoor and IfcWindow"""

    opening_elements, simplified_faces = [], []

    for element in elements:
        opening_elements.append(get_opening(element))
        if element.is_a() == 'IfcDoor':
            simplified_faces.append(get_door_face3d(
                get_polyface3d(element, settings)))
        elif element.is_a() == 'IfcWindow':
            simplified_faces.append(get_window_face3d(
                get_polyface3d(element, settings)))

    return opening_elements, simplified_faces


def get_projected_windows(windows: List[Element], settings: ifcopenshell.geom.settings,
                          ifc_file: File) -> List[Aperture]:

    elements = windows
    hb_apertures = []
    # Get ifc opening elements and simplified faces for ifc doors and ifc windows
    opening_elements, simplified_faces = get_simplified_faces_and_opening_elements(
        elements, settings)
    # Get nearby ifc spaces for ifc windows
    nearest_space_polyfaces = get_nearest_spaces(ifc_file, opening_elements, settings)

    for i in range(len(simplified_faces)):
        # Getting projcted window face
        if len(nearest_space_polyfaces[i]) == 0:
            continue
        polyface = nearest_space_polyfaces[i][0]
        window_face = simplified_faces[i]
        nearest_face = sorted(
            [face for face in polyface.faces], key=lambda x: x.plane.closest_point(
                window_face.center).distance_to_point(window_face.center))[0]

        plane = nearest_face.plane
        closest_point = plane.closest_point(window_face.center)
        line = LineSegment3D.from_end_points(window_face.center, closest_point)
        moved_face = window_face.move(line.v)
        hb_apertures.append(Aperture(clean_and_id_string('Aperture'), moved_face))

    return hb_apertures


def get_rooms(elements: List[Element], settings: ifcopenshell.geom.settings) -> List[Room]:
    return [Room.from_polyface3d(clean_and_id_string('Room'),
                                 get_polyface3d(element, settings))for element in elements]


def get_shades(elements: List[Element], settings: ifcopenshell.geom.settings) -> List[Shade]:
    return [Shade(clean_and_id_string('Shade'), face)
            for element in elements for face in get_polyface3d(element, settings).faces]


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

    plane = nearest_face.plane
    closest_point = plane.closest_point(window_face.center)
    line = LineSegment3D.from_end_points(window_face.center, closest_point)
    print(plane, window_face.center, closest_point, line.length)
    moved_face = window_face.move(line.v)
    hb_apertures = [Aperture(clean_and_id_string('Aperture'), moved_face)]

    return hb_apertures, hb_shades, hb_rooms


start_time = time.monotonic()
###############################################################################
hb_rooms, hb_apertures, hb_doors, hb_shades, hb_orphaned_faces = [], [], [], [], []

# Elements extracted from IFC
spaces, windows, doors, slabs = extract_elements(ifc_file, get_ifc_settings())

hb_apertures = get_projected_windows(windows, get_ifc_settings(), ifc_file)
hb_rooms = get_rooms(spaces, get_ifc_settings())
hb_shades = get_shades(slabs, get_ifc_settings())

# Export for debugging
# hb_apertures, hb_shades, hb_rooms = get_projected_window_and_space(
#     '1cN3lcP$19XxZTtlLeQ8qX', ifc_file, get_ifc_settings())

hb_model = Model('House', rooms=hb_rooms, orphaned_faces=hb_orphaned_faces,
                 orphaned_apertures=hb_apertures, orphaned_doors=hb_doors,
                 orphaned_shades=hb_shades)

hb_model.to_hbjson(name=file_name)
###############################################################################
end_time = time.monotonic()
print(f'Time elapsed: {timedelta(seconds = end_time - start_time)}')

chosen_window = '1cN3lcP$19XxZTtlLeQ8qX'

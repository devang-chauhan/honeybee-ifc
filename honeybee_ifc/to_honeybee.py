
import ifcopenshell
import random
from ifcopenshell.util.unit import calculate_unit_scale
from ifcopenshell.entity_instance import entity_instance as Element
from ifcopenshell.file import file as File
from ifcopenshell.util.placement import get_local_placement

from ladybug_geometry.geometry3d import Point3D, Polyface3D, Face3D, LineSegment3D, Ray3D
from honeybee.aperture import Aperture
from honeybee.door import Door
from honeybee.face import Face
from honeybee.room import Room
from honeybee.facetype import face_types
from honeybee.typing import clean_and_id_string
from typing import List, Tuple

from .geometry import get_face3d, get_polyface3d, get_door_face3d, get_window_face3d, get_moved_face


def get_opening(element: Element) -> Element:
    """Get an IfcOpeningElement for a IfcDoor or an IfcWindow element."""
    return element.FillsVoids[0].RelatingOpeningElement


def get_front_face_center_location(
        element: Element, location: Tuple[float, float, float],
        settings: ifcopenshell.geom.settings) -> Tuple[float, float, float]:
    """Get a center point on the outer face of the opening element.

    ifcOpenShell gives the location at the mid-point of the bottom edge of the front
    (outmost) face of the opening element.
    """

    point3d = Point3D(location[0], location[1], location[2])
    polyface3d = get_polyface3d(element, settings)
    # TODO: sorting faces based on area is not a great idea. Need to find a better way.
    largest_faces = sorted([face for face in polyface3d.faces],
                           key=lambda x: x.area, reverse=True)[:2]
    back_face = sorted([face for face in largest_faces], key=lambda x: x.plane.closest_point(
        point3d).distance_to_point(point3d))[0]

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
        # location provided by ifcOpenShell
        location = tuple(map(float, m4[0:3, 3] * length_unit_factor))
        # location calculated by honeybee-ifc
        back_face_center_location = get_front_face_center_location(
            element, location, settings)

        # search tree
        ifc_spaces = t.select(back_face_center_location, extend=search_radius)
        # if for some reason the back_face_center does not work, use the original location
        if not all(len(item) > 0 for item in ifc_spaces):
            ifc_spaces = t.select(location, extend=search_radius)
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
        if len(nearest_space_polyfaces[i]) == 1:
            polyface = nearest_space_polyfaces[i][0]
        elif len(nearest_space_polyfaces[i]) == 2:
            polyface = nearest_space_polyfaces[i][random.randint(0, 1)]
        else:
            print(f'Window {elements[i]} did not export.')
            continue

        window_face = simplified_faces[i]
        parallel_faces = [
            face for face in polyface.faces if not window_face.plane.intersect_plane(face.plane)]
        nearest_face = sorted(
            [face for face in parallel_faces], key=lambda x: x.plane.closest_point(
                window_face.center).distance_to_point(window_face.center))[0]

        # check if the nearest face is above or below the window face
        if window_face.plane.is_point_above(nearest_face.center):
            window_face = window_face.flip()

        # first method to project aperture
        plane = nearest_face.plane
        closest_point = plane.closest_point(window_face.center)
        line = LineSegment3D.from_end_points(window_face.center, closest_point)
        moved_face = window_face.move(line.v)

        # second method to project aperture
        if not moved_face.plane.is_coplanar(plane):
            magnitude = nearest_face.plane.distance_to_point(window_face.center)
            vector = window_face.normal.reverse().normalize() * magnitude
            moved_face = window_face.move(vector)

        hb_apertures.append(Aperture(clean_and_id_string('Aperture'), moved_face))

    return hb_apertures


def get_projected_doors(doors: List[Element], settings: ifcopenshell.geom.settings,
                        ifc_file: File) -> List[Aperture]:

    elements = doors
    hb_doors = []
    # Get ifc opening elements and simplified faces for ifc doors and ifc windows
    # opening_elements, simplified_faces = get_simplified_faces_and_opening_elements(
    #     elements, settings)
    opening_elements = [get_opening(element) for element in elements]
    simplified_faces = [get_door_face3d(get_polyface3d(
        elements[i], settings), get_polyface3d(opening_elements[i], settings)) for i in range(len(elements))]
    # Get nearby ifc spaces for ifc windows
    nearest_space_polyfaces = get_nearest_spaces(ifc_file, opening_elements, settings)

    for i in range(len(simplified_faces)):

        door_face = simplified_faces[i]

        if len(nearest_space_polyfaces[i]) == 1:
            polyfaces = nearest_space_polyfaces[i]
            nearest_faces = sorted([face for face in polyfaces[0].faces],
                                   key=lambda x: x.plane.closest_point(door_face.center).distance_to_point(door_face.center))
            for face in nearest_faces:
                line = LineSegment3D.from_end_points(
                    door_face.center, face.plane.closest_point(door_face.center))
                if face.intersect_line_ray(Ray3D(door_face.center, line.v)):
                    nearest_face = face
                    break
        elif len(nearest_space_polyfaces[i]) == 2:
            polyfaces = nearest_space_polyfaces[i]
            nearest_faces = []
            for polyface in polyfaces:
                nearest_faces.append(
                    sorted([face for face in polyface.faces],
                           key=lambda x: x.plane.closest_point(door_face.center).distance_to_point(door_face.center))[0])
            nearest_face = sorted(nearest_faces, key=lambda x: x.area)[-1]
        else:
            print(f'Door {elements[i]} did not export')
            continue

        moved_face = get_moved_face(door_face, nearest_face)

        hb_doors.append(Door(clean_and_id_string('Door'), moved_face))

    return hb_doors


# def get_walls(walls: List[Element], settings: ifcopenshell.geom.settings) -> List[Face]:
#     """Convert IfcWall elements in to honeybee wall objects."""

#     hb_walls = []
#     for wall in walls:
#         face3ds = get_polyface3d(wall, settings).faces
#         for face3d in face3ds:
#             hb_walls.append(Face(clean_and_id_string('Wall'), face3d, face_types.wall))

#     return hb_walls


def get_walls(walls: List[Element], settings: ifcopenshell.geom.settings) -> List[Room]:
    """Get honeybee rooms from IfcSpace elements."""
    rooms = []
    for i, space in enumerate(walls):
        polyface = get_polyface3d(space, settings)
        if not polyface.is_solid:
            faces = Polyface3D.get_outward_faces(polyface.faces, 0.01)
            polyface3d = Polyface3D.from_faces(faces, 0.01)
            room = Room.from_polyface3d('Wall_'+str(i), polyface3d)
            rooms.append(room)
    return rooms

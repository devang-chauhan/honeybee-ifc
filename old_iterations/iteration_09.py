from posixpath import normcase
from honeybee.door import Door
from honeybee.shade import Shade
from honeybee.aperture import Aperture
from honeybee.room import Room
from honeybee.model import Model
from honeybee.typing import clean_and_id_string, clean_string
from honeybee.face import Face
from ladybug_geometry.geometry3d.pointvector import Vector3D
from ladybug_geometry.intersection3d import intersect_line3d_plane
from ladybug_geometry.geometry3d import Face3D, Point3D, Polyface3D, LineSegment3D,\
    Plane, Polyline3D, Ray3D
from enum import Enum
from typing import List, Tuple, Dict, Union
import pathlib
import ifcopenshell
from ifcopenshell import geom
import multiprocessing
import FreeCAD
import Part
import math
from ifcopenshell.util.element import get_container


file_1 = pathlib.Path("D:\simulation\ifc\FamilyHouse_AC13.ifc")
file_2 = pathlib.Path("D:\simulation\ifc\SmallOffice_d_IFC2x3.ifc")

file_path = file_1
file_name = file_path.stem

ifc_file = ifcopenshell.open(file_path)

hb_faces = []
hb_rooms = []
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)
settings.set(settings.USE_BREP_DATA, True)


class IFCEntity(Enum):
    room = 'IfcSpace'
    aperture = 'IfcOpeningElement'
    door = 'IfcDoor'
    window = 'IfcWindow'


def distance_to_closest_point_on_plane(point: Point3D, plane: Plane):
    cp = plane.closest_point(point)
    return cp.distance_to_point(point)


def get_door_face3d(face3ds: list):
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


def get_window_face3d(face3ds: list):
    # sort faces based on area
    area_sorted_faces = sorted(
        face3ds, key=lambda x: x.area, reverse=True)
    return area_sorted_faces[0]


def get_shape(ifc_entity, settings):
    """Convert ifc entity to a basic FreeCAD shape"""

    shape = geom.create_shape(settings, ifc_entity)
    occ_shape = shape.geometry.brep_data

    with open("brep_data", "w") as file:
        file.write(occ_shape)

    fc_shape = Part.Shape()
    fc_shape.importBrepFromString(occ_shape)
    return fc_shape


def get_face3ds_from_shape_face(face: Part.Shape.Faces) -> Face3D:
    edges = face.Edges

    lines = [LineSegment3D.from_end_points(
        Point3D(edge.Vertexes[0].X, edge.Vertexes[0].Y, edge.Vertexes[0].Z),
        Point3D(edge.Vertexes[1].X, edge.Vertexes[1].Y, edge.Vertexes[1].Z))
        for edge in edges]
    polylines = Polyline3D.join_segments(lines, 0.01)
    face3d = Face3D(boundary=polylines[0].vertices)

    return face3d


def get_face3ds_from_shape(shape: Part.Shape) -> Polyface3D:
    face3ds = [get_face3ds_from_shape_face(face) for face in shape.Faces]
    return face3ds


def extract_hb_objects() -> list:
    """Extract geometry from IFC and turn it into Honeybee objects.

    Returns:
        A list of Honeybee objects.
    """
    rooms, apertures, doors, shades = [], [], [], []

    iterator = ifcopenshell.geom.iterator(
        settings, ifc_file, multiprocessing.cpu_count())
    if iterator.initialize():
        while iterator.next():
            shape = iterator.get()
            element = ifc_file.by_guid(shape.guid)
            if element.is_a() not in ('IfcSpace', 'IfcWindow', 'IfcDoor', 'IfcSlab',
                                      'IfcOpeningElement'):
                continue
            else:
                if element.is_a() == 'IfcSpace':

                    part_shape = get_shape(element, settings)
                    face3ds = get_face3ds_from_shape(part_shape)
                    polyface3d = Polyface3D.from_faces(face3ds, 0.01)
                    room = Room.from_polyface3d(
                        clean_and_id_string('Room'), polyface3d)
                    rooms.append(room)

                elif element.is_a() == 'IfcWindow':
                    a = ifc_file.get_inverse(element)
                    names = set([item.is_a() for item in a])
                    print(names, '\n')
                    part_shape = get_shape(element, settings)
                    face3ds = get_face3ds_from_shape(part_shape)
                    polyface3d = Polyface3D.from_faces(face3ds, 0.01)
                    face3d = get_window_face3d(polyface3d.faces)
                    apertures.append(Aperture(clean_and_id_string('Aperture'), face3d))

                elif element.is_a() == 'IfcDoor':
                    part_shape = get_shape(element, settings)
                    face3ds = get_face3ds_from_shape(part_shape)
                    polyface3d = Polyface3D.from_faces(face3ds, 0.01)
                    face3d = get_door_face3d(polyface3d.faces)
                    doors.append(Door(clean_and_id_string('Door'), face3d))

                elif element.is_a() == 'IfcSlab':
                    part_shape = get_shape(element, settings)
                    face3ds = get_face3ds_from_shape(part_shape)
                    polyface3d = Polyface3D.from_faces(face3ds, 0.01)
                    for face3d in polyface3d.faces:
                        shades.append(Shade(clean_and_id_string('Shade'), face3d))

    return rooms, apertures, doors, shades


rooms, apertures, doors, shades = extract_hb_objects()


hb_model = Model('House', rooms=rooms,
                 orphaned_apertures=apertures, orphaned_doors=doors, orphaned_shades=shades)
hb_model.to_hbjson(name=file_name)

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

file_path = file_2
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


def get_single_face3d(face3ds: list):
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


def get_shape(ifc_entity, settings):
    """Convert ifc entity to a basic FreeCAD shape"""

    shape = geom.create_shape(settings, ifc_entity)
    occ_shape = shape.geometry.brep_data

    with open("brep_data", "w") as file:
        file.write(occ_shape)

    fc_shape = Part.Shape()
    fc_shape.importBrepFromString(occ_shape)
    return fc_shape


def get_det(vec1, vec2, normal):
    x1, y1, z1 = (vec1.x, vec1.y, vec1.z)
    x2, y2, z2 = (vec2.x, vec2.y, vec2.z)
    xn, yn, zn = (normal.x, normal.y, normal.z)

    return x1*y2*zn + x2*yn*z1 + xn*y1*z2 - z1*y2*xn - z2*yn*x1 - zn*y1*x2


def get_face3ds_from_shape_face(face: Part.Shape.Faces) -> Face3D:
    point3ds = [Point3D(vertex.X, vertex.Y, vertex.Z) for vertex in face.Vertexes]
    ################################################################################

    center_point = Point3D(sum(point.x for point in point3ds) / len(point3ds), sum(
        point.y for point in point3ds) / len(point3ds), sum(point.z for point in point3ds) / len(point3ds))
    vectors = [LineSegment3D.from_end_points(
        center_point, point).v for point in point3ds]
    ##########################
    # temp_plane = Plane.from_three_points(center_point, point3ds[0], point3ds[1])
    # normal = temp_plane.n
    # x_direction = temp_plane.x
    # plane = Plane(normal, center_point, x_direction)
    # angles = [plane.x.angle(vector) for vector in vectors]
    ##########################
    # vector_one = vectors[0]
    # angles = [vector_one.angle(vector) for vector in vectors]
    # point_angle_dict = dict(zip(angles, point3ds))
    # angles_sorted = sorted(point_angle_dict)
    # points = [point_angle_dict[angle] for angle in angles_sorted]
    # print(point_angle_dict)
    # print(angles_sorted)
    # print(points, '\n')
    # return Face3D(points)
    ##########################
    # face3d = Face3D(point3ds)
    # center_point = face3d.center
    # normal = face3d.normal
    # x_direction = face3d.plane.x
    # plane = Plane(normal, center_point, x_direction)
    # angles = [plane.x.angle(vector) for vector in vectors]
    ###########################
    plane = Plane.from_three_points(center_point, point3ds[0], point3ds[1])
    normal = plane.n
    vector_one = vectors[0]
    angles = []
    for vector in vectors:
        cross = vector_one.cross(vector)
        if cross.normalize() == normal:
            angles.append(vector_one.angle(vector))
        else:
            angles.append((math.pi*2) - (vector_one.angle(vector)))
    point_angle_dict = dict(zip(point3ds, angles))
    sorted_dict = sorted(point_angle_dict.items(), key=lambda x: x[1])
    sorted_points = [item[0] for item in sorted_dict]
    return Face3D(sorted_points)
    ###########################
    if round(point3ds[0].x, 2) == 15.91 and round(point3ds[0].y, 2) == 6.42 and round(point3ds[0].z, 2) == 0.00:
        print(point3ds)
        # print("Normal", normal)
        # print("X vector", plane.x)
        # print("plane", plane)
        print(angles, '\n')
    ################################################################################
    return Face3D(point3ds)


def get_face3ds_from_shape(shape: Part.Shape) -> Polyface3D:
    face3ds = [get_face3ds_from_shape_face(face) for face in shape.Faces]
    ################################################################################

    ################################################################################

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
                # faces = shape.geometry.faces
                # verts = shape.geometry.verts

                # point3ds = [Point3D(verts[i], verts[i + 1], verts[i + 2])
                #             for i in range(0, len(verts), 3)]

                # face3ds = [Face3D([point3ds[faces[i]], point3ds[faces[i + 1]],
                #                    point3ds[faces[i + 2]]])
                #            for i in range(0, len(faces), 3)]

                if element.is_a() == 'IfcSpace':
                    part_shape = get_shape(element, settings)
                    face3ds = get_face3ds_from_shape(part_shape)
                    polyface3d = Polyface3D.from_faces(face3ds, 0.01)
                    if not polyface3d.is_solid:
                        room = Room.from_polyface3d(
                            clean_and_id_string('Room'), polyface3d)
                        rooms.append(room)

                # elif element.is_a() == 'IfcWindow':
                #     face3d = get_single_face3d(face3ds)
                #     apertures.append(Aperture(clean_and_id_string('Aperture'), face3d))

                # elif element.is_a() == 'IfcOpeningElement':
                #     pass

                # elif element.is_a() == 'IfcDoor':
                #     face3d = get_single_face3d(face3ds)
                #     doors.append(Door(clean_and_id_string('Door'), face3d))

                # elif element.is_a() == 'IfcSlab':
                #     for face3d in face3ds:
                #         shades.append(Shade(clean_and_id_string('Shade'), face3d))

    return rooms, apertures, doors, shades


rooms, apertures, doors, shades = extract_hb_objects()


hb_model = Model('House', rooms=rooms,
                 orphaned_apertures=apertures, orphaned_doors=doors, orphaned_shades=shades)
hb_model.to_hbjson(name=file_name)

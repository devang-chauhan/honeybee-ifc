
import ifcopenshell
from ifcopenshell import geom
from ifcopenshell.entity_instance import entity_instance as Element
from ifcopenshell.file import file as File

import FreeCAD
import Part

from typing import List
from ladybug_geometry.geometry3d import Point3D, Plane, Polyline3D, Polyface3D, Face3D,\
    LineSegment3D


def distance_to_closest_point_on_plane(point: Point3D, plane: Plane) -> float:
    """Get the distance from a point to a point on a plane."""
    cp = plane.closest_point(point)
    return cp.distance_to_point(point)


def get_window_face3d(polyface: Polyface3D) -> Face3D:
    """Get a simplified Face3D to represent apertue from a Polyface3D."""
    face3ds = polyface.faces
    # sort faces based on area
    area_sorted_faces = sorted(
        face3ds, key=lambda x: x.area, reverse=True)
    return area_sorted_faces[0]


def get_door_face3d(door_polyface: Polyface3D, opening_polyface: Polyface3D) -> Face3D:
    """Get a simplified Face3D to represent door from a Polyface3D."""
    face3ds = door_polyface.faces
    # sort faces based on area
    area_sorted_faces = sorted(
        face3ds, key=lambda x: x.area, reverse=True)

    # Select faces with the large area
    faces_to_use = [face for face in area_sorted_faces if face.area >= 0.5]
    if len(faces_to_use) == 0:
        return get_face3d_from_opening(opening_polyface)

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

    if face3d.center.distance_to_point(door_polyface.center) > 0.1:
        return get_face3d_from_opening(opening_polyface)

    return face3d


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

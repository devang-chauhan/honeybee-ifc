"""helper methods for other modules."""

import time
from functools import wraps
from datetime import timedelta
from typing import List

from ladybug_geometry.geometry3d import Point3D, Plane, Face3D, LineSegment3D, Polyline3D

import ifcopenshell
from ifcopenshell import geom
from ifcopenshell.entity_instance import entity_instance as Element

import FreeCAD
import Part


def duration(func):
    """Decorator to measure time used by a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        """This is a wrapper function."""
        start_time = time.monotonic()
        result = func(*args, **kwargs)
        end_time = time.monotonic()
        print(f'Time elapsed: {timedelta(seconds = end_time - start_time)}')
        return result
    return wrapper


def distance_to_closest_point_on_plane(point: Point3D, plane: Plane) -> float:
    """Get the distance from a point to a point on a plane."""
    cp = plane.closest_point(point)
    return cp.distance_to_point(point)


def get_shape(element: Element, settings: ifcopenshell.geom.settings) -> Part.Shape:
    """Convert an ifc element to a FreeCAD shape object.

    This functions is using the Part module of the FreeCAD package
    https://github.com/FreeCAD/FreeCAD/releases to access the Shape object of an 
    IFC element.

    Args:
        element: An IFC element
        settings: An ifcopenshell.geom.settings object

    Returns:
        A FreeCAD shape object
    """
    shape = geom.create_shape(settings, element)
    occ_shape = shape.geometry.brep_data
    fc_shape = Part.Shape()
    fc_shape.importBrepFromString(occ_shape)
    return fc_shape


def get_face3d_from_shape(shape: Part.Shape.Faces) -> Face3D:
    """Get a Face3D from a FreeCAD shape object."""
    edges = shape.Edges

    lines = [LineSegment3D.from_end_points(
        Point3D(edge.Vertexes[0].X, edge.Vertexes[0].Y, edge.Vertexes[0].Z),
        Point3D(edge.Vertexes[1].X, edge.Vertexes[1].Y, edge.Vertexes[1].Z))
        for edge in edges]
    polylines = Polyline3D.join_segments(lines, 0.01)
    face3d = Face3D(boundary=polylines[0].vertices)

    return face3d


def get_face3ds_from_shape(shape: Part.Shape) -> List[Face3D]:
    """Get a list of Face3D from a FreeCAD shape object."""
    face3ds = [get_face3d_from_shape(face) for face in shape.Faces]
    return face3ds


def get_nearby_face(simplified_face: Face3D, space):

    # Dict of Face3D : Honeybee Face structure
    faces = {face.geometry: face for face in space.Room.faces}

    # find faces parallel to the window face
    parallel_faces = [
        face for face in faces if not
        simplified_face.plane.intersect_plane(face.plane)]

    # find the nearest face from the parallel faces
    nearby_face = sorted(
        parallel_faces,
        key=lambda x: x.center.distance_to_point(simplified_face.center))[0]
    hb_face = faces[nearby_face]

    return nearby_face, hb_face


def move_face(element_face: Face3D, nearest_face: Face3D) -> Face3D:
    """Move the element face to the nearest face and get the moved face."""

    # check if the nearest face is above or below the element face
    if element_face.plane.is_point_above(nearest_face.center):
        element_face = element_face.flip()

    # first method to project aperture
    plane = nearest_face.plane
    closest_point = plane.closest_point(element_face.center)
    line = LineSegment3D.from_end_points(element_face.center, closest_point)
    moved_face = element_face.move(line.v)

    # second method to project aperture
    if not moved_face.plane.is_coplanar(plane):
        magnitude = nearest_face.plane.distance_to_point(element_face.center)
        vector = element_face.normal.reverse().normalize() * magnitude
        moved_face = element_face.move(vector)

    return moved_face

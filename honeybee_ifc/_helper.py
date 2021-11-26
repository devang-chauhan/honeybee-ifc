"""helper methods for other modules."""

import time
from functools import wraps
from datetime import timedelta
from typing import List

from ladybug_geometry.geometry3d import Point3D, Plane, Face3D, LineSegment3D, Polyline3D

import ifcopenshell
from ifcopenshell import geom
from ifcopenshell.entity_instance import entity_instance as IfcElement

import FreeCAD
import Part


def report_time(seconds):
    if seconds <= 60:
        return f'{round(seconds, 2)} seconds.'
    elif 60 < seconds <= 3600:
        return f'{round(seconds / 60, 2)} minutes.'
    else:
        return f'{round(seconds / 3600, 2)} hours.'


def duration(func):
    """Decorator to measure time used by a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        """This is a wrapper function."""
        start = time.perf_counter()
        result = func(*args, **kwargs)
        finish = time.perf_counter()
        print(f'Finished in {report_time(finish-start)}')
        return result
    return wrapper


def element_to_shape(element: IfcElement) -> Part.Shape:
    """Convert an ifc element to a FreeCAD shape object.

    This functions is using the Part module of the FreeCAD package
    https://github.com/FreeCAD/FreeCAD/releases to access the Shape object of an 
    IFC element.

    Args:
        element: An IFC element

    Returns:
        A FreeCAD shape object
    """
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.USE_BREP_DATA, True)

    shape = geom.create_shape(settings, element)
    occ_shape = shape.geometry.brep_data
    fc_shape = Part.Shape()
    fc_shape.importBrepFromString(occ_shape)
    if len(fc_shape.Faces) < 4:
        return None
    return fc_shape


def get_face3d_from_shape_face(face: Part.Shape.Faces) -> Face3D:
    """Get a Face3D from a FreeCAD shape object."""
    edges = face.Edges
    lines = [LineSegment3D.from_end_points(
        Point3D(edge.Vertexes[0].X, edge.Vertexes[0].Y, edge.Vertexes[0].Z),
        Point3D(edge.Vertexes[1].X, edge.Vertexes[1].Y, edge.Vertexes[1].Z))
        for edge in edges if len(edge.Vertexes) == 2]

    polylines = Polyline3D.join_segments(lines, 0.01)
    face3d = Face3D(boundary=polylines[0].vertices)

    return face3d


def get_face3ds_from_shape(shape: Part.Shape) -> List[Face3D]:
    """Get a list of Face3D from a FreeCAD shape object."""
    face3ds = [get_face3d_from_shape_face(face)
               for face in shape.Faces]
    return face3ds


def element_to_face3ds(element) -> List[Face3D]:
    """Get a list of Face3D objects for the Element."""

    # geometry settings
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)

    # create shape
    shape = geom.create_shape(settings, element)

    # Indices of vertices per triangle face e.g. [f1v1, f1v2, f1v3, f2v1, f2v2, f2v3, ...]
    faces = shape.geometry.faces
    # X Y Z of vertices in flattened list e.g. [v1x, v1y, v1z, v2x, v2y, v2z, ...]
    verts = shape.geometry.verts

    point3ds = [Point3D(verts[i], verts[i + 1], verts[i + 2])
                for i in range(0, len(verts), 3)]
    face3ds = [Face3D([point3ds[faces[i]], point3ds[faces[i + 1]], point3ds[faces[i + 2]]])
               for i in range(0, len(faces), 3)]

    return face3ds

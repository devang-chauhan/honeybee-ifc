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

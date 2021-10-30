"""Honeybee-IFC Opening object."""

from typing import Tuple
import ifcopenshell
from ifcopenshell.entity_instance import entity_instance as IfcElement
from ladybug_geometry.geometry3d import Point3D, Face3D, LineSegment3D
from .element import Element


class Opening(Element):
    """Honeybee-IFC Opening object.

    Args:
        opening: An IfcOpeningElement object.
        settings: An ifcopenshell.geom.settings object.
    """

    def __init__(self, opening: IfcElement, settings: ifcopenshell.geom.settings):
        super().__init__(opening, settings)
        self.opening = opening
        self.settings = settings

    def get_search_location(self, location: Tuple[float, float, float]) -> \
            Tuple[float, float, float]:
        """Get a center point on the outer face of the opening element.

        Args:
            location: The location that ifcOpenShell gives, which is at the 
            mid-point of the bottom  edge of the outmost face of the opening element.

        Returns:
            A tuple of three floats representing the x, y, and z coordinates of the
            center point of the opening element.
        """

        point3d = Point3D(location[0], location[1], location[2])
        polyface3d = self.polyface3d
        largest_faces = sorted([face for face in polyface3d.faces],
                               key=lambda x: x.area, reverse=True)[:2]
        back_face = sorted([face for face in largest_faces],
                           key=lambda x: x.plane.closest_point(point3d).
                           distance_to_point(point3d))[0]

        return back_face.center.x, back_face.center.y, back_face.center.z

    def get_face3d_at_center(self) -> Face3D:
        """Get a simplified face3d at the center of the object."""

        polyface3d = self.polyface3d
        # sort faces based on area
        area_sorted_faces = sorted(
            polyface3d.faces, key=lambda x: x.area, reverse=True)

        line = LineSegment3D.from_end_points(
            area_sorted_faces[0].center, polyface3d.center)
        # move the largest face to the center of the opening element
        moved_face = area_sorted_faces[0].move(line.v)

        return moved_face

"""Honeybee-IFC Window object."""

import ifcopenshell
from ifcopenshell.entity_instance import entity_instance as IfcElement
from ladybug_geometry.geometry3d import Face3D, LineSegment3D
from honeybee.aperture import Aperture
from honeybee.typing import clean_and_id_string
from ladybug_geometry.geometry3d.polyface import Polyface3D
from .element import Element
from .opening import Opening


class Window(Element):
    """Honeybee-IFC Window object.

    Args:
        window: An IFC window object.
        settings: An IFC settings object.
    """

    def __init__(self, window: IfcElement) -> None:
        super().__init__(window)
        self.window = window
        self._polyface3d = self.to_polyface3d()

    @property
    def opening(self) -> Opening:
        """Honeybee-IFC Element for the IfcOpeningElement of an IfcWindow"""
        try:
            return Opening(self.element.FillsVoids[0].RelatingOpeningElement)
        except Exception as e:
            print(e, self.guid)
            raise ValueError('FillsVoids is empty for this window.')

    @property
    def polyface3d(self) -> Polyface3D:
        return self._polyface3d

    @property
    def face3d(self) -> Face3D:
        """A Face3D representation."""
        return sorted(self.polyface3d.faces, key=lambda x: x.area, reverse=True)[0]

    def moved_opening_face3d(self) -> Face3D:
        """Get a simplified Face3D representation that is moved to the center of the opening."""
        # faces parallel to the plane
        # we need to do this check because people create openings that are way more
        # extruded than the thickness of the wall. Which means the face with the largest
        # area may not be the one that we want.
        parallel_faces = [
            face for face in self.opening.polyface3d.faces if
            face.normal.normalize().is_equivalent(self.face3d.plane.n.normalize(), 0.001)]

        area_sorted_faces = sorted(
            parallel_faces, key=lambda x: x.area, reverse=True)

        face3d = area_sorted_faces[0]

        line = LineSegment3D.from_end_points(face3d.center, self.polyface3d.center)
        # move the largest face to the center of the window object.
        return face3d.move(line.v)

    def to_honeybee(self) -> Aperture:
        """Get a Honeybee Aperture object."""
        return Aperture(clean_and_id_string('Aperture'), self.moved_opening_face3d())

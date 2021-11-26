"""Honeybee-IFC Door object."""

import ifcopenshell
from ifcopenshell.entity_instance import entity_instance as IfcElement
from ladybug_geometry.geometry3d import Face3D, LineSegment3D
from ladybug_geometry.geometry3d import Polyface3D
from honeybee.door import Door as HBDoor
from honeybee.typing import clean_and_id_string
from .element import Element
from .opening import Opening


class Door(Element):
    """Honeybee-IFC Door object.

    Args:
        door: IfcDoor element.
        settings: An ifcopenshell.geom.settings object.
    """

    def __init__(self, door: IfcElement) -> None:
        super().__init__(door)
        self.door = door
        self._polyface3d = self.to_polyface3d()

    @property
    def opening(self) -> Opening:
        """Honeybee-IFC Element for the IfcOpeningElement of an IfcWindow"""
        return Opening(self.element.FillsVoids[0].RelatingOpeningElement)

    @property
    def polyface3d(self) -> Polyface3D:
        return self._polyface3d

    def moved_opening_face3d(self) -> Face3D:
        """Get a simplified Face3D representation that is moved to the center of the opening."""

        parallel_faces = [
            face for face in self.opening.polyface3d.faces if
            face.normal.normalize().is_equivalent(self.face3d.plane.n.normalize(), 0.001)]

        if not parallel_faces:
            print(f'In Door {self.guid}, the door panel does not seem parallel to the'
                  ' door opening. This door might not be translated correctly.')
            # This means a door or a window is not parallel to the opening.
            area_sorted_faces = sorted(
                self.opening.polyface3d.faces, key=lambda x: x.area, reverse=True)
            face3d = area_sorted_faces[0]
            line = LineSegment3D.from_end_points(
                face3d.center, self.opening.polyface3d.center)
            # move the largest face to the center of the opening element
            return face3d.move(line.v)

        # use the larges face in the opening if the door or the window is not parallel
        area_sorted_faces = sorted(
            parallel_faces, key=lambda x: x.area, reverse=True)

        face3d = area_sorted_faces[0]
        line = LineSegment3D.from_end_points(
            face3d.center, self.polyface3d.center)
        # move the largest face to the center of the opening element
        return face3d.move(line.v)

    def to_honeybee(self) -> HBDoor:
        """Get a Honeybee Aperture object."""
        return HBDoor(clean_and_id_string('Door'), self.moved_opening_face3d())

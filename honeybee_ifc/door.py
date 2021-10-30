"""Honeybee-IFC Door object."""

import ifcopenshell
from ifcopenshell.entity_instance import entity_instance as IfcElement
from ladybug_geometry.geometry3d import Face3D, Polyface3D, Polyline3D
from .element import Element
from .opening import Opening
from ._helper import distance_to_closest_point_on_plane


class Door(Element):
    """Honeybee-IFC Door object.

    Args:
        door: IfcDoor element.
        settings: An ifcopenshell.geom.settings object.
    """

    def __init__(self, door: IfcElement, settings: ifcopenshell.geom.settings) -> None:
        super().__init__(door, settings)
        self.door = door
        self.settings = settings

    @property
    def opening(self) -> Opening:
        """Honeybee-IFC Opening object for the IfcOpeningElement of an IfcDoor"""
        return Opening(self.element.FillsVoids[0].RelatingOpeningElement, self.settings)

    @property
    def face3d(self) -> Face3D:
        """A Face3D representation."""
        # sort faces based on area
        area_sorted_faces = sorted(
            self.polyface3d.faces, key=lambda x: x.area, reverse=True)

        # Select faces with the large area
        faces_to_use = [face for face in area_sorted_faces if face.area >= 0.5]
        # if none of the faces are large enough, use the center face of the opening
        # element of the door
        if len(faces_to_use) == 0:
            return self.opening.get_face3d_at_center()

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

        # if the door is open and generated face3ed is far from the center of the door
        # use the center face of the opening element
        if face3d.center.distance_to_point(self.polyface3d.center) > 0.1:
            return self.opening.get_face3d_at_center()

        return face3d

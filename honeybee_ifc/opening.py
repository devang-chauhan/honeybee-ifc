"""Honeybee-IFC Opening object."""


from ifcopenshell.entity_instance import entity_instance as IfcElement
from ladybug_geometry.geometry3d import Polyface3D
from .element import Element


class Opening(Element):
    """Honeybee-IFC Opening object.

    Args:
        opening: An IfcOpeningElement object.
        settings: An ifcopenshell.geom.settings object.
    """

    def __init__(self, opening: IfcElement):
        super().__init__(opening)
        self.opening = opening
        self._polyface3d = self.to_polyface3d()

    @property
    def polyface3d(self) -> Polyface3D:
        return self._polyface3d

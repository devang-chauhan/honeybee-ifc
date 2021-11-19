"""Honeybee-IFC Opening object."""


import ifcopenshell
from ifcopenshell.entity_instance import entity_instance as IfcElement
from .element import Element


class Opening(Element):
    """Honeybee-IFC Opening object.

    Args:
        opening: An IfcOpeningElement object.
        settings: An ifcopenshell.geom.settings object.
    """

    def __init__(self, opening: IfcElement,  settings: ifcopenshell.geom.settings = None):
        super().__init__(opening, settings)
        self.opening = opening
        self.settings = settings or self._settings()

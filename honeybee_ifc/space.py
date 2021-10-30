"""Honeybee-IFC Space object."""

import ifcopenshell
from ifcopenshell.entity_instance import entity_instance as IfcElement
from .element import Element


class Space(Element):
    """Honeybee-IFC Space object.

    Args:
        space: IfcElement object.
        settings: ifcopenshell.geom.settings object.
    """

    def __init__(self, space: IfcElement, settings: ifcopenshell.geom.settings) -> None:
        super().__init__(space, settings)
        self.space = space
        self.settings = settings

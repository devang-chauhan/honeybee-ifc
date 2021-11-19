"""Honeybee-IFC Shade object."""


import ifcopenshell
from ifcopenshell.entity_instance import entity_instance as IfcElement
from honeybee.shade import Shade as HBShade
from honeybee.typing import clean_and_id_string
from .element import Element


class Shade(Element):
    """Honeybee-IFC Opening object.

    Args:
        shade: Any Ifc object that needs to be converted to shade.
        settings: An ifcopenshell.geom.settings object.
    """

    def __init__(self, shade: IfcElement,  settings: ifcopenshell.geom.settings = None):
        super().__init__(shade, settings)
        self.shade = shade
        self.settings = settings or self._settings()

    def to_honeybee(self):
        """Convert IFC object to Honeybee shade."""
        return [HBShade(clean_and_id_string('Shade'), face)
                for face in self.polyface3d.faces]

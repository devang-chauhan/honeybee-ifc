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

    def __init__(self, shade: IfcElement):
        super().__init__(shade)
        self.shade = shade

    def to_honeybee(self):
        """Convert IFC object to Honeybee shade."""

        if not self.brep_possible():
            return [HBShade(clean_and_id_string('Shade'), face)
                    for face in self.to_face3ds()]

        return [HBShade(clean_and_id_string('Shade'), face)
                for face in self.to_polyface3d().faces]

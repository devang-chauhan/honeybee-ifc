"""Honeybee-IFC Slab object."""

import ifcopenshell
from ifcopenshell.entity_instance import entity_instance as IfcElement
from ladybug_geometry.geometry3d import Face3D
from .element import Element
from typing import List


class Slab(Element):
    """Honeybee-IFC Slab object.

    Args:
        slab: An IFC object.
        settings: An IFC settings object.
    """

    def __init__(self, slab: IfcElement, settings: ifcopenshell.geom.settings) -> None:
        super().__init__(slab, settings)
        self.slab = slab
        self.settings = settings

    @property
    def face3ds(self) -> List[Face3D]:
        """A list of Ladybug Face3D representations."""
        return self.polyface3d.faces

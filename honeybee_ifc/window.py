"""Honeybee-IFC Window object."""

import ifcopenshell
from ifcopenshell.entity_instance import entity_instance as IfcElement
from ladybug_geometry.geometry3d import Face3D
from .element import Element
from .opening import Opening


class Window(Element):
    """Honeybee-IFC Window object.

    Args:
        window: An IFC window object.
        settings: An IFC settings object.
    """

    def __init__(self, window: IfcElement, settings: ifcopenshell.geom.settings) -> None:
        super().__init__(window, settings)
        self.window = window
        self.settings = settings

    @property
    def opening(self) -> Opening:
        """Honeybee-IFC Element for the IfcOpeningElement of an IfcWindow"""
        return Opening(self.element.FillsVoids[0].RelatingOpeningElement, self.settings)

    @property
    def face3d(self) -> Face3D:
        """A Face3D representation."""
        return sorted(self.polyface3d.faces, key=lambda x: x.area, reverse=True)[0]

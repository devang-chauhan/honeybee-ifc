"""Honeybee-IFC Space object."""

from typing import List
from honeybee.room import Room as HBRoom
from honeybee.typing import clean_and_id_string
import ifcopenshell
from ifcopenshell.entity_instance import entity_instance as IfcElement
from .element import Element
from .door import Door
from .window import Window


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
        self.room = HBRoom.from_polyface3d(clean_and_id_string('Room'), self.polyface3d)

    @property
    def Room(self) -> HBRoom:
        """A Honeybee Room object."""
        return self.room

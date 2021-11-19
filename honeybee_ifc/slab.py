"""Honeybee-IFC Slab object."""

import ifcopenshell
from ifcopenshell.entity_instance import entity_instance as IfcElement
from honeybee.face import Face as Face
from honeybee.typing import clean_and_id_string
from .element import Element
from typing import List


class Slab(Element):
    """Honeybee-IFC Slab object.

    Args:
        slab: An IFC object.
        settings: An IFC settings object.
    """

    def __init__(self, slab: IfcElement, predefined_type: str,
                 settings: ifcopenshell.geom.settings = None) -> None:
        super().__init__(slab, settings)
        self.slab = slab
        self.predefined_type = predefined_type
        self.settings = settings or self._settings()

    def to_honeybee(self) -> List[Face]:
        """Get a list of Honeybee Face objects for the wall."""
        return [Face(clean_and_id_string('Face'), face.flip()) for
                face in self.polyface3d.faces]

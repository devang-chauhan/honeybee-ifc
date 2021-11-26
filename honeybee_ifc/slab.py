"""Honeybee-IFC Slab object."""


from ifcopenshell.entity_instance import entity_instance as IfcElement
from honeybee.face import Face as Face
from honeybee.typing import clean_and_id_string
from ladybug_geometry.geometry3d import Polyface3D
from .element import Element
from typing import List


class Slab(Element):
    """Honeybee-IFC Slab object.

    Args:
        slab: An IFC object.
        settings: An IFC settings object.
    """

    def __init__(self, slab: IfcElement, predefined_type: str) -> None:
        super().__init__(slab)
        self.slab = slab
        self.predefined_type = predefined_type
        self._polyface3d = self.to_polyface3d()

    @property
    def polyface3d(self) -> Polyface3D:
        return self._polyface3d

    def to_honeybee(self) -> List[Face]:
        """Get a list of Honeybee Face objects for the wall."""
        return [Face(clean_and_id_string('Face'), face.flip()) for
                face in self.polyface3d.faces]

"""Honeybee-IFC Wall object."""


from typing import List
from ifcopenshell.entity_instance import entity_instance as IfcElement

from honeybee.face import Face as Face
from honeybee.facetype import face_types
from honeybee.typing import clean_and_id_string

from .element import Element


class Wall(Element):
    """Honeybee-IFC Wall object.

    Args:
        wall: An IFC wall object.
        settings: An IFC settings object.
    """

    def __init__(self, wall: IfcElement, representation: str = 'mesh') -> None:
        super().__init__(wall, representation)
        self.wall = wall
        self.body = self.wall.Representation.Representations[0].RepresentationIdentifier

    @ staticmethod
    def has_parts(element) -> bool:
        pass

    def to_honeybee(self) -> List[Face]:
        """Get a list of Honeybee Face objects for the wall."""
        try:
            return [Face(clean_and_id_string('Wall'), face, face_types.wall) for
                    face in self.to_face3ds()]
        except Exception as e:
            print(e, self.guid)
            raise Exception

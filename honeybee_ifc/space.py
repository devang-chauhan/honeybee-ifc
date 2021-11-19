"""Honeybee-IFC Space object."""

import ifcopenshell
from typing import List
from ifcopenshell.entity_instance import entity_instance as IfcElement
from honeybee_radiance.sensorgrid import SensorGrid
from honeybee.typing import clean_and_id_string
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

    def get_grids(self, offset=0.75, size=0.6) -> List[SensorGrid]:
        """Generate sensor grids from the floor of the space."""

        faces = []
        for face in self.polyface3d.faces:
            if face.normal.z == -1:
                faces.append(face)

        return SensorGrid.from_face3d(clean_and_id_string('Grid'),
                                      faces, x_dim=size, y_dim=size,
                                      offset=offset, flip=True)

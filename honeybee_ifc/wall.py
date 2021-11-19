"""Honeybee-IFC Wall object."""

import ifcopenshell
from typing import List
from ifcopenshell.entity_instance import entity_instance as IfcElement
from ladybug_geometry.geometry3d import Face3D, Point3D
from honeybee.face import Face as Face
from honeybee.facetype import face_types
from honeybee.typing import clean_and_id_string
from ifcopenshell import geom


class Wall():
    """Honeybee-IFC Wall object.

    Args:
        wall: An IFC wall object.
        settings: An IFC settings object.
    """

    def __init__(self, wall: IfcElement, settings: ifcopenshell.geom.settings = None) -> None:
        self.wall = wall
        self.settings = settings or self._settings()
        self.shape = geom.create_shape(self.settings, self.wall)

    @staticmethod
    def _settings() -> ifcopenshell.geom.settings:
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        return settings

    def to_face3ds(self) -> List[Face3D]:
        """Get a list of Face3D objects for the wall."""

        # Indices of vertices per triangle face e.g. [f1v1, f1v2, f1v3, f2v1, f2v2, f2v3, ...]
        faces = self.shape.geometry.faces
        # X Y Z of vertices in flattened list e.g. [v1x, v1y, v1z, v2x, v2y, v2z, ...]
        verts = self.shape.geometry.verts

        point3ds = [Point3D(verts[i], verts[i + 1], verts[i + 2])
                    for i in range(0, len(verts), 3)]
        face3ds = [Face3D([point3ds[faces[i]], point3ds[faces[i + 1]], point3ds[faces[i + 2]]])
                   for i in range(0, len(faces), 3)]

        return face3ds

    def to_honeybee(self) -> List[Face]:
        """Get a list of Honeybee Face objects for the wall."""
        return [Face(clean_and_id_string('Wall'), face, face_types.wall) for
                face in self.to_face3ds()]

"""Honeybee-ifc Element object."""

from typing import List
from ladybug_geometry.geometry3d import Polyface3D, Face3D, Point3D

from ._helper import element_to_shape, get_face3ds_from_shape, element_to_face3ds

import ifcopenshell
from ifcopenshell import geom
from ifcopenshell.entity_instance import entity_instance as IfcElement
import FreeCAD
import Part


class Element:
    """Honeybee-ifc Element object.

    All other Honeybee-IFC objects inherits this object.

    Args:
        element: An IFC element.
        settings: An ifcopenshell.geom.settings object.
    """

    def __init__(self, element: IfcElement, representation: str = 'brep') -> None:
        self.element = element
        self.representation = representation

    @staticmethod
    def settings(representation: str = 'brep') -> ifcopenshell.geom.settings:
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        if representation == 'brep':
            settings.set(settings.USE_BREP_DATA, True)
        elif representation == 'mesh':
            settings.set(settings.USE_BREP_DATA, False)
        return settings

    @property
    def ifc_element(self):
        """Original IFC Element."""
        return self.element

    @property
    def guid(self):
        """Global id of the IFC element."""
        return self.element.GlobalId

    def brep_possible(self) -> None:
        """Check if the Brep can be created from a Shape."""

        if self.representation == 'brep':
            # TODO: Capture this repeated code in a helper function
            shape = geom.create_shape(self.settings(), self.element)
            occ_shape = shape.geometry.brep_data
            fc_shape = Part.Shape()
            fc_shape.importBrepFromString(occ_shape)
            if len(fc_shape.Faces) < 4:
                return False
            return True

        return False

    def to_polyface3d(self) -> Polyface3D:
        """Polyface3D object from an IFC element."""
        # TODO: Capture this repeated code in a helper function
        shape = geom.create_shape(self.settings(), self.element)
        occ_shape = shape.geometry.brep_data
        fc_shape = Part.Shape()
        fc_shape.importBrepFromString(occ_shape)
        shape = fc_shape

        face3ds = get_face3ds_from_shape(shape)
        polyface3d = Polyface3D.from_faces(face3ds, tolerance=0.01)
        # if the Polyface is solid return it or return a new Polyface with all faces
        # flipped
        if polyface3d.is_solid:
            return polyface3d

        faces = Polyface3D.get_outward_faces(polyface3d.faces, 0.01)
        polyface3d = Polyface3D.from_faces(faces, tolerance=0.01)
        return polyface3d

    def to_face3ds(self) -> List[Face3D]:
        """Get a list of Ladybug Face3D objects for the element."""

        shape = geom.create_shape(self.settings('mesh'), self.element)

        # Indices of vertices per triangle face e.g. [f1v1, f1v2, f1v3, f2v1, f2v2, f2v3, ...]
        faces = shape.geometry.faces
        # X Y Z of vertices in flattened list e.g. [v1x, v1y, v1z, v2x, v2y, v2z, ...]
        verts = shape.geometry.verts

        point3ds = [Point3D(verts[i], verts[i + 1], verts[i + 2])
                    for i in range(0, len(verts), 3)]
        face3ds = [Face3D([point3ds[faces[i]], point3ds[faces[i + 1]], point3ds[faces[i + 2]]])
                   for i in range(0, len(faces), 3)]

        return face3ds

    def to_freecad_shape(self) -> FreeCAD.Part.Shape:
        """Get a FreeCAD Shape object for the element."""
        ifc_shapes = []
        for part in self.element.IsDecomposedBy[0].RelatedObjects:
            ifc_shapes.append(geom.create_shape(self.settings(), part))

        # TODO: Capture this repeated code in a helper function

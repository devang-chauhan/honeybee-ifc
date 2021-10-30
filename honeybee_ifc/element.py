"""Honeybee-ifc Element object."""

import ifcopenshell
from ladybug_geometry.geometry3d import Polyface3D
from ifcopenshell.entity_instance import entity_instance as IfcElement
from ._helper import get_shape, get_face3ds_from_shape


class Element:
    """Honeybee-ifc Element object.

    All other Honeybee-IFC objects inherits this object.

    Args:
        element: An IFC element.
        settings: An ifcopenshell.geom.settings object.
    """

    def __init__(self, element: IfcElement, settings: ifcopenshell.geom.settings):
        self.element = element
        self.settings = settings
        self._polyface3d = self._get_polyface3d()

    @property
    def ifc_element(self):
        """Original IFC Element."""
        return self.element

    @property
    def guid(self):
        """Global id of the IFC element."""
        return self.element.GlobalId

    @property
    def polyface3d(self):
        """Ladybug Polyface3D representation."""
        return self._polyface3d

    def _get_polyface3d(self) -> Polyface3D:
        """Polyface3D object from an IFC element."""
        shape = get_shape(self.element, self.settings)
        face3ds = get_face3ds_from_shape(shape)
        polyface3d = Polyface3D.from_faces(face3ds, tolerance=0.01)
        # if the Polyface is solid return it or return a new Polyface with all faces
        # flipped
        if polyface3d.is_solid:
            return polyface3d
        else:
            faces = Polyface3D.get_outward_faces(polyface3d.faces, 0.01)
            polyface3d = Polyface3D.from_faces(faces, tolerance=0.01)
            return polyface3d

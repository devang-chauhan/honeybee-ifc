"""
Import an IFC file and turn it into a Honeybee model.
Currently, only supporting IFC files with IFC2x3 schema.
"""
import pathlib
import random
import multiprocessing

from typing import List
from enum import Enum

import ifcopenshell
from ifcopenshell.util.unit import calculate_unit_scale
from ifcopenshell.util.placement import get_local_placement

from ladybug_geometry.geometry3d import LineSegment3D, Face3D, Ray3D
from honeybee.model import Model as HBModel
from honeybee.aperture import Aperture as HBAperture
from honeybee.door import Door as HBDoor
from honeybee.shade import Shade as HBShade
from honeybee.typing import clean_and_id_string

from .window import Window
from .space import Space
from .slab import Slab
from ._helper import move_face, get_nearby_face


class OpeningElement(Enum):
    window = 'window'
    door = 'door'


class Model:
    """Honeybee-IFC model.

    Args:
        ifc_file_path: A string. The path to the IFC file.
    """

    def __init__(self, ifc_file_path: str) -> None:
        self.ifc_file_path = self._validate_path(ifc_file_path)
        self.ifc_file = ifcopenshell.open(self.ifc_file_path)
        self.settings = self._ifc_settings()
        self.unit_factor = calculate_unit_scale(self.ifc_file)
        self.elements = ('IfcSpace', 'IfcWindow', 'IfcSlab')
        self.spaces = {}
        self.doors = []
        self.windows = []
        self.slabs = []
        self._extract_elements()

    @staticmethod
    def _validate_path(path: str) -> pathlib.Path:
        """Validate path."""
        path = pathlib.Path(path)
        if not path.exists():
            raise ValueError(f'Path {path} does not exist.')
        return path

    def _ifc_settings(self):
        """IFC settings."""
        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)
        settings.set(settings.USE_BREP_DATA, True)
        return settings

    def _extract_elements(self) -> None:
        """Extract elements from the IFC file."""
        iterator = ifcopenshell.geom.iterator(
            self.settings, self.ifc_file, multiprocessing.cpu_count(),
            include=self.elements)

        if iterator.initialize():
            while iterator.next():
                shape = iterator.get()
                element = self.ifc_file.by_guid(shape.guid)

                if element.is_a() == 'IfcSpace':
                    self.spaces[element.GlobalId] = Space(element, self.settings)

                elif element.is_a() == 'IfcSlab':
                    self.slabs.append(Slab(element, self.settings))

                elif element.is_a() == 'IfcWindow':
                    self.windows.append(Window(element, self.settings))

    def _get_nearby_spaces(self, element: OpeningElement,
                           search_radius: float = 0.5) -> List[List[Space]]:
        """Get nearby spaces.

        Args:
            element: A OpeningElement object.
            search_radius: A float number. Defaults to 0.5 meters.

        Returns:
            A list of nearby space objects. Each list has a list of nearby spaces for
            either a window or the door object based on argument element.
        """
        # setup BVH tree
        tree_settings = ifcopenshell.geom.settings()
        tree_settings.set(tree_settings.DISABLE_TRIANGULATION, True)
        tree_settings.set(tree_settings.DISABLE_OPENING_SUBTRACTIONS, True)
        iterator = ifcopenshell.geom.iterator(
            tree_settings, self.ifc_file, include=("IfcSpace",))
        tree = ifcopenshell.geom.tree()
        tree.add_iterator(iterator)

        if element.value == 'window':
            elements = self.windows
        else:
            elements = self.doors

        near_by_spaces = []
        # Get element location
        for element in elements:
            # get the location from where search will happen
            matrix = ifcopenshell.util.placement.get_local_placement(
                element.ifc_element.ObjectPlacement)
            # location provided by ifcOpenShell
            location = tuple(map(float, matrix[0:3, 3] * self.unit_factor))
            # location calculated by honeybee-ifc
            outer_face_center_location = element.opening.get_search_location(location)

            # search tree
            ifc_spaces = tree.select(outer_face_center_location, extend=search_radius)
            # if for some reason the back_face_center does not work,
            # use the original location
            if not all(len(item) > 0 for item in ifc_spaces):
                ifc_spaces = tree.select(location, extend=search_radius)

            # Matching the IfcSpace objects with existing Space objects through GlobalID
            spaces = [self.spaces[space.GlobalId] for space in ifc_spaces]
            near_by_spaces.append(spaces)

        return near_by_spaces

    def _project_windows_on_nearby_space(self) -> List[Face3D]:
        """Move the Face3D representation of Window object to the nearby Space object.

        If the Face3D can be a sub-face of any of the face of
        the Room property of the Space object then the Face3D will be turned into a
        Honeybee Aperture object and will be added to a particular face of the Room as a
        child.

        The Face3Ds that cannot be a sub-face of any of the face of the Room property
        of the Space object then the Face3D will be returned.
        """

        # simplified window faces and their nearby spaces
        simplified_faces = [window.face3d for window in self.windows]
        nearby_spaces = self._get_nearby_spaces(OpeningElement.window)

        moved_face3ds = []

        for i in range(len(simplified_faces)):
            window_face = simplified_faces[i]
            # get the nearby space
            if len(nearby_spaces[i]) == 1:
                nearby_space = nearby_spaces[i][0]
                nearby_face, hb_face = get_nearby_face(simplified_faces[i], nearby_space)
                # Move the Face3D to the nearest face
                moved_face3d = move_face(window_face, nearby_face)
                # If the moved face can be a subface of the nearby face, add as a
                # Honeybee Aperture object
                scaled_face3d = moved_face3d.scale(0.99, moved_face3d.center)
                if nearby_face.is_sub_face(scaled_face3d, tolerance=0.01, angle_tolerance=0.0):
                    aperture = HBAperture(clean_and_id_string('Aperture'), scaled_face3d)
                    hb_face.add_aperture(aperture)
                else:
                    moved_face3ds.append(moved_face3d)

            elif len(nearby_spaces[i]) == 2:

                # Simplified window face as a Face3D
                window_face = simplified_faces[i]
                spaces = nearby_spaces[i]
                # shoot rays on two sides of the window face
                ray_1 = Ray3D(window_face.center, window_face.normal)
                ray_2 = Ray3D(window_face.center, window_face.normal.reverse())

                if spaces[0].Room.geometry.does_intersect_line_ray_exist(ray_1):
                    nearby_space = spaces[0]
                    nearby_face, hb_face = get_nearby_face(
                        simplified_faces[i], nearby_space)
                    # Move the Face3D to the nearest face
                    moved_face3d = move_face(window_face, nearby_face)
                    # If the moved face can be a subface of the nearby face, add as a
                    # Honeybee Aperture object
                    scaled_face3d = moved_face3d.scale(0.99, moved_face3d.center)
                    if nearby_face.is_sub_face(scaled_face3d, tolerance=0.01, angle_tolerance=0.0):
                        aperture = HBAperture(
                            clean_and_id_string('Aperture'), scaled_face3d)
                        hb_face.add_aperture(aperture)
                    else:
                        moved_face3ds.append(moved_face3d)

                if spaces[1].Room.geometry.does_intersect_line_ray_exist(ray_2):
                    nearby_space = spaces[1]
                    nearby_face, hb_face = get_nearby_face(
                        simplified_faces[i], nearby_space)
                    # Move the Face3D to the nearest face
                    moved_face3d = move_face(window_face, nearby_face)
                    # If the moved face can be a subface of the nearby face, add as a
                    # Honeybee Aperture object
                    scaled_face3d = moved_face3d.scale(0.99, moved_face3d.center)
                    if nearby_face.is_sub_face(scaled_face3d, tolerance=0.01, angle_tolerance=0.0):
                        aperture = HBAperture(
                            clean_and_id_string('Aperture'), scaled_face3d)
                        hb_face.add_aperture(aperture)
                    else:
                        moved_face3ds.append(moved_face3d)

            else:
                print(f'Window {self.windows[i].guid} did not export.')
                continue

        return moved_face3ds

    def to_hbjson(self, target_folder: str = '.', file_name: str = None) -> str:
        """Write the model to an HBJSON file.

        Args:
            target_folder: The folder where the HBJSON file will be saved.
                Default to the current working directory.
            file_name: The name of the HBJSON file. Default to the name of the
                IFC file.

        Returns:
            Path to the written HBJSON file.
        """

        rooms, apertures, doors, shades = [], [], [], []

        # Try adding the simplified Face3D representation of IfcWindow objects to the
        # Room property of the nearby Space object.
        moved_window_faces = self._project_windows_on_nearby_space()
        # If any of the Face3Ds cannot be added to the Rooms, add them as orphaned
        # Apertures
        if len(moved_window_faces) > 0:
            apertures = [HBAperture(clean_and_id_string('Aperture'), face)
                         for face in moved_window_faces]

        shades = [HBShade(clean_and_id_string('Shade'), face)
                  for slab in self.slabs for face in slab.face3ds]

        rooms = [space.Room for space in self.spaces.values()]

        hb_model = HBModel('Model', rooms=rooms, orphaned_apertures=apertures,
                           orphaned_doors=doors, orphaned_shades=shades)

        if not file_name:
            file_name = self.ifc_file_path.stem

        path = hb_model.to_hbjson(name=file_name, folder=target_folder)

        return path

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
from honeybee.room import Room as HBRoom
from honeybee.aperture import Aperture as HBAperture
from honeybee.door import Door as HBDoor
from honeybee.shade import Shade as HBShade
from honeybee.typing import clean_and_id_string

from .window import Window
from .door import Door
from .space import Space
from .slab import Slab
from ._helper import move_face


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
        self.elements = ('IfcSpace', 'IfcWindow', 'IfcDoor', 'IfcSlab')
        self.spaces = []
        self.doors = []
        self.windows = []
        self.slabs = []
        self._extract_elements()

    def _validate_path(self, path: str) -> pathlib.Path:
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

                # convert to a honeybee object directly
                if element.is_a() == 'IfcSpace':
                    self.spaces.append(Space(element, self.settings))

                # convert to a honeybee object directly
                elif element.is_a() == 'IfcSlab':
                    self.slabs.append(Slab(element, self.settings))

                # save for further processing
                elif element.is_a() == 'IfcWindow':
                    self.windows.append(Window(element, self.settings))

                # save for further processing
                elif element.is_a() == 'IfcDoor':
                    self.doors.append(Door(element, self.settings))

    def get_nearby_spaces(self, element: OpeningElement,
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

            spaces = [Space(space, self.settings) for space in ifc_spaces]
            near_by_spaces.append(spaces)

        return near_by_spaces

    def project_windows_on_nearby_space(self) -> List[Face3D]:
        """Move the windows to the nearby spaces."""

        simplified_faces = [window.face3d for window in self.windows]
        nearby_spaces = self.get_nearby_spaces(OpeningElement.window)

        moved_faces = []
        for i in range(len(simplified_faces)):
            # get the nearby space
            if len(nearby_spaces[i]) == 1:
                polyface = nearby_spaces[i][0].polyface3d
            elif len(nearby_spaces[i]) == 2:
                polyface = nearby_spaces[i][random.randint(0, 1)].polyface3d
            else:
                print(f'Window {self.windows[i].guid} did not export.')
                continue

            # Find the face to move the nearby face
            window_face = simplified_faces[i]
            parallel_faces = [
                face for face in polyface.faces if not
                window_face.plane.intersect_plane(face.plane)]
            nearby_face = sorted(
                [face for face in parallel_faces],
                key=lambda x: x.plane.closest_point(window_face.center)
                .distance_to_point(window_face.center))[0]

            # move the face
            moved_faces.append(move_face(window_face, nearby_face))

        return moved_faces

    def project_doors_on_nearby_space(self) -> List[Face3D]:
        """Move the doors to the nearby spaces."""

        simplified_faces = [door.face3d for door in self.doors]
        nearby_spaces = self.get_nearby_spaces(OpeningElement.door)

        moved_faces = []
        for i in range(len(simplified_faces)):

            door_face = simplified_faces[i]

            # Find the face to move the nearby face
            if len(nearby_spaces[i]) == 1:
                polyface = nearby_spaces[i][0].polyface3d
                nearby_faces = sorted(
                    [face for face in polyface.faces],
                    key=lambda x: x.plane.closest_point(door_face.center).
                    distance_to_point(door_face.center))
                for face in nearby_faces:
                    line = LineSegment3D.from_end_points(
                        door_face.center, face.plane.closest_point(door_face.center))
                    if face.intersect_line_ray(Ray3D(door_face.center, line.v)):
                        nearby_face = face
                        break

            elif len(nearby_spaces[i]) == 2:
                spaces = nearby_spaces[i]
                nearby_faces = []
                for space in spaces:
                    nearby_faces.append(sorted(
                        [face for face in space.polyface3d.faces],
                        key=lambda x: x.plane.closest_point(door_face.center)
                        .distance_to_point(door_face.center))[0])
                nearby_face = sorted(nearby_faces, key=lambda x: x.area)[-1]

            else:
                print(f'Door {self.doors[i].guid} did not export')
                continue

            # move the face
            moved_faces.append(move_face(door_face, nearby_face))

        return moved_faces

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

        rooms = [HBRoom.from_polyface3d(clean_and_id_string(
            'Room'), space.polyface3d) for space in self.spaces]

        apertures = [HBAperture(clean_and_id_string('Aperture'), face)
                     for face in self.project_windows_on_nearby_space()]

        doors = [HBDoor(clean_and_id_string('door'), face)
                 for face in self.project_doors_on_nearby_space()]

        shades = [HBShade(clean_and_id_string('Shade'), face)
                  for slab in self.slabs for face in slab.face3ds]

        hb_model = HBModel('Model', rooms=rooms, orphaned_apertures=apertures,
                           orphaned_doors=doors, orphaned_shades=shades)

        if not file_name:
            file_name = self.ifc_file_path.stem

        path = hb_model.to_hbjson(name=file_name, folder=target_folder)

        return path

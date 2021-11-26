"""
Import an IFC file and turn it into a Honeybee model.
Currently, only supporting IFC files with IFC2x3 schema.
"""
import pathlib
import multiprocessing
from enum import Enum
from typing import List

import ifcopenshell
from ifcopenshell.util import element
from ifcopenshell.util.unit import calculate_unit_scale
from ifcopenshell.util.placement import get_local_placement
from ifcopenshell.util.selector import Selector

from honeybee.model import Model as HBModel

from .wall import Wall
from .window import Window
from .door import Door
from .slab import Slab
from .shade import Shade
from .space import Space


class IfcEntity(Enum):
    """An enumeration of IFC entities that can be imported."""

    window = 'IfcWindow'
    door = 'IfcDoor'
    slab = 'IfcSlab'
    shade = 'IfcColumn'
    space = 'IfcSpace'


class Model:
    """Honeybee-IFC model.

    Args:
        ifc_file_path: A string. The path to the IFC file.
    """

    def __init__(self, ifc_file_path: str, elements: List[IfcEntity] = None,
                 extract_walls: bool = False) -> None:
        self.ifc_file_path = self._validate_path(ifc_file_path)
        self.ifc_file = ifcopenshell.open(self.ifc_file_path)
        self.settings = self._ifc_settings()
        self.unit_factor = calculate_unit_scale(self.ifc_file)
        self.elements = self._elements(elements)
        self.spaces = []
        self.doors = []
        self.windows = []
        self.slabs = []
        self.walls = []
        self.shades = []
        self.extract_walls = extract_walls
        if self.extract_walls:
            self._extract_walls()
        if not self.elements:
            self._extract_elements()

    @staticmethod
    def _elements(elements):
        if elements:
            return (item.value for item in elements)
        return ()

    @staticmethod
    def _validate_path(path: str) -> pathlib.Path:
        """Validate path."""
        path = pathlib.Path(path)
        if not path.exists():
            raise ValueError(f'Path {path} does not exist.')
        return path

    @staticmethod
    def _ifc_settings() -> ifcopenshell.geom.settings:
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

        # TODO: Make the exceptions specific at some point.
        if iterator.initialize():
            while iterator.next():
                shape = iterator.get()
                element = self.ifc_file.by_guid(shape.guid)

                if element.is_a() == 'IfcWindow':
                    try:
                        self.windows.append(Window(element))
                    except Exception as e:
                        print("Window", e, element.GlobalId)

                if element.is_a() == 'IfcDoor':
                    try:
                        self.doors.append(Door(element))
                    except Exception as e:
                        print("Door", e, element.GlobalId)

                elif element.is_a() == 'IfcSlab':
                    try:
                        self.slabs.append(
                            Slab(element, element.PredefinedType))
                    except Exception as e:
                        print("Slab", e, element.GlobalId)

                elif element.is_a() == 'IfcColumn':
                    try:
                        self.shades.append(
                            Shade(element))
                    except Exception as e:
                        print("Shade", e, element.GlobalId)

                elif element.is_a() == 'IfcSpace':
                    try:
                        self.spaces.append(Space(element))
                    except Exception as e:
                        print("Space", e, element.GlobalId)

    def _extract_walls(self) -> None:
        """Extract IfcWall elements from the IFC file."""
        # Don't use BREP data here. Which will give original trinagulated meshes.
        # Since for walls we're not looking for BREP data, we're extracting them
        # separately
        selector = Selector()
        for element in selector.parse(self.ifc_file, '.IfcWall | .IfcWallStandardCase'):
            if len(element.IsDecomposedBy) > 0:
                for part in element.IsDecomposedBy[0].RelatedObjects:
                    self.walls.append(Wall(part))
            else:
                self.walls.append(Wall(element))

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

        print("Starting Honeybee translation! \n")
        faces, apertures, doors, shades, grids = [], [], [], [], []

        if self.extract_walls:
            for wall in self.walls:
                faces.extend(wall.to_honeybee())
            print("walls done")

        if IfcEntity.window.value in self.elements:
            apertures = [window.to_honeybee() for window in self.windows]
            print("apertures done")

        if IfcEntity.door.value in self.elements:
            doors = [door.to_honeybee() for door in self.doors]
            print("doors done")

        if IfcEntity.slab.value in self.elements:
            for slab in self.slabs:
                faces.extend(slab.to_honeybee())
            print("slabs done")

        if IfcEntity.shade.value in self.elements:
            for shade in self.shades:
                shades.extend(shade.to_honeybee())
            print("shade done")

        if IfcEntity.space.value in self.elements:
            for space in self.spaces:
                grids.append(space.get_grids(size=0.3))
            print("grids done")

        hb_model = HBModel('Model', orphaned_faces=faces,
                           orphaned_apertures=apertures, orphaned_doors=doors,
                           orphaned_shades=shades)

        # hb_model.properties.radiance.add_sensor_grids(grids)

        if not file_name:
            file_name = self.ifc_file_path.stem

        path = hb_model.to_hbjson(name=file_name, folder=target_folder)

        return path

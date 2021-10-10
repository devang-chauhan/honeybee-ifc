import ifcopenshell
import multiprocessing
import pathlib

from typing import List, Tuple
from ifcopenshell.entity_instance import entity_instance as Element
from ifcopenshell.file import file as File
from honeybee.shade import Shade
from honeybee.room import Room
from honeybee.model import Model
from honeybee.typing import clean_and_id_string

from .geometry import get_polyface3d
from .apertures import get_projected_windows, get_projected_doors
from .helper import duration
from .close_gap import get_gap_closed_rooms


def get_ifc_settings() -> ifcopenshell.geom.settings:
    """Get ifc geometry settings."""
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    settings.set(settings.USE_BREP_DATA, True)
    return settings


def extract_elements(ifc_file: File,
                     settings: ifcopenshell.geom.settings) -> Tuple[
                         List[Element], List[Element], List[Element], List[Element]]:
    """Extract elements from an IFC file."""
    spaces, windows, doors, slabs = [], [], [], []

    elements = ('IfcSpace', 'IfcWindow', 'IfcDoor', 'IfcSlab')

    iterator = ifcopenshell.geom.iterator(
        settings, ifc_file, multiprocessing.cpu_count(), include=elements)

    if iterator.initialize():
        while iterator.next():
            shape = iterator.get()
            element = ifc_file.by_guid(shape.guid)

            if element.is_a() == 'IfcSpace':
                spaces.append(element)

            elif element.is_a() == 'IfcWindow':
                windows.append(element)

            elif element.is_a() == 'IfcDoor':
                doors.append(element)

            elif element.is_a() == 'IfcSlab':
                slabs.append(element)

    return spaces, windows, doors, slabs


def get_rooms(elements: List[Element], settings: ifcopenshell.geom.settings) -> List[Room]:
    """Get honeybee rooms from IfcSpace elements."""
    return [Room.from_polyface3d('Room_'+str(count),
                                 get_polyface3d(element, settings))for count, element in enumerate(elements)]


def get_shades(elements: List[Element], settings: ifcopenshell.geom.settings) -> List[Shade]:
    """Get honeybee shades from Ifc elements."""
    return [Shade(clean_and_id_string('Shade'), face)
            for element in elements for face in get_polyface3d(element, settings).faces]


@duration
def export_hbjson(ifc_file_path: pathlib.Path, folder: pathlib.Path = None) -> None:
    """Export HBJSON from IFC"""

    file_name = ifc_file_path.stem
    ifc_file = ifcopenshell.open(ifc_file_path)

    hb_rooms, hb_apertures, hb_doors, hb_shades, hb_orphaned_faces = [], [], [], [], []

    # Elements extracted from IFC
    spaces, windows, doors, slabs = extract_elements(ifc_file, get_ifc_settings())

    hb_apertures = get_projected_windows(windows, get_ifc_settings(), ifc_file)
    hb_doors = get_projected_doors(doors, get_ifc_settings(), ifc_file)
    hb_rooms = get_rooms(spaces, get_ifc_settings())
    hb_shades = get_shades(slabs, get_ifc_settings())

    # Export model
    hb_model = Model('House', rooms=hb_rooms, orphaned_faces=hb_orphaned_faces,
                     orphaned_apertures=hb_apertures, orphaned_doors=hb_doors,
                     orphaned_shades=hb_shades)
    hb_model.to_hbjson(name=file_name, folder=folder)

    # Export gap closed rooms for zones shell
    gap_closed_rooms = get_gap_closed_rooms(hb_rooms)
    shell_model = Model('Shell', rooms=gap_closed_rooms)
    shell_model.to_hbjson(name=file_name + '_gap_closed_zones', folder=folder)

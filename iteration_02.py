import ifcopenshell
import ifcopenshell.geom
import multiprocessing
from typing import List, Tuple, Dict, Union
from enum import Enum
from ladybug_geometry.geometry3d import Face3D, Point3D, Polyface3D
from honeybee.face import Face
from honeybee.typing import clean_and_id_string
from honeybee.model import Model
from honeybee.room import Room
from honeybee.aperture import Aperture
from honeybee.shade import Shade

ifc_file = ifcopenshell.open("D:\simulation\ifc\FamilyHouse_AC13.ifc")

hb_faces = []
hb_rooms = []
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)


class IFCEntity(Enum):
    room = 'IfcSpace'
    aperture = 'IfcOpeningElement'
    door = 'IfcDoor'
    window = 'IfcWindow'


def create_face_from_center_point(center: Point3D, width: float, height: float) -> Face3D:
    """Create a face from a center point and width and height."""
    return Face3D(
        [
            Point3D(center.x - width / 2, center.y - height / 2, center.z),
            Point3D(center.x + width / 2, center.y - height / 2, center.z),
            Point3D(center.x + width / 2, center.y + height / 2, center.z),
            Point3D(center.x - width / 2, center.y + height / 2, center.z)
        ]
    )


def extract_hb_objects() -> list:
    """Extract geometry from IFC and turn it into Honeybee objects.

    Returns:
        A list of Honeybee objects.
    """
    rooms, apertures, doors = [], [], []

    iterator = ifcopenshell.geom.iterator(
        settings, ifc_file, multiprocessing.cpu_count())
    if iterator.initialize():
        while iterator.next():
            shape = iterator.get()
            element = ifc_file.by_guid(shape.guid)

            if element.is_a() not in ('IfcSpace', 'IfcWindow', 'IfcDoor'):
                continue
            else:
                faces = shape.geometry.faces
                verts = shape.geometry.verts
                # Point3Ds
                point3ds = [Point3D(verts[i], verts[i + 1], verts[i + 2])
                            for i in range(0, len(verts), 3)]
                # Face3Ds
                face3ds = [Face3D([point3ds[faces[i]], point3ds[faces[i + 1]], point3ds[faces[i + 2]]])
                           for i in range(0, len(faces), 3)]
                # Polyface3D
                polyface3d = Polyface3D.from_faces(face3ds, tolerance=0.01)
                polyface3d.merge_overlapping_edges(tolerance=0.01, angle_tolerance=0)

                # Honeybee Element assignment
                if element.is_a() == 'IfcSpace':
                    room = Room.from_polyface3d(
                        clean_and_id_string('Room'), polyface3d)
                    rooms.append(room)
                elif element.is_a() == 'IfcWindow':
                    room = Room.from_polyface3d(
                        clean_and_id_string('Window'), polyface3d)
                    rooms.append(room)
                    print(element.OverallHeight, element.OverallWidth)

                elif element.is_a() == 'IfcDoor':
                    room = Room.from_polyface3d(
                        clean_and_id_string('Door'), polyface3d)
                    rooms.append(room)

    return rooms


# rooms = extract_hb_objects(IFCEntity.room, "Room", Room)
hb_objects = extract_hb_objects()

hb_model = Model('House', rooms=hb_objects)
hb_model.to_hbjson(name='ifc_apertures',)

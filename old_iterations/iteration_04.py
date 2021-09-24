import ifcopenshell
import ifcopenshell.geom
import multiprocessing


from typing import List, Tuple, Dict, Union
from enum import Enum
from ladybug_geometry.geometry3d import Face3D, Point3D, Polyface3D, LineSegment3D, Plane
from ladybug_geometry.intersection3d import intersect_line3d_plane
from honeybee.face import Face
from honeybee.typing import clean_and_id_string, clean_string
from honeybee.model import Model
from honeybee.room import Room
from honeybee.aperture import Aperture
from honeybee.shade import Shade
from honeybee.facetype import Wall

file_1 = "D:\simulation\ifc\FamilyHouse_AC13.ifc"
file_2 = "D:\simulation\ifc\Single family house.IFC"
file_3 = "D:\simulation\ifc\SmallOffice_d_IFC2x3.ifc"

ifc_file = ifcopenshell.open(file_3)

hb_faces = []
hb_rooms = []
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)


class IFCEntity(Enum):
    room = 'IfcSpace'
    aperture = 'IfcOpeningElement'
    door = 'IfcDoor'
    window = 'IfcWindow'


def extract_hb_objects() -> list:
    """Extract geometry from IFC and turn it into Honeybee objects.

    Returns:
        A list of Honeybee objects.
    """
    rooms, opening_rooms = [], []

    iterator = ifcopenshell.geom.iterator(
        settings, ifc_file, multiprocessing.cpu_count())
    if iterator.initialize():
        while iterator.next():
            shape = iterator.get()
            element = ifc_file.by_guid(shape.guid)
            if element.is_a() not in ('IfcSpace', 'IfcWindow', 'IfcDoor', 'IfcOpeningElement'):
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

                if element.is_a() == 'IfcSpace':

                    polyface3d = Polyface3D.from_faces(face3ds, tolerance=0.01)
                    polyface3d.merge_overlapping_edges(tolerance=0.01, angle_tolerance=0)
                    room = Room.from_polyface3d(clean_and_id_string('Room'), polyface3d)
                    rooms.append(room)

                elif element.is_a() == 'IfcOpeningElement':
                    polyface3d = Polyface3D.from_faces(face3ds, tolerance=0.01)
                    polyface3d.merge_overlapping_edges(tolerance=0.01, angle_tolerance=0)
                    room = Room.from_polyface3d(
                        clean_and_id_string('Opening'), polyface3d)
                    opening_rooms.append(room)

    return rooms, opening_rooms


rooms, opening_rooms = extract_hb_objects()

# opening room : rooms that intersects
opening_room_dict = {opening_room: [room for room in rooms if Polyface3D.overlapping_bounding_boxes(
    room.geometry, opening_room.geometry, tolerance=0.01)] for opening_room in opening_rooms}


def assign_aperture(faceds):
    return [Aperture(clean_and_id_string('Aperture'), face) for face in faceds]


apertures = []
for key, value in opening_room_dict.items():
    # it is a door
    if len(value) > 1:
        continue
    # It is a window
    else:
        room_faces = value[0].geometry.faces
        opening_faces = key.geometry.faces
        for opening_face in opening_faces:
            plane = opening_face.plane
            for room_face in room_faces:
                cp = plane.closest_point(room_face.center)
                print(cp.distance_to_point(room_face.center))
                if cp.distance_to_point(room_face.center) > 0.01:
                    continue
                else:
                    apertures.append(
                        Aperture(clean_and_id_string('Aperture'), opening_face))

hb_model = Model('House', rooms=rooms, orphaned_apertures=apertures)
hb_model.to_hbjson(name='ifc_apertures',)

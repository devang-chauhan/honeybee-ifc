import ifcopenshell
import ifcopenshell.geom
import multiprocessing
from ladybug_geometry.geometry3d.face import Face3D, Point3D
from honeybee.face import Face
from honeybee.typing import clean_and_id_string
from honeybee.model import Model
from honeybee.room import Room

ifc_file = ifcopenshell.open("D:\simulation\ifc\FamilyHouse_AC13.ifc")

hb_faces = []
hb_rooms = []
settings = ifcopenshell.geom.settings()
settings.set(settings.USE_WORLD_COORDS, True)
iterator = ifcopenshell.geom.iterator(settings, ifc_file, multiprocessing.cpu_count())
if iterator.initialize():
    while iterator.next():
        shape = iterator.get()
        element = ifc_file.by_guid(shape.guid)
        if element.is_a() == 'IfcSpace':
            print(element.id)
            faces = shape.geometry.faces
            verts = shape.geometry.verts
            point3ds = [Point3D(verts[i], verts[i + 1], verts[i + 2])
                        for i in range(0, len(verts), 3)]
            faces = [Face(clean_and_id_string('Room'),
                          Face3D([point3ds[faces[i]], point3ds[faces[i + 1]], point3ds[faces[i + 2]]]))
                     for i in range(0, len(faces), 3)]
            room = Room(clean_and_id_string('Room'), faces)
            hb_rooms.append(room)

print(len(hb_faces))
hb_model = Model('House', rooms=hb_rooms)
hb_model.to_hbjson(name='ifc_rooms',)

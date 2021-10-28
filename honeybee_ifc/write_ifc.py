import pathlib
from honeybee_ifc.to_hbjson import export_model, export_close_gapped_zones, extract_elements,\
    get_ifc_settings


from honeybee_ifc.ifc import Ifc, ElementType
from honeybee.model import Model

file_1 = pathlib.Path("D:\simulation\ifc\FamilyHouse_AC13.ifc")
file_2 = pathlib.Path("D:\simulation\ifc\SmallOffice_d_IFC2x3.ifc")
file_3 = pathlib.Path("D:\simulation\ifc\BEM_Example_ArchiCAD.ifc")

spaces, walls, windows, doors, slabs = extract_elements(file_2, get_ifc_settings())

# export_model(file_2, spaces, walls, windows, doors, slabs)
# export_close_gapped_zones(file_2, spaces, get_ifc_settings())

#################################################################
file_path = r"C:\Users\devan\simulation\SmallOffice_d_IFC2x3.hbjson"

model = Model.from_hbjson(file_path)


def point3d_to_tuple(points):
    return [(point.x, point.y, point.z) for point in points]


ifc = Ifc()
for aperture in model.apertures:
    points = point3d_to_tuple(aperture.vertices)
    ifc.add_ifc_elements(ElementType.window, [points])

for door in model.doors:
    points = point3d_to_tuple(door.vertices)
    ifc.add_ifc_elements(ElementType.door, [points])

for shade in model.orphaned_shades:
    points = point3d_to_tuple(shade.vertices)
    ifc.add_ifc_elements(ElementType.slab, [points])

for room in model.rooms:
    if 'Room' in room.display_name:
        points_list = [point3d_to_tuple(face.vertices) for face in room.faces]
        ifc.add_ifc_elements(ElementType.space, points_list)
    else:
        print(room.display_name)
        points_list = [point3d_to_tuple(face.vertices) for face in room.faces]
        ifc.add_ifc_elements(ElementType.wall, points_list)

ifc.write_ifc()

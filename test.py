import ifcopenshell
import ifcopenshell.geom


ifc = ifcopenshell.open("FamilyHouse_AC13.ifc")
columns = ifc.by_type("IfcColumn")
item = columns[0]

settings = ifcopenshell.geom.settings()
settings.set(settings.USE_BREP_DATA, True)
settings.set(settings.USE_WORLD_COORDS, True)
ifc_shape = ifcopenshell.geom.create_shape(settings, item)
ifc_shape = ifc_shape.geometry.brep_data
print(item.id)
with open("geometry", "w") as file:
    file.write(ifc_shape)

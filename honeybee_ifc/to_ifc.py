"""Write .ifc files."""

import uuid
import time
import tempfile
import ifcopenshell

O = 0., 0., 0.
X = 1., 0., 0.
Y = 0., 1., 0.
Z = 0., 0., 1.


def create_guid():
    """Create a unique Guid."""
    return ifcopenshell.guid.compress(uuid.uuid1().hex)


def template_variables():
    """Create variables to put into the template."""

    file_name = "hello_wall.ifc"
    time_stamp = time.time()
    time_now = time.gmtime(time_stamp)
    time_string = f'{time_now[0]}-{time_now[1]}-{time_now[2]}T{time_now[3]}:'\
        f'{time_now[4]}:{time_now[5]}'
    creator = "honeybee-ifc"
    organization = "Ladybug Tools"
    application = "IfcOpenShell"
    application_version = "0.0.0"
    project_global_id = create_guid()
    project_name = "Hello Wall"

    return file_name, time_string, creator, organization, application,\
        application_version, time_stamp, project_global_id, project_name


def template_ifc(file_name, time_string, creator, organization, application,
                 application_version, time_stamp, project_global_id, project_name):
    """Write a template .ifc file."""

    template = f"""
    ISO-10303-21;
    HEADER;
    FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
    FILE_NAME('{file_name}','{time_string}',('{creator}'),('{organization}'),\
        '{application}','{application}','');
    FILE_SCHEMA(('IFC2X3'));
    ENDSEC;
    DATA;
    #1=IFCPERSON($,$,'{creator}',$,$,$,$,$);
    #2=IFCORGANIZATION($,'{organization}',$,$,$);
    #3=IFCPERSONANDORGANIZATION(#1,#2,$);
    #4=IFCAPPLICATION(#2,{application_version},'{application}','');
    #5=IFCOWNERHISTORY(#3,#4,$,.ADDED.,$,#3,#4,{time_stamp});
    #6=IFCDIRECTION((1.,0.,0.));
    #7=IFCDIRECTION((0.,0.,1.));
    #8=IFCCARTESIANPOINT((0.,0.,0.));
    #9=IFCAXIS2PLACEMENT3D(#8,#7,#6);
    #10=IFCDIRECTION((0.,1.,0.));
    #11=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#9,#10);
    #12=IFCDIMENSIONALEXPONENTS(0,0,0,0,0,0,0);
    #13=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
    #14=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
    #15=IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
    #16=IFCSIUNIT(*,.PLANEANGLEUNIT.,$,.RADIAN.);
    #17=IFCMEASUREWITHUNIT(IFCPLANEANGLEMEASURE(0.017453292519943295),#16);
    #18=IFCCONVERSIONBASEDUNIT(#12,.PLANEANGLEUNIT.,'DEGREE',#17);
    #19=IFCUNITASSIGNMENT((#13,#14,#15,#18));
    #20=IFCPROJECT('{project_global_id}',#5,'{project_name}',$,$,$,$,(#11),#19);
    ENDSEC;
    END-ISO-10303-21;
    """

    # convert the text into binary
    binary = template.encode('utf-8')
    temp_filename = tempfile.mkstemp(suffix=".ifc")[1]
    with open(temp_filename, "wb") as f:
        f.write(binary)

    ifcfile = ifcopenshell.open(temp_filename)

    return ifcfile


def create_ifcaxis2placement(ifcfile, point=O, dir1=Z, dir2=X):
    point = ifcfile.createIfcCartesianPoint(point)
    dir1 = ifcfile.createIfcDirection(dir1)
    dir2 = ifcfile.createIfcDirection(dir2)
    axis2placement = ifcfile.createIfcAxis2Placement3D(point, dir1, dir2)
    return axis2placement


def create_ifclocalplacement(ifcfile, point=O, dir1=Z, dir2=X, relative_to=None):
    axis2placement = create_ifcaxis2placement(ifcfile, point, dir1, dir2)
    ifclocalplacement2 = ifcfile.createIfcLocalPlacement(relative_to, axis2placement)
    return ifclocalplacement2


def create_ifcpolyline(ifcfile, point_list):
    ifcpts = []
    for point in point_list:
        point = ifcfile.createIfcCartesianPoint(point)
        ifcpts.append(point)
    polyline = ifcfile.createIfcPolyLine(ifcpts)
    return polyline


def create_cartesian_point(ifc_file, points):
    return [ifc_file.createIfcCartesianPoint(point) for point in points]


def create_polyloop(ifc_file, ifc_points):
    loop = ifc_file.createIfcPolyLoop(ifc_points)
    return loop


def create_outer_boundary(ifc_file, ifc_loop):
    return ifc_file.createIfcFaceOuterBound(ifc_loop, True)


def create_face(ifc_file, ifc_outer_boundary):
    return ifc_file.createIfcFace([ifc_outer_boundary])


def create_faceted_brep(ifc_file, ifc_faces):
    return ifc_file.createIfcFacetedBrep(ifc_file.createIfcClosedShell(ifc_faces))


ifcfile = template_ifc(*template_variables())
points = [(0.0, 0.0, 0.0), (5.0, 0.0, 0.0), (5.0, 0.0, 5.0), (0.0, 0.0, 5.0)]

ifc_points = create_cartesian_point(ifcfile, points)
ifc_loop = create_polyloop(ifcfile, ifc_points)
ifc_outer_boundary = create_outer_boundary(ifcfile, ifc_loop)
ifc_face = create_face(ifcfile, ifc_outer_boundary)
ifc_brep = create_faceted_brep(ifcfile, [ifc_face])


##################################################

owner_history = ifcfile.by_type("IfcOwnerHistory")[0]
project = ifcfile.by_type("IfcProject")[0]
context = ifcfile.by_type("IfcGeometricRepresentationContext")[0]

# IFC hierarchy creation
site_placement = create_ifclocalplacement(ifcfile)
site = ifcfile.createIfcSite(create_guid(), owner_history, "Site", None,
                             None, site_placement, None, None, "ELEMENT", None, None, None, None, None)

building_placement = create_ifclocalplacement(ifcfile, relative_to=site_placement)
building = ifcfile.createIfcBuilding(create_guid(
), owner_history, 'Building', None, None, building_placement, None, None, "ELEMENT", None, None, None)

storey_placement = create_ifclocalplacement(ifcfile, relative_to=building_placement)
elevation = 0.0
building_storey = ifcfile.createIfcBuildingStorey(create_guid(
), owner_history, 'Storey', None, None, storey_placement, None, None, "ELEMENT", elevation)

container_storey = ifcfile.createIfcRelAggregates(
    create_guid(), owner_history, "Building Container", None, building, [building_storey])
container_site = ifcfile.createIfcRelAggregates(
    create_guid(), owner_history, "Site Container", None, site, [building])
container_project = ifcfile.createIfcRelAggregates(
    create_guid(), owner_history, "Project Container", None, project, [site])

# Wall creation: Define the wall shape as a polyline axis and an extruded area solid
wall_placement = create_ifclocalplacement(ifcfile, relative_to=storey_placement)
polyline = create_ifcpolyline(ifcfile, [(0.0, 0.0, 0.0), (5.0, 0.0, 0.0)])
axis_representation = ifcfile.createIfcShapeRepresentation(
    context, "Axis", "Curve2D", [polyline])

body_representation = ifcfile.createIfcShapeRepresentation(
    context, "Body", "Brep", [ifc_brep])

product_shape = ifcfile.createIfcProductDefinitionShape(
    None, None, [axis_representation, body_representation])

wall = ifcfile.createIfcWallStandardCase(create_guid(
), owner_history, "Wall", "An awesome wall", None, wall_placement, product_shape, None)

# Define and associate the wall material
material = ifcfile.createIfcMaterial("wall material")
material_layer = ifcfile.createIfcMaterialLayer(material, 0.2, None)
material_layer_set = ifcfile.createIfcMaterialLayerSet([material_layer], None)
material_layer_set_usage = ifcfile.createIfcMaterialLayerSetUsage(
    material_layer_set, "AXIS2", "POSITIVE", -0.1)
ifcfile.createIfcRelAssociatesMaterial(create_guid(), owner_history, RelatedObjects=[
                                       wall], RelatingMaterial=material_layer_set_usage)

# Create and assign property set
property_values = [
    ifcfile.createIfcPropertySingleValue("Reference", "Reference", ifcfile.create_entity(
        "IfcText", "Describe the Reference"), None),
    ifcfile.createIfcPropertySingleValue(
        "IsExternal", "IsExternal", ifcfile.create_entity("IfcBoolean", True), None),
    ifcfile.createIfcPropertySingleValue(
        "ThermalTransmittance", "ThermalTransmittance", ifcfile.create_entity("IfcReal", 2.569), None),
    ifcfile.createIfcPropertySingleValue(
        "IntValue", "IntValue", ifcfile.create_entity("IfcInteger", 2), None)
]
property_set = ifcfile.createIfcPropertySet(
    create_guid(), owner_history, "Pset_WallCommon", None, property_values)
ifcfile.createIfcRelDefinesByProperties(
    create_guid(), owner_history, None, None, [wall], property_set)


ifcfile.write("hello_wall.ifc")

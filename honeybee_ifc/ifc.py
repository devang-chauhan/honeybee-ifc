"""Ifc object and methods to add elements to the class."""

import uuid
import time
import tempfile
import pathlib
from enum import Enum
from typing import List, Tuple

import ifcopenshell
from ifcopenshell.entity_instance import entity_instance as Element
from ifcopenshell.api.project.append_asset import Usecase
from .to_hbjson import get_ifc_settings


class ElementType(Enum):
    window = 'window'
    door = 'door'
    slab = 'slab'
    space = 'space'
    wall = 'wall'


class Ifc:
    """Instantiate an IFC object.

    Args:
        file_name: Name of the file as a string. Defaults to 'model'.
        project_name: Name of the project as a string. Defaults to 'project'.
    """

    def __init__(self, file_name: str = 'model', project_name: str = 'project') -> None:
        self.file_name = file_name + '.ifc'
        self.project_name = project_name
        self.time_stamp = time.time()
        self.time_now = time.gmtime(self.time_stamp)
        self.time_string = f'{self.time_now[0]}-{self.time_now[1]}-{self.time_now[2]}'\
            f'T{self.time_now[3]}:{self.time_now[4]}:{self.time_now[5]}'
        self.creator = "honeybee-ifc"
        self.organization = "Ladybug Tools"
        self.application = "IfcOpenShell"
        self.application_version = " "
        self.project_global_id = self.create_guid()
        self.template = f"""
        ISO-10303-21;
        HEADER;
        FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
        FILE_NAME('{self.file_name}','{self.time_string}',('{self.creator}'),\
            ('{self.organization}'),'{self.application}','{self.application}','');
        FILE_SCHEMA(('IFC2X3'));
        ENDSEC;
        DATA;
        #1=IFCPERSON($,$,'{self.creator}',$,$,$,$,$);
        #2=IFCORGANIZATION($,'{self.organization}',$,$,$);
        #3=IFCPERSONANDORGANIZATION(#1,#2,$);
        #4=IFCAPPLICATION(#2,{self.application_version},'{self.application}','');
        #5=IFCOWNERHISTORY(#3,#4,$,.ADDED.,$,#3,#4,{self.time_stamp});
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
        #20=IFCPROJECT('{self.project_global_id}',#5,'{self.project_name}',$,$,$,$,(#11),#19);
        ENDSEC;
        END-ISO-10303-21;
        """
        self.byte_template = self.template.encode('utf-8')
        self.ifc_file = self.create_ifc_file()
        self.origin = 0.0, 0.0, 0.0
        self.x_dir = 1.0, 0.0, 0.0
        self.y_dir = 0.0, 1.0, 0.0
        self.z_dir = 0.0, 0.0, 1.0
        self.owner_history = self.ifc_file.by_type("IfcOwnerHistory")[0]
        self.project = self.ifc_file.by_type("IfcProject")[0]
        self.context = self.ifc_file.by_type("IfcGeometricRepresentationContext")[0]

        # IFC hierarchy creation
        self.site_placement = self.create_ifclocalplacement()
        self.site = self.ifc_file.createIfcSite(
            self.create_guid(), self.owner_history, "Site", None,
            None, self.site_placement, None, None, "ELEMENT", None, None, None, None,
            None)

        self.building_placement = self.create_ifclocalplacement(
            relative_to=self.site_placement)
        self.building = self.ifc_file.createIfcBuilding(
            self.create_guid(), self.owner_history, 'Building', None, None,
            self.building_placement, None, None, "ELEMENT", None, None, None)

        self.storey_placement = self.create_ifclocalplacement(
            relative_to=self.building_placement)
        self.elevation = 0.0
        self.building_storey = self.ifc_file.createIfcBuildingStorey(
            self.create_guid(), self.owner_history, 'Storey', None, None,
            self.storey_placement, None, None, "ELEMENT", self.elevation)

        self.container_storey = self.ifc_file.createIfcRelAggregates(
            self.create_guid(), self.owner_history, "Building Container", None,
            self.building, [self.building_storey])
        self.container_site = self.ifc_file.createIfcRelAggregates(
            self.create_guid(), self.owner_history, "Site Container", None, self.site,
            [self.building])
        self.container_project = self.ifc_file.createIfcRelAggregates(
            self.create_guid(), self.owner_history, "Project Container", None,
            self.project, [self.site])

    @staticmethod
    def create_guid() -> str:
        """Get a unique Guid as a string."""
        return ifcopenshell.guid.compress(uuid.uuid1().hex)

    def create_ifc_file(self) -> ifcopenshell.file:
        """Get an ifc file object."""
        temp_filename = tempfile.mkstemp(suffix=".ifc")[1]
        with open(temp_filename, "wb") as f:
            f.write(self.byte_template)
        ifc_file = ifcopenshell.open(temp_filename)
        return ifc_file

    def write_ifc(self, target_path: str = None) -> str:
        """Write an ifc file to disk.

        Args:
            target_path: Valid path to the folder where the file will be written.

        Returns:
            Path to the written ifc file.
        """
        if target_path:
            path = pathlib.Path(target_path)
            assert path.exists(), f"{target_path} does not exist."
            path = str(path.joinpath(self.file_name))
        else:
            path = self.file_name

        self.ifc_file.write(path)

        return path

    def create_ifcaxis2placement(self) -> Element:
        """Create ifc axis placement element."""

        point = self.ifc_file.createIfcCartesianPoint(self.origin)
        dir1 = self.ifc_file.createIfcDirection(self.z_dir)
        dir2 = self.ifc_file.createIfcDirection(self.x_dir)
        axis2placement = self.ifc_file.createIfcAxis2Placement3D(point, dir1, dir2)

        return axis2placement

    def create_ifclocalplacement(self, relative_to: Element = None) -> Element:
        """Create ifc local placement element.

        Args:
            relative_to: Ifc object to which the location is relative.

        Returns:
            An ifc local placement element.
        """

        axis2placement = self.create_ifcaxis2placement()
        ifclocalplacement2 = self.ifc_file.createIfcLocalPlacement(
            relative_to, axis2placement)

        return ifclocalplacement2

    def create_ifc_brep(
            self, points_lists: List[List[Tuple[float, float, float]]]) -> Element:
        """Create ifc face brep.

        Args:
            point_lists: A list of list of points as tuple of (x,y,z) coordinates.

        Returns:
            An ifc face brep element.
        """

        ifc_faces = []
        for points in points_lists:
            ifc_points = [self.ifc_file.createIfcCartesianPoint(
                point) for point in points]
            ifc_loop = self.ifc_file.createIfcPolyLoop(ifc_points)
            ifc_outer_boundary = self.ifc_file.createIfcFaceOuterBound(ifc_loop, True)
            ifc_face = self.ifc_file.createIfcFace([ifc_outer_boundary])
            ifc_faces.append(ifc_face)

        ifc_brep = self.ifc_file.createIfcFacetedBrep(
            self.ifc_file.createIfcClosedShell(ifc_faces))

        return ifc_brep

    def create_shape(self, ifc_element: Element) -> Tuple[Element, Element]:
        """Get placement and shape for an ifc element."""

        placement = self.create_ifclocalplacement(
            relative_to=self.storey_placement)

        representation = self.ifc_file.createIfcShapeRepresentation(
            self.context, "Body", "Brep", [ifc_element])

        shape = self.ifc_file.createIfcProductDefinitionShape(
            None, None, [representation])

        return placement, shape

    def add_ifc_elements(
            self, element_type: ElementType,
            points_lists: List[List[Tuple[float, float, float]]]) -> None:
        """Add elements to an ifc file object.

        Args:
            element_type: Type of the element to be added.
            points_lists: A list of list of points as tuple of (x,y,z) coordinates.
        """

        assert isinstance(
            element_type, ElementType), "Element type must be of type ElementType."
        assert isinstance(points_lists[0], list), 'points_lists must be a list of lists'\
            ' where each list has vertices of a face.'

        ifc_brep = self.create_ifc_brep(points_lists)
        placement, shape = self.create_shape(ifc_brep)

        if element_type.value == 'space':
            space = self.ifc_file.createIfcSpace(
                self.create_guid(), self.owner_history, "Space",
                "Zone", None, placement, shape, None, 'ELEMENT')

            self.ifc_file.createIfcRelContainedInSpatialStructure(self.create_guid(
            ), self.owner_history, "Building Storey Container", None, [space], self.building_storey)

        elif element_type.value == 'window':
            window = self.ifc_file.createIfcWindow(
                self.create_guid(), self.owner_history, "Window",
                "Window", None, placement, shape, None, None)

            self.ifc_file.createIfcRelContainedInSpatialStructure(self.create_guid(
            ), self.owner_history, "Building Storey Container", None, [window], self.building_storey)

        elif element_type.value == 'door':
            door = self.ifc_file.createIfcDoor(
                self.create_guid(), self.owner_history, "Door",
                "Door", None, placement, shape, None, None)

            self.ifc_file.createIfcRelContainedInSpatialStructure(self.create_guid(
            ), self.owner_history, "Building Storey Container", None, [door], self.building_storey)

        elif element_type.value == 'slab':
            slab = self.ifc_file.createIfcSlab(
                self.create_guid(), self.owner_history, "Slab",
                "Slab", None, placement, shape, None, None)

            self.ifc_file.createIfcRelContainedInSpatialStructure(self.create_guid(
            ), self.owner_history, "Building Storey Container", None, [slab], self.building_storey)

        elif element_type.value == 'wall':
            wall = self.ifc_file.createIfcWallStandardCase(
                self.create_guid(), self.owner_history, "Wall",
                "wall", None, placement, shape)

            self.ifc_file.createIfcRelContainedInSpatialStructure(self.create_guid(
            ), self.owner_history, "Building Storey Container", None, [wall], self.building_storey)

    def add_walls(self, walls: List[Element]) -> None:
        """Add walls to an ifc file object.

        Args:
            walls: A list of ifc wall elements.
        """

        for wall in walls:
            self.ifc_file.add(wall)

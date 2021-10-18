import uuid
import time
import tempfile
import ifcopenshell


def create_guid():
    return ifcopenshell.guid.compress(uuid.uuid1().hex)


def template_variables():
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
    return file_name, time_string, creator, organization, application, application_version, \
        time_stamp, project_global_id, project_name


def template_ifc(file_name, time_string, creator, organization, application,
                 application_version, time_stamp, project_global_id, project_name):
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

    b = template.encode('utf-8')
    # Write the template to a temporary file
    temp_handle, temp_filename = tempfile.mkstemp(suffix=".ifc")
    with open(temp_filename, "wb") as f:
        f.write(b)

    ifcfile = ifcopenshell.open(temp_filename)
    ifcfile.write(file_name)


template_ifc(*template_variables())

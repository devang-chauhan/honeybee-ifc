"""Verify assets and write files to be used by unit tests in other modules."""

import pathlib
from honeybee_ifc.model import Model


def test_convert_to_hbjson(tmp_path_hbjson: pathlib.Path,
                           ifc_family_house: pathlib.Path,
                           ifc_small_office: pathlib.Path):
    """Convert IFC to HBJSONs to a temp folder."""
    # NOTE: This test takes the longest to run.

    hbjson_1 = Model(ifc_family_house).to_hbjson(target_folder=tmp_path_hbjson)
    hbjson_2 = Model(ifc_small_office).to_hbjson(target_folder=tmp_path_hbjson)

    assert pathlib.Path(hbjson_1).name == ifc_family_house.stem + '.hbjson'
    assert pathlib.Path(hbjson_2).name == ifc_small_office.stem + '.hbjson'

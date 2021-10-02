"""This test removes the temp folder after all tests have run."""

import shutil


def test_delete_temp():
    """Delete the temp folder."""
    temp_folder = r'tests/assets/temp'
    shutil.rmtree(temp_folder)

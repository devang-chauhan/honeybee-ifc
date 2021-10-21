"""Remove temp folder after all other tests have finished."""

import shutil
import os


def test_remove_temp():
    """Remove the temp folder."""
    temp_folder = r'tests/assets/temp'

    if os.path.isdir(temp_folder):
        shutil.rmtree(temp_folder)

    assert not os.path.isdir(temp_folder)

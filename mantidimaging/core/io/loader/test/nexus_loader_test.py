import unittest
from unittest import mock

import h5py

from mantidimaging.core.io.loader.nexus_loader import _missing_field_message, get_tomo_data, load_nexus_data, \
    TOMO_ENTRY_PATH

LOAD_NEXUS_FILE = "mantidimaging.core.io.loader.nexus_loader._load_nexus_file"

DATA_PATH = TOMO_ENTRY_PATH + "/data"
IMAGE_KEY_PATH = TOMO_ENTRY_PATH + "/image_key"


def test_missing_field_message():
    assert _missing_field_message(
        "missing_field") == "The NeXus file does not contain the required missing_field field."


class NexusLoaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.nexus = h5py.File("data", "w", driver="core", backing_store=False)
        self.nexus.create_group(TOMO_ENTRY_PATH)
        self.nexus.create_group("/entry1/tomo_entry/data")
        self.nexus.create_group("/entry1/tomo_entry/image_key")

    def tearDown(self) -> None:
        self.nexus.close()

    def test_get_tomo_data(self):
        self.assertIsNotNone(get_tomo_data(self.nexus, TOMO_ENTRY_PATH))

    def test_no_tomo_data_returns_none(self):
        del self.nexus[TOMO_ENTRY_PATH]
        self.assertIsNone(get_tomo_data(self.nexus, TOMO_ENTRY_PATH))

    def test_load_nexus_data_returns_none_when_no_tomo_entry(self):
        del self.nexus[TOMO_ENTRY_PATH]
        with mock.patch(LOAD_NEXUS_FILE, return_value=self.nexus):
            self.assertIsNone(load_nexus_data("filename"))

    def test_load_nexus_data_returns_none_when_no_data(self):
        del self.nexus[DATA_PATH]
        with mock.patch(LOAD_NEXUS_FILE, return_value=self.nexus):
            self.assertIsNone(load_nexus_data("filename"))

    def test_load_nexus_data_returns_none_when_no_image_key(self):
        del self.nexus[IMAGE_KEY_PATH]
        with mock.patch(LOAD_NEXUS_FILE, return_value=self.nexus):
            self.assertIsNone(load_nexus_data("filename"))

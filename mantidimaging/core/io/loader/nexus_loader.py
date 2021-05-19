# Copyright (C) 2021 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import enum
from typing import Union, Optional

import h5py
from logging import getLogger

import numpy as np

from mantidimaging.core.data import Images
from mantidimaging.core.data.dataset import Dataset

logger = getLogger(__name__)

TOMO_ENTRY_PATH = "/entry1/tomo_entry"
DATA_PATH = TOMO_ENTRY_PATH + "/data"
IMAGE_KEY_PATH = TOMO_ENTRY_PATH + "/image_key"


class ImageKeys(enum.Enum):
    Projections = 0
    FlatField = 1
    DarkField = 2


def _missing_data_message(field_name: str) -> str:
    """
    Creates a message for logging when a certain field is missing in the NeXus file.
    :param field_name: The name of the missing field.
    :return: A string telling the user that the field is missing.
    """
    return f"The NeXus file does not contain the required {field_name} field."


def get_tomo_data(nexus_data: Union[h5py.File, h5py.Group], entry_path: str) -> Optional[h5py.Group]:
    """
    Retrieve data from the NeXus file structure.
    :param nexus_data: The NeXus file or group.
    :param entry_path: The path in which the data is found.
    :return: The Nexus group if it exists, None otherwise.
    """
    try:
        return nexus_data[entry_path]
    except KeyError:
        logger.error(_missing_data_message(entry_path))
        return None


def _load_nexus_file(file_path: str) -> h5py.File:
    """
    Load a NeXus file.
    :param file_path: The NeXus file path.
    :return: The h5py File object.
    """
    with h5py.File(file_path, 'r') as nexus_file:
        return nexus_file


def _get_images(image_key_number: ImageKeys, image_key: np.array, data: np.array) -> np.array:
    """
    Retrieve images from the data based on an image key number.
    :param image_key_number: The image key number.
    :param image_key: The image key array.
    :param data: The entire data array.
    :return: The set of images that correspond with a given image key.
    """
    indices = image_key[...] == image_key_number.value
    return data[np.where(indices)]


def load_nexus_data(file_path: str) -> Optional[Dataset]:
    """
    Load the NeXus file and attempt to create a Dataset.
    :param file_path: The NeXus file path.
    :return: A Dataset containing sample, flat field, and dark field images if the file has the expected structure.
    """
    missing_data = False
    nexus_file = _load_nexus_file(file_path)

    tomo_entry = get_tomo_data(nexus_file, TOMO_ENTRY_PATH)
    if tomo_entry is None:
        return

    data = get_tomo_data(nexus_file, DATA_PATH)
    if data is None:
        missing_data = True

    image_key = get_tomo_data(nexus_file, IMAGE_KEY_PATH)
    if image_key is None:
        missing_data = True

    if missing_data:
        return

    sample = _get_images(ImageKeys.Projections, image_key, data)
    if sample.size == 0:
        logger.error("No sample images found in NeXus file.")
        return

    flat_before = _get_images(ImageKeys.FlatField, image_key, data)
    if flat_before.size == 0:
        logger.info("No flat before images found in the NeXus file.")
        flat_field = None

    dark_field = _get_images(ImageKeys.DarkField, image_key, data)
    if dark_field.size == 0:
        logger.info("No dark field images found in the NeXus file.")
        dark_field = None

    return Dataset(Images(sample),
                   Images(flat_field) if flat_field.size > 0 else None,
                   Images(dark_field) if dark_field.size > 0 else None)

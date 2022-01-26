# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import math
import numpy
from typing import Iterable


def _determine_dtype_size(dtype: numpy.dtype) -> int:
    try:
        return numpy.dtype(dtype).itemsize
    except TypeError:
        raise ValueError(f"Can't get size of {dtype}, ({type(dtype)=})")


def full_size(shape: Iterable[int]) -> int:
    """
    Compute the full size of the data, i.e. the number of elements

    :param shape: The shape of the data for which the size will be calculated
    :returns: The size
    """

    return math.prod(shape)


def full_size_KB(shape: Iterable[int], dtype: numpy.dtype):
    return full_size(shape) * _determine_dtype_size(dtype) / 1024


def full_size_MB(shape: Iterable[int], dtype: numpy.dtype):
    return full_size(shape) * _determine_dtype_size(dtype) / 1024 / 1024


def number_of_images_from_indices(start, end, increment):
    return int((end - start) / increment) if increment != 0 else 0

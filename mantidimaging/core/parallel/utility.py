# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later

import multiprocessing
import os
from functools import partial
from logging import getLogger
from multiprocessing.shared_memory import SharedMemory
from multiprocessing.pool import Pool
from typing import List, Tuple, Union, TYPE_CHECKING, Optional

import numpy as np

if TYPE_CHECKING:
    import numpy.typing as npt

from mantidimaging.core.utility.memory_usage import system_free_memory
from mantidimaging.core.utility.progress_reporting import Progress
from mantidimaging.core.utility.size_calculator import full_size_KB, full_size_bytes
from mantidimaging.core.parallel import manager as pm

LOG = getLogger(__name__)


def enough_memory(shape, dtype):
    return full_size_KB(shape=shape, dtype=dtype) < system_free_memory().kb()


def create_array(shape: Tuple[int, ...], dtype: 'npt.DTypeLike' = np.float32) -> 'SharedArray':
    """
    Create an array, either in a memory file (if name provided), or purely in memory (if name is None)

    :param shape: Shape of the array
    :param dtype: Dtype of the array
    :param name: Name of the shared memory array. If None, a non-shared array will be created
    :param random_name: Whether to randomise the name. Will discard anything in the `name` parameter
    :return: The created Numpy array
    """
    if not enough_memory(shape, dtype):
        raise RuntimeError(
            "The machine does not have enough physical memory available to allocate space for this data.")

    return _create_shared_array(shape, dtype)


def _create_shared_array(shape: Tuple[int, ...], dtype: 'npt.DTypeLike' = np.float32) -> 'SharedArray':
    size = full_size_bytes(shape, dtype)

    LOG.info(f'Requested shared array with shape={shape}, size={size}, dtype={dtype}')

    mem = pm.memory_manager.SharedMemory(size=size)
    array = _read_array_from_shared_memory(shape, dtype, mem)

    return SharedArray(array, mem)


def _read_array_from_shared_memory(shape: Tuple[int, ...], dtype: 'npt.DTypeLike', mem: SharedMemory) -> np.ndarray:
    return np.ndarray(shape, dtype=dtype, buffer=mem.buf)


def get_cores():
    return multiprocessing.cpu_count()


def calculate_chunksize(cores):
    # TODO possible proper calculation of chunksize, although best performance
    # has been with 1
    return 1


def multiprocessing_necessary(shape: Union[int, Tuple[int, int, int], List], cores) -> bool:
    # This environment variable will be present when running PYDEVD from PyCharm
    # and that has the bug that multiprocessing Pools can never finish `.join()` ing
    # thus never actually finish their processing.
    if 'PYDEVD_LOAD_VALUES_ASYNC' in os.environ and 'PYTEST_CURRENT_TEST' not in os.environ:
        LOG.info("Debugging environment variable 'PYDEVD_LOAD_VALUES_ASYNC' found. Running synchronously on 1 core")
        return False

    if cores == 1:
        LOG.info("1 core specified. Running synchronously on 1 core")
        return False
    elif isinstance(shape, int):
        if shape <= 10:
            LOG.info("Shape under 10. Running synchronously on 1 core")
            return False
    elif isinstance(shape, tuple) or isinstance(shape, list):
        if shape[0] <= 10:
            LOG.info("3D axis 0 shape under 10. Running synchronously on 1 core")
            return False

    LOG.info(f"Running async on {cores} cores")
    return True


def execute_impl(img_num: int, partial_func: partial, cores: int, chunksize: int, progress: Progress, msg: str):
    task_name = f"{msg} {cores}c {chunksize}chs"
    progress = Progress.ensure_instance(progress, num_steps=img_num, task_name=task_name)
    indices_list = range(img_num)
    if multiprocessing_necessary(img_num, cores):
        with Pool(cores) as pool:
            for _ in pool.imap(partial_func, indices_list, chunksize=chunksize):
                progress.update(1, msg)
    else:
        for ind in indices_list:
            partial_func(ind)
            progress.update(1, msg)
    progress.mark_complete()


class SharedArray:
    def __init__(self, array: np.ndarray, shared_memory: Optional[SharedMemory]):
        self.array = array
        self._shared_memory = shared_memory

    def __del__(self):
        if self.has_shared_memory:
            try:
                self._shared_memory.close()
                self._shared_memory.unlink()
            except FileNotFoundError:
                # Do nothing, memory has already been freed
                pass

    @property
    def has_shared_memory(self) -> bool:
        return self._shared_memory is not None

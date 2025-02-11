# Copyright (C) 2022 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
from logging import getLogger
from typing import Tuple

LOG = getLogger(__name__)


def _import_cupy() -> None:
    import cupy  # noqa: F401


def _cuda_is_present() -> bool:
    """
    Checks if we can import CuPy to confirm that there's a CUDA installation on the device that we can work with
    """
    cuda_is_present = False

    try:
        _import_cupy()
        cuda_is_present = True
    except ModuleNotFoundError:
        LOG.error('CuPy not installed')
    except ImportError:
        LOG.error('CuPy installed, but unable to load CUDA')

    return cuda_is_present


def not_found_message() -> Tuple[str, str]:
    """
    Generates a message that can be displayed if a working CUDA installation isn't found.
    """
    cuda_not_found_msg = "Working CUDA installation not found."
    return cuda_not_found_msg, cuda_not_found_msg + " Will only use gridrec algorithm for reconstruction.",


class CudaChecker:
    _instance = None
    _cuda_is_present = False

    def __new__(cls):
        """
        Creates a singleton for storing the result of the Cuda check.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._cuda_is_present = _cuda_is_present()
        return cls._instance

    @classmethod
    def cuda_is_present(cls) -> bool:
        """
        Returns the shared cuda check result.
        """
        return cls._cuda_is_present

    @classmethod
    def clear_instance(cls):
        """
        Resets the instance. Used for making sure mocks don't leak in tests.
        """
        cls._instance = None

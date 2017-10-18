from __future__ import absolute_import, division, print_function

import numpy as np

from mantidimaging import helper as h
from mantidimaging.core.parallel import two_shared_mem as ptsm
from mantidimaging.core.parallel import utility as pu
from mantidimaging.core.utility.progress_reporting import Progress

# The smallest and largest allowed pixel value
MINIMUM_PIXEL_VALUE = 1e-9
MAXIMUM_PIXEL_VALUE = 3


def _cli_register(parser):
    # this doesn't have anything to add,
    # the options are added in the functional config,
    # which should be moved to here TODO
    return parser


def _divide(data, norm_divide):
    np.true_divide(data, norm_divide, out=data)


def _subtract(data, dark=None):
    # specify out to do in place, otherwise the data is copied
    np.subtract(data, dark, out=data)


def execute(data,
            flat=None,
            dark=None,
            clip_min=MINIMUM_PIXEL_VALUE,
            clip_max=MAXIMUM_PIXEL_VALUE,
            cores=None,
            chunksize=None,
            progress=None):
    """
    Do background correction with flat and dark images.

    :param data: Sample data which is to be processed. Expected in radiograms
    :param flat: Flat (open beam) image to use in normalization
    :param dark: Dark image to use in normalization
    :param clip_min: After normalisation, clip any pixels under this value.
    :param clip_max: After normalisation, clip any pixels over this value.
    :param cores: The number of cores that will be used to process the data.
    :param chunksize: The number of chunks that each worker will receive.
    :return: Filtered data (stack of images)
    """
    h.check_data_stack(data)

    if flat is not None and dark is not None and isinstance(
            flat, np.ndarray) and isinstance(dark, np.ndarray):
        if 2 != flat.ndim or 2 != dark.ndim:
            raise ValueError(
                "Incorrect shape of the flat image ({0}) or dark image ({1}) \
                which should match the shape of the sample images ({2})"
                .format(flat.shape, dark.shape, data[0].shape))

        if pu.multiprocessing_available():
            _execute_par(data, flat, dark, clip_min, clip_max, cores,
                         chunksize, progress)
        else:
            _execute_seq(data, flat, dark, clip_min, clip_max, progress)

    h.check_data_stack(data)
    return data


def _execute_par(data,
                 flat=None,
                 dark=None,
                 clip_min=MINIMUM_PIXEL_VALUE,
                 clip_max=MAXIMUM_PIXEL_VALUE,
                 cores=None,
                 chunksize=None,
                 progress=None):
    """
    A benchmark justifying the current implementation, performed on
    500x2048x2048 images.

    #1 Separate runs
    Subtract (sequential with np.subtract(data, dark, out=data)) - 13s
    Divide (par) - 1.15s

    #2 Separate parallel runs
    Subtract (par) - 5.5s
    Divide (par) - 1.15s

    #3 Added subtract into _divide so that it is:
                np.true_divide(
                    np.subtract(data, dark, out=data), norm_divide, out=data)
    Subtract then divide (par) - 55s
    """
    progress = Progress.ensure_instance(progress,
                                        task_name='Background Correction')

    with progress:
        progress.update(msg="PARALLEL normalization by flat/dark images")

        norm_divide = pu.create_shared_array((1, data.shape[1], data.shape[2]))
        # remove a dimension, I found this to be the easiest way to do it
        norm_divide = norm_divide.reshape(data.shape[1], data.shape[2])

        # subtract dark from flat and copy into shared array with [:]
        norm_divide[:] = np.subtract(flat, dark)

        # prevent divide-by-zero issues, and negative pixels make no sense
        norm_divide[norm_divide == 0] = MINIMUM_PIXEL_VALUE

        # subtract the dark from all images
        f = ptsm.create_partial(_subtract, fwd_function=ptsm.inplace_second_2d)
        data, dark = ptsm.execute(
                data, dark, f, cores, chunksize, "Subtract Dark")

        # divide the data by (flat - dark)
        f = ptsm.create_partial(_divide, fwd_function=ptsm.inplace_second_2d)
        data, norm_divide = ptsm.execute(
                data, norm_divide, f, cores, chunksize, "Norm by Flat")

        # After scaling back the values some images will have pixels with big
        # negative values -25626262 which throws off contrast adjustments.
        # This will crop those negative pixels out, and set them to nearly
        # zero.
        # The negative values will also get scaled back after this in
        # value_scaling which will increase their values futher!
        np.clip(data, clip_min, clip_max, out=data)

    return data


def _execute_seq(data,
                 flat=None,
                 dark=None,
                 clip_min=MINIMUM_PIXEL_VALUE,
                 clip_max=MAXIMUM_PIXEL_VALUE,
                 progress=None):
    progress = Progress.ensure_instance(progress,
                                        task_name='Background Correction')

    with progress:
        progress.update(msg="Normalization by flat/dark images")

        norm_divide = np.subtract(flat, dark)

        # prevent divide-by-zero issues
        norm_divide[norm_divide == 0] = MINIMUM_PIXEL_VALUE
        np.subtract(data, dark, out=data)
        np.subtract(flat, dark, out=flat)
        np.true_divide(data, flat, out=data)
        np.clip(data, clip_min, clip_max, out=data)

    return data

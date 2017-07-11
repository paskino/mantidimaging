from __future__ import absolute_import, division, print_function

import numpy as np

from isis_imaging import helper as h
from isis_imaging.core.parallel import two_shared_mem as ptsm
from isis_imaging.core.parallel import utility as pu

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
            chunksize=None):
    """
    Do background correction with flat and dark images

    :param data: Sample data which is to be processed. Expected in radiograms

    :param flat: Flat (open beam) image to use in normalization

    :param dark: Dark image to use in normalization

    :param clip_min: After normalisation, clip any pixels under this value.

    :param clip_max: After normalisation, clip any pixels over this value.

    :param cores: The number of cores that will be used to process the data.

    :param chunksize: The number of chunks that each worker will receive.

    :return: filtered data (stack of images)

    Example command line:
    isis_imaging -i /some/data -F /some/flat/images -D /some/dark/images

    isis_imaging -i /some/data --input-path-flat /some/flat/images
                   --input-path-flat /some/dark/images
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
                         chunksize)
        else:
            _execute_seq(data, flat, dark, clip_min, clip_max)

    h.check_data_stack(data)
    return data


def _execute_par(data,
                 flat=None,
                 dark=None,
                 clip_min=MINIMUM_PIXEL_VALUE,
                 clip_max=MAXIMUM_PIXEL_VALUE,
                 cores=None,
                 chunksize=None):
    """
    A benchmark justifying the current implementation, performed on 500x2048x2048 images

    #1 Separate runs
    Subtract (sequential with np.subtract(data, dark, out=data)) - 13s
    Divide (par) - 1.15s

    #2 Separate parallel runs
    Subtract (par) - 5.5s
    Divide (par) - 1.15s

    #3 Added subtract into _divide so that it is:
                np.true_divide(np.subtract(data, dark, out=data), norm_divide, out=data)
    Subtract then divide (par) - 55s
    """
    h.pstart("Starting PARALLEL normalization by flat/dark images.")

    norm_divide = pu.create_shared_array((1, data.shape[1], data.shape[2]))
    # remove a dimension, I found this to be the easiest way to do it
    norm_divide = norm_divide.reshape(data.shape[1], data.shape[2])

    # subtract dark from flat and copy into shared array with [:]
    norm_divide[:] = np.subtract(flat, dark)

    # prevent divide-by-zero issues, and negative pixels make no sense
    norm_divide[norm_divide == 0] = MINIMUM_PIXEL_VALUE

    # subtract the dark from all images
    f = ptsm.create_partial(_subtract, fwd_function=ptsm.inplace_second_2d)
    data, dark = ptsm.execute(data, dark, f, cores, chunksize, "Subtract Dark")

    f = ptsm.create_partial(_divide, fwd_function=ptsm.inplace_second_2d)
    data, norm_divide = ptsm.execute(data, norm_divide, f, cores, chunksize,
                                     "Norm by Flat")

    # After scaling back the values some images will have pixels
    # with big negative values -25626262 which throws off contrast adjustments.
    # This will crop those negative pixels out, and set them to nearly zero
    # The negative values will also get scaled back after this in
    # value_scaling which will increase their values futher!
    np.clip(data, clip_min, clip_max, out=data)
    h.pstop("Finished PARALLEL normalization by flat/dark images.")

    return data


def _execute_seq(data,
                 flat=None,
                 dark=None,
                 clip_min=MINIMUM_PIXEL_VALUE,
                 clip_max=MAXIMUM_PIXEL_VALUE):
    h.pstart("Starting normalization by flat/dark images.")

    norm_divide = np.subtract(flat, dark)

    # prevent divide-by-zero issues
    norm_divide[norm_divide == 0] = MINIMUM_PIXEL_VALUE
    np.subtract(data, dark, out=data)
    np.subtract(flat, dark, out=flat)
    np.true_divide(data, flat, out=data)
    h.prog_close()
    np.clip(data, clip_min, clip_max, out=data)
    h.pstop("Finished normalization by flat/dark images.")

    return data

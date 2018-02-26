from logging import getLogger

from mantidimaging.core.data import const


LOG = getLogger(__name__)


def get_last_cor_tilt_find(images):
    """
    Gets the properties from the last instance of COR/Tilt finding that was run
    on a given image stack.
    """
    if not images.has_history:
        return None, None

    # Copy the history and reverse it
    history = images.properties[const.OPERATION_HISTORY][:]
    history.reverse()

    # Iterate over history and find the first instance of COR/Tilt finding
    # (which is the last given that the history was reversed)
    for i, e in enumerate(history):
        if 'cor_tilt_finding' in e['name']:
            return e['kwargs'], len(history) - 1 - i

    return None, None


def get_crop_operations(images, start=None, end=None):
    """
    Gets a list of crop operations that happened between two points in the
    image operation history.
    """
    if not images.has_history:
        return []

    history = images.properties[const.OPERATION_HISTORY][start:end]
    crops = [e for e in history if 'crop_coords' in e['name']]
    return crops


def get_crop(images, axis, start=None, end=None):
    """
    Gets a sum along a given axis of all crop operations that happened between
    two points in the image operation history.
    """
    total_crop = 0.0
    for crop in get_crop_operations(images, start, end):
        total_crop += crop['kwargs']['region_of_interest'][axis]
    return total_crop


def get_cor_tilt_from_images(images):
    """
    Gets rotation centre at top of image and gradient with which to calculate
    rotation centre arrays for reconstruction.
    """
    if not images or not images.has_history:
        return (0, 0.0, 0.0)

    last_find, last_find_idx = get_last_cor_tilt_find(images)

    cor = last_find['rotation_centre']
    tilt = last_find['tilt_angle_rad']
    m = last_find['fitted_gradient']

    cor -= get_crop(images, 0, start=last_find_idx)

    # Get total offset from linear regression origin from total crop length on
    # top edge
    top = get_crop(images, 1, start=last_find_idx)
    LOG.debug('Total top crop: {}'.format(top))

    # Calculate new rotation centre at new top of image
    new_cor = (top * m) + cor
    LOG.debug('New COR corrected for top crop: {}'.format(new_cor))

    return (new_cor, tilt, m)

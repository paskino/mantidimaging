from __future__ import (absolute_import, division, print_function)
import numpy as np


def execute(sample, flat, dark, config, indices):
    i1 = indices[0]
    i2 = indices[1]
    sample = np.swapaxes(sample, 0, 1)

    cube_show_slider(sample[i1:i2], 0)

    # stop python from exiting
    import matplotlib.pyplot as plt
    plt.show()

    return sample


def cube_show_slider(cube, axis=2, cmap='Greys_r', **kwargs):
    """
    Display a 3d ndarray with a slider to move along the third dimension.

    Extra keyword arguments are passed to imshow.

    Source: http://nbarbey.github.io/2011/07/08/matplotlib-slider.html
    """
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Slider, Button, RadioButtons

    # check dim
    if not cube.ndim == 3:
        raise ValueError("cube should be an ndarray with ndim == 3")

    # generate figure
    fig = plt.figure()
    ax = plt.subplot(111)
    fig.subplots_adjust(left=0.25, bottom=0.25)
    # select first image
    s = [slice(0, 1) if i == axis else slice(None) for i in range(3)]
    im = cube[s].squeeze()

    # display image
    l = ax.imshow(im, cmap=cmap, **kwargs)

    # define slider
    axcolor = 'lightgoldenrodyellow'
    ax = fig.add_axes([0.25, 0.1, 0.65, 0.03], axisbg=axcolor)

    slider = Slider(ax, 'Axis %i index' % axis, 0, cube.shape[axis] - 1,
                    valinit=0, valfmt='%i')

    def update(val):
        ind = int(slider.val)
        s = [slice(ind, ind + 1) if i == axis else slice(None) for i in range(3)]
        im = cube[s].squeeze()
        l.set_data(im)
        fig.canvas.draw()

    slider.on_changed(update)

    plt.show(block=False)

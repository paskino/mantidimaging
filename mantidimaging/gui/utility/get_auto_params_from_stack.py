from __future__ import absolute_import, division, print_function


def get_auto_params_from_stack(stack, params):
    return {k: stack.get_parameter_value(v) for (k, v) in params.items()} \
        if params else {}

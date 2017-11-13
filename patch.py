
import unittest
import unittest.mock
from contextlib import ExitStack


def _cast(class_type, x):
    if x.objectType == class_type:
        return x
    else:
        return None


def add_standard_patches(cls_str, patches):
    """ Standard "base" attributes that all classes should have """
    patches['objectType'] = cls_str
    patches['classType'] = lambda: cls_str
    patches['cast'] = lambda x: _cast(cls_str, x) 
    return patches


def apply_patches(patches_by_class):
    """ Apply patches using unittest.mock.patch.

        Patches are applied using an ExitStack, which means we can apply multiple patches
        in the same context manager.

        Note: you can use this to code to globally patch classes before importing them,

        e.g.

        apply_patches({'adsk.core.StringValueCommandInput': {'_get_value': _special_get_value_fn}})

        from . import string_value_input_operations

    """
    stack = ExitStack()

    for cls_str in patches_by_class:
        print('Patching ' + cls_str + ': ' + str(patches_by_class[cls_str]))
        p = add_standard_patches(cls_str, patches_by_class[cls_str] or {})
        stack.enter_context(unittest.mock.patch.multiple(cls_str, **p))
    
    return stack

import sys
from . import patch

import inspect
import unittest
import unittest.mock


class EnhancedMock(unittest.mock.Mock):
    """ An enhanced mock object that supports a wider array of mock patching than the base framework.
    """

    # Because we're building a strict mock, we need some machinery to let us keep
    # internal state.  See override of __setattr__ below.
    members = ['special_children']

    def __init__(self, cls, patches):
        """
        Init a mock for the specified class, and apply the specified patches to the mocked instance.

        Unlike the base Mock/PropertyMock classes, this lets a caller patch a property with a function.

        This also lets a caller apply a patch that deviates from the strict spec.

        :param cls: The class to mock.  This is used as the strict spec by unittest.mock
        :param patches: A dictionary of property name to patch values/functions.
        """
        unittest.mock.Mock.__init__(self, spec_set=cls)
        prop_names = [n for n, _ in inspect.getmembers(cls, inspect.isdatadescriptor)]
        self.special_children = {}
        for k in patches:
            #print('patching ' + k + ', ' + str(patches[k]) + ', is prop? ' + str(k in prop_names))
            p = None
            if k in prop_names:
                p = unittest.mock.PropertyMock()
                if callable(patches[k]):
                    # Set up the property mock to call the patch function passed in
                    p.__get__ = lambda a, instance, b, fn=patches[k]: fn(instance)
                else:
                    p.return_value = patches[k]
            else:
                p = unittest.mock.Mock()
                if callable(patches[k]):
                    p.side_effect = patches[k]
                else:
                    p.return_value = patches[k]
            self.special_children[k] = p

    def __setattr__(self, name, value):
        if name in EnhancedMock.members:
            self.__dict__[name] = value
        else:
            unittest.mock.Mock.__setattr__(self, name, value)

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            result = unittest.mock.Mock.__getattr__(self, name)
            #print('in EnhancedMock.__getattr__: ' + name + ", " + str(result.side_effect))
            if isinstance(result, unittest.mock.PropertyMock) and result.__get__:
                # Only handle the case of a custom getter here...property mocks with a return_value will
                # be handled in the elif
                return result.__get__(self, type(self))
            elif isinstance(result, unittest.mock.Mock) and not result.side_effect:
                # If we have a mock object WITHOUT a side effect, call it
                # We don't call mocks with side effects because the caller of this
                # is going to call the function with arguments.  We do call the Mock
                # object in this case to get any value it may hold.
                return result()
            else:
                return result

    def _get_child_mock(self, **kw):
        if kw['name'] in self.special_children:
            return self.special_children[kw['name']]
        else:
            return unittest.mock.MagicMock(**kw)


def from_name(full_name):
    """
        Finds and returns a class object from name.
    """
    pkg, cls_name = full_name.rsplit('.', 1)
    core = sys.modules[pkg]
    return getattr(core, cls_name)


# Keep track of what's been patched to avoid double-patching
_patched_classes = set()

def create_mock(cls_str, additional_patches=None):
    """
    Create a mock object by class name, applying patches as needed.

    If the class hasn't been patched yet, patches it first. Then creates and returns
    a mock instance of that class.

    Args:
        cls_str: Full class name like 'adsk.core.ListItem'
        additional_patches: Dict of additional patches for this class

    Usage:
        list_item = create_mock('adsk.core.ListItem')
        bool_input = create_mock('adsk.core.BoolValueCommandInput', {'_custom': custom_fn})
    """
    if additional_patches is None:
        additional_patches = {}

    # Check if this class needs patching
    if cls_str not in _patched_classes:
        from . import patch
        # Patch just this one class
        patch_dict = {cls_str: additional_patches}
        patch.apply_patches(patch_dict)
        _patched_classes.add(cls_str)

    # Get the patched class and create an instance
    cls = from_name(cls_str)
    inst = cls()
    unittest.mock.seal(inst)
    return inst

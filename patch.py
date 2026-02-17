
import unittest
import unittest.mock
from contextlib import ExitStack


def _cast(class_type, x):
    if x.objectType == class_type:
        return x
    else:
        return None


def add_standard_patches(cls_str, patches):
    """
        Standard "base" attributes that all classes should have.
    """
    patches['objectType'] = cls_str
    patches['classType'] = lambda: cls_str
    patches['cast'] = lambda x: _cast(cls_str, x)
    return patches

import sys

def from_name(full_name):
    """
        Finds and returns a class object from name.
    """
    pkg, cls_name = full_name.rsplit('.', 1)
    core = sys.modules[pkg]
    return getattr(core, cls_name)

# Keep track of what's been patched to avoid double-patching
_patched_classes = set()

def is_already_patched(cls_str):
    return cls_str in _patched_classes

def apply_patches(patches_by_class=None):
    """Apply patches to specified classes using unittest.mock.patch.

    Patches are applied using an ExitStack, which means we can apply multiple patches
    in the same context manager.

    Args:
        patches_by_class: Dict mapping class names to their patches
                         e.g. {'adsk.core.StringValueCommandInput': {'_get_value': special_fn}}

    Usage:
        # Patch specific classes with their patches
        apply_patches({'adsk.core.StringValueCommandInput': {'_get_value': special_fn}})

        # Can be called with no args to patch nothing (useful for compatibility)
        apply_patches()
    """
    if patches_by_class is None:
        patches_by_class = {}

    stack = ExitStack()

    for cls_str in patches_by_class:
        if is_already_patched(cls_str):
            continue
        print('Patching ' + cls_str + ': ' + str(patches_by_class[cls_str]))

        p = add_standard_patches(cls_str, patches_by_class[cls_str] or {})

        # We're mocking a class and sealing it below.  This section
        # adds basic python expected methos for a class
        p['__hash__'] = lambda _: cls_str.__hash__()

        real_class = from_name(cls_str)
        # Create a mock class that returns new instances each time
        mock_class = unittest.mock.MagicMock(spec=real_class)

        # Add the patches to the mock class itself
        for patch_name, patch_value in p.items():
            setattr(mock_class, patch_name, patch_value)

        # Set up side_effect to return new mock instances with patches applied
        # Use default parameter to capture current value of p
        def make_create_instance(mc: unittest.mock.MagicMock):
            def create_instance(*args, patches=p.copy(), **kwargs):
                instance = unittest.mock.MagicMock(spec=mc.__class__)

                # Apply patches to each new instance
                for patch_name, patch_value in patches.items():
                    setattr(instance, patch_name, patch_value)

                # Pre-get all attributes from the spec to allow them to be set later
                # This ensures attributes exist before sealing so tests can set them
                if hasattr(instance, '_mock_methods') and instance._mock_methods:
                    for attr_name in instance._mock_methods:
                        # Access the attribute to create the mock child
                        getattr(instance, attr_name)

                unittest.mock.seal(instance)
                return instance
            return create_instance

        mock_class.side_effect = make_create_instance(mock_class)
        unittest.mock.seal(mock_class)

        # Patch the class with our mock
        patch = unittest.mock.patch(cls_str, mock_class)
        class PatchContext:

            def __enter__(self):
                _patched_classes.add(cls_str)
                return patch.start()

            def __exit__(self, exc_type, exc_val, exc_tb):
                patch.stop()
                _patched_classes.remove(cls_str)


        stack.enter_context(PatchContext())

    return stack

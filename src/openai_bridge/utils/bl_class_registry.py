# <pep8-80 compliant>

import bpy


class BlClassRegistry:
    class_list = []

    def __init__(self, *_, **kwargs):
        self.legacy = kwargs.get('legacy', False)

    def __call__(self, cls):
        if hasattr(cls, "bl_idname"):
            BlClassRegistry.add_class(cls.bl_idname, cls, self.legacy)
        elif hasattr(cls, "bl_label"):
            bl_idname = "{}-{}".format(cls.__name__, cls.bl_label)
            BlClassRegistry.add_class(bl_idname, cls, self.legacy)
        else:
            bl_idname = cls.__name__
            BlClassRegistry.add_class(bl_idname, cls, self.legacy)
        return cls

    @classmethod
    def add_class(cls, bl_idname, op_class, legacy):
        for class_ in cls.class_list:
            if (class_["bl_idname"] == bl_idname) and \
               (class_["legacy"] == legacy):
                raise RuntimeError("{} is already registered"
                                   .format(bl_idname))

        new_op = {
            "bl_idname": bl_idname,
            "class": op_class,
            "legacy": legacy,
        }
        cls.class_list.append(new_op)

    @classmethod
    def register(cls):
        for class_ in cls.class_list:
            bpy.utils.register_class(class_["class"])

    @classmethod
    def unregister(cls):
        for class_ in cls.class_list:
            bpy.utils.unregister_class(class_["class"])

    @classmethod
    def cleanup(cls):
        cls.class_list = []

import os
from ctypes import (
    c_void_p,
    cast,
    POINTER,
)

DATA_DIR = f"{os.path.dirname(__file__)}/../_data"
IMAGE_DATA_DIR = f"{DATA_DIR}/image"
CHAT_DATA_DIR = f"{DATA_DIR}/chat"
CODE_DATA_DIR = f"{DATA_DIR}/code"
ICON_DIR = f"{os.path.dirname(__file__)}/../icon"


def get_area_region_space(context, area_type, region_type, space_type):
    area = None
    region = None
    space = None

    for a in context.screen.areas:
        if a.type == area_type:
            area = a
            break
    else:
        return area, region, space

    for r in a.regions:
        if r.type == region_type:
            region = r
            break
    else:
        return area, region, space

    for s in area.spaces:
        if s.type == space_type:
            space = s
            break

    return area, region, space


def get_info_report_message(context, kind='ERROR', index_from_last=0):
    pass
    # wm_addr = context.window_manager.as_pointer()
    # wm = cast(c_void_p(wm_addr), POINTER(cstruct.wmWindowManager))
    # wm.report()

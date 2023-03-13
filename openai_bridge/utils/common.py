import os

DATA_DIR = f"{os.path.dirname(__file__)}/../_data"
IMAGE_DATA_DIR = f"{DATA_DIR}/image"
CHAT_DATA_DIR = f"{DATA_DIR}/chat"
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

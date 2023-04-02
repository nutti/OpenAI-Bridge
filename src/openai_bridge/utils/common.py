import os
import json
import textwrap

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


class ChatTextFile:
    def __init__(self):
        self.filepath = None
        self.json_raw = {}

    @classmethod
    def remove(cls, topic):
        os.remove(f"{CHAT_DATA_DIR}/topics/{topic}.json")

    def new(self, topic):
        self.filepath = f"{CHAT_DATA_DIR}/topics/{topic}.json"
        self.json_raw = {
            "topic": {
                "parts": []
            }
        }

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.json_raw, f, ensure_ascii=False, indent=4, sort_keys=True, separators=(",", ": "))

    def load_from_topic(self, topic):
        filepath = f"{CHAT_DATA_DIR}/topics/{topic}.json"
        self.load(filepath)

    def load(self, filepath):
        self.filepath = filepath
        if not os.path.isfile(self.filepath):
            self.json_raw = {
                "topic": {
                    "parts": []
                }
            }
            return
        with open(self.filepath, "r", encoding="utf-8") as f:
            self.json_raw = json.load(f)

    def add_part(self, user_data, condition_data, response_data):
        self.json_raw["topic"]["parts"].append({
            "user": user_data,
            "system": condition_data,
            "assistant": response_data,
        })

    def modify_part(self, part, *, user_data=None, condition_data=None, response_data=None):
        if user_data is not None:
            self.json_raw["topic"]["parts"][part]["user"] = user_data
        if condition_data is not None:
            self.json_raw["topic"]["parts"][part]["system"] = condition_data
        if response_data is not None:
            self.json_raw["topic"]["parts"][part]["assistant"] = response_data

    def num_parts(self):
        return len(self.json_raw["topic"]["parts"])

    def get_part(self, part):
        return self.json_raw["topic"]["parts"][part]

    def get_user_data(self, part):
        return self.json_raw["topic"]["parts"][part]["user"]

    def get_condition_data(self, part):
        return self.json_raw["topic"]["parts"][part]["system"]

    def get_response_data(self, part):
        return self.json_raw["topic"]["parts"][part]["assistant"]


def parse_response_data(response_data):
    sections = []

    lines = response_data.split("\n")
    in_code = False
    section = []
    for l in lines:
        if l.startswith("```"):
            if in_code:
                sections.append({
                    "kind": 'CODE',
                    "body": "\n".join(section)
                })
                section = []
                in_code = False
            else:
                sections.append({
                    "kind": 'TEXT',
                    "body": "\n".join(section)
                })
                section = []
                in_code = True
        else:
            section.append(l)
    if section:
        sections.append({
            "kind": 'TEXT',
            "body": "\n".join(section)
        })

    return sections


def get_code_from_response_data(response_data, code_index):
    sections = parse_response_data(response_data)
    codes = []
    for section in sections:
        if section["kind"] == 'CODE':
            codes.append(section["body"])

    if code_index >= len(codes):
        return None

    return codes[code_index]


def draw_data_on_ui_layout(context, layout, lines):
    user_prefs = context.preferences
    prefs = user_prefs.addons["openai_bridge"].preferences

    wrapped_length = int(context.region.width * prefs.chat_log_wrap_width)
    wrapper = textwrap.TextWrapper(width=wrapped_length)
    col = layout.column(align=True)
    for l in lines:
        wrappeed_lines = wrapper.wrap(text=l)
        for wl in wrappeed_lines:
            col.scale_y = 0.8
            col.label(text=wl)
        if len(wrappeed_lines) == 0:
            col.label(text="")

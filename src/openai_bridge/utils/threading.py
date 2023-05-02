import json
import os
import threading
import time
from urllib.parse import urlparse
import math
from collections import OrderedDict
import uuid
import requests
import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader

from ..utils.common import (
    get_area_region_space,
    parse_response_data,
    IMAGE_DATA_DIR,
    CHAT_DATA_DIR,
    CODE_DATA_DIR,
    ChatTextFile,
)
from ..utils import error_storage


class OPENAI_OT_ProcessMessage(bpy.types.Operator):

    bl_idname = "system.openai_process_message"
    bl_description = "Process Message"
    bl_label = "Process Message"

    message_queue_lock = threading.Lock()
    message_queue = []
    section_stats = {
        "transaction_total": 0,
        "transaction_consumed_total": 0,
    }

    transaction_ids = OrderedDict()
    transaction_ids_lock = threading.Lock()

    timer = None
    draw_cb = {"space_data": None, "handler": None}

    @classmethod
    def process(cls, transaction_id, type_, data, options, exec_params):
        message = {"transaction_id": transaction_id, "type": type_,
                   "data": data, "options": options}
        if exec_params["sync"]:
            cls.sync_process(exec_params["context"],
                             exec_params["operator_instance"], message)
        else:
            cls.async_process(message)

    @classmethod
    def async_process(cls, message):
        with cls.message_queue_lock:
            cls.message_queue.append(message)

    @classmethod
    def sync_process(cls, context, operator_instance, message):
        cls.process_message_internal(context, operator_instance, message)

    @classmethod
    def process_message_internal(cls, context, operator_instance, message):
        transaction_id = message["transaction_id"]
        msg_type = message["type"]
        data = message["data"]
        options = message["options"]

        if data and "usage_stats" in data:
            sc = context.scene
            for tool, stat in data["usage_stats"].items():
                if tool == 'IMAGE':
                    stats_image_tool = sc.openai_usage_statistics_image_tool
                    if stat["size"] == "1024x1024":
                        stats_image_tool.images_1024x1024 += stat["num_images"]
                    elif stat["size"] == "512x512":
                        stats_image_tool.images_512x512 += stat["num_images"]
                    elif stat["size"] == "256x256":
                        stats_image_tool.images_256x256 += stat["num_images"]
                elif tool == 'AUDIO':
                    stats_audio_tool = sc.openai_usage_statistics_audio_tool
                    if stat["model"] == "whisper-1":
                        stats_audio_tool.seconds_whisper += stat["num_seconds"]
                elif tool == 'CHAT':
                    stats_chat_tool = sc.openai_usage_statistics_chat_tool
                    if stat["model"] == "gpt-3.5-turbo":
                        stats_chat_tool.tokens_gpt35_turbo += \
                            stat["num_tokens"]
                    elif stat["model"] == "gpt-4":
                        stats_chat_tool.tokens_gpt4_8k += stat["num_tokens"]
                    elif stat["model"] == "gpt-4-32k":
                        stats_chat_tool.tokens_gpt4_32k += stat["num_tokens"]
                elif tool == 'CODE':
                    stats_code_tool = sc.openai_usage_statistics_code_tool
                    if stat["model"] == "gpt-3.5-turbo":
                        stats_code_tool.tokens_gpt35_turbo += \
                            stat["num_tokens"]
                    elif stat["model"] == "gpt-4":
                        stats_code_tool.tokens_gpt4_8k += stat["num_tokens"]
                    elif stat["model"] == "gpt-4-32k":
                        stats_code_tool.tokens_gpt4_32k += stat["num_tokens"]

        if msg_type == 'IMAGE':
            filepath = data["filepath"]
            new_image = bpy.data.images.load(filepath=filepath)
            # Focus on the generated image in Image Editor.
            _, _, space = get_area_region_space(
                context, 'IMAGE_EDITOR', 'WINDOW', 'IMAGE_EDITOR')
            if space is not None:
                space.image = new_image
        elif msg_type == 'AUDIO':
            text = data["text"]
            if options["target"] == 'TEXT_EDITOR':
                if options["target_text_name"] not in bpy.data.texts:
                    bpy.data.texts.new(options["target_text_name"])
                text_data = bpy.data.texts[options["target_text_name"]]
                text_data.write(text)
                # Focus on the text in Text Editor.
                _, _, space = get_area_region_space(
                    context, 'TEXT_EDITOR', 'WINDOW', 'TEXT_EDITOR')
                if space is not None:
                    space.text = text_data
            elif options["target"] == 'TEXT_STRIP':
                seq_data = context.scene.sequence_editor.sequences.new_effect(
                    name="Transcript", type='TEXT',
                    channel=options["target_sequence_channel"],
                    frame_start=options["strip_start"],
                    frame_end=options["strip_end"])
                seq_data.text = text
                # Focus on the sequence in Sequencer.
                for s in context.scene.sequence_editor.sequences:
                    s.select = False
                seq_data.select = True
        elif msg_type == 'CHAT':
            # Focus on the topic.
            context.scene.openai_chat_tool_props.topic = options["topic"]
            context.scene.openai_chat_tool_props.new_topic = False
        elif msg_type == 'CODE':
            os.makedirs(CODE_DATA_DIR, exist_ok=True)
            filepath = f"{CODE_DATA_DIR}/{options['code']}.py"
            with open(filepath, "r", encoding="utf-8") as f:
                code_to_execute = f.read()
            if options["show_text_editor"]:
                text_data = bpy.data.texts.new(options["code"])
                text_data.write(code_to_execute)
                # Focus on the text in Text Editor.
                _, _, space = get_area_region_space(
                    context, 'TEXT_EDITOR', 'WINDOW', 'TEXT_EDITOR')
                if space is not None:
                    space.text = text_data
            if options["execute_immediately"]:
                try:
                    exec(code_to_execute)   # pylint: disable=W0122
                except Exception as e:  # pylint: disable=W0703
                    error_key = error_storage.get_error_key(
                        'CODE', code_to_execute, 0, 0)
                    error_storage.store_error(error_key, str(e))
        elif message["type"] == 'ERROR':
            exception = data["exception"]
            operator_instance.report({'WARNING'}, f"Error: {exception}")
        elif message["type"] == 'END_OF_TRANSACTION':
            cls.section_stats["transaction_consumed_total"] += 1
            return transaction_id

        return None

    def process_message(self, context):
        cls = self.__class__
        with cls.message_queue_lock:
            if len(cls.message_queue) == 0:
                return None
            message = cls.message_queue.pop(0)

        transaction_id = cls.process_message_internal(context, self, message)

        # Update screen.
        for area in context.screen.areas:
            area.tag_redraw()

        return transaction_id

    def modal(self, context, event):
        cls = self.__class__

        if event.type == 'TIMER':
            msg_key = self.process_message(context)
            if msg_key is not None:
                with cls.transaction_ids_lock:
                    assert msg_key in cls.transaction_ids
                    del cls.transaction_ids[msg_key]
                    if len(cls.transaction_ids) == 0:
                        wm = context.window_manager
                        wm.event_timer_remove(cls.timer)
                        cls.timer = None
                        if cls.draw_cb["space_data"] is not None and \
                                cls.draw_cb["handler"] is not None:
                            cls.draw_cb["space_data"].draw_handler_remove(
                                cls.draw_cb["handler"], 'WINDOW')

                        print("Terminated Message Processing Timer")
                        return {'FINISHED'}

            context.area.tag_redraw()

        return {'PASS_THROUGH'}

    @classmethod
    def draw_status(cls, context):
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        font_id = 0

        base_x = prefs.request_status_location[0]
        base_y = prefs.request_status_location[1]

        # Draw background.
        original_state = gpu.state.blend_get()
        gpu.state.blend_set('ALPHA')
        rect_width = 250.0
        rect_height = 180.0
        vertex_data = {
            "pos": [
                [base_x, base_y],
                [base_x, base_y + rect_height],
                [base_x + rect_width, base_y + rect_height],
                [base_x + rect_width, base_y],
            ]
        }
        index_data = [
            [0, 1, 2],
            [2, 3, 0]
        ]
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(
            shader, 'TRIS', vertex_data, indices=index_data)
        shader.bind()
        shader.uniform_float("color", [0.0, 0.0, 0.0, 0.6])
        batch.draw(shader)
        gpu.state.blend_set(original_state)

        blf.color(font_id, 1.0, 1.0, 0.0, 1.0)

        # Draw title.
        blf.position(font_id, base_x + 10.0, base_y + 150.0, 0)
        blf.size(font_id, 16)
        blf.draw(font_id, "Processing Requests ...")

        # Draw rest transactions.
        consumed = cls.section_stats["transaction_consumed_total"]
        total = cls.section_stats["transaction_total"]
        blf.position(font_id, base_x + 10.0, base_y + 120.0, 0)
        blf.size(font_id, 12)
        blf.draw(font_id, f"({consumed}/{total})")

        # Draw process transaction.
        count = 0
        for item in cls.transaction_ids.values():
            if count >= 5:
                break
            ts_type = item["type"]
            ts_title = item["title"]
            blf.position(
                font_id, base_x + 10.0, base_y + 100.0 - count * 20.0, 0)
            blf.draw(font_id, f"[{ts_type}] {ts_title}")
            count += 1

    def execute(self, context):
        cls = self.__class__
        wm = context.window_manager
        user_prefs = context.preferences
        prefs = user_prefs.addons["openai_bridge"].preferences

        cls.section_stats["transaction_total"] += 1

        if cls.timer:
            return {'FINISHED'}

        # Initialize statistics.
        cls.section_stats["transaction_total"] = 1
        cls.section_stats["transaction_consumed_total"] = 0

        cls.timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        if prefs.show_request_status:
            if context.space_data.type in ('VIEW_3D', 'IMAGE_EDITOR',
                                           'SEQUENCE_EDITOR', 'TEXT_EDITOR'):
                cls.draw_cb["space_data"] = context.space_data
                cls.draw_cb["handler"] = context.space_data.draw_handler_add(
                    cls.draw_status, (context, ), 'WINDOW', 'POST_PIXEL')
            else:
                cls.draw_cb["space_data"] = bpy.types.SpaceView3D
                cls.draw_cb["handler"] = \
                    bpy.types.SpaceView3D.draw_handler_add(
                        cls.draw_status, (context, ), 'WINDOW', 'POST_PIXEL')
        else:
            cls.draw_cb["space_data"] = None
            cls.draw_cb["handler"] = None

        print("Launched Message Processing Timer")

        return {'RUNNING_MODAL'}


class RequestHandler:

    request_queue = []
    request_queue_lock = None
    send_loop_thread = None
    should_stop = True

    @classmethod
    def add_request(cls, request):
        with cls.request_queue_lock:    # pylint: disable=E1129
            cls.request_queue.append(request)

    @classmethod
    def start(cls):
        print("RequestHandler is started.")
        cls.send_loop_thread = threading.Thread(target=cls.send_loop)
        cls.request_queue_lock = threading.Lock()
        cls.should_stop = False
        cls.send_loop_thread.start()

    @classmethod
    def stop(cls):
        cls.should_stop = True
        while cls.send_loop_thread.is_alive():
            print(".", end="")
            time.sleep(1)
            continue
        print()
        cls.request_queue_lock = None
        cls.request_queue = []
        cls.send_loop_thread = None
        print("RequestHandler is stopped.")

    @classmethod
    def handle_generate_image_request(
            cls, api_key, transaction_id, req_data, options, exec_params):
        # Send prompt.
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        proxies = {
            "http": options["http_proxy"],
            "https": options["https_proxy"],
        }
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers, data=json.dumps(req_data), proxies=proxies)
        response.raise_for_status()
        response_data = response.json()

        # Download image.
        for i, data in enumerate(response_data["data"]):
            download_url = data["url"]
            response = requests.get(download_url, proxies=proxies)
            response.raise_for_status()
            content_type = response.headers["content-type"]
            if "image" not in content_type:
                raise RuntimeError(f"Invalid content-type '{content_type}'")
            image_data = response.content

            # Save image
            dirname = f"{IMAGE_DATA_DIR}/generated"
            os.makedirs(dirname, exist_ok=True)
            if options["auto_image_name"]:
                filename = urlparse(download_url).path.split("/")[-1]
            else:
                filename = f"{options['image_name']}.png"
                if i >= 1:
                    filename = f"{filename}-{i}"
            filepath = f"{dirname}/{filename}"
            with open(filepath, "wb") as f:
                f.write(image_data)

            usage_stats = {
                'IMAGE': {
                    "size": req_data["size"],
                    "num_images": 1,
                },
            }

            OPENAI_OT_ProcessMessage.process(
                transaction_id, 'IMAGE',
                {"filepath": filepath, "usage_stats": usage_stats},
                options, exec_params)

        OPENAI_OT_ProcessMessage.process(
            transaction_id, 'END_OF_TRANSACTION', None, None, exec_params)

    @classmethod
    def handle_edit_image_request(
            cls, api_key, transaction_id, req_data, options, exec_params):
        # Send prompt.
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        proxies = {
            "http": options["http_proxy"],
            "https": options["https_proxy"],
        }
        response = requests.post("https://api.openai.com/v1/images/edits",
                                 headers=headers, files=req_data,
                                 proxies=proxies)
        response.raise_for_status()
        response_data = response.json()

        # Download image.
        for i, data in enumerate(response_data["data"]):
            download_url = data["url"]
            response = requests.get(download_url, proxies=proxies)
            response.raise_for_status()
            content_type = response.headers["content-type"]
            if "image" not in content_type:
                raise RuntimeError(f"Invalid content-type '{content_type}'")
            image_data = response.content

            # Save image
            dirname = f"{IMAGE_DATA_DIR}/generated"
            os.makedirs(dirname, exist_ok=True)
            filename = f"edit-{options['base_image_name']}.png"
            if i >= 1:
                filename = f"{filename}-{i}"
            filepath = f"{dirname}/{filename}"
            with open(filepath, "wb") as f:
                f.write(image_data)

            # Remove temporary files.
            os.remove(options["base_image_filepath"])
            os.remove(options["mask_image_filepath"])

            usage_stats = {
                'IMAGE': {
                    "size": req_data["size"],
                    "num_images": 1,
                },
            }

            OPENAI_OT_ProcessMessage.process(
                transaction_id, 'IMAGE',
                {"filepath": filepath, "usage_stats": usage_stats},
                options, exec_params)

        OPENAI_OT_ProcessMessage.process(
            transaction_id, 'END_OF_TRANSACTION', None, None, exec_params)

    @classmethod
    def handle_generate_variation_image_request(
            cls, api_key, transaction_id, req_data, options, exec_params):
        # Send prompt.
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        proxies = {
            "http": options["http_proxy"],
            "https": options["https_proxy"],
        }
        response = requests.post("https://api.openai.com/v1/images/variations",
                                 headers=headers, files=req_data,
                                 proxies=proxies)
        response.raise_for_status()
        response_data = response.json()

        # Download image.
        for i, data in enumerate(response_data["data"]):
            download_url = data["url"]
            response = requests.get(download_url, proxies=proxies)
            response.raise_for_status()
            content_type = response.headers["content-type"]
            if "image" not in content_type:
                raise RuntimeError(f"Invalid content-type '{content_type}'")
            image_data = response.content

            # Save image
            dirname = f"{IMAGE_DATA_DIR}/generated"
            os.makedirs(dirname, exist_ok=True)
            filename = f"variation-{options['base_image_name']}.png"
            if i >= 1:
                filename = f"{filename}-{i}"
            filepath = f"{dirname}/{filename}"
            with open(filepath, "wb") as f:
                f.write(image_data)

            # Remove temporary files.
            os.remove(options["base_image_filepath"])

            usage_stats = {
                'IMAGE': {
                    "size": req_data["size"],
                    "num_images": 1,
                },
            }

            OPENAI_OT_ProcessMessage.process(
                transaction_id, 'IMAGE',
                {"filepath": filepath, "usage_stats": usage_stats},
                options, exec_params)

        OPENAI_OT_ProcessMessage.process(
            transaction_id, 'END_OF_TRANSACTION', None, None, exec_params)

    @classmethod
    def handle_transcribe_audio_request(
            cls, api_key, transaction_id, req_data, options, exec_params):
        # Send audio.
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        proxies = {
            "http": options["http_proxy"],
            "https": options["https_proxy"],
        }
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=headers, files=req_data, proxies=proxies)
        response.raise_for_status()
        response_data = response.json()

        usage_stats = {}
        if "strip_start" in options and "strip_end" in options:
            # TODO: Improve the statistics by checking the length of
            #       audio file.
            duration = options["strip_end"] - options["strip_start"]
            usage_stats['AUDIO'] = {
                "model": req_data["model"][1],
                "num_seconds": math.ceil(duration / options["fps"]),
            }

        # Post message.
        OPENAI_OT_ProcessMessage.process(
            transaction_id, 'AUDIO',
            {"text": response_data["text"], "usage_stats": usage_stats},
            options, exec_params)
        OPENAI_OT_ProcessMessage.process(
            transaction_id, 'END_OF_TRANSACTION', None, None, exec_params)

    @classmethod
    def handle_chat_request(
            cls, api_key, transaction_id, req_data, options, exec_params):
        user_text = req_data["messages"][0]["content"]
        condition_texts = []
        for text in req_data["messages"][1:]:
            condition_texts.append(text["content"])

        # Save send text.
        dirname = f"{CHAT_DATA_DIR}/topics"
        os.makedirs(dirname, exist_ok=True)
        topic = options["topic"]

        chat_file = ChatTextFile()
        if options["new_topic"]:
            chat_file.new(topic)
        else:
            chat_file.load_from_topic(topic)
        # Response data will be added later
        chat_file.add_part(user_text, condition_texts, "")
        chat_file.save()

        for condition in options["hidden_conditions"]:
            req_data["messages"].append({
                "role": "system",
                "content": condition,
            })

        additional_messages = []
        for part in range(chat_file.num_parts() - 1):
            additional_messages.append({
                "role": "user",
                "content": chat_file.get_user_data(part),
            })
            for condition in chat_file.get_condition_data(part):
                additional_messages.append({
                    "role": "system",
                    "content": condition,
                })
            additional_messages.append({
                "role": "assistant",
                "content": chat_file.get_response_data(part),
            })
            req_data["messages"] = additional_messages + req_data["messages"]

        OPENAI_OT_ProcessMessage.process(
            transaction_id, 'CHAT', {}, options, exec_params)

        # Send prompt.
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        proxies = {
            "http": options["http_proxy"],
            "https": options["https_proxy"],
        }
        response = requests.post("https://api.openai.com/v1/chat/completions",
                                 headers=headers, data=json.dumps(req_data),
                                 proxies=proxies)
        response.raise_for_status()
        response_data = response.json()
        response_text = response_data["choices"][0]["message"]["content"]

        # Save response text.
        chat_file.modify_part(
            chat_file.num_parts() - 1, response_data=response_text)
        chat_file.save()

        usage_stats = {
            'CHAT': {
                "model": req_data["model"],
                "num_tokens": response_data["usage"]["total_tokens"],
            },
        }

        # Post to message queue.
        OPENAI_OT_ProcessMessage.process(
            transaction_id, 'CHAT', {"usage_stats": usage_stats},
            options, exec_params)
        OPENAI_OT_ProcessMessage.process(
            transaction_id, 'END_OF_TRANSACTION', None, None, exec_params)

    @classmethod
    def handle_generate_code_request(
            cls, api_key, transaction_id, req_data, options, exec_params):
        # Send prompt.
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        proxies = {
            "http": options["http_proxy"],
            "https": options["https_proxy"],
        }
        response = requests.post("https://api.openai.com/v1/chat/completions",
                                 headers=headers, data=json.dumps(req_data),
                                 proxies=proxies)
        response.raise_for_status()
        response_data = response.json()
        response_text = response_data["choices"][0]["message"]["content"]

        # Get code body.
        sections = parse_response_data(response_text)
        code_sections = []
        for section in sections:
            if section["kind"] == 'CODE':
                code_sections.append(section)
        if len(code_sections) != 1:
            raise ValueError(
                f"Number of code section must be 1 but {len(code_sections)}")
        code_body = code_sections[0]["body"]

        os.makedirs(CODE_DATA_DIR, exist_ok=True)
        filepath = f"{CODE_DATA_DIR}/{options['code']}.py"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_body)

        usage_stats = {
            'CODE': {
                "model": req_data["model"],
                "num_tokens": response_data["usage"]["total_tokens"],
            },
        }

        # Post to message queue.
        OPENAI_OT_ProcessMessage.process(
            transaction_id, 'CODE', {"usage_stats": usage_stats},
            options, exec_params)
        OPENAI_OT_ProcessMessage.process(
            transaction_id, 'END_OF_TRANSACTION', None, None, exec_params)

    @classmethod
    def handle_edit_code_request(
            cls, api_key, transaction_id, req_data, options, exec_params):
        cls.handle_generate_code_request(
            api_key, transaction_id, req_data, options, exec_params)

    @classmethod
    def handle_generate_code_from_audio_request(
            cls, api_key, transaction_id, req_data, options, exec_params):
        # Send audio.
        audio_request = {
            "file": (
                os.path.basename(options["audio_file"]),
                open(options["audio_file"], "rb")   # pylint: disable=R1732
            ),
            "model": (None, options["audio_model"]),
            "prompt": (None, ""),
            "response_format": (None, "json"),
            "temperature": (None, "0.0"),
            "language": (None, options["audio_language"]),
        }
        audio_headers = {
            "Authorization": f"Bearer {api_key}"
        }
        proxies = {
            "http": options["http_proxy"],
            "https": options["https_proxy"],
        }
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=audio_headers, files=audio_request, proxies=proxies)
        response.raise_for_status()
        response_data = response.json()
        req_data["messages"].append({
            "role": "user",
            "content": response_data["text"],
        })
        options["code"] = response_data["text"][0:64]

        # Send prompt.
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.post("https://api.openai.com/v1/chat/completions",
                                 headers=headers, data=json.dumps(req_data),
                                 proxies=proxies)
        response.raise_for_status()
        response_data = response.json()
        response_text = response_data["choices"][0]["message"]["content"]

        # Get code body.
        sections = parse_response_data(response_text)
        code_sections = []
        for section in sections:
            if section["kind"] == 'CODE':
                code_sections.append(section)
        if len(code_sections) != 1:
            raise ValueError(
                f"Number of code section must be 1 but {len(sections)}")
        code_body = code_sections[0]["body"]

        os.makedirs(CODE_DATA_DIR, exist_ok=True)
        filepath = f"{CODE_DATA_DIR}/{options['code']}.py"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_body)

        usage_stats = {
            # TODO: Add 'AUDIO' stat.
            'CODE': {
                "model": req_data["model"],
                "num_tokens": response_data["usage"]["total_tokens"],
            },
        }

        # Post to message queue.
        OPENAI_OT_ProcessMessage.process(
            transaction_id, 'CODE', {"usage_stats": usage_stats},
            options, exec_params)
        OPENAI_OT_ProcessMessage.process(
            transaction_id, 'END_OF_TRANSACTION', None, None, exec_params)

    @classmethod
    def handle_request(cls, request, exec_params):
        api_key = request[0]
        transaction_id = request[1]
        req_type = request[2]
        req_data = request[3]
        options = request[4]

        if req_type == 'GENERATE_IMAGE':
            cls.handle_generate_image_request(
                api_key, transaction_id, req_data, options, exec_params)
        elif req_type == 'EDIT_IMAGE':
            cls.handle_edit_image_request(
                api_key, transaction_id, req_data, options, exec_params)
        elif req_type == 'GENERATE_VARIATION_IMAGE':
            cls.handle_generate_variation_image_request(
                api_key, transaction_id, req_data, options, exec_params)
        elif req_type == 'TRANSCRIBE_AUDIO':
            cls.handle_transcribe_audio_request(
                api_key, transaction_id, req_data, options, exec_params)
        elif req_type == 'CHAT':
            cls.handle_chat_request(
                api_key, transaction_id, req_data, options, exec_params)
        elif req_type == 'GENERATE_CODE':
            cls.handle_generate_code_request(
                api_key, transaction_id, req_data, options, exec_params)
        elif req_type == 'GENERATE_CODE_FROM_AUDIO':
            cls.handle_generate_code_from_audio_request(
                api_key, transaction_id, req_data, options, exec_params)
        elif req_type == 'EDIT_CODE':
            cls.handle_edit_code_request(
                api_key, transaction_id, req_data, options, exec_params)

    @classmethod
    def send_loop(cls):
        exec_params = {
            "sync": False,
            "context": None,
            "operator_instance": None,
        }

        while True:
            try:
                if cls.should_stop:
                    break

                with cls.request_queue_lock:    # pylint: disable=E1129
                    if len(cls.request_queue) == 0:
                        time.sleep(0.01)
                        continue
                    request = cls.request_queue.pop(0)

                transaction_id = request[1]

                cls.handle_request(request, exec_params)

            except Exception as e:  # pylint: disable=W0703
                # pylint: disable=E0601
                OPENAI_OT_ProcessMessage.process(
                    transaction_id, 'ERROR', {"exception": e}, None,
                    exec_params)
                OPENAI_OT_ProcessMessage.process(
                    transaction_id, 'END_OF_TRANSACTION', None, None,
                    exec_params)


def sync_request(api_key, type_, data, options, context, operator_instance):
    request = [api_key, None, type_, data, options]
    exec_params = {
        "sync": True,
        "context": context,
        "operator_instance": operator_instance,
    }
    RequestHandler.handle_request(request, exec_params)


def async_request(api_key, type_, data, options, transaction_data):
    transaction_id = uuid.uuid4()
    with OPENAI_OT_ProcessMessage.transaction_ids_lock:
        OPENAI_OT_ProcessMessage.transaction_ids[transaction_id] = \
            transaction_data

    request = [api_key, transaction_id, type_, data, options]
    RequestHandler.add_request(request)

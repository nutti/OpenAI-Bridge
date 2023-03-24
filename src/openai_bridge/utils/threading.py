import bpy
import json
import os
import requests
import threading
import time
from urllib.parse import urlparse
import uuid
import re

from ..utils.common import (
    get_area_region_space,
    IMAGE_DATA_DIR,
    CHAT_DATA_DIR,
    CODE_DATA_DIR,
)


class OPENAI_OT_ProcessMessage(bpy.types.Operator):

    bl_idname = "system.openai_process_message"
    bl_description = "Process Message"
    bl_label = "Process Message"

    message_queue_lock = threading.Lock()
    message_queue = []

    transaction_ids = set()
    transaction_ids_lock = threading.Lock()
    _timer = None

    @classmethod
    def exec(cls, transaction_id, type, data, options, sync=False, context=None, operator_instance=None):
        message = {"transaction_id": transaction_id, "type": type, "data": data, "options": options}
        if sync:
            cls.sync_exec(context, operator_instance, message)
        else:
            cls.async_exec(message)

    @classmethod
    def async_exec(cls, message):
        cls.message_queue_lock.acquire()
        cls.message_queue.append(message)
        cls.message_queue_lock.release()

    @classmethod
    def sync_exec(cls, context, operator_instance, message):
        cls.process_message_internal(context, operator_instance, message)

    @classmethod
    def process_message_internal(cls, context, operator_instance, message):
        transaction_id = message["transaction_id"]
        msg_type = message["type"]
        data = message["data"]
        options = message["options"]

        if msg_type == 'IMAGE':
            filepath = data["filepath"]
            new_image = bpy.data.images.load(filepath=filepath)
            # Focus on the generated image in Image Editor.
            _, _, space = get_area_region_space(context, 'IMAGE_EDITOR', 'WINDOW', 'IMAGE_EDITOR')
            if space is not None:
                space.image = new_image
        elif msg_type == 'AUDIO':
            text = data["text"]
            if options["display_target"] == 'TEXT_EDITOR':
                if options["target_text_name"] not in bpy.data.texts:
                    bpy.data.texts.new(options["target_text_name"])
                text_data = bpy.data.texts[options["target_text_name"]]
                text_data.write(text)
                # Focus on the text in Text Editor.
                _, _, space = get_area_region_space(context, 'TEXT_EDITOR', 'WINDOW', 'TEXT_EDITOR')
                if space is not None:
                    space.text = text_data
            elif options["display_target"] == 'TEXT_OBJECT':
                object_data = bpy.data.objects[options["target_text_object_name"]]
                object_data.data.body = text
        elif msg_type == 'CHAT':
            filepath = data["filepath"]
            if options["topic"] not in bpy.data.texts:
                bpy.data.texts.new(options["topic"])
            text_data = bpy.data.texts[options["topic"]]
            text_data.clear()
            with open(filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for l in lines:
                text_data.write(f"{l}")
            # Focus on the chat in Text Editor.
            _, _, space = get_area_region_space(context, 'TEXT_EDITOR', 'WINDOW', 'TEXT_EDITOR')
            if space is not None:
                space.text = text_data
        elif msg_type == 'CODE':
            filepath = data["filepath"]
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

            code_blocks = []
            in_code_block = False
            code = ""
            for l in text.split("\n"):
                if l.startswith("```"):
                    if in_code_block:
                        code_blocks.append(code)
                        in_code_block = False
                    else:
                        code = ""
                        in_code_block = True
                else:
                    if in_code_block:
                        code += f"{l}\n"

            if options["code"] not in bpy.data.texts:
                bpy.data.texts.new(options["code"])
            text_data = bpy.data.texts[options["code"]]
            text_data.clear()
            if len(code_blocks) != 0:
                code = code_blocks[-1]
                text_data.write(code)
                if options["execute_immediately"]:
                    try:
                        exec(code)
                    except Exception as e:
                        error_message = str(e)
                        context.window_manager.clipboard = error_message
                        text_data.clear()
                        text_data.write("Failed to execute the generated code.\n")
                        text_data.write("The error code is copied to the clipboard.\n\n")
                        text_data.write(f"[Code]\n{code}\n\n")
                        text_data.write(f"[Error Message]\n{error_message}\n")
            else:
                text_data.clear()
                text_data.write("Failed to generate code.\nTry Again.\n")
            # Focus on the code in Text Editor.
            _, _, space = get_area_region_space(context, 'TEXT_EDITOR', 'WINDOW', 'TEXT_EDITOR')
            if space is not None:
                space.text = text_data
        elif message["type"] == 'ERROR':
            exception = data["exception"]
            operator_instance.report({'WARNING'}, f"Error: {exception}")
        elif message["type"] == 'END_OF_TRANSACTION':
            return transaction_id

        return None

    def process_message(self, context):
        cls = self.__class__
        cls.message_queue_lock.acquire()
        if len(cls.message_queue) == 0:
            cls.message_queue_lock.release()
            return None
        message = cls.message_queue.pop(0)
        cls.message_queue_lock.release()

        transaction_id = cls.process_message_internal(context, self, message)

        # Update screen.
        for area in context.screen.areas:
            area.tag_redraw()

        return transaction_id

    def modal(self, context ,event):
        cls = self.__class__

        if event.type == 'TIMER':
            msg_key = self.process_message(context)
            if msg_key is not None:
                cls.transaction_ids_lock.acquire()
                assert msg_key in cls.transaction_ids
                cls.transaction_ids.remove(msg_key)
                if len(cls.transaction_ids) == 0:
                    wm = context.window_manager
                    wm.event_timer_remove(cls._timer)
                    cls._timer = None
                    cls.transaction_ids_lock.release()
                    print("Terminated Message Processing Timer")
                    return {'FINISHED'}
                cls.transaction_ids_lock.release()

        return {'PASS_THROUGH'}

    def execute(self, context):
        cls = self.__class__
        wm = context.window_manager

        if cls._timer:
            return {'FINISHED'}

        cls._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        print("Launched Message Processing Timer")

        return {'RUNNING_MODAL'}


class RequestHandler:

    request_queue = []
    request_queue_lock = None
    send_loop_thread = None
    should_stop = True

    @classmethod
    def add_request(cls, request):
        cls.request_queue_lock.acquire()
        cls.request_queue.append(request)
        cls.request_queue_lock.release()

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
    def handle_image_request(cls, api_key, transaction_id, req_data, options, sync, context=None, operator_instance=None):
        # Send prompt.
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.post("https://api.openai.com/v1/images/generations",
                                 headers=headers, data=json.dumps(req_data))
        response.raise_for_status()
        response_data = response.json()

        # Download image.
        for data in response_data["data"]:
            download_url = data["url"]
            response = requests.get(download_url)
            response.raise_for_status()
            content_type = response.headers["content-type"]
            if "image" not in content_type:
                raise RuntimeError(f"Invalid content-type '{content_type}'")
            image_data = response.content

            # Save image
            dirname = IMAGE_DATA_DIR
            os.makedirs(dirname, exist_ok=True)
            if options["image_name"] == "":
                filename = urlparse(download_url).path.split("/")[-1]
            else:
                filename = options["image_name"]
            filepath = f"{dirname}/{filename}"
            with open(filepath, "wb") as f:
                f.write(image_data)

            OPENAI_OT_ProcessMessage.exec(transaction_id, 'IMAGE', {"filepath": filepath}, options, sync=sync, context=context, operator_instance=operator_instance)

        OPENAI_OT_ProcessMessage.exec(transaction_id, 'END_OF_TRANSACTION', None, None, sync=sync, context=context, operator_instance=operator_instance)

    @classmethod
    def handle_audio_request(cls, api_key, transaction_id, req_data, options, sync, context=None, operator_instance=None):
        # Send audio.
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.post("https://api.openai.com/v1/audio/transcriptions",
                                 headers=headers, files=req_data)
        response.raise_for_status()
        response_data = response.json()

        # Post message.
        OPENAI_OT_ProcessMessage.exec(transaction_id, 'AUDIO', {"text": response_data["text"]}, options, sync=sync, context=context, operator_instance=operator_instance)
        OPENAI_OT_ProcessMessage.exec(transaction_id, 'END_OF_TRANSACTION', None, None, sync=sync, context=context, operator_instance=operator_instance)

    @classmethod
    def get_user_text_data(cls, user_text):
        return [f"> {user_text}"]

    @classmethod
    def get_condition_text_data(cls, condition_texts):
        lines = []
        for i, text in enumerate(condition_texts):
            lines.append(f"[Condition {i+1}] {text}")
        return lines

    @classmethod
    def get_old_text_data(cls, filepath):
        if not os.path.isfile(filepath):
            return []

        # Parse all old text data.
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        text_data = []
        sections = text.split("====================\n")
        for section in sections:
            user_data = []
            condition_data = []
            response_data = []

            state = 'USER'
            for line in section.split("\n"):
                if state == 'USER':
                    if line == "---":
                        state = 'CONDITION'
                    elif line.startswith("> "):
                        user_data.append(line[2:])
                elif state == 'CONDITION':
                    if line == "--------------------":
                        state = 'RESPONSE'
                    else:
                        m = re.search(r"^\[Condition [0-9]+\] (.*)", line)
                        if m:
                            condition_data.append(m.group(1))
                elif state == 'RESPONSE':
                    response_data.append(line)

            if state == 'RESPONSE':
                text_data.append({
                    "user_data": "\n".join(user_data),
                    "condition_data": condition_data,
                    "response_data": "\n".join(response_data),
                })

        return text_data

    @classmethod
    def handle_chat_request(cls, api_key, transaction_id, req_data, options, sync, context=None, operator_instance=None):
        user_text = req_data["messages"][0]["content"]
        condition_texts = []
        for text in req_data["messages"][1:]:
            condition_texts.append(text["content"])
        user_text_data = cls.get_user_text_data(user_text)
        condition_text_data = cls.get_condition_text_data(condition_texts)

        # Save send text.
        dirname = f"{CHAT_DATA_DIR}/topics"
        os.makedirs(dirname, exist_ok=True)
        topic = options["topic"]
        filepath = f"{dirname}/{topic}.txt"
        mode = "w" if options["new_topic"] else "a"
        with open(filepath, mode) as f:
            f.write("\n".join(user_text_data))
            f.write("\n")
            f.write("---\n")
            f.write("\n".join(condition_text_data))
            f.write("\n")
            f.write("--------------------")
            f.write("\n" * 2)

        if not options["new_topic"]:
            dirname = f"{CHAT_DATA_DIR}/topics"
            filepath = f"{dirname}/{options['topic']}.txt"
            old_texts = cls.get_old_text_data(filepath)
            additional_messages = []
            for text in old_texts:
                additional_messages.append({
                    "role": "user",
                    "content": text["user_data"],
                })
                for condition in text["condition_data"]:
                    additional_messages.append({
                        "role": "system",
                        "content": condition,
                    })
                additional_messages.append({
                    "role": "assistant",
                    "content": text["response_data"]
                })
            req_data["messages"] = additional_messages + req_data["messages"]

        OPENAI_OT_ProcessMessage.exec(transaction_id, 'CHAT', {"filepath": filepath}, options, sync=sync, context=context, operator_instance=operator_instance)

        # Send prompt.
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.post("https://api.openai.com/v1/chat/completions",
                                 headers=headers, data=json.dumps(req_data))
        response.raise_for_status()
        response_data = response.json()

        # Get text.
        response_text = response_data["choices"][0]["message"]["content"]

        # Save response text.
        with open(filepath, "a") as f:
            f.write(response_text)
            f.write("\n" * 2)
            f.write("====================\n")
            f.write("\n")

        # Post to message queue.
        OPENAI_OT_ProcessMessage.exec(transaction_id, 'CHAT', {"filepath": filepath}, options, sync=sync, context=context, operator_instance=operator_instance)
        OPENAI_OT_ProcessMessage.exec(transaction_id, 'END_OF_TRANSACTION', None, None, sync=sync, context=context, operator_instance=operator_instance)

    @classmethod
    def handle_code_request(cls, api_key, transaction_id, req_data, options, sync, context=None, operator_instance=None):
        user_text = req_data["messages"][0]["content"]
        condition_texts = []
        for text in req_data["messages"][1:]:
            condition_texts.append(text["content"])
        user_text_data = cls.get_user_text_data(user_text)
        condition_text_data = cls.get_condition_text_data(condition_texts)

        # Save send text.
        dirname = f"{CODE_DATA_DIR}/codes"
        os.makedirs(dirname, exist_ok=True)
        code = options["code"]
        filepath = f"{dirname}/{code}.txt"
        mode = "w" if options["mode"] == 'GENERATE' else "a"
        with open(filepath, mode) as f:
            f.write("\n".join(user_text_data))
            f.write("\n")
            f.write("---\n")
            f.write("\n".join(condition_text_data))
            f.write("\n")
            f.write("--------------------")
            f.write("\n" * 2)

        if options["mode"] != 'GENERATE':
            old_texts = cls.get_old_text_data(filepath)
            additional_messages = []
            for text in old_texts:
                additional_messages.append({
                    "role": "user",
                    "content": text["user_data"],
                })
                for condition in text["condition_data"]:
                    additional_messages.append({
                        "role": "system",
                        "content": condition,
                    })
                additional_messages.append({
                    "role": "assistant",
                    "content": text["response_data"]
                })
            req_data["messages"] = additional_messages + req_data["messages"]

        # Send prompt.
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.post("https://api.openai.com/v1/chat/completions",
                                 headers=headers, data=json.dumps(req_data))
        response.raise_for_status()
        response_data = response.json()

        # Get text.
        response_text = response_data["choices"][0]["message"]["content"]

        # Save response text.
        with open(filepath, "a") as f:
            f.write(response_text)
            f.write("\n" * 2)
            f.write("====================\n")
            f.write("\n")

        # Post to message queue.
        OPENAI_OT_ProcessMessage.exec(transaction_id, 'CODE', {"filepath": filepath}, options, sync=sync, context=context, operator_instance=operator_instance)
        OPENAI_OT_ProcessMessage.exec(transaction_id, 'END_OF_TRANSACTION', None, None, sync=sync, context=context, operator_instance=operator_instance)

    @classmethod
    def handle_request(cls, request, sync=False, context=None, operator_instance=None):
        api_key = request[0]
        transaction_id = request[1]
        req_type = request[2]
        req_data = request[3]
        options = request[4]

        if req_type == 'IMAGE':
            cls.handle_image_request(api_key, transaction_id, req_data, options, sync=sync, context=context, operator_instance=operator_instance)
        elif req_type == 'AUDIO':
            cls.handle_audio_request(api_key, transaction_id, req_data, options, sync=sync, context=context, operator_instance=operator_instance)
        elif req_type == 'CHAT':
            cls.handle_chat_request(api_key, transaction_id, req_data, options, sync=sync, context=context, operator_instance=operator_instance)
        elif req_type == 'CODE':
            cls.handle_code_request(api_key, transaction_id, req_data, options, sync=sync, context=context, operator_instance=operator_instance)

    @classmethod
    def send_loop(cls):
        while True:
            try:
                if cls.should_stop:
                    break

                cls.request_queue_lock.acquire()
                if len(cls.request_queue) == 0:
                    cls.request_queue_lock.release()
                    time.sleep(1)
                    continue
                request = cls.request_queue.pop(0)
                cls.request_queue_lock.release()

                transaction_id = request[1]

                cls.handle_request(request)

            except Exception as e:
                OPENAI_OT_ProcessMessage.exec(transaction_id, 'ERROR', {"exception": e}, None, sync=False)
                OPENAI_OT_ProcessMessage.exec(transaction_id, 'END_OF_TRANSACTION', None, None, sync=False)


def sync_request(api_key, type, data, options, context, operator_instance):
    request = [api_key, None, type, data, options]
    RequestHandler.handle_request(request, sync=True, context=context, operator_instance=operator_instance)


def async_request(api_key, type, data, options):
    transaction_id = uuid.uuid4()
    OPENAI_OT_ProcessMessage.transaction_ids_lock.acquire()
    OPENAI_OT_ProcessMessage.transaction_ids.add(transaction_id)
    OPENAI_OT_ProcessMessage.transaction_ids_lock.release()

    request = [api_key, transaction_id, type, data, options]
    RequestHandler.add_request(request)

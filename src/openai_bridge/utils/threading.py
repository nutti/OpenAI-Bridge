import bpy
import json
import os
import requests
import threading
import time
from urllib.parse import urlparse
import uuid

from ..utils.common import (
    get_area_region_space,
    parse_response_data,
    IMAGE_DATA_DIR,
    CHAT_DATA_DIR,
    CODE_DATA_DIR,
    ChatTextFile,
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
    def process(cls, transaction_id, type, data, options, sync=False, context=None, operator_instance=None):
        message = {"transaction_id": transaction_id, "type": type, "data": data, "options": options}
        if sync:
            cls.sync_process(context, operator_instance, message)
        else:
            cls.async_process(message)

    @classmethod
    def async_process(cls, message):
        cls.message_queue_lock.acquire()
        cls.message_queue.append(message)
        cls.message_queue_lock.release()

    @classmethod
    def sync_process(cls, context, operator_instance, message):
        cls.process_message_internal(context, operator_instance, message)

    @classmethod
    def process_message_internal(cls, context: bpy.types.Context, operator_instance, message):
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
            if options["target"] == 'TEXT_EDITOR':
                if options["target_text_name"] not in bpy.data.texts:
                    bpy.data.texts.new(options["target_text_name"])
                text_data = bpy.data.texts[options["target_text_name"]]
                text_data.write(text)
                # Focus on the text in Text Editor.
                _, _, space = get_area_region_space(context, 'TEXT_EDITOR', 'WINDOW', 'TEXT_EDITOR')
                if space is not None:
                    space.text = text_data
            elif options["target"] == 'TEXT_STRIP':
                seq_data = context.scene.sequence_editor.sequences.new_effect(
                    name="Transcript", type='TEXT', channel=options["target_sequence_channel"],
                    frame_start=options["strip_start"], frame_end=options["strip_end"])
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
            if options["execute_immediately"]:
                try:
                    exec(code_to_execute)
                except Exception as e:
                    error_key = ErrorStorage.get_error_key('CODE', code_to_execute, 0, 0)
                    ErrorStorage.store_error(error_key, str(e))
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

            OPENAI_OT_ProcessMessage.process(transaction_id, 'IMAGE', {"filepath": filepath}, options, sync=sync, context=context, operator_instance=operator_instance)

        OPENAI_OT_ProcessMessage.process(transaction_id, 'END_OF_TRANSACTION', None, None, sync=sync, context=context, operator_instance=operator_instance)

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
        OPENAI_OT_ProcessMessage.process(transaction_id, 'AUDIO', {"text": response_data["text"]}, options, sync=sync, context=context, operator_instance=operator_instance)
        OPENAI_OT_ProcessMessage.process(transaction_id, 'END_OF_TRANSACTION', None, None, sync=sync, context=context, operator_instance=operator_instance)

    @classmethod
    def handle_chat_request(cls, api_key, transaction_id, req_data, options, sync, context=None, operator_instance=None):
        user_text = req_data["messages"][0]["content"]
        condition_texts = []
        for text in req_data["messages"][1:]:
            condition_texts.append(text["content"])

        # Save send text.
        dirname = f"{CHAT_DATA_DIR}/topics"
        os.makedirs(dirname, exist_ok=True)
        topic = options["topic"]

        chat_file = ChatTextFile()
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

        OPENAI_OT_ProcessMessage.process(transaction_id, 'CHAT', {}, options, sync=sync, context=context, operator_instance=operator_instance)

        # Send prompt.
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.post("https://api.openai.com/v1/chat/completions",
                                 headers=headers, data=json.dumps(req_data))
        response.raise_for_status()
        response_data = response.json()
        response_text = response_data["choices"][0]["message"]["content"]

        # Save response text.
        chat_file.modify_part(chat_file.num_parts() - 1, response_data=response_text)
        chat_file.save()

        # Post to message queue.
        OPENAI_OT_ProcessMessage.process(transaction_id, 'CHAT', {}, options, sync=sync, context=context, operator_instance=operator_instance)
        OPENAI_OT_ProcessMessage.process(transaction_id, 'END_OF_TRANSACTION', None, None, sync=sync, context=context, operator_instance=operator_instance)

    @classmethod
    def handle_code_request(cls, api_key, transaction_id, req_data, options, sync, context=None, operator_instance=None):
        # Send prompt.
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.post("https://api.openai.com/v1/chat/completions",
                                 headers=headers, data=json.dumps(req_data))
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
            raise ValueError(f"Number of code section must be 1 but {len(sections)}")
        code_body = code_sections[0]["body"]

        os.makedirs(CODE_DATA_DIR, exist_ok=True)
        filepath = f"{CODE_DATA_DIR}/{options['code']}.py"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code_body)

        # Post to message queue.
        OPENAI_OT_ProcessMessage.process(transaction_id, 'CODE', {}, options, sync=sync, context=context, operator_instance=operator_instance)
        OPENAI_OT_ProcessMessage.process(transaction_id, 'END_OF_TRANSACTION', None, None, sync=sync, context=context, operator_instance=operator_instance)

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
                OPENAI_OT_ProcessMessage.process(transaction_id, 'ERROR', {"exception": e}, None, sync=False)
                OPENAI_OT_ProcessMessage.process(transaction_id, 'END_OF_TRANSACTION', None, None, sync=False)


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

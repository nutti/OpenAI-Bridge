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
    IMAGE_DATA_DIR,
    CHAT_DATA_DIR,
)


class OPENAI_OT_ProcessMessage(bpy.types.Operator):

    bl_idname = "system.openai_process_message"
    bl_description = "Process Message"
    bl_label = "Process Message"

    transaction_ids = set()
    transaction_ids_lock = threading.Lock()
    _timer = None

    def process_message(self, context):
        MessageQueue.lock.acquire()
        if len(MessageQueue.data) == 0:
            MessageQueue.lock.release()
            return None
        message = MessageQueue.data.pop(0)
        MessageQueue.lock.release()

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
            if options["remove_file"]:
                os.remove(filepath)
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
            text = data["text"]
            direction = data["direction"]
            if options["text_name"] not in bpy.data.texts:
                bpy.data.texts.new(options["text_name"])
            text_data = bpy.data.texts[options["text_name"]]
            text_data.write(f"{direction} > ")
            lines = text.split("\n")
            for l in lines:
                text_data.write(f"{l}\n")
            # Focus on the chat in Text Editor.
            _, _, space = get_area_region_space(context, 'TEXT_EDITOR', 'WINDOW', 'TEXT_EDITOR')
            if space is not None:
                space.text = text_data
        elif message["type"] == 'ERROR':
            exception = data["exception"]
            self.report({'WARNING'}, f"Error: {exception}")
        elif message["type"] == 'END_OF_TRANSACTION':
            return transaction_id

        # Update screen.
        for area in context.screen.areas:
            area.tag_redraw()

        return None

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


class MessageQueue:
    lock = threading.Lock()
    data = []

    @classmethod
    def add_message(cls, transaction_id, type, data, options):
        cls.lock.acquire()
        cls.data.append({"transaction_id": transaction_id, "type": type, "data": data, "options": options})
        cls.lock.release()


class RequestHandler:

    request_queue = []
    request_queue_lock = None
    send_loop_thread = None
    should_stop = True

    @classmethod
    def add_request(cls, api_key, type, data, options):
        transaction_id = uuid.uuid4()
        OPENAI_OT_ProcessMessage.transaction_ids_lock.acquire()
        OPENAI_OT_ProcessMessage.transaction_ids.add(transaction_id)
        OPENAI_OT_ProcessMessage.transaction_ids_lock.release()

        cls.request_queue_lock.acquire()
        cls.request_queue.append((api_key, transaction_id, type, data, options))
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
    def handle_image_request(cls, api_key, transaction_id, req_data, options):
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

            MessageQueue.add_message(transaction_id, 'IMAGE', {"filepath": filepath}, options)

        MessageQueue.add_message(transaction_id, 'END_OF_TRANSACTION', None, None)

    @classmethod
    def handle_audio_request(cls, api_key, transaction_id, req_data, options):
        # Send audio.
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.post("https://api.openai.com/v1/audio/transcriptions",
                                 headers=headers, files=req_data)
        response.raise_for_status()
        response_data = response.json()

        # Post message.
        MessageQueue.add_message(transaction_id, 'AUDIO', {"text": response_data["text"]}, options)
        MessageQueue.add_message(transaction_id, 'END_OF_TRANSACTION', None, None)

    @classmethod
    def handle_chat_request(cls, api_key, transaction_id, req_data, options):
        send_text = req_data["messages"][0]["content"]
        MessageQueue.add_message(transaction_id, 'CHAT', {"text": send_text, "direction": 'TO'}, options)

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

        # Save text.
        dirname = CHAT_DATA_DIR
        os.makedirs(dirname, exist_ok=True)
        topic = options["topic"]
        filepath = f"{dirname}/{topic}.txt"
        with open(filepath, "w") as f:
            f.write(send_text)
            f.write(response_text)

        # Post to message queue.
        MessageQueue.add_message(transaction_id, 'CHAT', {"text": response_text, "direction": 'FROM'}, options)
        MessageQueue.add_message(transaction_id, 'END_OF_TRANSACTION', None, None)

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

                api_key = request[0]
                transaction_id = request[1]
                req_type = request[2]
                req_data = request[3]
                options = request[4]

                if req_type == 'IMAGE':
                    cls.handle_image_request(api_key, transaction_id, req_data, options)
                elif req_type == 'AUDIO':
                    cls.handle_audio_request(api_key, transaction_id, req_data, options)
                elif req_type == 'CHAT':
                    cls.handle_chat_request(api_key, transaction_id, req_data, options)

            except Exception as e:
                MessageQueue.add_message(transaction_id, 'ERROR', {"exception": e}, None)
                MessageQueue.add_message(transaction_id, 'END_OF_TRANSACTION', None, None)


def async_request(api_key, type, data, options):
    RequestHandler.add_request(api_key, type, data, options)

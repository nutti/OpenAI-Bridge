import wave
import audioop
import os
import threading

SUPPORT_AUDIO_RECORDING = True
try:
    import pyaudio
# pylint: disable=W0702
except:     # noqa
    SUPPORT_AUDIO_RECORDING = False


FORMAT_TO_PYAUDIO_FORMAT = {
    'FLOAT32': pyaudio.paFloat32,
    'INT32': pyaudio.paInt32,
    'INT24': pyaudio.paInt24,
    'INT16': pyaudio.paInt16,
    'INT8': pyaudio.paInt8,
    'UINT8': pyaudio.paUInt8,
}


class AudioRecorder:

    def __init__(
            self, format_='INT16', channels=2, rate=44100, chunk_size=1024,
            silence_threshold=100, silence_duration_limit=3):
        if not SUPPORT_AUDIO_RECORDING:
            raise SystemError("Audio recording is not supported.")

        self.audio = pyaudio.PyAudio()
        self.frames = []
        self.format = FORMAT_TO_PYAUDIO_FORMAT[format_]
        self.channels = channels
        self.rate = rate
        self.chunk_size = chunk_size
        self.silence_threshold = silence_threshold
        self.silence_duration_limit = silence_duration_limit
        self.record_thread = None
        self.recording_status = 'INIT'

    def get_recording_status(self):
        return self.recording_status

    def record_internal(self):
        print(f"Open the audio stream... (Format: {self.format}, "
              f"Channels: {self.channels}, Rate: {self.rate}, "
              f"Chunk: {self.chunk_size})")

        stream = self.audio.open(format=self.format, channels=self.channels,
                                 rate=self.rate, input=True,
                                 frames_per_buffer=self.chunk_size)

        print("Wait recording...")

        # Record the audio and detect silence
        self.frames = []
        self.recording_status = 'WAIT_RECORDING'
        silence_counter = 0
        while self.recording_status in ('RECORDING', 'WAIT_RECORDING'):
            data = stream.read(self.chunk_size)

            if self.recording_status == 'RECORDING':
                self.frames.append(data)

                # Check if the audio is silent
                rms = audioop.rms(data, 2)
                if rms < self.silence_threshold:
                    silence_counter += 1
                else:
                    silence_counter = 0

                # Stop recording if there's been enough silence
                limit = self.silence_duration_limit * self.rate / \
                    self.chunk_size
                limit = int(limit)
                if silence_counter >= limit:
                    self.recording_status = 'FINISHED'
                    print("Recording stopped...")

            elif self.recording_status == 'WAIT_RECORDING':
                rms = audioop.rms(data, 2)
                if rms > self.silence_threshold:
                    self.recording_status = 'RECORDING'
                    print("Recording started...")

        # Stop and close the audio stream
        stream.stop_stream()
        stream.close()
        self.audio.terminate()

        self.recording_status = 'TERMINATED'
        print("Recording terminated.")

    def record(self, async_execution=True):
        if async_execution:
            self.record_thread = threading.Thread(target=self.record_internal)
            self.record_thread.start()
        else:
            self.record_internal()

    def record_ended(self):
        if self.record_thread is None:
            return False
        return not self.record_thread.is_alive()

    def abort_recording(self):
        self.recording_status = 'ABORTED'

    def save(self, filename):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        print("Audio saved to", filename)

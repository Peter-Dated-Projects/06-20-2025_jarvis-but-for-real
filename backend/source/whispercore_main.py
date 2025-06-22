import ffmpeg
import pyaudio
import wave
import os
import time
import numpy as np
import threading

import pvporcupine
import json

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from queue import Queue
from typing import List, Tuple, Dict, Any

from pywhispercpp.model import Model as WhisperModel
from pywhispercpp.model import Segment as WhisperSegment
import traceback

import pickle


# ------------------------------------------------------------ #
# API functions
# ------------------------------------------------------------ #


# Audio Config
class AudioConfig:
    def __init__(self, sample_rate: int, channels: int, audio_format: int):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_format = audio_format

    def __repr__(self):
        return f"AudioConfig(sample_rate={self.sample_rate}, channels={self.channels}, audio_format={self.audio_format})"

    # --------------------------------------------- #

    @staticmethod
    def get_config_from_wav(filename: str) -> "AudioConfig":
        wf = wave.open(filename, "rb")
        sample_rate = wf.getframerate()
        channels = wf.getnchannels()
        audio_format = pyaudio.paInt16
        wf.close()
        return AudioConfig(sample_rate, channels, audio_format)

    def get_sample_rate(self) -> int:
        return self.sample_rate

    def get_sample_size_bytes(self) -> int:
        return pyaudio.get_sample_size(self.audio_format)

    def get_channels(self) -> int:
        return self.channels

    def get_audio_format(self) -> int:
        return self.audio_format

    def get_bytes_per_sample(self) -> int:
        return pyaudio.get_sample_size(self.audio_format)

    def get_bytes_per_second(self) -> int:
        return self.sample_rate * self.get_bytes_per_sample() * self.channels

    def get_samples_per_second(self) -> int:
        return self.sample_rate * self.channels  # No bytes multiplier here


# Async Microphone
class AsyncMicrophone(threading.Thread):

    def __init__(
        self,
        audio_config: AudioConfig,
        desired_config: AudioConfig,
        chunk_size: int,
        picovoice_phrase_files: List[str],
        filename: str = None,
        global_run_config: Dict[str, Any] = None,
    ):
        super().__init__(daemon=True, name=f"AsyncMicrophone-{int(time.time())}")

        self._audio = pyaudio.PyAudio()
        self._stream = None
        self._is_running = False
        self._audio_queue: Queue[np.array] = Queue()
        self._audio_queue_lock = threading.RLock()

        # Add buffer for accumulating audio data
        self._audio_buffer = np.array([], dtype=np.float32)
        self._buffer_lock = threading.RLock()

        # Store the original larger chunk size for whisper
        self._whisper_chunk_size = chunk_size

        # audio settings
        self._audio_config = audio_config
        self._sample_rate = audio_config.sample_rate
        self._audio_format = audio_config.audio_format
        self._channels = audio_config.channels
        self._chunk_size = chunk_size

        # audio properties
        self._bytes_per_sample = self._audio_config.get_bytes_per_sample()
        self._bytes_per_second = self._audio_config.get_bytes_per_second()

        # whisper settings
        self._desired_config = desired_config

        # is reading from a file
        self._is_file = filename is not None
        self._filename = filename

        self._GLOBAL_ARGS = global_run_config

        # create picovoice model instance
        self._porcupine_phrase_files = picovoice_phrase_files
        self._porcupine = pvporcupine.create(
            access_key=os.environ.get("PVPORCUPINE_API", None),
            keyword_paths=self._porcupine_phrase_files,
        )

        if filename:
            self._audio_config = AudioConfig.get_config_from_wav(filename)
            self._sample_rate = self._audio_config.sample_rate
            self._audio_format = self._audio_config.audio_format
            self._channels = self._audio_config.channels

    def run(self):
        """Start the audio stream and process audio data."""

        # If reading from file, stream WAV frames instead of live mic
        if self._is_file:
            # check if file is wav format with correct properties
            if not os.path.exists(self._filename):
                raise FileNotFoundError(f"File not found: {self._filename}")

            # if not wav, use ffmpeg
            if not self._filename.endswith(".wav"):
                # convert to wav
                print(f"Converting {self._filename} to wav format...")
                out_file = self._filename.replace(".m4a", ".wav")
                ffmpeg.input(self._filename).output(
                    out_file,
                    ar=self._desired_config.sample_rate,
                    ac=self._desired_config.channels,
                    acodec="pcm_s16le",
                    format="wav",
                ).run()
                self._filename = out_file

            # open wav file
            wf = wave.open(self._filename, "rb")

            # verify file format matches audio_config
            if (
                not wf.getframerate() == self._sample_rate
                or not wf.getnchannels() == self._channels
                or not wf.getsampwidth() == self._audio_config.get_bytes_per_sample()
            ):
                # use ffmpeg to convert to correct format
                print(
                    f"File format does not match audio_config. Converting {self._filename} to correct format..."
                )
                out_file = self._filename.replace(".wav", "_converted.wav")
                ffmpeg.input(self._filename).output(
                    out_file,
                    ar=self._desired_config.sample_rate,
                    ac=self._desired_config.channels,
                    acodec="pcm_s16le",
                    format="wav",
                ).run()
                self._filename = out_file
                wf = wave.open(self._filename, "rb")
                print(
                    f"Converted {self._filename} to correct format: {self._sample_rate}Hz, {self._channels} channels, {self._audio_config.get_bytes_per_sample()} bytes per sample"
                )

            # begin reading from file at same rate of time as real life
            print(f"Reading from file: {self._filename}")
            self._is_running = True
            while self._is_running:
                raw = wf.readframes(self._chunk_size)
                if not raw:
                    break

                # convert raw bytes to float32 normalized
                audio_data = (
                    np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                )

                # if multi-channel, average to mono
                if self._channels > 1:
                    audio_data = np.mean(
                        audio_data.reshape(-1, self._channels), axis=1
                    ).astype(np.float32)
                    audio_data = audio_data[0]

                # enqueue for processing
                with self._audio_queue_lock:
                    self._audio_queue.put(audio_data)

                # sleep to maintain sample rate
                time.sleep(self._chunk_size / self._sample_rate)

                # pause if not enabled
                if not self._GLOBAL_ARGS["enable_mic"]:
                    print("Pausing microphone recording...")

                    # wait until enabled again
                    while not self._GLOBAL_ARGS["enable_mic"]:
                        time.sleep(0.1)

            wf.close()
            print("Finished reading file.")
            return
        else:
            # ------------------------------------------------------------ #
            # pick a mic to use

            _mic_choices = []
            _info = self._audio.get_host_api_info_by_index(0)
            for i in range(_info["deviceCount"]):
                device = self._audio.get_device_info_by_index(i)
                if device["maxInputChannels"] > 0:
                    _mic_choices.append(device["name"])
                    print(f"Device {i}: {device['name']}")
            print("Select a microphone device:")

            # ------------------------------------------------------------ #
            # query user
            _input = int(input("Press Enter to start recording..."))
            # _input = 0
            print(f"Selected device: {_mic_choices[_input-1]}")

            # open mic stream
            self._stream = self._audio.open(
                format=self._audio_format,
                channels=self._channels,
                rate=self._sample_rate,
                input=True,
                input_device_index=_input,
            )
            print("Recording...")

            # ------------------------------------------------------------ #
            # start recording

            try:
                self._is_running = True
                while self._is_running:

                    # Check if we should process audio
                    self._GLOBAL_ARGS["mic_mutex"].acquire()
                    if self._GLOBAL_ARGS["enable_mic"]:
                        self._GLOBAL_ARGS["mic_mutex"].release()

                        # read audio data from stream
                        audio_data = self._stream.read(
                            self._chunk_size, exception_on_overflow=False
                        )
                        audio_data = np.frombuffer(audio_data, dtype=np.int16)
                        audio_data = audio_data.astype(np.float32) / 32768.0

                        # convert into 1 channel if multiple channels
                        if self._channels > 1:
                            # finds avg b/t channels
                            audio_data = np.mean(
                                # converts into 2d array with 2 cols
                                # 1 col for each channel
                                audio_data.reshape(-1, self._channels),
                                axis=1,
                            ).astype(np.float32)

                            # take first col
                            audio_data = audio_data[0]

                        # push audio into queue + thread safe
                        with self._audio_queue_lock:
                            self._audio_queue.put(audio_data)

                    else:
                        self._GLOBAL_ARGS["mic_mutex"].release()
                        # ------------------------------------------------ #
                        # Read small frames for wake word detection
                        audio_data = self._stream.read(
                            self._porcupine._frame_length, exception_on_overflow=False
                        )
                        # run porcupine code
                        audio_data = np.frombuffer(audio_data, dtype=np.int16)

                        # Wake word detection
                        pvporcupine_result = self._porcupine.process(audio_data)

                        if pvporcupine_result >= 0:
                            print("Wake word detected! Starting recording...")
                            with self._GLOBAL_ARGS["wake_word_mutex"]:
                                self._GLOBAL_ARGS["wake_word_detected"] = True
                            with self._GLOBAL_ARGS["mic_mutex"]:
                                self._GLOBAL_ARGS["enable_mic"] = True

            except KeyboardInterrupt:
                print("Recording stopped by user.")
            except Exception as e:
                print(f"Microphone Recording Error: {e}")

            # ------------------------------------------------------------ #
            # clean up when finished

            self._stream.stop_stream()
            self._stream.close()
            self._audio.terminate()
            self._porcupine.delete()
            print("Audio stream closed.")

    def stop(self):
        """Stop the audio stream."""
        self._is_running = False

    # ------------------------------------------------------------ #
    # helper functions

    def get_sample_rate(self) -> int:
        return self._sample_rate

    def get_audio_format(self) -> int:
        return self._audio_format

    def get_channels(self) -> int:
        return self._channels

    def get_chunk_size(self) -> int:
        return self._chunk_size

    def get_format(self) -> str:
        return self._audio_config.audio_format

    def get_bytes_per_sample(self) -> int:
        return self._bytes_per_sample

    def get_bytes_per_second(self) -> int:
        return self._bytes_per_second

    def get_audio_data(self) -> List[bytes]:
        """Flush audio data from the queue."""
        result = []

        # clear queue
        with self._audio_queue_lock:
            while not self._audio_queue.empty():
                result.append(self._audio_queue.get())

        return result

    def clear_audio_data(self):
        """Clear the audio queue."""
        with self._audio_queue_lock:
            while not self._audio_queue.empty():
                self._audio_queue.get()


class AudioChunk:
    """Audio chunk with proper timing calculations."""

    def __init__(
        self,
        audio_config: AudioConfig,
        default_data: np.ndarray = None,
        start_time: float = 0.0,
    ):
        self._audio_config = audio_config
        self._sample_rate = audio_config.sample_rate

        # Store audio as float32 [-1.0, 1.0]
        self._samples = (
            default_data if default_data is not None else np.array([], dtype=np.float32)
        )

        # Time tracking (in seconds)
        self._start_time = start_time
        self._num_samples = len(self._samples)
        self._end_time = start_time + (self._num_samples / self._sample_rate)

    def append_audio_data(self, audio_data: np.ndarray):
        """Append audio data to the chunk."""
        if len(audio_data) == 0:
            return

        self._samples = np.concatenate((self._samples, audio_data))
        self._num_samples = len(self._samples)
        self._end_time = self._start_time + (self._num_samples / self._sample_rate)

    def get_audio_from_time(
        self, start_time: float, end_time: float = -1
    ) -> np.ndarray:
        """Get audio data for a specified time range (in seconds)."""
        if end_time == -1:
            end_time = self._end_time

        # Make sure times are within chunk bounds
        if start_time > self._end_time or end_time < self._start_time:
            # This chunk doesn't contain data for the requested time range
            return np.array([], dtype=np.float32)

        # Clamp times to chunk boundaries
        start_time = max(start_time, self._start_time)
        end_time = min(end_time, self._end_time)

        # Convert to sample indices
        start_sample = int((start_time - self._start_time) * self._sample_rate)
        end_sample = int((end_time - self._start_time) * self._sample_rate)

        # Ensure valid indices
        start_sample = max(0, min(start_sample, self._num_samples))
        end_sample = max(start_sample, min(end_sample, self._num_samples))

        # Return the slice
        return self._samples[start_sample:end_sample]

    def get_audio_duration(self) -> float:
        """Get duration of the audio in seconds."""
        return self._num_samples / self._sample_rate

    def get_samples(self) -> np.ndarray:
        """Get all audio samples."""
        return self._samples

    def __len__(self):
        """Get the number of samples."""
        return self._num_samples


class AudioStorage:
    """Audio storage with correct timing and sample handling."""

    def __init__(self, audio_config: AudioConfig, max_chunk_duration: float = 10.0):
        self._audio_config = audio_config
        self._sample_rate = audio_config.sample_rate
        self._total_duration = 0.0

        # Audio storage in chunks
        self._chunks = []
        self._audio_cache_lock = threading.RLock()
        self._max_chunk_duration = max_chunk_duration  # seconds per chunk

    def append_audio(self, audio_data: np.ndarray):
        """Add audio data to storage."""
        if len(audio_data) == 0:
            return

        with self._audio_cache_lock:
            # Create first chunk if needed
            if not self._chunks:
                self._chunks.append(AudioChunk(self._audio_config))

            # If current chunk is full, create a new one
            current_chunk = self._chunks[-1]
            if current_chunk.get_audio_duration() >= self._max_chunk_duration:
                new_chunk = AudioChunk(
                    self._audio_config, start_time=self._total_duration
                )
                self._chunks.append(new_chunk)
                current_chunk = new_chunk

            # Add the data
            current_chunk.append_audio_data(audio_data)

            # Update total duration
            added_duration = len(audio_data) / self._sample_rate
            self._total_duration += added_duration

    def get_audio_range_seconds(
        self, start_sec: float, end_sec: float = -1
    ) -> np.ndarray:
        """Get audio data for a time range in seconds."""
        with self._audio_cache_lock:
            # Handle default end time
            if end_sec == -1:
                end_sec = self._total_duration

            # Validate inputs
            if start_sec < 0:
                start_sec = 0
            if end_sec > self._total_duration:
                end_sec = self._total_duration
            if start_sec >= end_sec:
                return np.array([], dtype=np.float32)

            # Collect audio from chunks
            result = np.array([], dtype=np.float32)
            for chunk in self._chunks:
                chunk_data = chunk.get_audio_from_time(start_sec, end_sec)
                if len(chunk_data) > 0:
                    result = np.concatenate((result, chunk_data))

            return result

    def get_audio_range_millis(self, start_ms: int, end_ms: int = -1) -> np.ndarray:
        """Get audio data for a time range in milliseconds."""
        # Convert milliseconds to seconds and use the seconds method
        start_sec = start_ms / 1000.0
        end_sec = end_ms / 1000.0 if end_ms != -1 else -1
        return self.get_audio_range_seconds(start_sec, end_sec)

    def get_total_duration_seconds(self) -> float:
        """Get total duration of all audio in seconds."""
        with self._audio_cache_lock:
            return self._total_duration

    def get_total_duration_millis(self) -> int:
        """Get total duration of all audio in milliseconds."""
        return int(self.get_total_duration_seconds() * 1000)

    def seconds_to_millis(self, seconds: float) -> int:
        """Convert seconds to milliseconds."""
        return int(seconds * 1000)

    def millis_to_seconds(self, millis: int) -> float:
        """Convert milliseconds to seconds."""
        return millis / 1000.0

    def reset(self):
        """Reset the audio storage."""
        with self._audio_cache_lock:
            self._chunks = []
            self._total_duration = 0.0

    def __iter__(self):
        """Iterate over chunks."""
        for chunk in self._chunks:
            yield chunk


class WhisperCoreSave:
    def __init__(self, audio_storage: AudioStorage, segments: List[WhisperSegment]):
        self._audio_storage = audio_storage
        self._saved_segments = segments

    # ------------------------------------------------------------ #
    # io functions

    def save(self, save_file: str):
        """
        Save the current state to a single file.

        File Format:
        [1] Header Segment
        [2] Whisper Model Config
        [3] Audio File Storage
        [4] Whisper Segment Storage

        """
        # 15 in length
        _header = b"WhisperCoreSave"

        # model config
        _config_chunk = {"bytes": pickle.dumps(self._audio_storage._audio_config)}

        # model audio chunks
        _audio_chunks = {
            "count": len(self._audio_storage._chunks),
            "duration": self._audio_storage.get_total_duration_millis(),
            "max_chunk_duration": self._audio_storage._max_chunk_duration,
            "chunks": [],
        }
        for i, chunk in enumerate(self._audio_storage._chunks):
            _audio_chunks["chunks"].append(
                {
                    "index": i,
                    "start_time": chunk._start_time,
                    "end_time": chunk._end_time,
                    "samples": chunk.get_samples(),
                }
            )

        # segment data
        _segment_data = {
            "count": len(self._saved_segments),
            "segments": [pickle.dumps(seg) for seg in self._saved_segments],
        }

        result = {
            "header": _header,
            "config": _config_chunk,
            "audio_chunks": _audio_chunks,
            "segment_data": _segment_data,
        }

        # write to file as json
        with open(save_file, "wb") as f:
            pickle.dump(result, f)


class WhisperSegmentChunk:
    def __init__(self, timestamp: float, segment: WhisperSegment):
        self.timestamp = timestamp
        self.segment = segment


# whisper core
class WhisperCore:
    """
    Here's the idea:
    - function to add new audio data
    - function to process all audio data

    Data Retrieval:
    - user can only retrieve transcription data
    """

    def __init__(
        self,
        model: str,
        audio_storage: AudioStorage,
        **kwargs,
    ):
        self._audio_storage = audio_storage
        self._model = WhisperModel(model, **kwargs)
        self._model_lock = threading.RLock()

        # results container
        self._results_container = []
        self._results_container_lock = threading.RLock()
        self._whisper_model_lock = threading.RLock()

        # threading
        self._thread_pool = ThreadPoolExecutor(max_workers=1)

        # inactivity detection system
        self._last_activity = [time.time(), None]

    # ------------------------------------------------------------ #
    # audio processing / transcription functions

    def update_stream(self):
        """Updates the transcription with new audio data using correct time handling."""

        # here's how i'm going to approach this:
        #   - retrieve audio data range from audio storage
        #   - transcribe audio data
        #   - add results to results container
        #   - update audio storage with new results

        # STEP 1
        start_millis = 0
        end_millis = -1  # always the end

        with self._results_container_lock:
            # find the proper start of the audio
            if not len(self._results_container):
                # add empty segment item
                _obj = WhisperSegmentChunk(
                    time.time(),
                    WhisperSegment(
                        t0=0,
                        t1=0,
                        text="",
                    ),
                )
                self._results_container.append(_obj)

            elif len(self._results_container) > 1:
                # yes results, start from end of last results
                start_millis = int(self._results_container[-1].segment.t0)

        # STEP 2
        with self._audio_storage._audio_cache_lock:
            audio_clip = self._audio_storage.get_audio_range_millis(
                start_millis, end_millis
            )
        if len(audio_clip) == 0:
            # no audio data to process
            return
        # print("Time Range", start_millis, end_millis)
        # print("Audio Clip Size", len(audio_clip))
        # print("Audio Clip Duration", len(audio_clip) / self._audio_storage._sample_rate)

        # STEP 3
        results = self.transcribe_audio(audio_clip)
        if len(results) == 0:
            # no results to process
            return

        # STEP 4
        for seg in results:
            seg.t0 += start_millis
            seg.t1 += start_millis
            seg.text = seg.text.strip()

        # just check last segment for updates + etc -- detection algo
        if (
            self._last_activity[1] is not None
            and self._last_activity[1] != results[-1].text
        ):
            # update last activity
            self._last_activity[0] = time.time()
            self._last_activity[1] = results[-1].text
        if not self._last_activity[1]:
            self._last_activity[0] = time.time()
            self._last_activity[1] = results[-1].text

        # STEP 5
        # update results container with new results
        with self._results_container_lock:
            _old_text = self._results_container[-1].segment.text
            _new_text = results[0].text
            self._results_container[-1].segment = results[0]

            # only change timestamp if text changes
            if _old_text.strip() != _new_text.strip():
                self._results_container[-1].timestamp = time.time()

            if len(results) > 1:
                # add new results
                for seg in results[1:]:
                    # add new segment to results container
                    self._results_container.append(
                        WhisperSegmentChunk(time.time(), seg)
                    )

    def transcribe_audio(self, audio_data: np.array, **kwargs):
        """
        Transcribe audio data

        kwargs:
        - language: str

        """
        # check if audio is in right format
        if not isinstance(audio_data, np.ndarray):
            raise TypeError(
                f"audio_data must be of type np.ndarray, not {type(audio_data)}"
            )
        if audio_data.ndim != 1:
            raise ValueError(
                f"audio_data must be 1D array, not {audio_data.ndim}D array"
            )
        if audio_data.dtype != np.float32:
            raise ValueError(
                f"audio_data must be of type np.float32, not {audio_data.dtype}"
            )

        # transcribe audio data
        with self._whisper_model_lock:
            results = self._model.transcribe(
                audio_data,
                **kwargs,
            )

        # process results
        for seg in results:
            seg.t0 *= 10
            seg.t1 *= 10
            seg.text = seg.text.strip()

        return list(results)

    def transcribe_file(self, audio_file: str, **kwargs):
        """Transcribe audio file."""
        # check if file exists
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"File not found: {audio_file}")

        # check if file is wav format
        if not audio_file.endswith(".wav"):
            raise ValueError("File must be in wav format")

        # transcribe audio file
        with self._whisper_model_lock:
            results = self._model.transcribe(
                audio_file,
                **kwargs,
            )

        # process results
        for seg in results:
            seg.t0 *= 10
            seg.t1 *= 10
            seg.text = seg.text.strip()

        return list(results)

    def reset_stream(self, save: bool = False) -> WhisperCoreSave:
        """Reset the transcription stream."""
        instance = None
        if save:
            instance = WhisperCoreSave(
                self._audio_storage,
                self._results_container,
            )

        # clear the results container and audio storage
        with self._results_container_lock:
            # reset the results container
            self._results_container.clear()
            # reset the audio storage
            self._audio_storage.reset()

        # reset the last activity
        self._last_activity = [time.time(), None]

        print(self._last_activity)
        return instance

    def get_save(self) -> WhisperCoreSave:
        """Get the current state of the transcription stream."""
        return WhisperCoreSave(
            self._audio_storage,
            self._results_container,
        )

    def restore_save(self, save: WhisperCoreSave):
        """Restore the transcription stream from a saved state."""
        with self._results_container_lock:
            self._audio_storage = save._audio_storage
            self._results_container = save._saved_segments

    def has_new_phrases(self, timeout: float = 1.0) -> bool:
        """
        Check if there are new phrases in the results container.

        Args:
            timeout (float): Time in seconds to consider activity as "recent"

        Returns:
            bool: True if there has been phrase activity within the timeout period
        """
        # If we're just starting (no text yet), give more time
        # if self._last_activity[1] is None:
        #     return True  # Always return true immediately after reset

        # Normal timing check
        time_since_activity = time.time() - self._last_activity[0]
        return time_since_activity < timeout


# ------------------------------------------------------------ #
# main
# ------------------------------------------------------------ #


def run_whisper_core(
    toggles: Dict[str, Any],
):
    """
    Toggles = {
        # mic
        "enable_mic": False,
        "mic_mutex": threading.RLock(),

        # whispercore
        "enable_whispercore": False,
        "whispercore_mutex": threading.RLock(),

        # wake word
        "wake_word_detected": False,
        "wake_word_mutex": threading.RLock(),


        # for thread -- disables duplicates
        "threads_mutex": threading.RLock(),
    }


    Whenever these events happen:
    - update segment -> GET
    - new segment -> GET
    - finished recording -> GET
    - inactive -> GET
    - error -> GET

    Then the backend handles it accordingly

    """

    with toggles["threads_mutex"]:
        # check if threads are running
        active_threads = threading.enumerate()
        existing_mics = [
            t for t in active_threads if isinstance(t, AsyncMicrophone) and t.is_alive()
        ]

        if len(existing_mics) > 0:
            print("Microphone is already in use.")

            # stop other mics
            for mic in existing_mics:
                print(f"Stopping microphone: {mic.name}")
                mic.stop()
                mic.join(timeout=1.0)
            return

    # ------------------------------------------------------------ #
    # create objects

    # start printing out mic audio
    UPDATE_INTERVAL = 0.25
    WHISPERCORE_INACTIVITY_TIMEOUT = 3.0  # seconds

    SAMPLE_RATE = 16000  # samples per sec
    CHUNK_SIZE = 1024 * 4  # samples per chunk
    FORMAT = pyaudio.paInt16  # 16-bit signed int
    CHANNELS = 1  # channels

    A_CONFIG = AudioConfig(SAMPLE_RATE, CHANNELS, FORMAT)
    WHISPER_CONFIG = AudioConfig(SAMPLE_RATE, 1, FORMAT)

    mic = AsyncMicrophone(
        A_CONFIG,
        WHISPER_CONFIG,
        chunk_size=CHUNK_SIZE,
        # filename="whispercpp-audio-test.wav",
        global_run_config=toggles,
        picovoice_phrase_files=[
            "assets/porcupine/Hey-SONA_en_mac_v3_0_0.ppn",
        ],
    )

    audio_storage = AudioStorage(WHISPER_CONFIG)
    whisper = WhisperCore(
        os.environ.get("WHISPER_MODEL_FILE", "assets/models/ggml-small.en.bin"),
        audio_storage,
        # redirect_whispercpp_logs_to="stdout",
    )

    # ------------------------------------------------------------ #
    # start mic thread
    mic.start()
    print("Waiting for microphone to start...")
    while not mic._is_running:
        time.sleep(0.1)

    # ------------------------------------------------------------ #
    # start the model
    try:

        running = True
        while running:

            # ------------------------------------------------------------- #
            # pause the whispercore if not toggled
            toggles["whispercore_mutex"].acquire()
            if not toggles["enable_whispercore"]:
                toggles["whispercore_mutex"].release()

                # debug
                print("\n" * 2)
                print("Pausing WhisperCore processing...")

                # pause
                while True:
                    with toggles["wake_word_mutex"]:
                        if toggles["wake_word_detected"]:
                            break
                    time.sleep(0.1)

                print("Wake word detected, resuming processing...")
                print("\n" * 2)

                # wake word was detected, resume processing
                with toggles["wake_word_mutex"]:
                    toggles["wake_word_detected"] = False
                with toggles["whispercore_mutex"]:
                    toggles["enable_whispercore"] = True
                print("Resuming WhisperCore processing...")

                # reset the audio storage
                whisper.reset_stream()

            # ------------------------------------------------------------ #
            # get start time
            start_time = time.time()

            print("# --------------------------------------------- #")
            # retrieve audio data for this segment
            print("Recording Audio...")
            with mic._audio_queue_lock:
                _audio_batch: List[np.array] = mic.get_audio_data()

            # get stats
            _blob_count = len(_audio_batch)
            _audio_size = sum([len(x) for x in _audio_batch])
            _audio_time = _audio_size / mic.get_bytes_per_second()

            # add audio to storage
            for blob in _audio_batch:
                audio_storage.append_audio(blob)

            whisper.update_stream()

            # ---------------------------------------------- #
            # logic to determine if continue detecting or not
            # if no new phrases in 1 second, end stt
            if not whisper.has_new_phrases(WHISPERCORE_INACTIVITY_TIMEOUT):
                print("No new phrases detected, ending STT...")
                # start blocking everything again
                with toggles["whispercore_mutex"]:
                    toggles["enable_whispercore"] = False
                with toggles["mic_mutex"]:
                    toggles["enable_mic"] = False
                print("WhisperCore processing paused.")

            # --------------------------------------------- #

            # print stats
            print(f"Audio blob count: {_blob_count}")
            print(f"Audio blob size: {_audio_size} bytes")
            print(f"Audio blob time: {_audio_time:.2f} seconds")
            print()
            # print out audio storage stats
            total_duration = audio_storage.get_total_duration_seconds()
            print(f"Audio storage total duration: {total_duration:.2f} seconds")

            # iterate over each audio chunk stored in audio_storage
            # for i, chunk in enumerate(audio_storage):
            #     chunk_duration = chunk.get_audio_duration()
            #     num_samples = len(chunk)
            #     print(f"Chunk {i}:")
            #     print(f"  Samples: {num_samples}")
            #     print(f"  Duration: {chunk_duration:.2f} seconds")
            #     print(f"  Start time: {chunk._start_time:.2f} seconds")
            #     print(f"  End time: {chunk._end_time:.2f} seconds")
            # print()
            for i, seg in enumerate(whisper._results_container):
                print(f"Segment {i}:")
                print(f"    Text: {seg.segment.text}")
                print(f"    Start: {seg.segment.t0:.4f} ms")
                print(f"    End: {seg.segment.t1:.4f} ms")
                print(f"    Last Edited: {time.time() - seg.timestamp:.4f} seconds")

            print(f"Total segments processed: {len(whisper._results_container)}")

            print()

            # --------------------------------------------- #
            # process audio

            computational_delta = time.time() - start_time
            if computational_delta < UPDATE_INTERVAL:
                # sleep for the remaining time
                time.sleep(UPDATE_INTERVAL - computational_delta)

    # ------------------------------------------------------------ #

    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Main Thread Error: {e}")
        tb = traceback.extract_tb(e.__traceback__)
        for frame in tb:
            print(
                f"File: {frame.filename}, Function: {frame.name}, Line: {frame.lineno}"
            )
    finally:
        mic.stop()
        mic.join()
        print("Exiting...")
        # save the data
        whisper.get_save().save("whispercpp-audio-test.save")
        os._exit(0)

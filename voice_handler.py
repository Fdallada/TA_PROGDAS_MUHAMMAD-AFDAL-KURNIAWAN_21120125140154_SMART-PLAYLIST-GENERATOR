import speech_recognition as sr
import threading

class VoiceRecognizer:
    def __init__(self, callback):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        try:
            self.microphone = sr.Microphone()
        except Exception as e:
            print("Microphone init error:", e)
            self.microphone = None
        self.callback = callback
        self._recording = False
        self._audio_data = None

    def start_listening(self):
        if self._recording:
            return
        if self.microphone is None:
            print("No microphone available.")
            return
        self._recording = True
        t = threading.Thread(target=self._record_thread, daemon=True)
        t.start()

    def stop_listening(self):
        if not self._recording:
            return
        self._recording = False
        t = threading.Thread(target=self._process_thread, daemon=True)
        t.start()

    def _record_thread(self):
        try:
            with self.microphone as src:
                self.recognizer.adjust_for_ambient_noise(src, duration=0.5)
                print("[voice] start listening...")
                self._audio_data = self.recognizer.listen(src, timeout=None, phrase_time_limit=None)
                print("[voice] raw audio captured")
        except Exception as e:
            print("[voice] record error:", e)
            self._audio_data = None
            self._recording = False

    def _process_thread(self):
        if not self._audio_data:
            return
        try:
            print("[voice] processing...")
            text = self.recognizer.recognize_google(self._audio_data, language="id-ID")
            print("[voice] recognized:", text)
            if callable(self.callback):
                # callback may interact with GUI; GUI should schedule into main thread
                self.callback(text)
        except sr.UnknownValueError:
            print("[voice] tidak bisa mengenali suara")
        except sr.RequestError:
            print("[voice] request error (cek koneksi)")
        except Exception as e:
            print("[voice] processing error:", e)

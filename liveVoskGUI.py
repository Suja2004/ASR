import tkinter as tk
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import threading
import time
import re
from collections import deque
import difflib


class SpeechRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech Recognition - Final Results Only")
        self.root.geometry("1000x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Initialize running state
        self.running = True

        # Setup Vosk
        try:
            self.model = Model(r"C:\Users\DELL\PycharmProjects\ASR\vosk-model-small-en-us-0.15")
            self.recognizer = KaldiRecognizer(self.model, 16000)

            # Setup audio stream
            self.mic = pyaudio.PyAudio()
            self.stream = self.mic.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8192
            )
            self.stream.start_stream()
            self.setup_successful = True
        except Exception as e:
            self.setup_successful = False
            print(f"Error initializing: {e}")

        # UI Components
        self.top_frame = tk.Frame(root, bg="#f0f0f0", pady=10)
        self.top_frame.pack(fill=tk.X)

        self.status_label = tk.Label(
            self.top_frame,
            text="Status: Initializing...",
            font=("Segoe UI", 12),
            fg="#444444",
            bg="#f0f0f0"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        self.live_label = tk.Label(
            self.top_frame,
            text="Listening...",
            font=("Segoe UI", 14, "italic"),
            fg="#666666",
            bg="#f0f0f0",
            wraplength=700
        )
        self.live_label.pack(side=tk.RIGHT, padx=10)

        self.separator = tk.Frame(root, height=2, bg="#cccccc")
        self.separator.pack(fill=tk.X, padx=10)

        # Main transcript area
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.main_box = tk.Text(
            self.main_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 14),
            padx=10,
            pady=10
        )
        self.main_box.pack(side=tk.LEFT, expand=True, fill="both")

        self.scrollbar = tk.Scrollbar(self.main_frame, command=self.main_box.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_box.config(yscrollcommand=self.scrollbar.set)
        self.main_box.config(state=tk.DISABLED)

        # Button frame
        self.button_frame = tk.Frame(root, pady=10)
        self.button_frame.pack()

        self.reset_button = tk.Button(
            self.button_frame,
            text="Reset Transcript",
            command=self.reset_transcript,
            font=("Segoe UI", 12),
            padx=10,
            pady=5,
            bg="#f44336",
            fg="white"
        )
        self.reset_button.pack(side=tk.LEFT, padx=10)

        self.toggle_button = tk.Button(
            self.button_frame,
            text="Pause Recognition",
            command=self.toggle_recognition,
            font=("Segoe UI", 12),
            padx=10,
            pady=5,
            bg="#2196f3",
            fg="white"
        )
        self.toggle_button.pack(side=tk.LEFT, padx=10)

        # For handling text processing
        self.full_transcript = ""  # The complete transcript text
        self.recent_segments = deque(maxlen=10)  # Store recent text segments for comparison
        self.recognition_active = True
        self.min_similarity_threshold = 0.7  # Threshold for considering text similar

        if self.setup_successful:
            self.status_label.config(text="Status: Ready")
            # Start listening thread
            self.listen_thread = threading.Thread(target=self.listen, daemon=True)
            self.listen_thread.start()
        else:
            self.status_label.config(text="Status: Failed to initialize")

    def reset_transcript(self):
        """Clear the transcript and reset processing variables"""
        self.full_transcript = ""
        self.recent_segments.clear()
        self.update_mainbox("")
        self.status_label.config(text="Status: Transcript Reset")

    def toggle_recognition(self):
        """Toggle speech recognition on/off"""
        self.recognition_active = not self.recognition_active
        if self.recognition_active:
            self.toggle_button.config(text="Pause Recognition", bg="#2196f3")
            self.status_label.config(text="Status: Recognition Active")
        else:
            self.toggle_button.config(text="Resume Recognition", bg="#4caf50")
            self.status_label.config(text="Status: Recognition Paused")

    def similarity_ratio(self, text1, text2):
        """Calculate similarity between two text segments using difflib"""
        return difflib.SequenceMatcher(None, text1, text2).ratio()

    def is_duplicate_segment(self, text):
        """Check if text is too similar to recent segments"""
        if not text:
            return True

        # Clean text
        cleaned_text = re.sub(r'\s+', ' ', text).strip().lower()
        if not cleaned_text:
            return True

        # Check against recent segments
        for recent in self.recent_segments:
            similarity = self.similarity_ratio(cleaned_text, recent)
            if similarity > self.min_similarity_threshold:
                return True

        # Check if this is contained in the last part of transcript
        last_part = self.full_transcript.lower().split()[-20:]
        last_part_text = " ".join(last_part) if last_part else ""

        if cleaned_text in last_part_text:
            return True

        return False

    def add_text_to_transcript(self, text):
        """Add new text to transcript, avoiding repetition"""
        if not text or self.is_duplicate_segment(text):
            return False

        # Clean and prepare text
        cleaned_text = re.sub(r'\s+', ' ', text).strip()

        # Add to recent segments for future comparison
        self.recent_segments.append(cleaned_text.lower())

        # Add to transcript with proper spacing and capitalization
        if self.full_transcript:
            # Add appropriate punctuation/spacing
            if self.full_transcript[-1] in ".!?":
                self.full_transcript += " " + cleaned_text.capitalize()
            else:
                self.full_transcript += ". " + cleaned_text.capitalize()
        else:
            self.full_transcript = cleaned_text.capitalize()

        return True

    def safe_ui_update(self, func):
        """Safely update UI elements from any thread"""
        try:
            self.root.after(0, func)
        except Exception as e:
            print(f"UI update error: {e}")

    def update_mainbox(self, new_text=None):
        """Update the main transcript box"""

        def _update():
            self.main_box.config(state=tk.NORMAL)
            self.main_box.delete(1.0, tk.END)

            # Use provided text or full transcript
            text_to_display = new_text if new_text is not None else self.full_transcript

            self.main_box.insert(tk.END, text_to_display)
            self.main_box.see(tk.END)
            self.main_box.config(state=tk.DISABLED)

        self.safe_ui_update(_update)

    def update_live_label(self, text):
        """Update the live speech label"""

        def _update():
            self.live_label.config(text=text)

        self.safe_ui_update(_update)

    def update_status(self, text):
        """Update the status label"""

        def _update():
            self.status_label.config(text=text)

        self.safe_ui_update(_update)

    def listen(self):
        """Main listening function that processes audio and updates transcript"""
        speaking = False
        silence_time = 0

        while self.running:
            try:
                if not self.recognition_active:
                    time.sleep(0.1)
                    continue

                data = self.stream.read(4096, exception_on_overflow=False)

                if self.recognizer.AcceptWaveform(data):
                    # Only process final results
                    result = json.loads(self.recognizer.Result())
                    final_text = result.get("text", "").strip()

                    if final_text:
                        speaking = True
                        silence_time = 0

                        # Show in live display briefly
                        self.update_live_label(f"Final: {final_text}")

                        # Add to transcript if not a duplicate
                        if self.add_text_to_transcript(final_text):
                            self.update_mainbox()
                            self.update_status(f"Status: Added new text")
                        else:
                            self.update_status(f"Status: Duplicate text ignored")

                        # Reset live display after a short delay
                        self.root.after(1000, lambda: self.update_live_label("Listening..."))
                else:
                    # We still process partial results to update the live label
                    # but we don't add them to the transcript
                    partial_result = json.loads(self.recognizer.PartialResult())
                    partial_text = partial_result.get("partial", "").strip()

                    if partial_text:
                        speaking = True
                        silence_time = 0
                        self.update_live_label(f"Listening: {partial_text}")
                    else:
                        # No speech detected
                        if speaking:
                            silence_time += 0.1
                            if silence_time > 1.0:  # After 1 second of silence
                                speaking = False
                                self.update_live_label("Listening...")

                time.sleep(0.1)  # Prevent CPU hogging

            except Exception as e:
                print(f"Error in listen thread: {e}")
                self.update_status(f"Error: {str(e)[:30]}...")
                time.sleep(1)

    def on_closing(self):
        """Clean up resources when window is closed"""
        self.running = False
        time.sleep(0.2)  # Give thread time to exit

        # Clean up audio resources
        if hasattr(self, 'stream') and self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'mic') and self.mic:
            self.mic.terminate()

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SpeechRecognitionApp(root)
    root.mainloop()
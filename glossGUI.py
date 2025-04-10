import tkinter as tk
from tkinter import ttk
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import threading
import time
import re
from collections import deque
import difflib
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
import os


class GlossConverter:
    """Class for converting English text to sign language gloss notation"""

    def __init__(self):
        # Check if NLTK data exists and download if needed
        self.ensure_nltk_resources()

        # Stopwords with pronouns kept
        self.stop_words = set(stopwords.words('english')) - {
            'i', 'you', 'we', 'he', 'she', 'they', 'me', 'my', 'your', 'our', 'his', 'her', 'their'
        }

        # Mapping for common words to their gloss representation
        self.gloss_map = {
            "i": "ME", "you": "YOU", "we": "US", "he": "HE", "she": "SHE", "they": "THEY",
            "am": "", "is": "", "are": "", "was": "", "were": "",
            "going": "GO", "go": "GO", "want": "WANT", "have": "HAVE", "had": "HAVE",
            "don't": "NOT", "not": "NOT", "doesn't": "NOT", "didn't": "NOT",
            "store": "STORE", "because": "", "milk": "MILK", "to": "",
            "the": "", "a": "", "an": "", "and": "", "or": "", "but": "",
            "this": "THIS", "that": "THAT", "these": "THESE", "those": "THOSE",
            "for": "FOR", "with": "WITH", "without": "WITHOUT",
            "can": "CAN", "cannot": "CANNOT", "could": "COULD", "would": "WOULD", "should": "SHOULD",
            "yes": "YES", "no": "NO", "maybe": "MAYBE",
            "like": "LIKE", "need": "NEED", "think": "THINK",
            "today": "TODAY", "tomorrow": "TOMORROW", "yesterday": "YESTERDAY",
            "now": "NOW", "later": "LATER", "soon": "SOON",
            "here": "HERE", "there": "THERE"
        }

    def ensure_nltk_resources(self):
        """Ensure NLTK resources are downloaded"""
        nltk_data_path = os.path.expanduser('~/nltk_data')

        # Check if the resources already exist
        punkt_exists = os.path.exists(os.path.join(nltk_data_path, 'tokenizers', 'punkt'))
        stopwords_exists = os.path.exists(os.path.join(nltk_data_path, 'corpora', 'stopwords'))

        # Download only if needed
        if not punkt_exists:
            nltk.download('punkt', quiet=True)
        if not stopwords_exists:
            nltk.download('stopwords', quiet=True)

    def convert_to_sign_gloss(self, text):
        """Convert English text to sign language gloss notation"""
        # Tokenize the input text
        words = word_tokenize(text.lower())

        # Remove punctuation
        words = [word for word in words if word not in string.punctuation]

        # Filter out stopwords (except pronouns)
        filtered = [word for word in words if word not in self.stop_words]

        # Convert to gloss using the mapping, skip empty strings
        gloss_sequence = [self.gloss_map.get(word, word.upper()) for word in filtered]
        gloss_sequence = [term for term in gloss_sequence if term]  # Remove empty strings

        # Return both string and structured format
        gloss_string = " ".join(gloss_sequence)
        gloss_json = {"gloss_sequence": gloss_sequence}

        return gloss_string, gloss_json


class SpeechRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech Recognition with Sign Gloss Conversion")
        self.root.geometry("1000x700")  # Larger to accommodate gloss display
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Initialize the gloss converter
        self.gloss_converter = GlossConverter()

        # Initialize running state
        self.running = True

        # Setup Vosk
        try:
            self.model = Model(r"C:\Users\DELL\PycharmProjects\ASR\vosk-model-small-en-us-0.15")
            # Use larger buffer size and enable words with timestamps
            self.recognizer = KaldiRecognizer(self.model, 16000)
            self.recognizer.SetWords(True)  # Enable word timestamps

            # Setup audio stream with smaller buffer for more frequent updates
            self.mic = pyaudio.PyAudio()
            self.stream = self.mic.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024  # Smaller buffer for frequent processing
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
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=5)

        # English transcript area
        tk.Label(self.main_frame, text="Speech Transcript:", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, padx=5)

        self.english_frame = tk.Frame(self.main_frame)
        self.english_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.main_box = tk.Text(
            self.english_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 14),
            padx=10,
            pady=10,
            height=8
        )
        self.main_box.pack(side=tk.LEFT, expand=True, fill="both")

        self.scrollbar = tk.Scrollbar(self.english_frame, command=self.main_box.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_box.config(yscrollcommand=self.scrollbar.set)
        self.main_box.config(state=tk.DISABLED)

        # Gloss transcript area
        tk.Label(self.main_frame, text="Sign Gloss:", font=("Segoe UI", 12, "bold")).pack(anchor=tk.W, padx=5,
                                                                                          pady=(10, 0))

        self.gloss_frame = tk.Frame(self.main_frame)
        self.gloss_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.gloss_box = tk.Text(
            self.gloss_frame,
            wrap=tk.WORD,
            font=("Consolas", 14, "bold"),  # Monospace for gloss
            padx=10,
            pady=10,
            height=4,
            bg="#f5f5f5"  # Light gray background to differentiate
        )
        self.gloss_box.pack(side=tk.LEFT, expand=True, fill="both")

        self.gloss_scrollbar = tk.Scrollbar(self.gloss_frame, command=self.gloss_box.yview)
        self.gloss_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.gloss_box.config(yscrollcommand=self.gloss_scrollbar.set)
        self.gloss_box.config(state=tk.DISABLED)

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

        # Control for update behavior
        self.control_frame = tk.Frame(self.button_frame)
        self.control_frame.pack(side=tk.LEFT, padx=10)

        # Update interval control
        self.interval_frame = tk.Frame(self.control_frame)
        self.interval_frame.pack(side=tk.TOP, padx=5, pady=2)

        tk.Label(self.interval_frame, text="Update Interval:").pack(side=tk.LEFT)

        self.interval_var = tk.StringVar(value="0.5")  # Default to faster updates
        interval_options = ["0.1", "0.3", "0.5", "1.0", "2.0"]
        self.interval_dropdown = tk.OptionMenu(self.interval_frame, self.interval_var, *interval_options)
        self.interval_dropdown.pack(side=tk.LEFT, padx=5)

        tk.Label(self.interval_frame, text="seconds").pack(side=tk.LEFT)

        # Real-time mode toggle
        self.real_time_frame = tk.Frame(self.control_frame)
        self.real_time_frame.pack(side=tk.TOP, padx=5, pady=2)

        self.real_time_var = tk.BooleanVar(value=True)
        self.real_time_check = tk.Checkbutton(
            self.real_time_frame,
            text="Real-time Updates",
            variable=self.real_time_var,
            onvalue=True,
            offvalue=False
        )
        self.real_time_check.pack(side=tk.LEFT)

        # Auto gloss conversion toggle
        self.auto_gloss_var = tk.BooleanVar(value=True)
        self.auto_gloss_check = tk.Checkbutton(
            self.real_time_frame,
            text="Auto-convert to Gloss",
            variable=self.auto_gloss_var,
            onvalue=True,
            offvalue=False
        )
        self.auto_gloss_check.pack(side=tk.LEFT, padx=(20, 0))

        # For handling text processing
        self.full_transcript = ""  # The complete transcript text
        self.current_partial = ""  # Current partial text for real-time display
        self.recent_segments = deque(maxlen=10)  # Store recent text segments for comparison
        self.recognition_active = True
        self.min_similarity_threshold = 0.7  # Threshold for considering text similar
        self.last_update_time = time.time()
        self.force_update_timer = 0.5  # Force update more frequently initially
        self.word_update_threshold = 2  # Update after this many new words (reduced from 5)

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
        self.current_partial = ""
        self.recent_segments.clear()
        self.update_mainbox("")
        self.update_gloss_box("")
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

        # Convert to gloss if enabled
        if self.auto_gloss_var.get():
            self.update_gloss_from_transcript()

        return True

    def update_gloss_from_transcript(self):
        """Convert current transcript to gloss and update the gloss box"""
        if not self.full_transcript:
            self.update_gloss_box("")
            return

        # Convert the text to gloss
        gloss_string, _ = self.gloss_converter.convert_to_sign_gloss(self.full_transcript)

        # Update the gloss box
        self.update_gloss_box(gloss_string)

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

            # In real-time mode, append current partial text if available
            if self.real_time_var.get() and self.current_partial:
                if text_to_display:
                    # Add proper punctuation/spacing to connect with partial
                    if text_to_display[-1] in ".!?":
                        text_to_display += " " + self.current_partial.capitalize()
                    else:
                        text_to_display += ". " + self.current_partial.capitalize()
                else:
                    text_to_display = self.current_partial.capitalize()

            self.main_box.insert(tk.END, text_to_display)
            self.main_box.see(tk.END)
            self.main_box.config(state=tk.DISABLED)

            # Update gloss if real-time and auto-convert enabled
            if self.real_time_var.get() and self.auto_gloss_var.get() and self.current_partial:
                # Convert combined text to gloss
                gloss_string, _ = self.gloss_converter.convert_to_sign_gloss(text_to_display)
                self.update_gloss_box(gloss_string)

        self.safe_ui_update(_update)

    def update_gloss_box(self, text):
        """Update the gloss transcript box"""

        def _update():
            self.gloss_box.config(state=tk.NORMAL)
            self.gloss_box.delete(1.0, tk.END)
            self.gloss_box.insert(tk.END, text)
            self.gloss_box.see(tk.END)
            self.gloss_box.config(state=tk.DISABLED)

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
        last_result_time = time.time()
        accumulated_text = ""
        last_word_count = 0
        last_display_update = time.time()

        while self.running:
            try:
                if not self.recognition_active:
                    time.sleep(0.1)
                    continue

                # Get update interval from UI
                try:
                    self.force_update_timer = float(self.interval_var.get())
                except ValueError:
                    self.force_update_timer = 0.5

                current_time = time.time()
                elapsed_since_last_update = current_time - last_result_time
                elapsed_since_display_update = current_time - last_display_update

                # Get audio data with smaller buffer for more frequent updates
                data = self.stream.read(512, exception_on_overflow=False)

                # Process the audio data
                if self.recognizer.AcceptWaveform(data):
                    # Got a final result
                    result = json.loads(self.recognizer.Result())
                    final_text = result.get("text", "").strip()

                    if final_text:
                        # Accumulate text
                        if accumulated_text:
                            accumulated_text += " " + final_text
                        else:
                            accumulated_text = final_text

                        # Show in live label
                        self.update_live_label(f"Recognized: {final_text}")

                        # Update transcript if enough time has passed or enough new words
                        current_word_count = len(accumulated_text.split())
                        new_words = current_word_count - last_word_count

                        # Lowered the word threshold to 2
                        if elapsed_since_last_update >= self.force_update_timer or new_words >= self.word_update_threshold:
                            if self.add_text_to_transcript(accumulated_text):
                                self.current_partial = ""  # Clear partial text
                                self.update_mainbox()
                                self.update_status(f"Status: Updated transcript ({elapsed_since_last_update:.1f}s)")

                            # Reset accumulation
                            accumulated_text = ""
                            last_word_count = 0
                            last_result_time = current_time
                            last_display_update = current_time
                        else:
                            last_word_count = current_word_count
                else:
                    # Process partial result
                    partial_result = json.loads(self.recognizer.PartialResult())
                    partial_text = partial_result.get("partial", "").strip()

                    if partial_text:
                        self.update_live_label(f"Recognizing: {partial_text}")

                        # Store current partial for real-time display
                        if self.real_time_var.get():
                            self.current_partial = partial_text

                            # Update display with partial text more frequently
                            if elapsed_since_display_update >= 0.2:  # Update display frequently
                                self.update_mainbox()
                                last_display_update = current_time

                        # Force update after specified interval regardless of pauses
                        if elapsed_since_last_update >= self.force_update_timer and accumulated_text:
                            if self.add_text_to_transcript(accumulated_text):
                                self.current_partial = partial_text  # Keep current partial
                                self.update_mainbox()
                                self.update_status(f"Status: Forced update after {self.force_update_timer}s")

                            # Reset accumulation but keep partial
                            accumulated_text = ""
                            last_word_count = 0
                            last_result_time = current_time
                    else:
                        # No speech - if we have accumulated text and it's been a while, add it
                        if accumulated_text and elapsed_since_last_update >= 0.8:  # Reduced from 1.0
                            if self.add_text_to_transcript(accumulated_text):
                                self.current_partial = ""  # Clear partial
                                self.update_mainbox()
                                self.update_status("Status: Added text after pause")

                            # Reset accumulation
                            accumulated_text = ""
                            last_word_count = 0
                            last_result_time = current_time
                            last_display_update = current_time
                            self.update_live_label("Listening...")

                # Very short sleep to prevent CPU hogging but allow frequent updates
                time.sleep(0.01)

            except Exception as e:
                print(f"Error in listen thread: {e}")
                self.update_status(f"Error: {str(e)[:30]}...")
                time.sleep(0.5)

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
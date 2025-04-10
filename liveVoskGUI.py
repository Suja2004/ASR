import tkinter as tk
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import threading
import time
import re
from collections import deque


class SpeechRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech Recognition - No Repeats")
        self.root.geometry("1000x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Initialize running state
        self.running = True  # Add this line to fix the first error

        # Setup Vosk
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

        # UI Components
        self.top_frame = tk.Frame(root, bg="#f0f0f0", pady=10)
        self.top_frame.pack(fill=tk.X)

        self.status_label = tk.Label(
            self.top_frame,
            text="Status: Ready",
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

        # For handling last n spoken words
        self.word_history = []  # All recognized words
        self.processed_chunks = deque(maxlen=10)  # Last 10 text chunks for repetition detection
        self.recognition_active = True
        self.last_update_time = time.time()

        # Start threads
        self.listen_thread = threading.Thread(target=self.listen, daemon=True)
        self.listen_thread.start()

    def reset_transcript(self):
        self.word_history = []
        self.processed_chunks.clear()
        self.update_mainbox()
        self.status_label.config(text="Status: Transcript Reset")

    def toggle_recognition(self):
        self.recognition_active = not self.recognition_active
        if self.recognition_active:
            self.toggle_button.config(text="Pause Recognition", bg="#2196f3")
            self.status_label.config(text="Status: Recognition Active")
        else:
            self.toggle_button.config(text="Resume Recognition", bg="#4caf50")
            self.status_label.config(text="Status: Recognition Paused")

    def process_chunk(self, text):
        """Process text chunk and add only new words to the transcript"""
        if not text or not text.strip():
            return False

        # Clean and normalize text
        text = re.sub(r'\s+', ' ', text).strip().lower()

        # Check if this chunk is too similar to recently processed chunks
        for recent_chunk in self.processed_chunks:
            if text in recent_chunk or recent_chunk in text:
                return False

        # Split into words
        words = text.split()

        # If no existing words, add all
        if not self.word_history:
            self.word_history = words
            self.processed_chunks.append(text)
            return True

        # Try to find where (if at all) this chunk overlaps with existing transcript
        added_words = False

        # Check for potential overlaps with existing word history
        existing_text = ' '.join(self.word_history[-30:])  # Check last 30 words

        # If no overlap or minimal overlap, add all words
        # Fix the string comparison logic below
        if len(words) > 5 and not ' '.join(words[:3]) in existing_text:
            self.word_history.extend(words)
            added_words = True
        else:
            # Try to find where new content starts
            for i in range(min(len(words), 15)):
                test_sequence = ' '.join(words[:i + 1])
                if test_sequence in existing_text:
                    continue
                else:
                    # Found new content
                    self.word_history.extend(words[i:])
                    added_words = True
                    break

        if added_words:
            self.processed_chunks.append(text)
            return True

        return False

    def update_mainbox(self):
        full_text = ' '.join(self.word_history)

        self.main_box.config(state=tk.NORMAL)
        self.main_box.delete(1.0, tk.END)
        self.main_box.insert(tk.END, full_text)
        self.main_box.see(tk.END)
        self.main_box.config(state=tk.DISABLED)

    def listen(self):
        last_final_time = time.time()
        silence_time = 0
        speaking = False

        while True:
            try:
                if not self.running:
                    break

                if not self.recognition_active:
                    time.sleep(0.1)
                    continue

                data = self.stream.read(4096, exception_on_overflow=False)
                current_time = time.time()

                if self.recognizer.AcceptWaveform(data):
                    # Final result
                    result = json.loads(self.recognizer.Result())
                    final_text = result.get("text", "").strip()

                    if final_text:
                        speaking = True
                        silence_time = 0
                        if self.process_chunk(final_text):
                            self.update_mainbox()
                            self.status_label.config(text=f"Status: Added text ({len(self.word_history)} words)")

                        last_final_time = current_time
                        # Clear live display
                        self.root.after(0, lambda: self.live_label.config(text=""))

                else:
                    # Partial result
                    partial_result = json.loads(self.recognizer.PartialResult())
                    partial_text = partial_result.get("partial", "").strip()

                    if partial_text:
                        speaking = True
                        silence_time = 0
                        self.root.after(0, lambda t=partial_text: self.live_label.config(text=f"🗣️ {t}"))

                        # Add partial text occasionally if enough time has passed since last update
                        if current_time - last_final_time > 3.0 and current_time - self.last_update_time > 1.5:
                            if self.process_chunk(partial_text):
                                self.update_mainbox()
                                self.last_update_time = current_time
                    else:
                        # No speech detected
                        if speaking:
                            silence_time += 0.1
                            if silence_time > 1.0:  # After 1 second of silence
                                speaking = False
                                self.root.after(0, lambda: self.live_label.config(text="Listening..."))

                time.sleep(0.1)  # Prevent CPU hogging

            except Exception as e:
                print(f"Error in listen thread: {e}")
                self.status_label.config(text=f"Error: {str(e)[:30]}...")
                time.sleep(1)

    def on_closing(self):
        self.running = False
        time.sleep(0.5)  # Give thread time to exit
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
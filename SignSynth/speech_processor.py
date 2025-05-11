import json
import threading
import time
import re
import difflib
from collections import deque

# Import speech recognition libraries
from vosk import Model, KaldiRecognizer
import pyaudio

# Import NLP tools
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string

# Ensure NLTK resources are downloaded
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')


class SpeechProcessor:
    """Class to handle speech recognition and processing"""

    def __init__(self, model_path="C:\\Users\\DELL\\PycharmProjects\\ASR\\vosk-model-small-en-us-0.15",
                 on_status_update=None, on_transcript_update=None,
                 on_gloss_update=None, on_live_update=None):
        """Initialize speech processor with callback functions"""
        # Callback functions
        self.on_status_update = on_status_update
        self.on_transcript_update = on_transcript_update
        self.on_gloss_update = on_gloss_update
        self.on_live_update = on_live_update

        # Initialize state variables
        self.running = True
        self.recognition_active = True
        self.listen_thread = None
        self.model_path = model_path

        # For handling text processing
        self.full_transcript = ""
        self.full_gloss = ""
        self.recent_segments = deque(maxlen=10)
        self.min_similarity_threshold = 0.7

        # Setup Vosk and start listening
        self.setup_speech_recognition()

    def setup_speech_recognition(self):
        """Setup speech recognition system"""
        try:
            # Setup Vosk model
            self.model = Model(self.model_path)
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

            # Load stopwords and prepare gloss mapping
            self.load_nlp_resources()

            # Start the listening thread
            self.setup_successful = True
            self.send_status_update("Status: Ready")
            self.listen_thread = threading.Thread(target=self.listen, daemon=True)
            self.listen_thread.start()

        except Exception as e:
            self.setup_successful = False
            self.send_status_update(f"Status: Failed to initialize - {str(e)[:30]}")
            print(f"Error initializing: {e}")

    def load_nlp_resources(self):
        """Load stopwords and prepare gloss mapping dictionary"""
        # Stopwords with pronouns kept
        self.stop_words = set(stopwords.words('english')) - {
            'i', 'you', 'we', 'he', 'she', 'they', 'me', 'my', 'your', 'our', 'his', 'her', 'their'
        }

        # Gloss mapping for sign language
        self.gloss_map = {
            "i": "ME", "you": "YOU", "we": "US", "he": "HE", "she": "SHE", "they": "THEY",
            "am": "", "is": "", "are": "", "was": "", "were": "",
            "going": "GO", "go": "GO", "want": "WANT", "have": "HAVE", "had": "HAVE",
            "don't": "NOT", "not": "NOT", "no": "NOT", "won't": "NOT WILL",
            "store": "STORE", "because": "WHY", "milk": "MILK", "to": "",
            "the": "", "a": "", "an": "", "and": "PLUS", "but": "BUT",
            "this": "THIS", "that": "THAT", "there": "THERE", "here": "HERE",
            "what": "WHAT", "who": "WHO", "where": "WHERE", "when": "WHEN", "why": "WHY", "how": "HOW",
            "need": "NEED", "can": "CAN", "will": "WILL", "should": "SHOULD", "must": "MUST",
            "good": "GOOD", "bad": "BAD", "happy": "HAPPY", "sad": "SAD",
            "yes": "YES", "okay": "OK", "like": "LIKE", "help": "HELP"
        }

    def send_status_update(self, text):
        """Send status update via callback if available"""
        if self.on_status_update:
            self.on_status_update(text)

    def send_transcript_update(self, text):
        """Send transcript update via callback if available"""
        if self.on_transcript_update:
            self.on_transcript_update(text)

    def send_gloss_update(self, text):
        """Send gloss update via callback if available"""
        if self.on_gloss_update:
            self.on_gloss_update(text)

    def send_live_update(self, text):
        """Send live update via callback if available"""
        if self.on_live_update:
            self.on_live_update(text)

    def toggle_recognition(self):
        """Toggle speech recognition on/off"""
        self.recognition_active = not self.recognition_active
        return self.recognition_active

    def reset_transcript(self):
        """Clear the transcript, gloss, and reset processing variables"""
        self.full_transcript = ""
        self.full_gloss = ""
        self.recent_segments.clear()
        self.send_transcript_update("")
        self.send_gloss_update("")
        self.send_status_update("Status: Transcript & Gloss Reset")
        return True

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

        # Convert to gloss and update gloss display
        gloss_string, _ = self.convert_to_sign_gloss(cleaned_text)

        # Add to full gloss with proper spacing
        if self.full_gloss:
            self.full_gloss += " | " + gloss_string
        else:
            self.full_gloss = gloss_string

        # Update both displays
        self.send_transcript_update(self.full_transcript)
        self.send_gloss_update(self.full_gloss)

        return True

    def convert_to_sign_gloss(self, text):
        """Convert normal text to sign language gloss notation"""
        words = word_tokenize(text.lower())
        words = [word for word in words if word not in string.punctuation]
        filtered = [word for word in words if word not in self.stop_words or word.lower() in self.gloss_map]

        gloss_sequence = []
        for word in filtered:
            gloss_word = self.gloss_map.get(word.lower(), word.upper())
            if gloss_word:  # Only add non-empty strings
                gloss_sequence.append(gloss_word)

        gloss_string = " ".join(gloss_sequence)
        gloss_json = {"gloss_sequence": gloss_sequence}
        return gloss_string, gloss_json

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
                    # Process final results
                    result = json.loads(self.recognizer.Result())
                    final_text = result.get("text", "").strip()

                    if final_text:
                        speaking = True
                        silence_time = 0

                        # Show in live display briefly
                        self.send_live_update(f"Final: {final_text}")

                        # Add to transcript if not a duplicate
                        if self.add_text_to_transcript(final_text):
                            self.send_status_update(f"Status: Added new speech + gloss")
                        else:
                            self.send_status_update(f"Status: Duplicate text ignored")

                        # Schedule to reset live display (GUI needs to handle this)
                        threading.Timer(1.0, lambda: self.send_live_update("Listening...")).start()

                else:
                    # Process partial results for live display
                    partial_result = json.loads(self.recognizer.PartialResult())
                    partial_text = partial_result.get("partial", "").strip()

                    if partial_text:
                        speaking = True
                        silence_time = 0
                        # Also convert partial text to gloss for live preview
                        partial_gloss, _ = self.convert_to_sign_gloss(partial_text)
                        self.send_live_update(f"Listening: {partial_text} → {partial_gloss}")
                    else:
                        # No speech detected
                        if speaking:
                            silence_time += 0.1
                            if silence_time > 1.0:  # After 1 second of silence
                                speaking = False
                                self.send_live_update("Listening...")

                time.sleep(0.1)  # Prevent CPU hogging

            except Exception as e:
                print(f"Error in listen thread: {e}")
                self.send_status_update(f"Error: {str(e)[:30]}...")
                time.sleep(1)

    def cleanup(self):
        """Clean up resources before closing"""
        self.running = False
        time.sleep(0.2)  # Give threads time to exit

        # Clean up audio resources
        if hasattr(self, 'stream') and self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'mic') and self.mic:
            self.mic.terminate()

        return True

    def get_transcript(self):
        """Return the current transcript"""
        return self.full_transcript

    def get_gloss(self):
        """Return the current gloss"""
        return self.full_gloss

    def is_active(self):
        """Return the current recognition state"""
        return self.recognition_active

    def is_setup_successful(self):
        """Return whether setup was successful"""
        return self.setup_successful


# For testing the module independently
if __name__ == "__main__":
    # Basic test callbacks
    def print_status(text):
        print(f"STATUS: {text}")


    def print_transcript(text):
        print(f"TRANSCRIPT: {text}")


    def print_gloss(text):
        print(f"GLOSS: {text}")


    def print_live(text):
        print(f"LIVE: {text}")


    # Create processor with test callbacks
    processor = SpeechProcessor(
        on_status_update=print_status,
        on_transcript_update=print_transcript,
        on_gloss_update=print_gloss,
        on_live_update=print_live
    )

    try:
        print("Testing speech processor. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        processor.cleanup()
        print("Speech processor test ended.")
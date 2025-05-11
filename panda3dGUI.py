import sys
import json
import threading
import time
import re
import difflib
import pyautogui
from collections import deque

# Import Panda3D modules
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from direct.task import Task
from panda3d.core import *

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


class SpeechRecognitionApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Set window properties
        self.setBackgroundColor(0.9, 0.9, 0.9, 1)  # Light gray background
        props = WindowProperties()
        props.setTitle("Speech Recognition with Live Gloss and Media Control")
        props.setSize(1200, 800)
        self.win.requestProperties(props)

        # Initialize running state
        self.running = True

        # Media control settings
        self.media_running = False
        self.pause_interval = 2  # seconds
        self.play_interval = 10  # seconds

        # Setup GUI
        self.setup_gui()

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
            self.update_status_label("Status: Ready")
        except Exception as e:
            self.setup_successful = False
            self.update_status_label(f"Status: Failed to initialize - {str(e)[:30]}")
            print(f"Error initializing: {e}")

        # For handling text processing
        self.full_transcript = ""
        self.full_gloss = ""
        self.recent_segments = deque(maxlen=10)
        self.recognition_active = True
        self.min_similarity_threshold = 0.7

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

        # Start listening thread if setup was successful
        if self.setup_successful:
            self.listen_thread = threading.Thread(target=self.listen, daemon=True)
            self.listen_thread.start()

        # Add a task to check for window close
        self.taskMgr.add(self.check_running, "CheckRunningTask")

    def setup_gui(self):
        """Setup all GUI elements"""
        # Create a main frame
        self.main_frame = DirectFrame(
            frameColor=(0.8, 0.8, 0.8, 1),
            frameSize=(-0.98, 0.98, -0.98, 0.98),
            pos=(0, 0, 0)
        )

        # Create tabs using Panda3D buttons
        self.create_tabs()

        # Create content for speech tab
        self.create_speech_tab()

        # Create content for media control tab
        self.create_media_control_tab()

        # Initially show speech tab
        self.show_speech_tab()

    def create_tabs(self):
        """Create tab buttons"""
        # Tab container
        self.tab_frame = DirectFrame(
            parent=self.main_frame,
            frameColor=(0.7, 0.7, 0.7, 1),
            frameSize=(-0.98, 0.98, -0.02, 0.07),
            pos=(0, 0, 0.91)
        )

        # Speech tab button - FIX: No need to pass event, use lambda with None
        self.speech_tab_btn = DirectButton(
            parent=self.tab_frame,
            text="Speech & Gloss",
            text_scale=0.03,
            frameSize=(-0.2, 0.2, -0.04, 0.04),
            relief=DGG.RAISED,
            command=lambda: self.show_speech_tab(),
            pos=(-0.75, 0, 0),
            frameColor=(0.6, 0.6, 0.8, 1)
        )

        # Media control tab button - FIX: No need to pass event, use lambda with None
        self.media_tab_btn = DirectButton(
            parent=self.tab_frame,
            text="Media Control",
            text_scale=0.03,
            frameSize=(-0.2, 0.2, -0.04, 0.04),
            relief=DGG.RAISED,
            command=lambda: self.show_media_tab(),
            pos=(-0.3, 0, 0),
            frameColor=(0.6, 0.6, 0.6, 1)
        )

    def create_speech_tab(self):
        """Create speech recognition tab content"""
        # Main container for speech tab
        self.speech_frame = DirectFrame(
            parent=self.main_frame,
            frameColor=(0.9, 0.9, 0.9, 1),
            frameSize=(-0.97, 0.97, -0.97, 0.82),
            pos=(0, 0, 0)
        )

        # Status header section
        self.header_frame = DirectFrame(
            parent=self.speech_frame,
            frameColor=(0.85, 0.85, 0.85, 1),
            frameSize=(-0.97, 0.97, -0.08, 0.08),
            pos=(0, 0, 0.74)
        )

        # Status label
        self.status_label = DirectLabel(
            parent=self.header_frame,
            text="Status: Initializing...",
            text_scale=0.05,
            text_align=TextNode.ALeft,
            frameColor=(0.85, 0.85, 0.85, 0),
            pos=(-0.95, 0, 0)
        )

        # Live listening label
        self.live_label = DirectLabel(
            parent=self.header_frame,
            text="Listening...",
            text_scale=0.05,
            text_align=TextNode.ARight,
            frameColor=(0.85, 0.85, 0.85, 0),
            pos=(0.95, 0, 0)
        )

        # Create transcript section (upper half)
        self.transcript_frame = DirectFrame(
            parent=self.speech_frame,
            frameColor=(1, 1, 1, 1),
            frameSize=(-0.95, 0.95, -0.25, 0.25),
            pos=(0, 0, 0.35)
        )

        # Transcript label
        self.transcript_label = DirectLabel(
            parent=self.transcript_frame,
            text="Speech Transcript",
            text_scale=0.04,
            frameColor=(1, 1, 1, 0),
            pos=(0, 0, 0.28)
        )

        # Transcript text area
        self.transcript_text = DirectScrolledFrame(
            parent=self.transcript_frame,
            frameSize=(-0.93, 0.93, -0.23, 0.23),
            canvasSize=(-0.9, 0.9, -0.5, 0.5),  # Can be adjusted dynamically
            frameColor=(1, 1, 1, 1),
            scrollBarWidth=0.04,
            pos=(0, 0, 0)
        )

        # Text display for transcript
        self.transcript_display = OnscreenText(
            parent=self.transcript_text.getCanvas(),
            text="",
            scale=0.04,
            align=TextNode.ALeft,
            mayChange=True,
            wordwrap=36,
            pos=(-0.9, 0.45)
        )

        # Create gloss section (lower half)
        self.gloss_frame = DirectFrame(
            parent=self.speech_frame,
            frameColor=(0.95, 0.95, 0.95, 1),
            frameSize=(-0.95, 0.95, -0.25, 0.25),
            pos=(0, 0, -0.2)
        )

        # Gloss label
        self.gloss_label = DirectLabel(
            parent=self.gloss_frame,
            text="Live Gloss Translation",
            text_scale=0.04,
            frameColor=(0.95, 0.95, 0.95, 0),
            pos=(0, 0, 0.28)
        )

        # Gloss text area
        self.gloss_text = DirectScrolledFrame(
            parent=self.gloss_frame,
            frameSize=(-0.93, 0.93, -0.23, 0.23),
            canvasSize=(-0.9, 0.9, -0.5, 0.5),  # Can be adjusted dynamically
            frameColor=(0.95, 0.95, 0.95, 1),
            scrollBarWidth=0.04,
            pos=(0, 0, 0)
        )

        # Text display for gloss
        self.gloss_display = OnscreenText(
            parent=self.gloss_text.getCanvas(),
            text="",
            scale=0.04,
            align=TextNode.ALeft,
            mayChange=True,
            wordwrap=30,  # Adjust for your window width
            pos=(-0.9, 0.45)
        )

        # Button frame
        self.button_frame = DirectFrame(
            parent=self.speech_frame,
            frameColor=(0.9, 0.9, 0.9, 0),
            frameSize=(-0.5, 0.5, -0.05, 0.05),
            pos=(0, 0, -0.7)
        )

        # Reset button
        self.reset_button = DirectButton(
            parent=self.button_frame,
            text="Reset Transcript & Gloss",
            text_scale=0.03,
            frameSize=(-0.25, 0.25, -0.06, 0.06),
            relief=DGG.RAISED,
            command=self.reset_transcript,
            pos=(-0.3, 0, 0),
            frameColor=(0.9, 0.3, 0.3, 1)
        )

        # Toggle button
        self.toggle_button = DirectButton(
            parent=self.button_frame,
            text="Pause Recognition",
            text_scale=0.03,
            frameSize=(-0.25, 0.25, -0.06, 0.06),
            relief=DGG.RAISED,
            command=self.toggle_recognition,
            pos=(0.3, 0, 0),
            frameColor=(0.3, 0.6, 0.9, 1)
        )

    def create_media_control_tab(self):
        """Create media control tab content"""
        # Main container for media control tab
        self.media_frame = DirectFrame(
            parent=self.main_frame,
            frameColor=(0.9, 0.9, 0.9, 1),
            frameSize=(-0.97, 0.97, -0.97, 0.82),
            pos=(0, 0, 0)
        )
        # Initially hide media frame
        self.media_frame.hide()

        # Media tab title
        self.media_title = DirectLabel(
            parent=self.media_frame,
            text="YouTube/Video Media Controller",
            text_scale=0.07,
            frameColor=(0.9, 0.9, 0.9, 0),
            pos=(0, 0, 0.7)
        )

        # Instructions label
        instructions_text = (
            "This feature will automatically play and pause media (like YouTube videos).\n"
            "1. Click 'Start Media Control'\n"
            "2. Switch to your media tab within 3 seconds\n"
            "3. The controller will periodically play and pause the media"
        )

        self.instruction_text = OnscreenText(
            parent=self.media_frame,
            text=instructions_text,
            scale=0.04,
            wordwrap=30,
            pos=(0, 0.5)
        )

        # Interval settings
        self.interval_frame = DirectFrame(
            parent=self.media_frame,
            frameColor=(0.9, 0.9, 0.9, 0),
            frameSize=(-0.5, 0.5, -0.2, 0.2),
            pos=(0, 0, 0.1)
        )

        # Pause duration label
        self.pause_label = DirectLabel(
            parent=self.interval_frame,
            text="Pause Duration (seconds):",
            text_scale=0.05,
            text_align=TextNode.ARight,
            frameColor=(0.9, 0.9, 0.9, 0),
            pos=(-0.1, 0, 0.1)
        )

        # Pause duration entry
        self.pause_entry = DirectEntry(
            parent=self.interval_frame,
            initialText=str(self.pause_interval),
            width=5,
            scale=0.05,
            pos=(0.2, 0, 0.1),
            frameColor=(1, 1, 1, 1)
        )

        # Play duration label
        self.play_label = DirectLabel(
            parent=self.interval_frame,
            text="Play Duration (seconds):",
            text_scale=0.05,
            text_align=TextNode.ARight,
            frameColor=(0.9, 0.9, 0.9, 0),
            pos=(-0.1, 0, -0.1)
        )

        # Play duration entry
        self.play_entry = DirectEntry(
            parent=self.interval_frame,
            initialText=str(self.play_interval),
            width=5,
            scale=0.05,
            pos=(0.2, 0, -0.1),
            frameColor=(1, 1, 1, 1)
        )

        # Media control button
        self.media_toggle_button = DirectButton(
            parent=self.media_frame,
            text="Start Media Control",
            text_scale=0.05,
            frameSize=(-0.3, 0.3, -0.1, 0.1),
            relief=DGG.RAISED,
            command=self.toggle_media_control,
            pos=(0, 0, -0.2),
            frameColor=(0.3, 0.6, 0.9, 1)
        )

        # Media status label
        self.media_status = DirectLabel(
            parent=self.media_frame,
            text="Status: Idle",
            text_scale=0.05,
            frameColor=(0.9, 0.9, 0.9, 0),
            pos=(0, 0, -0.4)
        )

    def show_speech_tab(self):
        """Show speech recognition tab - FIX: Remove event parameter"""
        self.speech_frame.show()
        self.media_frame.hide()
        self.speech_tab_btn["frameColor"] = (0.6, 0.6, 0.8, 1)
        self.media_tab_btn["frameColor"] = (0.6, 0.6, 0.6, 1)

    def show_media_tab(self):
        """Show media control tab - FIX: Remove event parameter"""
        self.speech_frame.hide()
        self.media_frame.show()
        self.speech_tab_btn["frameColor"] = (0.6, 0.6, 0.6, 1)
        self.media_tab_btn["frameColor"] = (0.6, 0.6, 0.8, 1)

    def update_status_label(self, text):
        """Update the status label text"""
        self.status_label["text"] = text

    def update_live_label(self, text):
        """Update the live listening label text"""
        self.live_label["text"] = text

    def update_transcript_text(self, text=None):
        """Update the transcript text area"""
        # Use provided text or full transcript
        display_text = text if text is not None else self.full_transcript
        self.transcript_display.setText(display_text)

        # Adjust canvas size if needed
        text_height = len(display_text.split('\n')) * 0.06
        if text_height > 1.0:
            self.transcript_text["canvasSize"] = (-0.9, 0.9, -text_height, 0.5)

    def update_gloss_text(self, text=None):
        """Update the gloss text area"""
        # Use provided text or full gloss
        display_text = text if text is not None else self.full_gloss
        self.gloss_display.setText(display_text)

        # Adjust canvas size if needed
        text_height = len(display_text.split('\n')) * 0.07
        if text_height > 1.0:
            self.gloss_text["canvasSize"] = (-0.9, 0.9, -text_height, 0.5)

    def reset_transcript(self):
        """Clear the transcript, gloss, and reset processing variables"""
        self.full_transcript = ""
        self.full_gloss = ""
        self.recent_segments.clear()
        self.update_transcript_text("")
        self.update_gloss_text("")
        self.update_status_label("Status: Transcript & Gloss Reset")

    def toggle_recognition(self):
        """Toggle speech recognition on/off"""
        self.recognition_active = not self.recognition_active
        if self.recognition_active:
            self.toggle_button["text"] = "Pause Recognition"
            self.toggle_button["frameColor"] = (0.3, 0.6, 0.9, 1)
            self.update_status_label("Status: Recognition Active")
        else:
            self.toggle_button["text"] = "Resume Recognition"
            self.toggle_button["frameColor"] = (0.3, 0.9, 0.3, 1)
            self.update_status_label("Status: Recognition Paused")

    def toggle_media_control(self):
        """Toggle the media control function"""
        try:
            # Update intervals from entry fields
            self.pause_interval = float(self.pause_entry.get())
            self.play_interval = float(self.play_entry.get())

            if not self.media_running:
                self.media_running = True
                self.media_toggle_button["text"] = "Stop Media Control"
                self.media_toggle_button["frameColor"] = (0.9, 0.3, 0.3, 1)
                self.media_status["text"] = "Status: Starting..."

                # Start the media control thread
                self.media_thread = threading.Thread(target=self.media_control_loop, daemon=True)
                self.media_thread.start()
            else:
                self.media_running = False
                self.media_toggle_button["text"] = "Start Media Control"
                self.media_toggle_button["frameColor"] = (0.3, 0.6, 0.9, 1)
                self.media_status["text"] = "Status: Stopped"

        except ValueError:
            self.media_status["text"] = "Error: Invalid interval values"

    def media_control_loop(self):
        """Loop that handles automatic media play/pause"""
        # Give user time to switch to media tab
        self.media_status["text"] = "Status: Switch to media tab now..."
        time.sleep(3)

        self.media_status["text"] = "Status: Running"

        is_playing = True  # Assume media is initially playing

        while self.media_running:
            try:
                if is_playing:
                    # Pause the media
                    pyautogui.press('space')
                    self.media_status["text"] = "Status: Media Paused"
                    time.sleep(self.pause_interval)
                else:
                    # Play the media
                    pyautogui.press('space')
                    self.media_status["text"] = "Status: Media Playing"
                    time.sleep(self.play_interval)

                # Toggle state
                is_playing = not is_playing

                if not self.media_running:
                    break

            except Exception as e:
                print(f"Error in media control: {e}")
                self.media_status["text"] = f"Error: {str(e)[:30]}..."
                break

        self.media_status["text"] = "Status: Idle"

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
        self.update_transcript_text()
        self.update_gloss_text()

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
                        self.update_live_label(f"Final: {final_text}")

                        # Add to transcript if not a duplicate
                        if self.add_text_to_transcript(final_text):
                            self.update_status_label(f"Status: Added new speech + gloss")
                        else:
                            self.update_status_label(f"Status: Duplicate text ignored")

                        # Reset live display after a short delay (using Panda3D task)
                        self.taskMgr.doMethodLater(1.0, self.reset_live_label, "ResetLiveLabel")
                else:
                    # Process partial results for live display
                    partial_result = json.loads(self.recognizer.PartialResult())
                    partial_text = partial_result.get("partial", "").strip()

                    if partial_text:
                        speaking = True
                        silence_time = 0
                        # Also convert partial text to gloss for live preview
                        partial_gloss, _ = self.convert_to_sign_gloss(partial_text)
                        # FIX: Replace the arrow character with "→"
                        self.update_live_label(f"Listening: {partial_text} → {partial_gloss}")
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
                self.update_status_label(f"Error: {str(e)[:30]}...")
                time.sleep(1)

    def reset_live_label(self, task):
        """Reset the live label text"""
        self.update_live_label("Listening...")
        return Task.done

    def check_running(self, task):
        """Check if application is still running"""
        if not self.running:
            return Task.done
        return Task.cont

    def cleanup(self):
        """Clean up resources before closing"""
        self.running = False
        self.media_running = False
        time.sleep(0.2)  # Give threads time to exit

        # Clean up audio resources
        if hasattr(self, 'stream') and self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if hasattr(self, 'mic') and self.mic:
            self.mic.terminate()

    # def shutdown(self):
    #     """Clean up and shutdown application"""
    #     self.cleanup()
    #     sys.exit()


# Main entry point
if __name__ == "__main__":
    app = SpeechRecognitionApp()

    # Uncomment the line below to enable proper cleanup on window close
    # app.accept("window-closed", app.shutdown)

    app.run()
from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from direct.task import Task
from panda3d.core import *
import sys

# Import custom modules
from speech_processor import SpeechProcessor
from media_controller import MediaController


class SpeechAppGUI(ShowBase):
    """Main GUI class for the speech recognition application"""

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

        # Create default values for media controller
        self.default_pause_interval = 2  # seconds
        self.default_play_interval = 10  # seconds

        # Create main GUI structure first (without creating specific tab content yet)
        self.create_main_frame()
        self.create_tabs()

        # Create speech tab content
        self.create_speech_tab()

        # Initialize controllers
        self.media_controller = MediaController(
            on_status_update=self.update_media_status
        )

        self.speech_processor = SpeechProcessor(
            on_status_update=self.update_status_label,
            on_transcript_update=self.update_transcript_text,
            on_gloss_update=self.update_gloss_text,
            on_live_update=self.update_live_label
        )

        # Now create media control tab (after media_controller is initialized)
        self.create_media_control_tab()

        # Initially show speech tab
        self.show_speech_tab()

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

    def create_main_frame(self):
        """Create the main frame for the application"""
        self.main_frame = DirectFrame(
            frameColor=(0.8, 0.8, 0.8, 1),
            frameSize=(-0.98, 0.98, -0.98, 0.98),
            pos=(0, 0, 0)
        )

    def create_tabs(self):
        """Create tab buttons"""
        # Tab container
        self.tab_frame = DirectFrame(
            parent=self.main_frame,
            frameColor=(0.7, 0.7, 0.7, 1),
            frameSize=(-0.98, 0.98, -0.02, 0.07),
            pos=(0, 0, 0.91)
        )

        # Speech tab button
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

        # Media control tab button
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
            wordwrap=30,
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
            initialText=str(self.media_controller.pause_interval),
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
            initialText=str(self.media_controller.play_interval),
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
        """Show speech recognition tab"""
        self.speech_frame.show()
        self.media_frame.hide()
        self.speech_tab_btn["frameColor"] = (0.6, 0.6, 0.8, 1)
        self.media_tab_btn["frameColor"] = (0.6, 0.6, 0.6, 1)

    def show_media_tab(self):
        """Show media control tab"""
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

    def update_transcript_text(self, text):
        """Update the transcript text area"""
        self.transcript_display.setText(text)

        # Adjust canvas size if needed
        text_height = len(text.split('\n')) * 0.06
        if text_height > 1.0:
            self.transcript_text["canvasSize"] = (-0.9, 0.9, -text_height, 0.5)

    def update_gloss_text(self, text):
        """Update the gloss text area"""
        self.gloss_display.setText(text)

        # Adjust canvas size if needed
        text_height = len(text.split('\n')) * 0.07
        if text_height > 1.0:
            self.gloss_text["canvasSize"] = (-0.9, 0.9, -text_height, 0.5)

    def update_media_status(self, text):
        """Update the media status label"""
        self.media_status["text"] = text

    def reset_transcript(self):
        """Reset the transcript and gloss"""
        self.speech_processor.reset()
        self.update_status_label("Status: Transcript & Gloss Reset")

    def toggle_media_control(self):
        """Toggle the media control function"""
        try:
            # Update intervals from entry fields
            pause_interval = float(self.pause_entry.get())
            play_interval = float(self.play_entry.get())

            # Set the intervals first
            self.media_controller.set_intervals(pause_interval, play_interval)

            # Toggle media control
            is_running = self.media_controller.toggle_media_control()

            # Update UI based on state
            if is_running:
                self.media_toggle_button["text"] = "Stop Media Control"
                self.media_toggle_button["frameColor"] = (0.9, 0.3, 0.3, 1)
            else:
                self.media_toggle_button["text"] = "Start Media Control"
                self.media_toggle_button["frameColor"] = (0.3, 0.6, 0.9, 1)

        except ValueError:
            self.update_media_status("Error: Invalid interval values")

    def toggle_recognition(self):
        """Toggle speech recognition on/off"""
        # Make sure we're calling the right method in speech_processor
        is_active = self.speech_processor.toggle_recognition()

        if is_active:
            self.toggle_button["text"] = "Pause Recognition"
            self.toggle_button["frameColor"] = (0.3, 0.6, 0.9, 1)
            self.update_status_label("Status: Recognition Active")
        else:
            self.toggle_button["text"] = "Resume Recognition"
            self.toggle_button["frameColor"] = (0.3, 0.9, 0.3, 1)
            self.update_status_label("Status: Recognition Paused")

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

        # Clean up speech processor and media controller
        if hasattr(self, 'speech_processor'):
            self.speech_processor.cleanup()

        if hasattr(self, 'media_controller'):
            self.media_controller.cleanup()

    # def shutdown(self):
    #     """Clean up and shutdown application"""
    #     self.cleanup()
    #     sys.exit()


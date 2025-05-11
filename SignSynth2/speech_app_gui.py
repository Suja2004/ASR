from direct.showbase.ShowBase import ShowBase
from direct.gui.DirectGui import *
from direct.task import Task
from panda3d.core import *
import sys

# Import custom modules
from speech_processor import SpeechProcessor
from media_controller import MediaController
from pose_animator import PoseAnimator


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

        # Create main GUI structure first
        self.create_main_frame()
        self.create_tabs()
        # Now we can initialize controllers that need GUI references
        self.media_controller = MediaController(
            on_status_update=self.update_media_status
        )
        # Create individual tab content - this creates the status_label
        self.create_speech_tab()
        self.create_media_control_tab()
        self.create_animation_tab()

        self.speech_processor = SpeechProcessor(
            on_status_update=self.update_status_label,
            on_transcript_update=self.update_transcript_text,
            on_gloss_update=self.update_gloss_text,
            on_live_update=self.update_live_label
        )

        # Initially show speech tab
        self.show_speech_tab()

        # Add a task to check for window close
        self.taskMgr.add(self.check_running, "CheckRunningTask")


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
            command=self.show_speech_tab,
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
            command=self.show_media_tab,
            pos=(-0.3, 0, 0),
            frameColor=(0.6, 0.6, 0.6, 1)
        )

        # Animation tab button
        self.animation_tab_btn = DirectButton(
            parent=self.tab_frame,
            text="ASL Animation",
            text_scale=0.03,
            frameSize=(-0.2, 0.2, -0.04, 0.04),
            relief=DGG.RAISED,
            command=self.show_animation_tab,
            pos=(0.15, 0, 0),
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

    def create_animation_tab(self):
        """Create the new animation tab content"""
        # Main container for animation tab
        self.animation_frame = DirectFrame(
            parent=self.main_frame,
            frameColor=(0.9, 0.9, 0.9, 1),
            frameSize=(-0.97, 0.97, -0.97, 0.82),
            pos=(0, 0, 0)
        )
        # Initially hide animation frame
        self.animation_frame.hide()

        # Create a scene for our animation
        self.animation_root = NodePath("animation_root")
        self.animation_root.reparentTo(render)
        self.animation_root.hide()  # Hide the animation root initially

        # Create the display region properly through the window
        self.animation_viewport = self.win.makeDisplayRegion(0, 1, 0, 0.7)

        # Setup camera for animation viewport
        self.animation_camera = self.makeCamera(self.win)
        self.animation_camera.setPos(0, -15, 3.25)
        self.animation_camera.lookAt(0, 0, 3)
        self.animation_viewport.setCamera(self.animation_camera)

        # Rest of the method remains the same...
        # Title for animation tab
        self.animation_title = DirectLabel(
            parent=self.animation_frame,
            text="ASL Sign Animation",
            text_scale=0.06,
            frameColor=(0.9, 0.9, 0.9, 0),
            pos=(0, 0, 0.75)
        )
    def load_animation_models(self):
        """Load the 3D models needed for animation"""
        try:
            # Create a new nodePath for our models
            self.model_root = NodePath("model_root")
            self.model_root.reparentTo(self.animation_root)

            # Load the torso model
            self.torso = loader.loadModel('character/torso.glb')
            self.torso.setPos(0, 0, 0)
            self.torso.reparentTo(self.model_root)

            # Load the right arm and hand
            self.rarm = loader.loadModel('character/RArmX.glb')
            self.rarm.reparentTo(self.torso)

            # Find all the finger joints for the right hand
            self.rthumb1 = self.rarm.find("**/t1")
            self.rthumb2 = self.rarm.find("**/t2")
            self.rindex1 = self.rarm.find("**/i1")
            self.rindex2 = self.rarm.find("**/i2")
            self.rindex3 = self.rarm.find("**/i3")
            self.rmiddle1 = self.rarm.find("**/m1")
            self.rmiddle2 = self.rarm.find("**/m2")
            self.rmiddle3 = self.rarm.find("**/m3")
            self.rring1 = self.rarm.find("**/r1")
            self.rring2 = self.rarm.find("**/r2")
            self.rring3 = self.rarm.find("**/r3")
            self.rpinky1 = self.rarm.find("**/p1")
            self.rpinky2 = self.rarm.find("**/p2")
            self.rpinky3 = self.rarm.find("**/p3")

            # Load the left arm and hand
            self.larm = loader.loadModel('character/LArmX.glb')
            self.larm.reparentTo(self.torso)

            # Find all the finger joints for the left hand
            self.lthumb1 = self.larm.find("**/t1")
            self.lthumb2 = self.larm.find("**/t2")
            self.lindex1 = self.larm.find("**/i1")
            self.lindex2 = self.larm.find("**/i2")
            self.lindex3 = self.larm.find("**/i3")
            self.lmiddle1 = self.larm.find("**/m1")
            self.lmiddle2 = self.larm.find("**/m2")
            self.lmiddle3 = self.larm.find("**/m3")
            self.lring1 = self.larm.find("**/r1")
            self.lring2 = self.larm.find("**/r2")
            self.lring3 = self.larm.find("**/r3")
            self.lpinky1 = self.larm.find("**/p1")
            self.lpinky2 = self.larm.find("**/p2")
            self.lpinky3 = self.larm.find("**/p3")

            # Setup lighting for the animation
            self.setup_animation_lighting()

            self.animation_status['text'] = "Status: Models loaded successfully"
        except Exception as e:
            self.animation_status['text'] = f"Error loading models: {str(e)}"
            print(f"Error loading models: {str(e)}")

    def setup_animation_lighting(self):
        """Setup lighting for the animation scene"""
        # Create directional light
        mainLight = DirectionalLight('main light')
        mainLight.setShadowCaster(True)
        mainLightNodePath = self.animation_root.attachNewNode(mainLight)
        mainLightNodePath.setHpr(0, -70, 0)
        self.animation_root.setLight(mainLightNodePath)

        # Create ambient light
        ambientLight = AmbientLight('ambient light')
        ambientLight.setColor((0.2, 0.2, 0.2, 1))
        ambientLightNodePath = self.animation_root.attachNewNode(ambientLight)
        self.animation_root.setLight(ambientLightNodePath)

        # Enable auto shader
        self.animation_root.setShaderAuto()

    def initialize_animator(self):
        """Initialize the pose animator"""
        try:
            # Create dictionaries for left and right hand parts
            left_parts = {
                "arm": self.larm,
                "thumb": [self.lthumb1, self.lthumb2],
                "index": [self.lindex1, self.lindex2, self.lindex3],
                "middle": [self.lmiddle1, self.lmiddle2, self.lmiddle3],
                "ring": [self.lring1, self.lring2, self.lring3],
                "pinky": [self.lpinky1, self.lpinky2, self.lpinky3]
            }

            right_parts = {
                "arm": self.rarm,
                "thumb": [self.rthumb1, self.rthumb2],
                "index": [self.rindex1, self.rindex2, self.rindex3],
                "middle": [self.rmiddle1, self.rmiddle2, self.rmiddle3],
                "ring": [self.rring1, self.rring2, self.rring3],
                "pinky": [self.rpinky1, self.rpinky2, self.rpinky3]
            }

            # Create the pose animator with the hand parts
            self.pose_animator = PoseAnimator(left_parts, right_parts)

            # Apply default pose
            self.pose_animator.applyPoseInstantly(self.pose_animator.loadPoseNow("default"))

            self.animation_status['text'] = "Status: Animator initialized"
        except Exception as e:
            self.animation_status['text'] = f"Error initializing animator: {str(e)}"
            print(f"Error initializing animator: {str(e)}")

    def start_animation(self):
        """Start the animation sequence based on input gloss"""
        # Get the gloss text from the input field
        gloss_text = self.gloss_input.get().strip()

        if not gloss_text:
            self.animation_status['text'] = "Status: Please enter some gloss text to animate"
            return

        # Set the pose sequence
        self.pose_animator.pose_sequence = gloss_text.lower().split()

        # Expand the sequence
        self.pose_animator.expanded_sequence = self.pose_animator.expandPoseSequence(self.pose_animator.pose_sequence)

        if not self.pose_animator.expanded_sequence:
            self.animation_status['text'] = "Status: No valid signs found in input"
            return

        # Reset the animator index
        self.pose_animator.pose_index = 0

        # Start the animation task
        self.taskMgr.remove("AnimateSignsTask")
        self.taskMgr.doMethodLater(0.5, self.animate_next_pose, "AnimateSignsTask")

        self.animation_status['text'] = f"Status: Animating {len(self.pose_animator.expanded_sequence)} signs"

    def animate_next_pose(self, task):
        """Task to animate the next pose in sequence"""
        if self.pose_animator.pose_index >= len(self.pose_animator.expanded_sequence):
            # End of sequence, reset to default
            self.pose_animator.applyPoseInstantly(self.pose_animator.loadPoseNow("default"))
            self.animation_status['text'] = "Status: Animation complete"
            return Task.done

        # Get the next pose name
        pose_name = self.pose_animator.expanded_sequence[self.pose_animator.pose_index]

        # Load and apply the pose
        pose = self.pose_animator.loadPoseNow(pose_name)

        if pose:
            self.pose_animator.animatePose(pose, 0.1)  # Use slightly slower animation for clarity
            self.pose_animator.current_pose = pose_name
            self.animation_status[
                'text'] = f"Status: Sign {self.pose_animator.pose_index + 1}/{len(self.pose_animator.expanded_sequence)}: {pose_name}"
        else:
            self.animation_status['text'] = f"Status: Could not load pose: {pose_name}"

        # Increment pose index
        self.pose_animator.pose_index += 1

        # Schedule next pose after a delay
        return task.again

    def reset_animation(self):
        """Reset the animation to default pose"""
        # Remove animation task
        self.taskMgr.remove("AnimateSignsTask")

        # Apply default pose
        self.pose_animator.applyPoseInstantly(self.pose_animator.loadPoseNow("default"))

        # Reset pose index
        self.pose_animator.pose_index = 0

        # Clear input field
        self.gloss_input.set("")

        self.animation_status['text'] = "Status: Animation reset"

    def show_speech_tab(self):
        """Show speech recognition tab"""
        self.speech_frame.show()
        self.media_frame.hide()
        if hasattr(self, 'animation_frame'):
            self.animation_frame.hide()
        if hasattr(self, 'animation_root'):
            self.animation_root.hide()

        self.speech_tab_btn["frameColor"] = (0.6, 0.6, 0.8, 1)
        self.media_tab_btn["frameColor"] = (0.6, 0.6, 0.6, 1)
        self.animation_tab_btn["frameColor"] = (0.6, 0.6, 0.6, 1)

    def show_media_tab(self):
        """Show media control tab"""
        self.speech_frame.hide()
        self.media_frame.show()
        if hasattr(self, 'animation_frame'):
            self.animation_frame.hide()
        if hasattr(self, 'animation_root'):
            self.animation_root.hide()

        self.speech_tab_btn["frameColor"] = (0.6, 0.6, 0.6, 1)
        self.media_tab_btn["frameColor"] = (0.6, 0.6, 0.8, 1)
        self.animation_tab_btn["frameColor"] = (0.6, 0.6, 0.6, 1)

    def show_animation_tab(self):
        """Show animation tab"""
        if not hasattr(self, 'animation_frame'):
            print("Animation frame not created yet!")
            return

        self.speech_frame.hide()
        self.media_frame.hide()
        self.animation_frame.show()
        self.animation_root.show()

        self.speech_tab_btn["frameColor"] = (0.6, 0.6, 0.6, 1)
        self.media_tab_btn["frameColor"] = (0.6, 0.6, 0.6, 1)
        self.animation_tab_btn["frameColor"] = (0.6, 0.6, 0.8, 1)

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



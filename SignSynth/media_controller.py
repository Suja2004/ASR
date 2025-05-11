import threading
import time
import pyautogui

class MediaController:
    """Class for controlling media playback with automatic play/pause"""

    def __init__(self, on_status_update=None):
        """Initialize media controller with status update callback"""
        # Status update callback
        self.on_status_update = on_status_update

        # Media control settings
        self.media_running = False
        self.pause_interval = 2  # seconds
        self.play_interval = 10  # seconds
        self.media_thread = None

    def send_status_update(self, text):
        """Send status update via callback if available"""
        if self.on_status_update:
            self.on_status_update(text)

    def set_intervals(self, pause_interval, play_interval):
        """Set the play and pause intervals"""
        try:
            # Validate inputs
            self.pause_interval = float(pause_interval)
            self.play_interval = float(play_interval)
            return True
        except ValueError:
            self.send_status_update("Error: Invalid interval values")
            return False

    def toggle_media_control(self):
        """Toggle the media control function"""
        try:
            if not self.media_running:
                self.media_running = True
                self.send_status_update("Status: Starting...")

                # Start the media control thread
                self.media_thread = threading.Thread(target=self.media_control_loop, daemon=True)
                self.media_thread.start()
            else:
                self.media_running = False
                self.send_status_update("Status: Stopped")

            return self.media_running

        except Exception as e:
            self.send_status_update(f"Error: {str(e)[:30]}...")
            return False

    def media_control_loop(self):
        """Loop that handles automatic media play/pause"""
        # Give user time to switch to media tab
        self.send_status_update("Status: Switch to media tab now...")
        time.sleep(3)

        self.send_status_update("Status: Running")

        is_playing = True  # Assume media is initially playing

        while self.media_running:
            try:
                if is_playing:
                    # Pause the media
                    pyautogui.press('space')
                    self.send_status_update("Status: Media Paused")
                    time.sleep(self.pause_interval)
                else:
                    # Play the media
                    pyautogui.press('space')
                    self.send_status_update("Status: Media Playing")
                    time.sleep(self.play_interval)

                # Toggle state
                is_playing = not is_playing

                if not self.media_running:
                    break

            except Exception as e:
                print(f"Error in media control: {e}")
                self.send_status_update(f"Error: {str(e)[:30]}...")
                break

        self.send_status_update("Status: Idle")

    def is_running(self):
        """Return whether media control is currently running"""
        return self.media_running

    def get_intervals(self):
        """Return the current pause and play intervals"""
        return self.pause_interval, self.play_interval

    def cleanup(self):
        """Clean up resources before closing"""
        self.media_running = False
        return True


# For testing the module independently
if __name__ == "__main__":
    # Basic test callback
    def print_status(text):
        print(f"MEDIA STATUS: {text}")


    # Create controller with test callback
    controller = MediaController(on_status_update=print_status)

    # Set intervals
    controller.set_intervals(1.5, 5)  # 1.5s pause, 5s play

    try:
        # Start media control
        print("Starting media control. Switch to your media player.")
        controller.toggle_media_control()

        # Let it run for a while
        for i in range(30):
            time.sleep(1)
            if i == 15:  # Stop after 15 seconds
                print("Stopping media control.")
                controller.toggle_media_control()
                break

    except KeyboardInterrupt:
        controller.cleanup()
        print("Media controller test ended.")
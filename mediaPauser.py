import pyautogui
import time

# Define the interval (in seconds) at which to pause and play
pause_interval =  2  # for example, pause every 5 seconds
play_interval = 12    # pause for 2 seconds before resuming

# Start playing the YouTube video (make sure the video is open in the browser)
time.sleep(5)  # wait for 5 seconds before starting

try:
    while True:
        pyautogui.press('space')  # simulate pressing spacebar to pause
        print("Paused")
        time.sleep(pause_interval)  # wait for the pause interval

        pyautogui.press('space')  # simulate pressing spacebar to play
        print("Playing")
        time.sleep(play_interval)  # wait for the play interval

except KeyboardInterrupt:
    print("Stopped.")

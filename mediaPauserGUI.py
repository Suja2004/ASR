import pyautogui
import time
import threading
import tkinter as tk

running = False  # Flag to control the loop
interval_thread = None

pause_interval = 2  # seconds to pause
play_interval = 10     # seconds to play

def toggle_media_control():
    global running, interval_thread
    if not running:
        running = True
        toggle_button.config(text="Stop Media Control")
        interval_thread = threading.Thread(target=media_control_loop, daemon=True)
        interval_thread.start()
    else:
        running = False
        toggle_button.config(text="Start Media Control")

def media_control_loop():
    time.sleep(3)  # Give user time to switch to YouTube tab
    while running:
        pyautogui.press('space')  # pause
        print("Paused")
        time.sleep(pause_interval)
        if not running:
            break
        pyautogui.press('space')  # play
        print("Playing")
        time.sleep(play_interval)

# GUI setup
root = tk.Tk()
root.title("YouTube Media Controller")
root.geometry("300x100")

toggle_button = tk.Button(root, text="Start Media Control", command=toggle_media_control, font=("Arial", 12))
toggle_button.pack(pady=20)

root.mainloop()

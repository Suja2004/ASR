# import tkinter as tk
# from vosk import Model, KaldiRecognizer
# import pyaudio
# import json
# import threading
#
# # Load Vosk model
# model = Model(r"C:\Users\DELL\PycharmProjects\ASR\vosk-model-small-en-us-0.15")
# recognizer = KaldiRecognizer(model, 16000)
#
# # Setup PyAudio
# mic = pyaudio.PyAudio()
# stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000,
#                   input=True, frames_per_buffer=8192)
# stream.start_stream()
#
# # GUI setup
# root = tk.Tk()
# root.title("🎙️ Live Subtitles")
# root.geometry("800x400")
#
# # Scrollable text widget for accumulated subtitles
# text_box = tk.Text(root, wrap=tk.WORD, font=("Arial", 14))
# text_box.pack(expand=True, fill="both", padx=10, pady=10)
# text_box.insert(tk.END, "Listening...\n")
# text_box.config(state=tk.DISABLED)  # Start as read-only
#
# def update_subtitles():
#     while True:
#         data = stream.read(4096, exception_on_overflow=False)
#         if recognizer.AcceptWaveform(data):
#             result = json.loads(recognizer.Result())
#             text = result.get("text", "")
#             if text.strip():
#                 # Enable editing, insert text, disable again
#                 text_box.config(state=tk.NORMAL)
#                 text_box.insert(tk.END, text + "\n")
#                 text_box.see(tk.END)  # Auto-scroll to latest
#                 text_box.config(state=tk.DISABLED)
#
# # Start recognition in a background thread
# thread = threading.Thread(target=update_subtitles)
# thread.daemon = True
# thread.start()
#
# # Run the GUI loop
# root.mainloop()

import tkinter as tk
from vosk import Model, KaldiRecognizer
import pyaudio
import json
import threading

# Load model
model = Model(r"C:\Users\DELL\PycharmProjects\ASR\vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)
recognizer.SetWords(True)

# Audio setup
mic = pyaudio.PyAudio()
stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000,
                  input=True, frames_per_buffer=8192)
stream.start_stream()

# GUI
root = tk.Tk()
root.title("🎙️ Real-Time Subtitles")
root.geometry("800x450")

text_box = tk.Text(root, wrap=tk.WORD, font=("Arial", 14))
text_box.pack(expand=True, fill="both", padx=10, pady=10)
text_box.config(state=tk.DISABLED)

live_label = tk.Label(root, text="", font=("Arial", 14), fg="gray")
live_label.pack(pady=5)

def listen_and_transcribe():
    while True:
        data = stream.read(4096, exception_on_overflow=False)

        # Show partial result for real-time effect
        partial_result = json.loads(recognizer.PartialResult())
        partial_text = partial_result.get("partial", "")
        live_label.config(text=partial_text)

        # Append final result when complete
        if recognizer.AcceptWaveform(data):
            final_result = json.loads(recognizer.Result())
            text = final_result.get("text", "")
            if text.strip():
                text_box.config(state=tk.NORMAL)
                text_box.insert(tk.END, text + "\n")
                text_box.see(tk.END)
                text_box.config(state=tk.DISABLED)
                live_label.config(text="")  # Clear live line

# Threaded transcription
thread = threading.Thread(target=listen_and_transcribe)
thread.daemon = True
thread.start()

# Run GUI
root.mainloop()



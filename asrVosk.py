from vosk import Model, KaldiRecognizer
import pyaudio
import json

# Load Vosk model (Make sure the path is correct)
model = Model(r"C:\Users\DELL\PycharmProjects\ASR\vosk-model-small-en-us-0.15")
recognizer = KaldiRecognizer(model, 16000)

# Initialize microphone stream
mic = pyaudio.PyAudio()
stream = mic.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
stream.start_stream()

print("🎤 Listening... (Press Ctrl+C to stop)")

try:
    while True:
        data = stream.read(4096, exception_on_overflow=False)

        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "")
            if text.strip():
                print("📝", text)
        else:
            # Optional: partial results while still recognizing
            pass

except KeyboardInterrupt:
    print("\n🛑 Stopped by user.")
    stream.stop_stream()
    stream.close()
    mic.terminate()

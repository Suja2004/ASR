import speech_recognition as sr

def list_audio_devices():
    print("Available Audio Devices:")
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"{index}: {name}")

def transcribe_from_virtual_input(device_index):
    recognizer = sr.Recognizer()
    mic = sr.Microphone(device_index=device_index)

    with mic as source:
        print("Adjusting for ambient noise...")
        recognizer.adjust_for_ambient_noise(source)
        print("Listening from virtual input (e.g., YouTube/Meet)...")

        while True:
            try:
                audio = recognizer.listen(source)
                text = recognizer.recognize_google(audio)
                print(">>", text)
            except sr.UnknownValueError:
                print("** Could not understand audio **")
            except sr.RequestError:
                print("** Recognition service error **")

if __name__ == "__main__":
    list_audio_devices()
    idx = int(input("Enter the device index for virtual audio cable: "))
    transcribe_from_virtual_input(idx)

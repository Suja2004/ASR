from speech_app_gui import SpeechAppGUI


def main():
    """Main entry point for the application"""
    app = SpeechAppGUI()

    # Enable proper cleanup on window close
    # app.accept("window-closed", app.shutdown)

    app.run()


if __name__ == "__main__":
    main()
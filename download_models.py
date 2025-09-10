from RealtimeSTT import AudioToTextRecorder

if __name__ == '__main__':
    # List of all the models you might want to use.
    # The '.en' versions are English-only and generally faster/smaller.
    model_names = [
        "tiny.en",
        "base.en",
        "small.en",
        "medium.en",
        "large-v1",
        "large-v2",
        "large-v3",
        "large-v3-turbo"
    ]

    print("Starting download process for all RealtimeSTT models...")

    for model in model_names:
        try:
            print(f"\n--- Downloading model: {model} ---")
            # This line is all that's needed. 
            # Initializing the recorder will trigger the download if the model is not cached.
            recorder = AudioToTextRecorder(model=model, device="cuda")
            print(f"--- Successfully downloaded and cached {model} ---")
            
            # We add a shutdown to release the model from memory before loading the next one.
            recorder.shutdown()

        except Exception as e:
            print(f"Could not download model {model}. Error: {e}")

    print("\nAll models have been downloaded and are ready for offline use.")
#!/usr/bin/env python3
"""
Test script for emotion recognition using your torchenv environment
"""

def test_imports():
    """Test if all required packages can be imported"""
    try:
        print("Testing imports...")
        
        import torch
        print(f"✓ PyTorch {torch.__version__}")
        
        import transformers
        print(f"✓ Transformers {transformers.__version__}")
        
        import librosa
        print(f"✓ Librosa {librosa.__version__}")
        
        import funasr
        print(f"✓ FunASR {funasr.__version__}")
        
        import numpy as np
        print(f"✓ NumPy {np.__version__}")
        
        import scipy
        print(f"✓ SciPy {scipy.__version__}")
        
        print("\n🎉 All packages imported successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_emotion_recognition():
    """Test basic emotion recognition functionality"""
    try:
        from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
        import torch
        import librosa
        import numpy as np
        
        print("\nTesting emotion recognition model loading...")
        
        # Load model and feature extractor
        feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(
            "r-f/wav2vec-english-speech-emotion-recognition"
        )
        model = Wav2Vec2ForSequenceClassification.from_pretrained(
            "r-f/wav2vec-english-speech-emotion-recognition"
        )
        model.eval()
        
        print("✓ Emotion recognition model loaded successfully!")
        
        # Test with a simple audio signal
        print("\nTesting with synthetic audio...")
        duration = 2.0  # seconds
        sr = 16000
        t = np.linspace(0, duration, int(sr * duration))
        test_signal = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        
        # Process the signal
        inputs = feature_extractor(test_signal, sampling_rate=sr, return_tensors="pt", padding=True)
        
        with torch.no_grad():
            logits = model(**inputs).logits
        
        probs = torch.softmax(logits.squeeze(0), dim=-1)
        top_prob, predicted_id = torch.max(probs, dim=-1)
        emotion = model.config.id2label[predicted_id.item()]
        
        print(f"✓ Test prediction: {emotion} (confidence: {top_prob.item():.3f})")
        return True
        
    except Exception as e:
        print(f"❌ Emotion recognition test failed: {e}")
        return False

def test_funasr():
    """Test FunASR functionality"""
    try:
        from funasr import AutoModel
        
        print("\nTesting FunASR...")
        model = AutoModel(model="FunAudioLLM/SenseVoiceSmall", hub="hf", device="cpu")
        print("✓ FunASR model loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ FunASR test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TESTING EMOTION RECOGNITION SETUP")
    print("=" * 60)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test emotion recognition
        emotion_ok = test_emotion_recognition()
        
        # Test FunASR
        funasr_ok = test_funasr()
        
        if emotion_ok and funasr_ok:
            print("\n✅ All tests passed! Your environment is ready!")
            print("\nYou can now run your emotion recognition code directly in Cursor.")
        else:
            print("\n❌ Some tests failed. Check your setup.")
    else:
        print("\n❌ Import tests failed. Check your conda environment.")

#!/usr/bin/env python3
"""
Run emotion analysis directly in Cursor using your torchenv environment
"""

from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
import torch
import librosa
import math
import numpy as np
from collections import Counter, deque
import warnings
warnings.filterwarnings('ignore')

class SimpleEmotionRecognizer:
    def __init__(self, model_name="r-f/wav2vec-english-speech-emotion-recognition"):
        print(f"Loading emotion recognition model: {model_name}")
        self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_name)
        self.model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
        self.model.eval()
        print("✓ Model loaded successfully!")
    
    def is_valid_speech(self, audio_chunk, sr):
        """Check if audio chunk contains valid speech"""
        rms = np.sqrt(np.mean(audio_chunk**2))
        if rms < 0.005:
            return False
        
        zcr = np.mean(librosa.feature.zero_crossing_rate(audio_chunk)[0])
        if zcr > 0.4:
            return False
        
        return True
    
    def predict_emotion(self, audio_chunk, sr):
        """Predict emotion for a single audio chunk"""
        if not self.is_valid_speech(audio_chunk, sr):
            return None, 0.0
        
        try:
            inputs = self.feature_extractor(audio_chunk, sampling_rate=sr, return_tensors="pt", padding=True)
            
            with torch.no_grad():
                logits = self.model(**inputs).logits
            
            probs = torch.softmax(logits.squeeze(0), dim=-1)
            top_prob, predicted_id = torch.max(probs, dim=-1)
            
            emotion = self.model.config.id2label[predicted_id.item()]
            confidence = top_prob.item()
            
            return emotion, confidence
            
        except Exception as e:
            print(f"Error in prediction: {e}")
            return None, 0.0
    
    def analyze_audio_file(self, audio_file):
        """Analyze an audio file for emotions"""
        print(f"Analyzing audio file: {audio_file}")
        
        # Load and preprocess audio
        waveform, rate = librosa.load(audio_file, sr=16000)
        waveform = librosa.util.normalize(waveform)
        waveform, _ = librosa.effects.trim(waveform, top_db=20)
        
        total_duration = len(waveform) / rate
        print(f"Audio duration: {total_duration:.2f} seconds")
        
        # Split into chunks
        chunk_duration = 1.0  # seconds
        overlap_duration = 0.5
        chunk_size = int(chunk_duration * rate)
        overlap_size = int(overlap_duration * rate)
        
        chunks = []
        chunk_times = []
        
        step_size = chunk_size - overlap_size
        num_chunks = math.ceil((len(waveform) - chunk_size) / step_size) + 1
        
        for i in range(num_chunks):
            start_sample = i * step_size
            end_sample = min(start_sample + chunk_size, len(waveform))
            
            if end_sample - start_sample < chunk_size // 3:
                break
            
            chunk = waveform[start_sample:end_sample]
            
            if len(chunk) < chunk_size:
                chunk = np.pad(chunk, (0, chunk_size - len(chunk)), mode='constant')
            
            chunks.append(chunk)
            chunk_times.append((start_sample / rate, min(end_sample / rate, total_duration)))
        
        # Process chunks
        results = []
        print(f"\nProcessing {len(chunks)} audio chunks...")
        
        for i, (start_time, end_time, chunk) in enumerate(zip([t[0] for t in chunk_times], 
                                                             [t[1] for t in chunk_times], 
                                                             chunks)):
            
            emotion, confidence = self.predict_emotion(chunk, rate)
            
            if emotion is None:
                print(f"{start_time:6.1f}-{end_time:6.1f}s: [SKIP: No speech]")
                continue
            
            result = {
                'emotion': emotion,
                'confidence': confidence,
                'start': start_time,
                'end': end_time
            }
            
            results.append(result)
            print(f"{start_time:6.1f}-{end_time:6.1f}s: {emotion:12} (conf: {confidence:.3f})")
        
        return results

def main():
    """Main function to run emotion analysis"""
    print("=" * 60)
    print("EMOTION RECOGNITION ANALYSIS")
    print("=" * 60)
    
    # Initialize recognizer
    recognizer = SimpleEmotionRecognizer()
    
    # Example usage - replace with your audio file path
    audio_file = "/Users/madhusiddharthsuthagar/Downloads/input_9.mp3"  # Update this path
    
    try:
        results = recognizer.analyze_audio_file(audio_file)
        
        if not results:
            print("No valid speech segments detected.")
            return
        
        # Summary
        print("\n" + "=" * 60)
        print("EMOTION ANALYSIS SUMMARY")
        print("=" * 60)
        
        emotions = [r['emotion'] for r in results]
        confidences = [r['confidence'] for r in results]
        
        emotion_counts = Counter(emotions)
        print(f"Total analyzed duration: {results[-1]['end'] - results[0]['start']:.1f}s")
        print(f"Number of segments: {len(results)}")
        print(f"Average confidence: {np.mean(confidences):.3f}")
        print(f"Most common emotion: {emotion_counts.most_common(1)[0][0]}")
        
        print("\nEmotion distribution:")
        for emotion, count in emotion_counts.most_common():
            percentage = (count / len(emotions)) * 100
            print(f"  {emotion:12}: {count:2d} segments ({percentage:5.1f}%)")
        
    except FileNotFoundError:
        print(f"❌ Audio file not found: {audio_file}")
        print("Please update the audio_file path in the script.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

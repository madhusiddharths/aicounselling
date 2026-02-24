'use client';

import React, { useEffect, useRef, useState } from 'react';

type Props = {
  userId: string;
  uploadUrl?: string;
  size?: number;
};

const VoiceCircle: React.FC<Props> = ({
  userId,
  uploadUrl = '/api/audio',
  size = 200,
}) => {
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const start = async () => {
    if (recorderRef.current) return;
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100,
        },
      });
      streamRef.current = stream;

      const mime = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : (MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '');

      const mr = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);

      chunksRef.current = [];
      mr.ondataavailable = (ev) => {
        if (ev.data && ev.data.size > 0) {
          chunksRef.current.push(ev.data);
        }
      };

      recorderRef.current = mr;
      mr.start(); // collect all in one go until stopped
      setIsListening(true);
    } catch (e) {
      console.error('mic error', e);
      setError('Microphone permission required');
    }
  };

  const stopRecording = (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!recorderRef.current || recorderRef.current.state === 'inactive') {
        resolve(null);
        return;
      }
      recorderRef.current.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorderRef.current!.mimeType || 'audio/webm' });
        chunksRef.current = [];
        resolve(blob);
      };
      recorderRef.current.stop();
      setIsListening(false);
    });
  };

  const audioContextUnlocked = useRef(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    const audio = new Audio();
    audioRef.current = audio;
    return () => {
      if (recorderRef.current && recorderRef.current.state !== 'inactive') recorderRef.current.stop();
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const processVoice = async () => {
    try {
      const FASTAPI_BASE_URL = process.env.NEXT_PUBLIC_FASTAPI_BASE_URL || 'http://localhost:8000';
      const res = await fetch(`${FASTAPI_BASE_URL}/process_speech?userid=${encodeURIComponent(userId)}`);

      if (res.ok) {
        const data = await res.json();

        if (data.audio_base64 && audioRef.current) {
          audioRef.current.src = `data:audio/mp3;base64,${data.audio_base64}`;
          try {
            await audioRef.current.play();
          } catch (e) {
            console.error("Audio play error", e);
            setError("Audio playback blocked by browser.");
          }
        }
      } else {
        setError(`Backend Error: ${res.statusText}`);
      }
    } catch (e) {
      console.error('Processing error', e);
      setError("Failed to reach server for processing.");
    }
  };

  const onClick = async () => {
    if (!audioContextUnlocked.current && audioRef.current) {
      audioRef.current.src = "data:audio/mp3;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjYxLjEuMTAwAAAAAAAAAAAAAAD/+0DAAAAAAAAAAAAAAAAAAAAAAABqb2luZWQAR0A=";
      audioRef.current.play().catch(() => { });
      audioContextUnlocked.current = true;
    }

    if (!isListening) {
      start();
    } else {
      setIsProcessing(true);
      const blob = await stopRecording();

      if (blob && blob.size > 0) {
        try {
          const form = new FormData();
          form.append('file', new File([blob], `audio_complete.webm`, { type: blob.type }));
          form.append('userId', userId);
          form.append('timestamp', String(Date.now()));
          form.append('frameId', "0");

          const res = await fetch(uploadUrl, { method: 'POST', body: form });
          if (!res.ok) console.error('Upload failed', res.status);
        } catch (e) {
          console.error(e);
        }
        await processVoice();
      }

      setIsProcessing(false);

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
      recorderRef.current = null;
    }
  };

  return (
    <div className="flex flex-col items-center justify-center gap-6 w-full">
      <div className={`
        relative flex items-center justify-center w-32 h-32 rounded-full transition-all duration-500
        ${isListening ? 'bg-red-500/20 shadow-[0_0_50px_rgba(239,68,68,0.4)] scale-110' : 'bg-white/5 shadow-glow'}
        border border-white/10 backdrop-blur-md
      `}>
        <div className={`absolute inset-0 rounded-full border border-white/20 ${isListening ? 'animate-ping opacity-20' : 'opacity-0'}`} />

        <button
          onClick={onClick}
          className={`
            z-10 w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300
            ${isListening
              ? 'bg-gradient-to-br from-red-500 to-pink-600 text-white shadow-lg scale-90'
              : 'bg-gradient-to-br from-cyan-500 to-blue-600 text-white shadow-lg hover:scale-105'}
          `}
        >
          {isListening ? (
            <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
            </svg>
          ) : (
            <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          )}
        </button>
      </div>

      <div className="h-6">
        <p className={`text-sm font-medium transition-colors ${isProcessing ? 'text-emerald-400 animate-pulse' :
          isListening ? 'text-red-300 animate-pulse' : 'text-white/60'
          }`}>
          {isProcessing ? "Processing Speech..." : isListening ? "Listening..." : "Tap to Speak"}
        </p>
      </div>

      {error && (
        <p className="text-xs text-red-400 bg-red-900/20 px-3 py-1 rounded-full border border-red-500/20">
          {error}
        </p>
      )}
    </div>
  );
};

export default VoiceCircle;

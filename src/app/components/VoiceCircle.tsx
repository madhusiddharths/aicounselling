'use client';

import React, { useEffect, useRef, useState } from 'react';

type Props = {
  userId: string;              // <-- add
  uploadUrl?: string;          // <-- add (default to /api/uploadAudio)
  size?: number;
};

type PendingFrame = {
  blob: Blob;
  tsMs: number;
  seq: number;
};

const VoiceCircle: React.FC<Props> = ({
  userId,
  uploadUrl = '/api/uploadAudio',
  size = 200,
}) => {
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoaded, setIsLoaded] = useState(true); // Mock loaded state for now

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);

  const seqRef = useRef(0);
  const sendingRef = useRef<Promise<void> | null>(null);
  const pendingRef = useRef<PendingFrame | null>(null);

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

      mr.ondataavailable = (ev) => {
        if (!ev.data || ev.data.size === 0) return;
        pendingRef.current = {
          blob: ev.data,
          tsMs: Date.now(),
          seq: seqRef.current++,
        };
        if (!sendingRef.current) {
          sendingRef.current = sendLoop();
        }
      };

      mr.onstart = () => {
        seqRef.current = 0;
      };

      recorderRef.current = mr;
      mr.start(3000);
      setIsListening(true);
    } catch (e) {
      console.error('mic error', e);
      setError('Microphone permission required');
    }
  };

  const stop = () => {
    setIsListening(false);
    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      recorderRef.current.stop();
    }
    recorderRef.current = null;
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  };

  const sendLoop = async () => {
    try {
      while (true) {
        const next = pendingRef.current;
        if (!next) break;
        pendingRef.current = null;

        const file = new File([next.blob], `frame_${next.seq}.webm`, { type: next.blob.type || 'audio/webm' });
        const form = new FormData();
        form.append('file', file);
        form.append('userId', userId);
        form.append('timestamp', String(next.tsMs));
        form.append('frameId', String(next.seq));

        const res = await fetch(uploadUrl, { method: 'POST', body: form });
        if (!res.ok) {
          console.error('Upload failed', res.status, await res.text().catch(() => ''));
        }
      }
    } finally {
      sendingRef.current = null;
      if (pendingRef.current && !sendingRef.current) {
        sendingRef.current = sendLoop();
      }
    }
  };

  const processVoice = async () => {
    try {
      // Call backend to process the uploaded speech fragments
      const res = await fetch(`http://localhost:8000/process_speech?userid=${encodeURIComponent(userId)}`);
      if (res.ok) {
        const data = await res.json();

        // 1. Play Audio if available
        if (data.audio_base64) {
          const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`);
          audio.play().catch(e => console.error("Audio play error", e));
        }
      }
    } catch (e) {
      console.error('Processing error', e);
    }
  };

  const onClick = () => {
    if (!isListening) {
      start();
    } else {
      stop();
      // Small delay to ensure last chunk is processed before calling backend
      setTimeout(processVoice, 1000);
    }
  };

  useEffect(() => () => stop(), []);

  // Tailwind-powered circle with green hero palette; minimal-only circle (no X / no text)
  return (
    <div className="flex flex-col items-center justify-center gap-6 w-full">
      {/* Visualizer / Microphone Circle */}
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

      {/* Status Text */}
      <div className="h-6">
        <p className={`text-sm font-medium transition-colors ${isListening ? 'text-red-300 animate-pulse' : 'text-white/60'}`}>
          {isListening ? "Listening..." : "Tap to Speak"}
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <p className="text-xs text-red-400 bg-red-900/20 px-3 py-1 rounded-full border border-red-500/20">
          {error}
        </p>
      )}
    </div>
  );
};

export default VoiceCircle;

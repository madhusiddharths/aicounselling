'use client';

import { useEffect, useRef, useState } from 'react';

function pickSupportedMime(): string {
  const prefs = [
    'video/webm;codecs=vp9,opus',
    'video/webm;codecs=vp8,opus',
    'video/webm',
  ];
  for (const m of prefs) {
    if ((window as typeof window & { MediaRecorder: typeof MediaRecorder }).MediaRecorder?.isTypeSupported?.(m)) {
      return m;
    }
  }
  return 'video/webm'; // safest general fallback
}

export default function VideoRecorder({ userId }: { userId?: string }) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const [recording, setRecording] = useState<boolean>(false);
  const [status, setStatus] = useState<string>('');
  const [stream, setStream] = useState<MediaStream | null>(null);

  async function uploadToServer(blob: Blob): Promise<void> {
    const filename = `recording_${Date.now()}.webm`;
    const file = new File([blob], filename, { type: blob.type || 'video/webm' });
    const formData = new FormData();
    formData.append('file', file);
    // Backend expects 'user_id' as query param or form param? 
    // The backend `detect_video_emotions(user_id, file...)` -> query param usually in FastAPI if not Form(...)
    // Let's try appending as query param to be safe or FormData if it's Form.
    // Looking at main2.py: async def detect_video_emotions(user_id, file: UploadFile = File(...)):
    // FastAPI defaults scalar types to query params unless Body/Form is specified. 
    // Let's use query param for user_id to be safe match.

    setStatus('Analyzing emotions...');
    try {
      // Direct call to FastAPI backend
      const res = await fetch(`http://localhost:8000/detect_video_emotions?user_id=${encodeURIComponent(userId || 'anon')}`, {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error || 'Analysis failed');
      }

      const data = await res.json();
      // Expecting: { emotions_per_frame, total_frames, final_emotion, final_response }
      setStatus(`Emotion: ${data.final_emotion}. Response: ${data.final_response}`);

      // OPTIONAL: If you want to surface this response to the ChatPane or UI, 
      // you might need a callback prop on VideoRecorder, e.g. onResponse(data.final_response).
      // For now, displaying in status is a good step 1.
      if (data.final_response) {
        alert(`Therapist says: ${data.final_response}`); // Simple feedback for now
      }

    } catch (e: any) {
      setStatus(`Error: ${e.message}`);
    }
  }

  const startRecording = async (): Promise<void> => {
    try {
      setStatus('Requesting camera/mic...');
      const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      setStream(s);

      if (videoRef.current) {
        videoRef.current.srcObject = s;
        await videoRef.current.play();
      }

      const mimeType = pickSupportedMime();
      const options: MediaRecorderOptions = { mimeType };

      const mr = new MediaRecorder(s, options);
      mediaRecorderRef.current = mr;

      let chunks: Blob[] = [];

      mr.ondataavailable = (e: BlobEvent): void => {
        if (e.data && e.data.size > 0) chunks.push(e.data);
      };

      mr.onstart = (): void => {
        setStatus('Recording...');
        setRecording(true);
      };

      mr.onstop = async (): Promise<void> => {
        setRecording(false);
        setStatus('Finalizing recording...');
        const blob = new Blob(chunks, { type: mimeType });
        chunks = [];

        if (videoRef.current) {
          videoRef.current.pause();
          videoRef.current.srcObject = null;
        }
        if (stream) {
          stream.getTracks().forEach((t) => t.stop());
          setStream(null);
        }

        await uploadToServer(blob);
      };

      mr.start(); // optional: pass timeslice (ms) to get periodic chunks
    } catch {
      setStatus('Unable to start recording (permissions/device?)');
    }
  };

  const stopRecording = (): void => {
    const mr = mediaRecorderRef.current;
    if (mr && mr.state === 'recording') {
      setStatus('Stopping...');
      mr.stop();
    }
  };

  useEffect(() => {
    return () => {
      const mr = mediaRecorderRef.current;
      if (mr && mr.state === 'recording') {
        try {
          mr.stop();
        } catch {
          // ignore
        }
      }
      if (stream) {
        stream.getTracks().forEach((t) => t.stop());
      }
    };
  }, [stream]);

  return (
    <div className="space-y-4">
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        style={{ width: 480, maxWidth: '100%', borderRadius: 8, background: '#000' }}
      />
      <div className="flex gap-3">
        {!recording ? (
          <button
            onClick={startRecording}
            className="rounded bg-green-600 px-4 py-2 text-white hover:bg-green-700"
          >
            Start Recording
          </button>
        ) : (
          <button
            onClick={stopRecording}
            className="rounded bg-red-600 px-4 py-2 text-white hover:bg-red-700"
          >
            Stop &amp; Save
          </button>
        )}
      </div>
      {status && <p className="text-sm text-gray-600">{status}</p>}
    </div>
  );
}

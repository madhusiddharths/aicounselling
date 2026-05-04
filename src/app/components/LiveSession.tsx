'use client';

import React, { useEffect, useRef, useState } from 'react';

type Props = {
    userId: string;
};
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
    return 'video/webm';
}

export default function LiveSession({ userId }: Props) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const [isSessionActive, setIsSessionActive] = useState(false);
    const [status, setStatus] = useState("Idle");
    const [reply, setReply] = useState<string>("");
    const [liveEmotion, setLiveEmotion] = useState<string>("");
    const emotionsRef = useRef<string[]>([]);

    // Audio/Video Refs
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    const startSession = async () => {
        try {
            setStatus("Initializing...");
            setReply("");
            setLiveEmotion("");
            const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                videoRef.current.play();
            }

            emotionsRef.current = [];
            setIsSessionActive(true);
            setStatus("Listening & Watching...");

            // 1. Start Video Analysis Loop (Frame Capture)
            startVideoLoop(stream);

            // 2. Start Full Audio/Video Recording
            const mime = pickSupportedMime();
            const mr = new MediaRecorder(stream, { mimeType: mime });
            mediaRecorderRef.current = mr;

            audioChunksRef.current = [];
            mr.ondataavailable = (ev) => {
                if (ev.data.size > 0) audioChunksRef.current.push(ev.data);
            };
            mr.start();

        } catch (e) {
            console.error("Session start error", e);
            alert("Microphone/Camera permission required.");
        }
    };

    const stopRecording = (): Promise<Blob | null> => {
        return new Promise((resolve) => {
            if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
                resolve(null);
                return;
            }
            mediaRecorderRef.current.onstop = () => {
                const blob = new Blob(audioChunksRef.current, { type: mediaRecorderRef.current!.mimeType || 'video/webm' });
                audioChunksRef.current = [];
                resolve(blob);
            };
            mediaRecorderRef.current.stop();
        });
    };

    const stopSession = async () => {
        setStatus("Processing final response...");
        setIsSessionActive(false);

        // Stop Media
        if (videoRef.current) videoRef.current.srcObject = null;

        const blob = await stopRecording();

        if (streamRef.current) {
            streamRef.current.getTracks().forEach(t => t.stop());
            streamRef.current = null;
        }

        if (!blob || blob.size === 0) {
            setStatus("Idle");
            return;
        }

        try {
            const formData = new FormData();
            formData.append('file', new File([blob], `session.webm`, { type: blob.type }));
            formData.append('client_emotions', JSON.stringify(emotionsRef.current));

            const FASTAPI_BASE_URL = process.env.NEXT_PUBLIC_FASTAPI_BASE_URL || 'http://localhost:8000';
            const res = await fetch(`${FASTAPI_BASE_URL}/detect_video_emotions?user_id=${encodeURIComponent(userId)}`, {
                method: "POST",
                body: formData
            });

            if (res.ok) {
                const data = await res.json();
                console.log("Video Response:", data);
                setReply(data.final_response || "");
                setStatus("Replying...");

                if (data.audio_base64) {
                    const audio = new Audio(`data:audio/mp3;base64,${data.audio_base64}`);
                    audio.play();
                    audio.onended = () => setStatus("Idle");
                } else {
                    setStatus("Idle");
                }
            } else {
                setStatus("Error processing response.");
            }
        } catch (e) {
            console.error(e);
            setStatus("Error connecting to backend.");
        }
    };

    // --- Video Analysis Helpers ---
    const startVideoLoop = (stream: MediaStream) => {
        const track = stream.getVideoTracks()[0];
        const imageCapture = new (window as any).ImageCapture(track);

        const loop = async () => {
            if (!stream.active || !streamRef.current) return;

            try {
                const blob = await imageCapture.takePhoto();
                const formData = new FormData();
                formData.append("file", blob, "frame.jpg");

                const FASTAPI_BASE_URL = process.env.NEXT_PUBLIC_FASTAPI_BASE_URL || 'http://localhost:8000';
                const res = await fetch(`${FASTAPI_BASE_URL}/analyze_frame`, {
                    method: "POST",
                    body: formData
                });
                if (res.ok) {
                    const data = await res.json();
                    if (data.emotion && data.emotion !== "No face") {
                        emotionsRef.current.push(data.emotion);
                        setLiveEmotion(data.emotion);
                    }
                }
            } catch (e) {
                console.warn("Frame capture error", e);
            }

            if (streamRef.current?.active) {
                setTimeout(loop, 1000); // 1 FPS
            }
        };
        loop();
    };

    return (
        <div className="flex flex-col items-center gap-6 w-full h-full p-4 relative">
            <div className="relative w-full max-w-3xl aspect-video bg-black/40 rounded-3xl overflow-hidden shadow-2xl ring-1 ring-white/10 backdrop-blur-sm">
                <video
                    ref={videoRef}
                    muted
                    playsInline
                    className="w-full h-full object-cover transform scale-x-[-1]" // mirror effect
                />

                {/* Status Overlay */}
                <div className="absolute top-4 left-4 px-4 py-2 bg-black/40 backdrop-blur-md rounded-full border border-white/10 text-white/90 text-sm font-medium flex items-center gap-2 shadow-lg">
                    <div className={`w-2.5 h-2.5 rounded-full ${isSessionActive ? 'bg-red-500 animate-pulse shadow-[0_0_10px_#ef4444]' : 'bg-slate-500'}`} />
                    {status}
                </div>

                {liveEmotion && isSessionActive && (
                    <div className="absolute top-4 right-4 px-4 py-2 bg-black/40 backdrop-blur-md rounded-full border border-white/10 text-white/90 text-sm font-medium shadow-lg">
                        {liveEmotion}
                    </div>
                )}
            </div>

            {reply && !isSessionActive && (
                <div className="w-full max-w-3xl px-6 py-4 bg-white/5 backdrop-blur-md rounded-2xl border border-white/10 text-white/90 text-base leading-relaxed shadow-lg whitespace-pre-wrap">
                    {reply}
                </div>
            )}

            <div className="flex gap-4">
                {!isSessionActive ? (
                    <button
                        onClick={startSession}
                        className="btn-primary flex items-center gap-2 text-lg"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                        Start Live Session
                    </button>
                ) : (
                    <button
                        onClick={stopSession}
                        className="px-8 py-3 rounded-full bg-red-500/80 hover:bg-red-600 text-white font-medium text-lg shadow-lg shadow-red-500/20 transition-all hover:scale-105 active:scale-95 flex items-center gap-2 backdrop-blur-md border border-red-400/20"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                        </svg>
                        End & Response
                    </button>
                )}
            </div>
        </div>
    );
}

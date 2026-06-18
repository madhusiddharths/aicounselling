'use client';

import React, { useEffect, useRef, useState } from 'react';
import type * as FaceApi from '@vladmandic/face-api';

type Props = {
    userId: string;
};

// face-api is dynamically imported (browser-only) so it never runs during SSR.
// Models live in /public/models and are served statically. Load once per page.
let faceapi: typeof FaceApi | null = null;
let faceModelsLoaded = false;
async function loadFaceModels(): Promise<typeof FaceApi> {
    if (!faceapi) {
        faceapi = await import('@vladmandic/face-api');
    }
    if (!faceModelsLoaded) {
        await Promise.all([
            faceapi.nets.tinyFaceDetector.loadFromUri('/models'),
            faceapi.nets.faceExpressionNet.loadFromUri('/models'),
        ]);
        faceModelsLoaded = true;
    }
    return faceapi;
}

function pickAudioMime(): string {
    const prefs = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus'];
    for (const m of prefs) {
        if ((window as typeof window & { MediaRecorder: typeof MediaRecorder }).MediaRecorder?.isTypeSupported?.(m)) {
            return m;
        }
    }
    return 'audio/webm';
}

export default function LiveSession({ userId }: Props) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const [isSessionActive, setIsSessionActive] = useState(false);
    const [status, setStatus] = useState("Idle");
    const [reply, setReply] = useState<string>("");
    const [liveEmotion, setLiveEmotion] = useState<string>("");
    const emotionsRef = useRef<string[]>([]);

    // Audio-only recorder (we keep the video stream for preview + in-browser
    // emotion detection, but only upload audio to the backend).
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const faceLoopRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const startSession = async () => {
        try {
            setStatus("Initializing...");
            setReply("");
            setLiveEmotion("");

            // Kick off model load + camera in parallel.
            const [stream, fa] = await Promise.all([
                navigator.mediaDevices.getUserMedia({ video: true, audio: true }),
                loadFaceModels(),
            ]);
            streamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                await videoRef.current.play();
            }

            emotionsRef.current = [];
            setIsSessionActive(true);
            setStatus("Listening & Watching...");

            // 1. In-browser face-emotion loop (no backend round-trips).
            startVideoLoop(fa);

            // 2. Record AUDIO ONLY — the backend only needs audio for transcript + tone.
            const audioStream = new MediaStream(stream.getAudioTracks());
            const mime = pickAudioMime();
            const mr = new MediaRecorder(audioStream, { mimeType: mime });
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
                const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
                audioChunksRef.current = [];
                resolve(blob);
            };
            mediaRecorderRef.current.stop();
        });
    };

    const stopSession = async () => {
        setStatus("Processing final response...");
        setIsSessionActive(false);

        // Stop the face loop and media preview.
        if (faceLoopRef.current) {
            clearTimeout(faceLoopRef.current);
            faceLoopRef.current = null;
        }
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
            // Audio-only blob — kept as .webm so the backend's splitext + ffmpeg/pydub path works.
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

    // --- In-browser emotion detection (replaces per-second /analyze_frame calls) ---
    const startVideoLoop = (fa: typeof FaceApi) => {
        const options = new fa.TinyFaceDetectorOptions();

        const loop = async () => {
            const video = videoRef.current;
            if (!streamRef.current?.active || !video || video.readyState < 2) {
                if (streamRef.current?.active) {
                    faceLoopRef.current = setTimeout(loop, 1000);
                }
                return;
            }

            try {
                const result = await fa
                    .detectSingleFace(video, options)
                    .withFaceExpressions();

                if (result?.expressions) {
                    const top = result.expressions.asSortedArray()[0];
                    if (top && top.probability > 0.3) {
                        emotionsRef.current.push(top.expression);
                        setLiveEmotion(top.expression);
                    }
                }
            } catch (e) {
                console.warn("Face detection error", e);
            }

            if (streamRef.current?.active) {
                faceLoopRef.current = setTimeout(loop, 1000); // ~1 FPS
            }
        };
        loop();
    };

    // Cleanup on unmount.
    useEffect(() => {
        return () => {
            if (faceLoopRef.current) clearTimeout(faceLoopRef.current);
            if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
                try { mediaRecorderRef.current.stop(); } catch { /* ignore */ }
            }
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(t => t.stop());
                streamRef.current = null;
            }
        };
    }, []);

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

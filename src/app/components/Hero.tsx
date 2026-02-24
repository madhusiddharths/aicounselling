// src/app/components/Hero.tsx
'use client';

import { useState, useMemo } from 'react';
import ChatPane from './chat/ChatPane';
import ModeToggle from './ModeToggle';
import { useUser } from '@clerk/nextjs';
import VoiceCircle from './VoiceCircle';
import VideoRecorder from './VideoRecorder';
import LiveSession from './LiveSession';

const FASTAPI_BASE_URL = process.env.NEXT_PUBLIC_FASTAPI_BASE_URL || 'http://localhost:8000';

type ModeChoice = 'text' | 'voice' | 'video';

type PublicMetadataShape = {
  preferredMode?: string;
  mode?: string;
  preferences?: { mode?: string };
};

function coerceMode(s: string | undefined | null): ModeChoice {
  const v = String(s ?? '').toLowerCase();
  if (v === 'text' || v === 'voice' || v === 'video') return v;
  if (v === 'multimodal') return 'voice';
  return 'voice';
}

export default function Hero() {
  const { user, isLoaded } = useUser();

  // Initial mode derived from user preferences, but now managed by useState
  const initialMode: ModeChoice = useMemo(() => {
    if (!isLoaded) return 'voice';
    const pm = (user?.publicMetadata ?? {}) as PublicMetadataShape;
    const picked = pm.preferences?.mode ?? pm.preferredMode ?? pm.mode ?? '';
    return coerceMode(picked);
  }, [isLoaded, user?.publicMetadata]);

  const [mode, setMode] = useState<ModeChoice>(initialMode); // State for mode selection

  async function processSpeech() {
    if (!user?.id) return;
    try {
      const url = `${FASTAPI_BASE_URL}/process_speech?userid=${encodeURIComponent(user.id)}`;
      const res = await fetch(url);
      const json = await res.json();
      if (!res.ok) {
        console.error('Process failed:', json);
        return;
      }
      console.log('process_speech response:', json);
      // you can toast this JSON or render the answer in UI
    } catch (e) {
      console.error('Process request failed', e);
    }
  }

  const modeLabels = {
    text: "Chat",
    voice: "Voice",
    video: "Live Session"
  };

  return (
    <section className="relative flex min-h-screen flex-col items-center justify-center pt-24 pb-12 px-4">
      {/* Background Mesh (defined in globals.css) */}
      <div className="bg-mesh" />

      <div className="w-full max-w-4xl mx-auto flex flex-col items-center text-center space-y-8 z-10">

        {/* Header */}
        <div className="space-y-4 max-w-2xl">
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60">
            How are you feeling?
          </h1>
          <p className="text-lg text-white/60 font-light">
            I'm here to listen, whether you want to chat, talk, or share face-to-face.
          </p>
        </div>

        {/* Mode Selector - Tabs */}
        <div className="p-1 glass-pill inline-flex items-center gap-1">
          {(['text', 'voice', 'video'] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`
                px-6 py-2 rounded-full text-sm font-medium transition-all duration-300
                ${mode === m
                  ? 'bg-white/10 text-white shadow-sm'
                  : 'text-white/40 hover:text-white/70 hover:bg-white/5'}
              `}
            >
              {modeLabels[m]}
            </button>
          ))}
        </div>

        {/* Main Content Area */}
        <div className="w-full transition-all duration-500 ease-in-out transform">
          {mode === 'text' && (
            <div className="glass-panel w-full max-w-3xl mx-auto h-[600px] overflow-hidden flex flex-col p-1">
              <ChatPane />
            </div>
          )}

          {mode === 'voice' && (
            <div className="glass-panel w-full max-w-md mx-auto p-8 flex flex-col items-center gap-6 min-h-[400px] justify-center">
              {isLoaded && user?.id ? (
                <>
                  <VoiceCircle userId={user.id} uploadUrl="/api/audio" />
                </>
              ) : (
                <div className="text-center space-y-4">
                  <p className="text-white/60">Sign in to start a voice session.</p>
                  {/* Suggest signing in */}
                </div>
              )}
            </div>
          )}

          {mode === 'video' && (
            <div className="glass-panel w-full max-w-4xl mx-auto p-4 md:p-8 min-h-[500px] flex items-center justify-center">
              {isLoaded && user?.id ? (
                <LiveSession userId={user.id} />
              ) : (
                <p className="text-white/60">Sign in to start a video session.</p>
              )}
            </div>
          )}
        </div>

      </div>
    </section>
  );
}


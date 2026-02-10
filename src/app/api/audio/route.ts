// src/app/api/audio/route.ts
import { NextRequest, NextResponse } from 'next/server';
import crypto from 'node:crypto';
import { Storage } from '@google-cloud/storage';
import { auth } from '@clerk/nextjs/server';
import { insertAudioMeta } from '@/db/audio';

const storage = new Storage();
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(req: NextRequest) {
  const BUCKET_NAME = process.env.GCS_BUCKET!;
  const { userId, redirectToSignIn } = await auth();
  if (!userId) return redirectToSignIn({ returnBackUrl: '/session' });

  const form = await req.formData();

  // The VoiceCircle component sends 'file', but this route expects 'audio' or 'file'?
  // Let's handle both or update the component. Hero.tsx shows VoiceCircle sends 'file'.
  // audio/route.ts original code used form.get('audio').
  const file = form.get('file') || form.get('audio');
  const tsStr = form.get('timestamp')?.toString();
  const frameStr = form.get('frameId')?.toString() || form.get('frameNumber')?.toString();

  if (!(file instanceof File) || !tsStr || !frameStr) {
    return NextResponse.json({ error: 'Bad form data' }, { status: 400 });
  }

  const arrayBuf = await file.arrayBuffer();
  const buf = Buffer.from(arrayBuf);

  const fullMime = file.type || 'audio/webm';
  if (!fullMime.startsWith('audio/webm') && !fullMime.startsWith('audio/mp4')) {
    return NextResponse.json({ error: 'Unsupported mime' }, { status: 415 });
  }
  const mime = fullMime.startsWith('audio/webm') ? 'audio/webm' : ('audio/mp4' as const);
  if (buf.length > 5 * 1024 * 1024) {
    return NextResponse.json({ error: 'Frame too large' }, { status: 413 });
  }

  const checksum = crypto.createHash('sha256').update(buf).digest('hex');

  const frameNumber = Number(frameStr);
  const ts_ms = Number(tsStr);

  const key = `users/${userId}/audio/${mime === 'audio/webm' ? 'webm' : 'mp4'}/frame_${frameNumber}_${ts_ms}.${mime === 'audio/webm' ? 'webm' : 'mp4'}`;

  console.log('[audio] uploading to GCS', { userId, frameNumber, ts_ms, mime, bytes: buf.length, key });

  try {
    const bucket = storage.bucket(BUCKET_NAME);
    const gcsFile = bucket.file(key);
    await gcsFile.save(buf, {
      contentType: fullMime,
      metadata: {
        cacheControl: 'no-store',
      },
    });

    const insertedId = await insertAudioMeta({
      clerk_user_id: userId,
      frameNumber,
      ts_ms,
      mime,
      bytes: buf.length,
      s3Key: key, // Keeping s3Key field name for DB compatibility or rename later
      checksum,
      created_at: new Date(),
    });

    console.log('[audio] stored in GCS', {
      userId,
      mongoFrameId: insertedId.toHexString(),
      frameNumber,
      ts_ms,
      key: key,
    });

    return NextResponse.json({
      ok: true,
      frameId: insertedId.toHexString(),
      key: key,
    });
  } catch (error) {
    console.error('[audio] GCS upload error:', error);
    return NextResponse.json({ error: 'Upload failed' }, { status: 500 });
  }
}

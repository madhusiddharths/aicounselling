import { NextRequest, NextResponse } from 'next/server';
import { Storage } from '@google-cloud/storage';

export const runtime = 'nodejs';

const storage = new Storage();

export async function POST(req: NextRequest) {
  const BUCKET = process.env.GCS_BUCKET ?? '';
  const bucket = storage.bucket(BUCKET);
  if (!BUCKET) {
    return NextResponse.json({ error: 'GCS not configured' }, { status: 500 });
  }

  try {
    const form = await req.formData();
    // IMPORTANT: expected fields from VoiceCircle
    const file = form.get('file') as File | null;        // the audio chunk
    const userId = (form.get('userId') as string) || ''; // clerk user id
    const frameId = (form.get('frameId') as string) || '';
    const ts = (form.get('timestamp') as string) || `${Date.now()}`;

    if (!file || !userId) {
      return NextResponse.json({ error: 'Missing file or userId' }, { status: 400 });
    }

    const safeName = (file.name || 'chunk.webm').replace(/[^\w.\-]+/g, '_');
    const key = `${userId}/audio/frame_${frameId || ts}_${safeName}`;

    const body = Buffer.from(await file.arrayBuffer());
    const gcsFile = bucket.file(key);

    await gcsFile.save(body, {
      contentType: file.type || 'audio/webm',
    });

    return NextResponse.json({ success: true, key });
  } catch (error) {
    console.error('Upload failed:', error);
    return NextResponse.json({ error: 'Upload failed' }, { status: 500 });
  }
}

import { Storage } from '@google-cloud/storage';

// A single Storage client authenticated from the GCP_SA_JSON env var (the same
// service-account JSON the backend uses). On Vercel there's no metadata server
// or credentials file, so the default `new Storage()` (Application Default
// Credentials) can't authenticate — we pass the credentials explicitly.
// Locally, if GCP_SA_JSON is unset, fall back to ADC
// (GOOGLE_APPLICATION_CREDENTIALS) so existing dev setups keep working.
let cached: Storage | null = null;

export function getStorage(): Storage {
  if (cached) return cached;

  const raw = process.env.GCP_SA_JSON;
  if (raw) {
    const creds = JSON.parse(raw);
    cached = new Storage({
      projectId: creds.project_id,
      credentials: {
        client_email: creds.client_email,
        private_key: creds.private_key,
      },
    });
  } else {
    cached = new Storage();
  }
  return cached;
}

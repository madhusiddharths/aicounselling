// src/app/page.tsx
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import { auth, clerkClient } from '@clerk/nextjs/server';
import DebugUserConsole from './components/DebugUserConsole';
import { upsertUserFromClerk } from '@/db/users';

export default async function Page() {
  const { userId } = await auth();
  if (userId) {
    const c = await clerkClient();
    const u = await c.users.getUser(userId);

    // Sync user to DB
    await upsertUserFromClerk({
      clerk_user_id: u.id,
      email: u.primaryEmailAddress?.emailAddress ?? null,
      first_name: u.firstName ?? null,
      last_name: u.lastName ?? null,
      image_url: u.imageUrl ?? null,
    });

    // This prints into the **server** terminal
    console.log('[home] synced user:', u.id);
  }

  return (
    <div className="min-h-screen bg-sunset flex flex-col">
      <DebugUserConsole />
      <Navbar />
      <div>
        <Hero />
      </div>
    </div>
  );
}

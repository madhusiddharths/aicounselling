import { SignedIn, UserButton, SignedOut, SignInButton } from "@clerk/nextjs";


export default function Navbar() {
  return (
    <nav className="fixed top-6 left-1/2 -translate-x-1/2 z-50 glass-pill px-6 py-3 flex items-center justify-between gap-8 min-w-[320px] max-w-2xl w-[90%] duration-300">
      <div className="flex items-center gap-3">
        {/* Logo/Icon */}
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-400 to-blue-500 shadow-glow flex items-center justify-center">
          <span className="text-white font-bold text-lg">✦</span>
        </div>
        <span className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/70 tracking-wide">
          Serenity AI
        </span>
      </div>

      <div className="flex items-center gap-4">
        <SignedOut>
          <SignInButton mode="modal">
            <button className="text-sm font-medium text-white/80 hover:text-white transition-colors">
              Sign In
            </button>
          </SignInButton>
        </SignedOut>
        <SignedIn>
          <UserButton
            appearance={{
              elements: {
                avatarBox: "w-8 h-8 ring-2 ring-white/20 hover:ring-white/50 transition-all"
              }
            }}
            afterSignOutUrl="/"
          />
        </SignedIn>
      </div>
    </nav>
  );
}

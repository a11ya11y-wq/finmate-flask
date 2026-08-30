import { useState, useEffect } from "react";

export const OfflineIndicator = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  if (isOnline) return null;

  return (
    <div className="fixed bottom-20 sm:bottom-6 left-1/2 -translate-x-1/2 z-[100] flex items-center gap-3 rounded-full bg-rose-500/10 px-4 py-2.5 text-sm font-semibold text-rose-200 shadow-[0_10px_40px_rgba(0,0,0,0.5)] backdrop-blur-xl border border-rose-500/30 animate-in fade-in slide-in-from-bottom-5 duration-300">
      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-rose-500/20 text-rose-400">
        <i className="bi bi-wifi-off" />
      </div>
      <span>You are offline. Viewing cached data.</span>
    </div>
  );
};

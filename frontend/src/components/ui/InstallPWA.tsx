import { useState, useEffect } from "react";

export const InstallPWA = () => {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [isIOS, setIsIOS] = useState(false);
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    // Check if device is iOS
    const isIosDevice = /ipad|iphone|ipod/.test(navigator.userAgent.toLowerCase()) && !(window as any).MSStream;
    setIsIOS(isIosDevice);

    // Check if already installed
    const isStand = window.matchMedia('(display-mode: standalone)').matches || (window.navigator as any).standalone === true;
    setIsStandalone(isStand);

    // React race condition fix: get the event if it already fired before mount
    if ((window as any).deferredPWAInstallPrompt) {
      setDeferredPrompt((window as any).deferredPWAInstallPrompt);
    }

    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault(); // Stop default chrome banner
      setDeferredPrompt(e);
      (window as any).deferredPWAInstallPrompt = e;
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setDeferredPrompt(null);
    }
  };

  if (isStandalone) return null; // Already installed
  if (!deferredPrompt) return null; // Hide completely if not supported (e.g. iOS Safari)

  return (
    <button
      onClick={handleInstallClick}
      title="Install App"
      className="flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1.5 text-sm font-bold text-blue-400 transition-colors hover:bg-blue-500/20"
    >
      <i className="bi bi-download" />
      <span className="hidden sm:inline">Install App</span>
    </button>
  );
};

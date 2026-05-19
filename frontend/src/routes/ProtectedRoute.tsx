import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { accessToken, refreshSession } = useAuthStore();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const init = async () => {
      if (!accessToken) {
        await refreshSession();
      }
      setChecking(false);
    };

    void init();
  }, [accessToken, refreshSession]);

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-500">
        Checking session...
      </div>
    );
  }

  if (!useAuthStore.getState().accessToken) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;


import { Navigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { accessToken, isRestoring } = useAuthStore();

  if (isRestoring) {
    return (
      <div className="flex min-h-screen items-center justify-center text-slate-500">
        Checking session...
      </div>
    );
  }

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export default ProtectedRoute;


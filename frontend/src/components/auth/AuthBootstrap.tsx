import { useEffect, type ReactNode } from "react";
import { useAuthStore } from "../../store/authStore";

type AuthBootstrapProps = {
  children: ReactNode;
};

const AuthBootstrap = ({ children }: AuthBootstrapProps) => {
  const restoreSession = useAuthStore((state) => state.restoreSession);

  useEffect(() => {
    void restoreSession();
  }, [restoreSession]);

  return <>{children}</>;
};

export default AuthBootstrap;
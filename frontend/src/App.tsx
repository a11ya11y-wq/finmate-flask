import AppRoutes from "./routes/AppRoutes";
import { ToastProvider } from "./components/ui/toast";
import AuthBootstrap from "./components/auth/AuthBootstrap";
import { OfflineIndicator } from "./components/ui/OfflineIndicator";

const App = () => {
  return (
    <ToastProvider>
      <AuthBootstrap>
        <AppRoutes />
        <OfflineIndicator />
      </AuthBootstrap>
    </ToastProvider>
  );
};

export default App;


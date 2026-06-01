import AppRoutes from "./routes/AppRoutes";
import { ToastProvider } from "./components/ui/toast";
import AuthBootstrap from "./components/auth/AuthBootstrap";

const App = () => {
  return (
    <ToastProvider>
      <AuthBootstrap>
        <AppRoutes />
      </AuthBootstrap>
    </ToastProvider>
  );
};

export default App;


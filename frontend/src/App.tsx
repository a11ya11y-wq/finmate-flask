import AppRoutes from "./routes/AppRoutes";
import { ToastProvider } from "./components/ui/toast";

const App = () => {
  return (
    <ToastProvider>
      <AppRoutes />
    </ToastProvider>
  );
};

export default App;


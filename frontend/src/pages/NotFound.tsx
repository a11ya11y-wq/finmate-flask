import { Link } from "react-router-dom";
import { Button } from "../components/ui/button";

const NotFoundPage = () => {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#0a0e17] text-slate-100">
      <h1 className="text-3xl font-semibold">Page not found</h1>
      <p className="text-sm text-slate-400">The page you are looking for does not exist.</p>
      <Link to="/dashboard">
        <Button>Go to dashboard</Button>
      </Link>
    </div>
  );
};

export default NotFoundPage;


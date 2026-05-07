import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useToast } from "../components/ui/toast";
import { toErrorMessage } from "../api/error";

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, status } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await login(email, password, rememberMe);
      navigate("/dashboard");
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  return (
    <div className="auth-body relative flex min-h-screen items-center justify-center px-4">
      <div className="auth-background">
        <div className="auth-shape auth-shape-1" />
        <div className="auth-shape auth-shape-2" />
        <div className="auth-shape auth-shape-3" />
      </div>
      <Card className="auth-card w-full max-w-md">
        <CardHeader>
          <div className="flex flex-col items-center gap-3 text-center">
            <img src="/img/finmatelogo1.png" alt="FinMate" className="h-24 w-24" />
            <CardTitle className="auth-title">Welcome Back</CardTitle>
            <p className="auth-subtitle">Sign in to your account to continue</p>
          </div>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="text-sm font-medium text-slate-200">Email</label>
              <Input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="your.email@example.com"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-200">Password</label>
              <Input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter your password"
                required
              />
            </div>
            <label className="flex items-center gap-2 text-sm text-slate-400">
              <input
                type="checkbox"
                className="h-4 w-4 accent-blue-500"
                checked={rememberMe}
                onChange={(event) => setRememberMe(event.target.checked)}
              />
              Remember me
            </label>
            <Button type="submit" className="w-full" disabled={status === "loading"}>
              {status === "loading" ? "Signing in..." : "Sign in"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-slate-400">
            No account?{" "}
            <Link to="/register" className="text-blue-300">
              Create one
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default LoginPage;


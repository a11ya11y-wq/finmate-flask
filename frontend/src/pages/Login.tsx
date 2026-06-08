import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useToast } from "../components/ui/toast";
import { toErrorMessage } from "../api/error";
import { loginSchema } from "../validation/schemas";
import { validateForm } from "../validation/validate";

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, status } = useAuthStore();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const { toast } = useToast();

  const clearFieldError = (field: string) => {
    setErrors((prev) => {
      if (!prev[field]) {
        return prev;
      }
      const next = { ...prev };
      delete next[field];
      return next;
    });
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const validation = validateForm(loginSchema, { email, password });
    if (!validation.success) {
      setErrors(validation.fieldErrors ?? {});
      return;
    }
    try {
      setErrors({});
      await login(validation.data.email, validation.data.password, rememberMe);
      navigate("/dashboard");
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  const handleTryDemo = async () => {
    const demoEmail = "demo@test.com";
    const demoPass = "pass123123";
    setEmail(demoEmail);
    setPassword(demoPass);
    try {
      setErrors({});
      await login(demoEmail, demoPass, false);
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
          <form className="space-y-4" onSubmit={handleSubmit} noValidate>
            <div>
              <label className="text-sm font-medium text-slate-200">Email</label>
              <Input
                id="email-input"
                type="email"
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                  clearFieldError("email");
                }}
                placeholder="your.email@example.com"
                aria-invalid={!!errors.email}
                className={errors.email ? "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20" : undefined}
              />
              {errors.email && <p data-testid="email-error" className="mt-1 text-xs text-rose-400">{errors.email}</p>}
            </div>
            <div>
              <label className="text-sm font-medium text-slate-200">Password</label>
              <Input
                id="password-input"
                type="password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                  clearFieldError("password");
                }}
                placeholder="Enter your password"
                aria-invalid={!!errors.password}
                className={errors.password ? "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20" : undefined}
              />
              {errors.password && <p data-testid="password-error" className="mt-1 text-xs text-rose-400">{errors.password}</p>}
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
            <Button
              type="button"
              variant="tonal"
              className="w-full mt-2"
              onClick={handleTryDemo}
              disabled={status === "loading"}
            >
              {status === "loading" ? "Signing in..." : "Try Demo"}
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


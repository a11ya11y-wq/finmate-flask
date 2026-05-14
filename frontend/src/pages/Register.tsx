import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register as registerRequest } from "../api/auth";
import { toErrorMessage } from "../api/error";
import { useAuthStore } from "../store/authStore";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useToast } from "../components/ui/toast";
import { registerSchema } from "../validation/schemas";
import { validateForm } from "../validation/validate";

const RegisterPage = () => {
  const navigate = useNavigate();
  const { login, status } = useAuthStore();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirm_password: ""
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const { toast } = useToast();

  const handleChange = (field: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
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
    const validation = validateForm(registerSchema, form);
    if (!validation.success) {
      setErrors(validation.fieldErrors ?? {});
      return;
    }
    try {
      setErrors({});
      await registerRequest(validation.data);
      await login(validation.data.email, validation.data.password, false);
      navigate("/dashboard");
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  return (
    <div className="auth-body relative flex min-h-screen items-center justify-center px-4 py-8">
      <div className="auth-background">
        <div className="auth-shape auth-shape-1" />
        <div className="auth-shape auth-shape-2" />
        <div className="auth-shape auth-shape-3" />
      </div>
      <Card className="auth-card w-full max-w-md">
        <CardHeader>
          <div className="flex flex-col items-center gap-3 text-center">
            <img src="/img/finmatelogo1.png" alt="FinMate" className="h-24 w-24" />
            <CardTitle className="auth-title">Create Account</CardTitle>
            <p className="auth-subtitle">Join FinMate and start managing your finances</p>
          </div>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit} noValidate>
            <div>
              <label htmlFor="Username" className="text-sm font-medium text-slate-200">Username</label>
              <Input
                id="Username"
                value={form.username}
                onChange={handleChange("username")}
                aria-invalid={!!errors.username}
                className={errors.username ? "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20" : undefined}
              />
              {errors.username && <p data-testid="username-error" className="mt-1 text-xs text-rose-400">{errors.username}</p>}
            </div>
            <div>
              <label htmlFor="Email" className="text-sm font-medium text-slate-200">Email</label>
              <Input
                id="Email"
                type="email"
                value={form.email}
                onChange={handleChange("email")}
                aria-invalid={!!errors.email}
                className={errors.email ? "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20" : undefined}
              />
              {errors.email && <p data-testid="email-error" className="mt-1 text-xs text-rose-400">{errors.email}</p>}
            </div>
            <div>
              <label htmlFor="Password" className="text-sm font-medium text-slate-200">Password</label>
              <Input
                id="Password"
                type="password"
                value={form.password}
                onChange={handleChange("password")}
                aria-invalid={!!errors.password}
                className={errors.password ? "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20" : undefined}
              />
              {errors.password && <p data-testid="password-error" className="mt-1 text-xs text-rose-400">{errors.password}</p>}
            </div>
            <div>
              <label htmlFor="ConfirmPassword" className="text-sm font-medium text-slate-200">Confirm password</label>
              <Input
                id="ConfirmPassword"
                type="password"
                value={form.confirm_password}
                onChange={handleChange("confirm_password")}
                aria-invalid={!!errors.confirm_password}
                className={errors.confirm_password ? "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20" : undefined}
              />
              {errors.confirm_password && <p data-testid="confirm-password-error" className="mt-1 text-xs text-rose-400">{errors.confirm_password}</p>}
            </div>
            <Button type="submit" className="w-full" disabled={status === "loading"}>
              {status === "loading" ? "Creating..." : "Create account"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-slate-400">
            Already have an account? <Link to="/login" className="text-blue-300">Sign in</Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default RegisterPage;

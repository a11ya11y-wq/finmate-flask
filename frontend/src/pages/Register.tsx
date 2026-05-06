import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register as registerRequest } from "../api/auth";
import { toErrorMessage } from "../api/error";
import { useAuthStore } from "../store/authStore";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { useToast } from "../components/ui/toast";

const RegisterPage = () => {
  const navigate = useNavigate();
  const { login, status } = useAuthStore();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    confirm_password: ""
  });
  const { toast } = useToast();

  const handleChange = (field: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await registerRequest(form);
      await login(form.email, form.password, false);
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
            <img src="/img/finmatelogo1.png" alt="FinMate" className="h-16 w-16" />
            <CardTitle className="auth-title">Create Account</CardTitle>
            <p className="auth-subtitle">Join FinMate and start managing your finances</p>
          </div>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="text-sm font-medium text-slate-200">Username</label>
              <Input value={form.username} onChange={handleChange("username")} required />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-200">Email</label>
              <Input type="email" value={form.email} onChange={handleChange("email")} required />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-200">Password</label>
              <Input
                type="password"
                value={form.password}
                onChange={handleChange("password")}
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-200">Confirm password</label>
              <Input
                type="password"
                value={form.confirm_password}
                onChange={handleChange("confirm_password")}
                required
              />
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

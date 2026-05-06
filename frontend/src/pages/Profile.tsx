import { useEffect, useState } from "react";
import AppShell from "../components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import Modal from "../components/ui/modal";
import { changePassword, removeMonobankToken, setMonobankToken, updateProfile, deleteProfile } from "../api/profile";
import { createCategory, deleteCategory, getCategories, updateCategory } from "../api/categories";
import type { Category } from "../api/types";
import { toErrorMessage } from "../api/error";
import { useAuthStore } from "../store/authStore";

const selectStyles =
  "w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 focus:border-blue-400/60 focus:outline-none focus:ring-2 focus:ring-blue-500/20";

const iconOptions = [
  "bi-bag-fill",
  "bi-cart-fill",
  "bi-cup-hot-fill",
  "bi-basket2-fill",
  "bi-house-door-fill",
  "bi-lightning-fill",
  "bi-wifi",
  "bi-car-front-fill",
  "bi-bus-front-fill",
  "bi-fuel-pump-fill",
  "bi-controller",
  "bi-film",
  "bi-heart-pulse-fill",
  "bi-mortarboard-fill",
  "bi-piggy-bank-fill",
  "bi-wallet-fill",
  "bi-gift-fill",
  "bi-airplane-fill",
  "bi-tag-fill",
  "bi-question-circle-fill"
];

const ProfilePage = () => {
  const { user, setUser, logout } = useAuthStore();
  const [profileForm, setProfileForm] = useState({
    username: user?.username ?? "",
    currency: user?.currency ?? "USD",
    avatar: user?.avatar ?? "avatars/default/default.svg"
  });
  const [profileDraft, setProfileDraft] = useState(profileForm);
  const [passwordForm, setPasswordForm] = useState({
    old_password: "",
    new_password: "",
    confirm_password: ""
  });
  const [monoToken, setMonoToken] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isPasswordOpen, setIsPasswordOpen] = useState(false);
  const [isMonobankOpen, setIsMonobankOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryForm, setCategoryForm] = useState({ name: "", mcc_code: "", icon: "bi-tag-fill" });
  const [editCategory, setEditCategory] = useState<Category | null>(null);
  const [isEditCategoryOpen, setIsEditCategoryOpen] = useState(false);
  const [deleteCategoryId, setDeleteCategoryId] = useState<number | null>(null);
  const [isDeleteCategoryOpen, setIsDeleteCategoryOpen] = useState(false);

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await getCategories();
        setCategories(response.data);
      } catch (err) {
        setError(toErrorMessage(err));
      }
    };

    void loadCategories();
  }, []);

  const handleProfileSubmit = async () => {
    setError(null);
    setMessage(null);
    try {
      const updated = await updateProfile(profileDraft);
      setUser(updated);
      setProfileForm(updated);
      setMessage("Profile updated");
      setIsProfileOpen(false);
    } catch (err) {
      setError(toErrorMessage(err));
    }
  };

  const handlePasswordSubmit = async () => {
    setError(null);
    setMessage(null);
    try {
      const response = await changePassword(passwordForm);
      setMessage(response.message);
      setPasswordForm({ old_password: "", new_password: "", confirm_password: "" });
      setIsPasswordOpen(false);
    } catch (err) {
      setError(toErrorMessage(err));
    }
  };

  const handleMonobankSubmit = async () => {
    setError(null);
    setMessage(null);
    try {
      const updated = await setMonobankToken(monoToken);
      setUser(updated);
      setMessage("Monobank token saved");
      setMonoToken("");
      setIsMonobankOpen(false);
    } catch (err) {
      setError(toErrorMessage(err));
    }
  };

  const handleRemoveToken = async () => {
    setError(null);
    setMessage(null);
    try {
      await removeMonobankToken();
      if (user) {
        setUser({ ...user, monobank_token_is_set: false });
      }
      setMessage("Monobank token removed");
    } catch (err) {
      setError(toErrorMessage(err));
    }
  };

  const handleAddCategory = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      const created = await createCategory(categoryForm);
      setCategories((prev) => [created, ...prev]);
      setCategoryForm({ name: "", mcc_code: "", icon: "bi-tag-fill" });
    } catch (err) {
      setError(toErrorMessage(err));
    }
  };

  const handleUpdateCategory = async () => {
    if (!editCategory) {
      return;
    }
    setError(null);
    try {
      const updated = await updateCategory(editCategory.id, {
        name: editCategory.name,
        mcc_code: editCategory.mcc_code ?? "",
        icon: editCategory.icon
      });
      setCategories((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      setIsEditCategoryOpen(false);
      setEditCategory(null);
    } catch (err) {
      setError(toErrorMessage(err));
    }
  };

  const handleDeleteCategory = async () => {
    if (!deleteCategoryId) {
      return;
    }
    setError(null);
    try {
      await deleteCategory(deleteCategoryId);
      setCategories((prev) => prev.filter((item) => item.id !== deleteCategoryId));
      setIsDeleteCategoryOpen(false);
      setDeleteCategoryId(null);
    } catch (err) {
      setError(toErrorMessage(err));
    }
  };

  const handleDeleteAccount = async () => {
    setError(null);
    try {
      await deleteProfile();
      await logout();
    } catch (err) {
      setError(toErrorMessage(err));
    }
  };

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/15 text-blue-300">
            <i className="bi bi-person-circle text-xl" />
          </span>
          <div>
            <h1 className="text-3xl font-semibold text-slate-100">Profile</h1>
            <p className="text-sm text-slate-400">Manage your account settings</p>
          </div>
        </div>

        {(error || message) && (
          <div className={`rounded-xl border px-4 py-3 text-sm ${error ? "border-red-500/40 bg-red-500/10 text-red-300" : "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"}`}>
            {error ?? message}
          </div>
        )}

        <Card className="surface-card">
          <CardContent>
            <div className="flex flex-col gap-6 md:flex-row md:items-center">
              <div className="relative">
                <img
                  src={`/${profileForm.avatar}`}
                  alt="Avatar"
                  className="h-24 w-24 rounded-2xl border border-blue-500/30"
                />
                <span
                  className={`absolute -bottom-2 -right-2 flex h-9 w-9 items-center justify-center rounded-full border border-[#0a0e17] ${
                    user?.monobank_token_is_set ? "bg-emerald-500 text-white" : "bg-slate-700 text-slate-200"
                  }`}
                >
                  <i className="bi bi-credit-card" />
                </span>
              </div>
              <div className="flex-1">
                <h2 className="text-2xl font-semibold text-slate-100">{user?.username ?? "User"}</h2>
                <p className="text-sm text-slate-400">{user?.email ?? ""}</p>
                <div className="mt-3 flex flex-wrap gap-4 text-sm text-slate-400">
                  <span>
                    Currency: <strong className="text-slate-100">{user?.currency ?? "USD"}</strong>
                  </span>
                  <span>{user?.monobank_token_is_set ? "Monobank connected" : "Monobank not connected"}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid gap-4 md:grid-cols-3">
          <button
            type="button"
            className="surface-card flex items-center gap-4 rounded-2xl border border-white/10 p-5 text-left transition hover:border-blue-500/30"
            onClick={() => {
              setProfileDraft(profileForm);
              setIsProfileOpen(true);
            }}
          >
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/20 text-blue-300">
              <i className="bi bi-person-circle" />
            </span>
            <div>
              <p className="text-base font-semibold text-slate-100">Edit Profile</p>
              <p className="text-sm text-slate-400">Update avatar, name & currency</p>
            </div>
          </button>
          <button
            type="button"
            className="surface-card flex items-center gap-4 rounded-2xl border border-white/10 p-5 text-left transition hover:border-purple-500/30"
            onClick={() => setIsPasswordOpen(true)}
          >
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-purple-500/20 text-purple-300">
              <i className="bi bi-shield-lock" />
            </span>
            <div>
              <p className="text-base font-semibold text-slate-100">Security</p>
              <p className="text-sm text-slate-400">Change your password</p>
            </div>
          </button>
          <button
            type="button"
            className="surface-card flex items-center gap-4 rounded-2xl border border-white/10 p-5 text-left transition hover:border-emerald-500/30"
            onClick={() => setIsMonobankOpen(true)}
          >
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/20 text-emerald-300">
              <i className="bi bi-bank2" />
            </span>
            <div>
              <p className="text-base font-semibold text-slate-100">Monobank</p>
              <p className="text-sm text-slate-400">Connect your bank account</p>
            </div>
          </button>
        </div>

        <Card className="surface-card">
          <CardHeader>
            <CardTitle>Manage Categories</CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={handleAddCategory}>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium text-slate-200">Name</label>
                  <Input
                    value={categoryForm.name}
                    onChange={(event) => setCategoryForm((prev) => ({ ...prev, name: event.target.value }))}
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-200">MCC codes</label>
                  <Input
                    value={categoryForm.mcc_code}
                    onChange={(event) => setCategoryForm((prev) => ({ ...prev, mcc_code: event.target.value }))}
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-200">Icon</label>
                <div className="mt-2 grid grid-cols-5 gap-2">
                  {iconOptions.map((icon) => (
                    <button
                      type="button"
                      key={icon}
                      className={
                        categoryForm.icon === icon
                          ? "flex h-10 w-10 items-center justify-center rounded-lg border border-blue-500/50 bg-blue-500/20 text-blue-200"
                          : "flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-slate-400 hover:border-blue-500/40"
                      }
                      onClick={() => setCategoryForm((prev) => ({ ...prev, icon }))}
                    >
                      <i className={`bi ${icon}`} />
                    </button>
                  ))}
                </div>
              </div>
              <Button type="submit">Add category</Button>
            </form>

            <div className="mt-6 space-y-3">
              {categories.length === 0 && (
                <p className="text-sm text-slate-400">No categories yet. Add your first category above.</p>
              )}
              {categories.map((category) => (
                <div key={category.id} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 px-4 py-3">
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-lg border border-blue-500/30 bg-blue-500/10 text-blue-200">
                      <i className={`bi ${category.icon}`} />
                    </span>
                    <div>
                      <p className="text-sm font-semibold text-slate-100">{category.name}</p>
                      <p className="text-xs text-slate-400">{category.mcc_code || "No MCC"}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      onClick={() => {
                        setEditCategory(category);
                        setIsEditCategoryOpen(true);
                      }}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      className="border-red-500/40 text-red-300 hover:bg-red-500/10"
                      onClick={() => {
                        setDeleteCategoryId(category.id);
                        setIsDeleteCategoryOpen(true);
                      }}
                    >
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="surface-card border border-red-500/30">
          <CardContent>
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="text-lg font-semibold text-red-300">Danger Zone</h3>
                <p className="text-sm text-slate-400">
                  Permanently delete your account and all associated data.
                </p>
              </div>
              <Button variant="danger" onClick={() => setIsDeleteOpen(true)}>
                Delete account
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      <Modal
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
        title="Edit Profile"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsProfileOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleProfileSubmit}>Save</Button>
          </div>
        }
      >
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="text-sm font-medium text-slate-200">Username</label>
            <Input
              value={profileDraft.username}
              onChange={(event) => setProfileDraft((prev) => ({ ...prev, username: event.target.value }))}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-200">Currency</label>
            <select
              className={selectStyles}
              value={profileDraft.currency}
              onChange={(event) => setProfileDraft((prev) => ({ ...prev, currency: event.target.value }))}
            >
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="UAH">UAH</option>
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="text-sm font-medium text-slate-200">Avatar</label>
            <select
              className={selectStyles}
              value={profileDraft.avatar}
              onChange={(event) => setProfileDraft((prev) => ({ ...prev, avatar: event.target.value }))}
            >
              {Array.from({ length: 10 }, (_, index) => {
                const name = index === 0 ? "default" : String(index);
                const path = `avatars/default/${name}.svg`;
                return (
                  <option key={path} value={path}>
                    {path}
                  </option>
                );
              })}
            </select>
          </div>
        </div>
      </Modal>

      <Modal
        isOpen={isPasswordOpen}
        onClose={() => setIsPasswordOpen(false)}
        title="Security"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsPasswordOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handlePasswordSubmit}>Update</Button>
          </div>
        }
      >
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <label className="text-sm font-medium text-slate-200">Current password</label>
            <Input
              type="password"
              autoComplete="current-password"
              value={passwordForm.old_password}
              onChange={(event) => setPasswordForm((prev) => ({ ...prev, old_password: event.target.value }))}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-200">New password</label>
            <Input
              type="password"
              autoComplete="new-password"
              value={passwordForm.new_password}
              onChange={(event) => setPasswordForm((prev) => ({ ...prev, new_password: event.target.value }))}
            />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-200">Confirm password</label>
            <Input
              type="password"
              autoComplete="new-password"
              value={passwordForm.confirm_password}
              onChange={(event) => setPasswordForm((prev) => ({ ...prev, confirm_password: event.target.value }))}
            />
          </div>
        </div>
      </Modal>

      <Modal
        isOpen={isMonobankOpen}
        onClose={() => setIsMonobankOpen(false)}
        title="Monobank Integration"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsMonobankOpen(false)}>
              Close
            </Button>
            <Button onClick={handleMonobankSubmit}>Save</Button>
          </div>
        }
      >
        <div className="space-y-4">
          <div className="rounded-xl border border-blue-500/30 bg-blue-500/10 px-4 py-3 text-sm text-slate-300">
            Get your API token from the Monobank app: api.monobank.ua
          </div>
          <div>
            <label className="text-sm font-medium text-slate-200">API Token</label>
            <Input value={monoToken} onChange={(event) => setMonoToken(event.target.value)} />
          </div>
          {user?.monobank_token_is_set && (
            <Button variant="outline" className="border-red-500/40 text-red-300 hover:bg-red-500/10" onClick={handleRemoveToken}>
              Remove token
            </Button>
          )}
        </div>
      </Modal>

      <Modal
        isOpen={isEditCategoryOpen}
        onClose={() => setIsEditCategoryOpen(false)}
        title="Edit Category"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsEditCategoryOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateCategory}>Save</Button>
          </div>
        }
      >
        {editCategory && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-200">Name</label>
              <Input
                value={editCategory.name}
                onChange={(event) =>
                  setEditCategory((prev) => (prev ? { ...prev, name: event.target.value } : prev))
                }
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-200">MCC codes</label>
              <Input
                value={editCategory.mcc_code ?? ""}
                onChange={(event) =>
                  setEditCategory((prev) => (prev ? { ...prev, mcc_code: event.target.value } : prev))
                }
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-200">Icon</label>
              <div className="mt-2 grid grid-cols-5 gap-2">
                {iconOptions.map((icon) => (
                  <button
                    type="button"
                    key={icon}
                    className={
                      editCategory.icon === icon
                        ? "flex h-10 w-10 items-center justify-center rounded-lg border border-blue-500/50 bg-blue-500/20 text-blue-200"
                        : "flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-slate-400 hover:border-blue-500/40"
                    }
                    onClick={() =>
                      setEditCategory((prev) => (prev ? { ...prev, icon } : prev))
                    }
                  >
                    <i className={`bi ${icon}`} />
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>

      <Modal
        isOpen={isDeleteCategoryOpen}
        onClose={() => setIsDeleteCategoryOpen(false)}
        title="Delete Category"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsDeleteCategoryOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDeleteCategory}>
              Delete
            </Button>
          </div>
        }
      >
        <p className="text-sm text-slate-300">Are you sure you want to delete this category?</p>
      </Modal>

      <Modal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        title="Delete account"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setIsDeleteOpen(false)}>
              Cancel
            </Button>
            <Button variant="danger" onClick={handleDeleteAccount}>
              Delete
            </Button>
          </div>
        }
      >
        <p className="text-sm text-slate-300">
          This action cannot be undone. Your account and all associated data will be removed.
        </p>
      </Modal>
    </AppShell>
  );
};

export default ProfilePage;


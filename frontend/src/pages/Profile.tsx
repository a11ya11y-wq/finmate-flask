import { useEffect, useRef, useState } from "react";
import AppShell from "../components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import Modal from "../components/ui/modal";
import { FormModal } from "../components/ui/FormModal";
import { ConfirmDeleteModal } from "../components/ui/ConfirmDeleteModal";
import { useToast } from "../components/ui/toast";
import { changePassword, removeMonobankToken, setMonobankToken, updateProfile, deleteProfile } from "../api/profile";
import { createCategory, deleteCategory, getCategories, updateCategory } from "../api/categories";
import type { Category } from "../api/types";
import { toErrorMessage } from "../api/error";
import { useAuthStore } from "../store/authStore";
import { cn } from "../lib/utils";
import {
  categorySchema,
  monobankTokenSchema,
  passwordChangeSchema,
  profileSchema
} from "../validation/schemas";
import { validateForm } from "../validation/validate";

export const ProfileFormFields = ({ draft, setDraft, errors, onFieldChange }: any) => {
  const avatars = Array.from({ length: 10 }, (_, i) =>
    `avatars/default/${i === 0 ? "default" : i}.svg`
  );

  return (
    <div data-testid="edit-profile-form" className="flex flex-col gap-6">
      {/* Поля Username та Currency залишаємо без змін */}
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label htmlFor="username" className="mb-1.5 block text-sm font-medium text-slate-200">Username</label>
          <Input
            id="username"
            value={draft.username}
            onChange={(e) => {
              setDraft((prev: any) => ({ ...prev, username: e.target.value }));
              onFieldChange?.("username");
            }}
            aria-invalid={!!errors?.username}
            className={errors?.username ? "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20" : undefined}
          />
          {errors?.username && <p data-testid="username-error" className="mt-1 text-xs text-rose-400">{errors.username}</p>}
        </div>
        <div>
          <label htmlFor="currency" className="mb-1.5 block text-sm font-medium text-slate-200">Preferred Currency</label>
          <select
            id="currency"
            className={cn(
              selectStyles,
              errors?.currency && "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20"
            )}
            value={draft.currency}
            onChange={(e) => {
              setDraft((prev: any) => ({ ...prev, currency: e.target.value }));
              onFieldChange?.("currency");
            }}
            aria-invalid={!!errors?.currency}
          >
            <option value="USD">USD - US Dollar</option>
            <option value="EUR">EUR - Euro</option>
            <option value="UAH">UAH - Ukrainian Hryvnia</option>
          </select>
          {errors?.currency && <p data-testid="currency-error" className="mt-1 text-xs text-rose-400">{errors.currency}</p>}
        </div>
      </div>

      {/* НОВИЙ ВІЗУАЛЬНИЙ ВИБІР АВАТАРА */}
      <div>
        <label className="mb-3 block text-sm font-bold text-slate-200">Choose Avatar</label>
        <div className="grid h-48 grid-cols-5 gap-3 overflow-y-auto rounded-xl border border-white/5 bg-black/20 p-4 custom-scrollbar">
          {avatars.map((path) => {
            const isSelected = draft.avatar === path;
            return (
              <button
                key={path}
                type="button"
                onClick={() => {
                  setDraft((prev: any) => ({ ...prev, avatar: path }));
                  onFieldChange?.("avatar");
                }}
                className={`group relative flex aspect-square items-center justify-center rounded-xl border-2 transition-all ${
                  isSelected 
                    ? "border-blue-500 bg-blue-500/10 shadow-[0_0_15px_rgba(59,130,246,0.2)]" 
                    : "border-white/5 bg-white/5 hover:border-white/20"
                }`}
              >
                <img 
                  src={`/${path}`} 
                  alt="Avatar option" 
                  className={`h-full w-full p-1 transition-transform duration-300 ${isSelected ? "scale-90" : "group-hover:scale-105"}`} 
                />
                
                {/* Індикатор вибору (маленька синя точка) */}
                {isSelected && (
                  <div className="absolute -right-1.5 -top-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-blue-500 shadow-lg">
                    <div className="h-2 w-2 rounded-full bg-white" />
                  </div>
                )}
              </button>
            );
          })}
        </div>
        {errors?.avatar && <p data-testid="avatar-error" className="mt-2 text-xs text-rose-400">{errors.avatar}</p>}
      </div>
    </div>
  );
};

// Поля для категорій
export const CategoryFormFields = ({ form, setForm, icons, errors, onFieldChange }: any) => (
  <div data-testid="category-form" className="flex flex-col gap-4">
    <div className="grid gap-4 md:grid-cols-2">
      <div>
        <label htmlFor="category-name" className="mb-1.5 block text-sm font-medium text-slate-200">Name</label>
        <Input
          id="category-name"
          placeholder="e.g. Food"
          value={form.name}
          onChange={(e) => {
            setForm((prev: any) => ({ ...prev, name: e.target.value }));
            onFieldChange?.("name");
          }}
          aria-invalid={!!errors?.name}
          className={errors?.name ? "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20" : undefined}
        />
        {errors?.name && <p data-testid="name-error" className="mt-1 text-xs text-rose-400">{errors.name}</p>}
      </div>
      <div>
        <label htmlFor="category-mcc-code" className="mb-1.5 block text-sm font-medium text-slate-200">MCC Code</label>
        <Input
          id="category-mcc-code"
          placeholder="e.g. 5411"
          value={form.mcc_code}
          onChange={(e) => {
            setForm((prev: any) => ({ ...prev, mcc_code: e.target.value }));
            onFieldChange?.("mcc_code");
          }}
          aria-invalid={!!errors?.mcc_code}
          className={errors?.mcc_code ? "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20" : undefined}
        />
        {errors?.mcc_code && <p data-testid="mcc-code-error" className="mt-1 text-xs text-rose-400">{errors.mcc_code}</p>}
      </div>
    </div>
    <div>
      <label className="mb-1.5 block text-sm font-medium text-slate-200">Choose Icon</label>
      <div className="grid grid-cols-5 gap-2">
        {icons.map((icon: string) => (
          <button
            key={icon}
            type="button"
            className={`flex h-11 items-center justify-center rounded-xl border transition-all ${
              form.icon === icon 
                ? "border-blue-500/50 bg-blue-500/20 text-blue-200 shadow-[0_0_15px_rgba(59,130,246,0.1)]" 
                : "border-white/10 bg-white/5 text-slate-400 hover:border-white/20"
            }`}
            onClick={() => {
              setForm((prev: any) => ({ ...prev, icon }));
              onFieldChange?.("icon");
            }}
          >
            <i className={`bi ${icon} text-lg`} />
          </button>
        ))}
      </div>
      {errors?.icon && <p data-testid="icon-error" className="mt-1 text-xs text-rose-400">{errors.icon}</p>}
    </div>
  </div>
);

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
  const [isConfirmMonoDisconnectOpen, setIsConfirmMonoDisconnectOpen] = useState(false);
  const [isAddCategoryOpen, setIsAddCategoryOpen] = useState(false);
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
  const [profileErrors, setProfileErrors] = useState<Record<string, string>>({});
  const [passwordErrors, setPasswordErrors] = useState<Record<string, string>>({});
  const [monoErrors, setMonoErrors] = useState<Record<string, string>>({});
  const [categoryErrors, setCategoryErrors] = useState<Record<string, string>>({});
  const [monoToken, setMonoToken] = useState("");
  const { toast } = useToast();
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isPasswordOpen, setIsPasswordOpen] = useState(false);
  const [isMonobankOpen, setIsMonobankOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryForm, setCategoryForm] = useState({ name: "", mcc_code: "", icon: "bi-tag-fill" });
  const [editCategory, setEditCategory] = useState<Category | null>(null);
  const [editCategorySnapshot, setEditCategorySnapshot] = useState<Category | null>(null);
  const [isEditCategoryOpen, setIsEditCategoryOpen] = useState(false);
  const [deleteCategoryId, setDeleteCategoryId] = useState<number | null>(null);
  const [isDeleteCategoryOpen, setIsDeleteCategoryOpen] = useState(false);

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const response = await getCategories();
        setCategories(response.data);
      } catch (err) {
        toast({ variant: "error", message: toErrorMessage(err) });
      }
    };

    void loadCategories();
  }, [toast]);

  const handleProfileSubmit = async () => {
    const validation = validateForm(profileSchema, profileDraft);
    if (!validation.success) {
      setProfileErrors(validation.fieldErrors ?? {});
      return;
    }
    try {
      setProfileErrors({});
      const profileComparable = {
        username: validation.data.username.trim(),
        currency: validation.data.currency,
        avatar: validation.data.avatar
      };
      const currentComparable = {
        username: profileForm.username.trim(),
        currency: profileForm.currency,
        avatar: profileForm.avatar
      };
      const isDirty = Object.keys(currentComparable).some((key) => {
        return currentComparable[key as keyof typeof currentComparable] !== profileComparable[key as keyof typeof profileComparable];
      });
      if (!isDirty) {
        setIsProfileOpen(false);
        return;
      }
      const updated = await updateProfile(validation.data);
      setUser(updated);
      setProfileForm(updated);
      toast({ variant: "success", message: "Profile updated" });
      setIsProfileOpen(false);
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  const handlePasswordSubmit = async () => {
    const validation = validateForm(passwordChangeSchema, passwordForm);
    if (!validation.success) {
      setPasswordErrors(validation.fieldErrors ?? {});
      return;
    }
    try {
      setPasswordErrors({});
      const response = await changePassword(validation.data);
      toast({ variant: "success", message: response.message });
      setPasswordForm({ old_password: "", new_password: "", confirm_password: "" });
      setIsPasswordOpen(false);
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  const handleMonobankSubmit = async () => {
    const validation = validateForm(monobankTokenSchema, { token: monoToken });
    if (!validation.success) {
      setMonoErrors(validation.fieldErrors ?? {});
      return;
    }
    try {
      setMonoErrors({});
      const updated = await setMonobankToken(validation.data.token);
      setUser(updated);
      toast({ variant: "success", message: "Monobank token saved" });
      setMonoToken("");
      setIsMonobankOpen(false);
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  const handleRemoveToken = async () => {
  try {
    await removeMonobankToken();
    if (user) {
      setUser({ ...user, monobank_token_is_set: false });
    }
    toast({ variant: "success", message: "Monobank token removed" });
    
    // Закриваємо обидві модалки
    setIsConfirmMonoDisconnectOpen(false);
    setIsMonobankOpen(false);
  } catch (err) {
    toast({ variant: "error", message: toErrorMessage(err) });
  }
};

 const handleAddCategory = async () => {
  const validation = validateForm(categorySchema, categoryForm);
  if (!validation.success) {
    setCategoryErrors(validation.fieldErrors ?? {});
    return;
  }
  try {
    setCategoryErrors({});
    const created = await createCategory({
      ...categoryForm,
      name: validation.data.name,
      mcc_code: validation.data.mcc_code,
      icon: validation.data.icon ?? categoryForm.icon
    });
    setCategories((prev) => [created, ...prev]);
    setCategoryForm({ name: "", mcc_code: "", icon: "bi-tag-fill" });
    setIsAddCategoryOpen(false); // ДОДАНО: закриваємо модалку
    toast({ variant: "success", message: "Category added!" });
  } catch (err) {
    toast({ variant: "error", message: toErrorMessage(err) });
  }
};

  const handleEditCategory = async () => {
    if (!editCategory) {
      return;
    }
    const validation = validateForm(categorySchema, editCategory);
    if (!validation.success) {
      setCategoryErrors(validation.fieldErrors ?? {});
      return;
    }
    try {
      setCategoryErrors({});
      if (editCategorySnapshot) {
        const currentComparable = {
          name: validation.data.name.trim(),
          mcc_code: validation.data.mcc_code ?? "",
          icon: validation.data.icon ?? editCategory.icon
        };
        const snapshotComparable = {
          name: editCategorySnapshot.name.trim(),
          mcc_code: editCategorySnapshot.mcc_code ?? "",
          icon: editCategorySnapshot.icon
        };
        const isDirty = Object.keys(snapshotComparable).some((key) => {
          return snapshotComparable[key as keyof typeof snapshotComparable] !== currentComparable[key as keyof typeof currentComparable];
        });
        if (!isDirty) {
          setIsEditCategoryOpen(false);
          setEditCategory(null);
          return;
        }
      }
      const updated = await updateCategory(editCategory.id, {
        name: validation.data.name,
        mcc_code: validation.data.mcc_code ?? "",
        icon: validation.data.icon ?? editCategory.icon
      });
      setCategories((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      setIsEditCategoryOpen(false);
      setEditCategory(null);
      setEditCategorySnapshot(null);
      
      // ДОДАНО: Повідомлення про успішне редагування
      toast({ variant: "success", message: "Category updated successfully!" });
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  const handleDeleteCategory = async () => {
    if (!deleteCategoryId) {
      return;
    }
    try {
      await deleteCategory(deleteCategoryId);
      setCategories((prev) => prev.filter((item) => item.id !== deleteCategoryId));
      setIsDeleteCategoryOpen(false);
      setDeleteCategoryId(null);
      
      // ДОДАНО: Повідомлення про успішне видалення
      toast({ variant: "success", message: "Category deleted successfully!" });
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await deleteProfile();
      await logout();
    } catch (err) {
      toast({ variant: "error", message: toErrorMessage(err) });
    }
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-5xl space-y-8">
        {/* HEADER */}
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-500/10 text-blue-400 shadow-inner">
            <i className="bi bi-person-gear text-2xl" />
          </div>
          <div>
            <h1 className="text-3xl font-black tracking-tight text-white">Profile</h1>
            <p className="text-slate-400 font-medium">Manage your personal experience and security</p>
          </div>
        </div>

        {/* USER PROFILE INFO */}
        <Card className="surface-card border-blue-500/20 bg-gradient-to-r from-[#0b0f17] to-[#121826]">
          <CardContent className="py-8">
            <div data-testid="profile-user-info-container" className="flex flex-col gap-8 md:flex-row md:items-center">
              <div className="relative group">
                <div className="absolute -inset-1 rounded-3xl bg-blue-500/20 opacity-0 blur transition duration-500 group-hover:opacity-100"></div>
                <img
                  src={`/${profileForm.avatar}`}
                  alt="Avatar"
                  className="relative h-28 w-28 rounded-2xl border-2 border-white/10 object-cover shadow-2xl"
                />
                <div className={`absolute -bottom-2 -right-2 flex h-10 w-10 items-center justify-center rounded-full border-4 border-[#0b0f17] shadow-xl ${
                    user?.monobank_token_is_set ? "bg-emerald-500 text-white" : "bg-slate-700 text-slate-300"
                  }`}>
                  <i className={`bi ${user?.monobank_token_is_set ? "bi-check-circle-fill" : "bi-bank"}`} />
                </div>
              </div>
              <div className="flex-1 space-y-2">
                <h2 data-testid="profile-username" className="text-3xl font-bold text-white">{user?.username}</h2>
                <div className="flex flex-wrap gap-4 text-slate-400">
                  <span data-testid="profile-email" className="flex items-center gap-2 rounded-lg bg-white/5 px-3 py-1 text-sm border border-white/5">
                    <i className="bi bi-envelope text-blue-400" /> {user?.email}
                  </span>
                  <span data-testid="profile-currency" className="flex items-center gap-2 rounded-lg bg-white/5 px-3 py-1 text-sm border border-white/5">
                    <i className="bi bi-currency-exchange text-emerald-400" /> {user?.currency}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* QUICK ACTIONS GRID */}
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            { title: "Edit Profile", desc: "Identity & Currency", icon: "bi-person-vcard", color: "blue", onClick: () => { setProfileDraft(profileForm); setIsProfileOpen(true); } },
            { title: "Security", desc: "Password & Protection", icon: "bi-shield-lock", color: "purple", onClick: () => setIsPasswordOpen(true) },
            { title: "Monobank", desc: "Bank Integration", icon: "bi-wallet2", color: "emerald", onClick: () => setIsMonobankOpen(true) }
          ].map((item) => (
            <button
              data-testid={`quick-action-${item.title.toLowerCase().replace(" ", "-")}`}
              key={item.title}
              onClick={item.onClick}
              className="group surface-card flex flex-col gap-4 rounded-2xl border border-white/5 p-6 text-left transition-all hover:-translate-y-1 hover:border-white/20 hover:bg-white/5"
            >
              <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-${item.color}-500/10 text-${item.color}-400 group-hover:scale-110 transition-transform`}>
                <i className={`bi ${item.icon} text-xl`} />
              </div>
              <div>
                <p className="font-bold text-white">{item.title}</p>
                <p className="text-xs text-slate-500">{item.desc}</p>
              </div>
            </button>
          ))}
        </div>

        {/* CATEGORIES SECTION */}
        <Card data-testid="categories-section" className="surface-card">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Categories</CardTitle>
            <Button 
  variant="success" 
  size="sm" 
  onClick={() => {
    setCategoryForm({ name: "", mcc_code: "", icon: "bi-tag-fill" });
    setCategoryErrors({});
    setIsAddCategoryOpen(true); // Тепер вона відкриває модалку
  }}
>
  <i className="bi bi-plus-lg mr-2" /> Add New
</Button>
          </CardHeader>
          <CardContent>
             {/* Замість великої форми - акуратний список */}
             <div className="grid gap-3 sm:grid-cols-2">
               {categories.map((cat) => (
                 <div key={cat.id} className="group flex items-center justify-between rounded-2xl border border-white/5 bg-[#0f172a]/40 p-4 transition-all hover:bg-[#121a2b] hover:border-blue-500/30">
                   <div className="flex items-center gap-4">
                     <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400">
                       <i className={`bi ${cat.icon} text-lg`} />
                     </div>
                     <div>
                       <p className="text-sm font-bold text-white">{cat.name}</p>
                       <p className="text-[10px] font-medium uppercase tracking-wider text-slate-500">{cat.mcc_code || "No MCC"}</p>
                     </div>
                   </div>
                   <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                     <button onClick={() => { setEditCategory(cat); setEditCategorySnapshot(cat); setCategoryErrors({}); setIsEditCategoryOpen(true); }} data-testid="edit-category-button" className="h-8 w-8 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors">
                       <i className="bi bi-pencil-fill text-xs" />
                     </button>
                     <button onClick={() => { setDeleteCategoryId(cat.id); setIsDeleteCategoryOpen(true); }} data-testid="delete-category-button" className="h-8 w-8 rounded-lg bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-colors">
                       <i className="bi bi-trash-fill text-xs" />
                     </button>
                   </div>
                 </div>
               ))}
             </div>
          </CardContent>
        </Card>

        {/* DANGER ZONE */}
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h3 className="text-lg font-bold text-rose-400">Danger Zone</h3>
              <p className="text-sm text-slate-400">Permanently delete your account and all data. This is irreversible.</p>
            </div>
            <Button variant="danger" className="bg-rose-500/10 text-white border-rose-500/30 hover:bg-rose-600 hover:text-white" onClick={() => setIsDeleteOpen(true)}>
              Delete Account
            </Button>
          </div>
        </div>
      </div>

      {/* УСІ МОДАЛКИ ПЕРЕВЕДЕНІ НА FormModal ТА ConfirmDeleteModal */}
      
      <FormModal
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
        onSubmit={handleProfileSubmit}
        title="Edit Profile"
        type="edit"
      >
        <ProfileFormFields
          draft={profileDraft}
          setDraft={setProfileDraft}
          errors={profileErrors}
          onFieldChange={(field: string) => {
            setProfileErrors((prev) => {
              if (!prev[field]) {
                return prev;
              }
              const next = { ...prev };
              delete next[field];
              return next;
            });
          }}
        />
      </FormModal>

      <FormModal
        isOpen={isPasswordOpen}
        onClose={() => setIsPasswordOpen(false)}
        onSubmit={handlePasswordSubmit}
        title="Change Password"
        type="edit"
      >
        <div data-testid="password-form" className="flex flex-col gap-4">
          <div>
            <Input
              data-testid="current-password-input"
              type="password"
              placeholder="Current Password"
              value={passwordForm.old_password}
              onChange={(e) => {
                setPasswordForm((p) => ({ ...p, old_password: e.target.value }));
                setPasswordErrors((prev) => {
                  if (!prev.old_password) {
                    return prev;
                  }
                  const next = { ...prev };
                  delete next.old_password;
                  return next;
                });
              }}
              aria-invalid={!!passwordErrors.old_password}
              className={passwordErrors.old_password ? "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20" : undefined}
            />
            {passwordErrors.old_password && <p data-testid="old-password-error" className="mt-1 text-xs text-rose-400">{passwordErrors.old_password}</p>}
          </div>
          <div>
            <Input
              data-testid="new-password-input"
              type="password"
              placeholder="New Password"
              value={passwordForm.new_password}
              onChange={(e) => {
                setPasswordForm((p) => ({ ...p, new_password: e.target.value }));
                setPasswordErrors((prev) => {
                  if (!prev.new_password) {
                    return prev;
                  }
                  const next = { ...prev };
                  delete next.new_password;
                  return next;
                });
              }}
              aria-invalid={!!passwordErrors.new_password}
              className={passwordErrors.new_password ? "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20" : undefined}
            />
            {passwordErrors.new_password && <p data-testid="new-password-error" className="mt-1 text-xs text-rose-400">{passwordErrors.new_password}</p>}
          </div>
          <div>
            <Input
              data-testid="confirm-password-input"
              type="password"
              placeholder="Confirm New Password"
              value={passwordForm.confirm_password}
              onChange={(e) => {
                setPasswordForm((p) => ({ ...p, confirm_password: e.target.value }));
                setPasswordErrors((prev) => {
                  if (!prev.confirm_password) {
                    return prev;
                  }
                  const next = { ...prev };
                  delete next.confirm_password;
                  return next;
                });
              }}
              aria-invalid={!!passwordErrors.confirm_password}
              className={passwordErrors.confirm_password ? "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20" : undefined}
            />
            {passwordErrors.confirm_password && <p data-testid="confirm-password-error" className="mt-1 text-xs text-rose-400">{passwordErrors.confirm_password}</p>}
          </div>
        </div>
      </FormModal>

      <FormModal
        isOpen={isEditCategoryOpen}
        onClose={() => setIsEditCategoryOpen(false)}
        onSubmit={handleEditCategory}
        title="Edit Category"
        type="edit"
      >
        {editCategory && (
          <CategoryFormFields
            form={editCategory}
            setForm={setEditCategory}
            icons={iconOptions}
            errors={categoryErrors}
            onFieldChange={(field: string) => {
              setCategoryErrors((prev) => {
                if (!prev[field]) {
                  return prev;
                }
                const next = { ...prev };
                delete next[field];
                return next;
              });
            }}
          />
        )}
      </FormModal>

      <ConfirmDeleteModal
        isOpen={isDeleteCategoryOpen}
        onClose={() => setIsDeleteCategoryOpen(false)}
        onConfirm={handleDeleteCategory}
        description="Are you sure? All transactions in this category will become 'Uncategorized'."
      />

      <ConfirmDeleteModal
        isOpen={isDeleteOpen}
        onClose={() => setIsDeleteOpen(false)}
        onConfirm={handleDeleteAccount}
        title="Delete Account"
        description="Everything will be gone forever. Are you absolutely sure?"
      />
      {/* МОДАЛКА МОНОБАНКУ */}
<FormModal
  isOpen={isMonobankOpen}
  onClose={() => setIsMonobankOpen(false)}
  onSubmit={handleMonobankSubmit}
  title="Monobank Integration"
  type="edit"
  
>
  <div className="space-y-4">
    <div className="rounded-xl border border-blue-500/20 bg-blue-500/10 p-4 text-xs leading-relaxed text-blue-200">
      <i className="bi bi-info-circle-fill mr-2" />
      Get your Personal Access Token from <strong>api.monobank.ua</strong>. It allows us to sync your transactions automatically.
    </div>
    <div>
      <label  htmlFor="api-token-input" className="mb-1.5 block text-sm font-medium text-slate-200">API Token</label>
      <Input 
        id="api-token-input"
        placeholder="Paste your token here..." 
        value={monoToken} 
        onChange={(e) => {
          setMonoToken(e.target.value);
          setMonoErrors((prev) => {
            if (!prev.token) {
              return prev;
            }
            const next = { ...prev };
            delete next.token;
            return next;
          });
        }} 
        aria-invalid={!!monoErrors.token}
        className={monoErrors.token ? "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20" : undefined}
      />
      {monoErrors.token && <p data-testid="token-error" className="mt-1 text-xs text-rose-400">{monoErrors.token}</p>}
    </div>
    {user?.monobank_token_is_set && (
    <button 
      type="button"
      onClick={() => setIsConfirmMonoDisconnectOpen(true)} // ТЕПЕР ВІДКРИВАЄ ПІДТВЕРДЖЕННЯ
      className="text-xs font-bold text-rose-400 hover:text-rose-300 transition-colors mt-2"
    >
      <i className="bi bi-trash3 mr-1" /> Disconnect Monobank
    </button>
  )}
  </div>
</FormModal>
<ConfirmDeleteModal
  isOpen={isConfirmMonoDisconnectOpen}
  onClose={() => setIsConfirmMonoDisconnectOpen(false)}
  onConfirm={handleRemoveToken}
  title="Disconnect Monobank"
  description="Are you sure you want to remove your Monobank integration? You will no longer be able to sync your transactions automatically."
/>

{/* МОДАЛКА ДОДАВАННЯ КАТЕГОРІЇ */}
<FormModal
  isOpen={isAddCategoryOpen}
  onClose={() => setIsAddCategoryOpen(false)}
  onSubmit={handleAddCategory}
  title="New Category"
  type="add"
  submitLabel="Add Category"
>
  <CategoryFormFields 
    form={categoryForm} 
    setForm={setCategoryForm} 
    icons={iconOptions} 
    errors={categoryErrors}
    onFieldChange={(field: string) => {
      setCategoryErrors((prev) => {
        if (!prev[field]) {
          return prev;
        }
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }}
  />
</FormModal>
    </AppShell>
  );
};

export default ProfilePage;
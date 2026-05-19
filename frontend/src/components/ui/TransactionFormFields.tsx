import { useCurrency } from "../../hooks/useCurrency";
import { cn } from "../../lib/utils";

const selectStyles =
  "w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 focus:border-blue-400/60 focus:outline-none focus:ring-2 focus:ring-blue-500/20";

type TransactionFormFieldsProps = {
  form: any;
  setForm: React.Dispatch<React.SetStateAction<any>>;
  categories: any[];
  variant?: "success" | "primary";
  datatestid?: string;
  errors?: Record<string, string>;
  onFieldChange?: (field: string) => void;
};

export const TransactionFormFields = ({
  form,
  setForm,
  categories,
  variant = "success",
  "datatestid": testId,
  errors = {},
  onFieldChange
}: TransactionFormFieldsProps) => {
  const normalizeDateInput = (value: string) => {
    if (!value) {
      return "";
    }
    if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
      return value;
    }
    const match = value.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
    if (match) {
      return `${match[3]}-${match[2]}-${match[1]}`;
    }
    return value;
  };
  const formatCategoryLabel = (name: string) => {
    const maxLength = 30;
    if (name.length <= maxLength) {
      return name;
    }
    return `${name.slice(0, maxLength - 3)}...`;
  };
  // 1. СТАТИЧНІ КЛАСИ (щоб Tailwind їх не видалив)
  const inactiveBtn = "border-white/10 bg-white/5 text-slate-400 hover:bg-white/10";
  const inactiveDot = "bg-slate-500";

  // Використовуємо наш новий хук замість authStore та ручного словника
  const { currencySymbol } = useCurrency();

  // Активна кнопка отримує колір залежно від пропсу variant (emerald або blue)
  const activeBtn = variant === "success"
    ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.15)]"
    : "border-blue-500/50 bg-blue-500/10 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.15)]";

  const activeDot = variant === "success" ? "bg-emerald-400" : "bg-blue-400";

  return (
    <div data-testid={testId || "transaction-form-fields"} className="flex flex-col gap-4">
      {/* Title */}
      <div>
        <label htmlFor="title-input" className="mb-1.5 block text-sm font-medium text-slate-200">Title</label>
        <input
          id="title-input"
          className={cn(
            selectStyles,
            errors.title && "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20"
          )}
          placeholder="E.g. Grocery shopping"
          maxLength={50}
          value={form.title}
          onChange={(e) => {
            setForm((prev: any) => ({ ...prev, title: e.target.value }));
            onFieldChange?.("title");
          }}
          aria-invalid={!!errors.title}
        />
        {errors.title && <p data-testid="title-error" className="mt-1 text-xs text-rose-400">{errors.title}</p>}
      </div>

      {/* Transaction Type Buttons */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-slate-200">Type</label>
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            className={`flex items-center justify-center gap-2 rounded-xl border px-4 py-2 text-sm font-semibold transition-all ${
              form.transaction_type === "expense" ? activeBtn : inactiveBtn
            }`}
            onClick={() => {
              setForm((prev: any) => ({ ...prev, transaction_type: "expense" }));
              onFieldChange?.("transaction_type");
            }}
          >
            <span className={`h-2.5 w-2.5 rounded-sm ${form.transaction_type === "expense" ? activeDot : inactiveDot}`} />
            Expense
          </button>

          <button
            type="button"
            className={`flex items-center justify-center gap-2 rounded-xl border px-4 py-2 text-sm font-semibold transition-all ${
              form.transaction_type === "income" ? activeBtn : inactiveBtn
            }`}
            onClick={() => {
              setForm((prev: any) => ({ ...prev, transaction_type: "income" }));
              onFieldChange?.("transaction_type");
            }}
          >
            <span className={`h-2.5 w-2.5 rounded-sm ${form.transaction_type === "income" ? activeDot : inactiveDot}`} />
            Income
          </button>
        </div>
        {errors.transaction_type && <p data-testid="transaction-type-error" className="mt-1 text-xs text-rose-400">{errors.transaction_type}</p>}
      </div>

      {/* Amount */}
      <div>
        <label htmlFor="amount-input" className="mb-1.5 block text-sm font-medium text-slate-200">Amount</label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">{currencySymbol}</span>
          <input
            id="amount-input"
            type="number"
            step="0.01"
            max={99999999.99}
            className={cn(
              selectStyles,
              "pl-7",
              errors.amount && "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20"
            )}
            placeholder="0.00"
            value={form.amount}
            onChange={(e) => {
              setForm((prev: any) => ({ ...prev, amount: e.target.value }));
              onFieldChange?.("amount");
            }}
            aria-invalid={!!errors.amount}
          />
        </div>
        {errors.amount && <p data-testid="amount-error" className="mt-1 text-xs text-rose-400">{errors.amount}</p>}
      </div>

      {/* Category Dropdown */}
      <div>
        <label htmlFor="category-select" className="mb-1.5 block text-sm font-medium text-slate-200">Category</label>
        <select
          id="category-select"
          className={cn(
            selectStyles,
            errors.category_id && "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20"
          )}
          value={form.category_id}
          onChange={(e) => {
            setForm((prev: any) => ({ ...prev, category_id: e.target.value }));
            onFieldChange?.("category_id");
          }}
          aria-invalid={!!errors.category_id}
        >
          <option value="" disabled>Select category...</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id} title={category.name}>
              {formatCategoryLabel(category.name)}
            </option>
          ))}
        </select>
        {errors.category_id && <p data-testid="category-id-error" className="mt-1 text-xs text-rose-400">{errors.category_id}</p>}
      </div>

      {/* Date Picker */}
      <div>
        <label htmlFor="date-field" className="mb-1.5 block text-sm font-medium text-slate-200">Date</label>
        <input
          id="date-field"
          type="date"
          className={cn(
            selectStyles,
            errors.created_at && "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20"
          )}
          value={form.created_at}
          onChange={(e) => {
            const normalized = normalizeDateInput(e.target.value);
            setForm((prev: any) => ({ ...prev, created_at: normalized }));
            onFieldChange?.("created_at");
          }}
          aria-invalid={!!errors.created_at}
        />
        {errors.created_at && <p data-testid="created-at-error" className="mt-1 text-xs text-rose-400">{errors.created_at}</p>}
      </div>

      {/* Note Field */}
      <div>
        <label htmlFor="note-textarea" className="mb-1.5 block text-sm font-medium text-slate-200">Note (optional)</label>
        <textarea
          id="note-textarea"
          rows={2}
          className={cn(
            selectStyles,
            "resize-none py-3",
            errors.note && "border-rose-500/60 focus:border-rose-400/80 focus:ring-rose-500/20"
          )}
          placeholder="Add some details..."
          value={form.note}
          onChange={(e) => {
            setForm((prev: any) => ({ ...prev, note: e.target.value }));
            onFieldChange?.("note");
          }}
          aria-invalid={!!errors.note}
        />
        {errors.note && <p data-testid="note-error" className="mt-1 text-xs text-rose-400">{errors.note}</p>}
      </div>
    </div>
  );
};
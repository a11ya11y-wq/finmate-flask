const selectStyles = 
  "w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-100 focus:border-blue-400/60 focus:outline-none focus:ring-2 focus:ring-blue-500/20";

type TransactionFormFieldsProps = {
  form: any;
  setForm: React.Dispatch<React.SetStateAction<any>>;
  categories: any[];
  variant?: "success" | "primary";
};

export const TransactionFormFields = ({ form, setForm, categories, variant = "success" }: TransactionFormFieldsProps) => {
  
  // 1. СТАТИЧНІ КЛАСИ (щоб Tailwind їх не видалив)
  const inactiveBtn = "border-white/10 bg-white/5 text-slate-400 hover:bg-white/10";
  const inactiveDot = "bg-slate-500";

  // Активна кнопка отримує колір залежно від пропсу variant (emerald або blue)
  const activeBtn = variant === "success"
    ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.15)]"
    : "border-blue-500/50 bg-blue-500/10 text-blue-400 shadow-[0_0_15px_rgba(59,130,246,0.15)]";
  
  const activeDot = variant === "success" ? "bg-emerald-400" : "bg-blue-400";

  return (
    <div className="flex flex-col gap-4">
      {/* Title */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-slate-200">Title</label>
        <input
          className={selectStyles}
          placeholder="E.g. Grocery shopping"
          value={form.title}
          onChange={(e) => setForm((prev: any) => ({ ...prev, title: e.target.value }))}
        />
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
            onClick={() => setForm((prev: any) => ({ ...prev, transaction_type: "expense" }))}
          >
            <span className={`h-2.5 w-2.5 rounded-sm ${form.transaction_type === "expense" ? activeDot : inactiveDot}`} />
            Expense
          </button>
          
          <button
            type="button"
            className={`flex items-center justify-center gap-2 rounded-xl border px-4 py-2 text-sm font-semibold transition-all ${
              form.transaction_type === "income" ? activeBtn : inactiveBtn
            }`}
            onClick={() => setForm((prev: any) => ({ ...prev, transaction_type: "income" }))}
          >
            <span className={`h-2.5 w-2.5 rounded-sm ${form.transaction_type === "income" ? activeDot : inactiveDot}`} />
            Income
          </button>
        </div>
      </div>

      {/* Amount */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-slate-200">Amount</label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">$</span>
          <input
            type="number"
            step="0.01"
            className={`${selectStyles} pl-7`}
            placeholder="0.00"
            value={form.amount}
            onChange={(e) => setForm((prev: any) => ({ ...prev, amount: e.target.value }))}
          />
        </div>
      </div>

      {/* Category Dropdown */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-slate-200">Category</label>
        <select
          className={selectStyles}
          value={form.category_id}
          onChange={(e) => setForm((prev: any) => ({ ...prev, category_id: e.target.value }))}
        >
          <option value="" disabled>Select category...</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>{category.name}</option>
          ))}
        </select>
      </div>

      {/* Date Picker */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-slate-200">Date</label>
        <input
          type="date"
          className={selectStyles}
          value={form.created_at}
          onChange={(e) => setForm((prev: any) => ({ ...prev, created_at: e.target.value }))}
        />
      </div>

      {/* Note Field */}
      <div>
        <label className="mb-1.5 block text-sm font-medium text-slate-200">Note (optional)</label>
        <textarea
          rows={2}
          className={`${selectStyles} resize-none py-3`}
          placeholder="Add some details..."
          value={form.note}
          onChange={(e) => setForm((prev: any) => ({ ...prev, note: e.target.value }))}
        />
      </div>
    </div>
  );
};
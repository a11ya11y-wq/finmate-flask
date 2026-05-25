export const queryKeys = {
  profile: ["profile"] as const,
  categories: ["categories"] as const,
  budgets: ["budgets"] as const,
  reportStatus: (reportId: number) => ["reports", "status", reportId] as const,
  reportHistory: ["reports", "history"] as const,
  dashboard: (period: string) => ["dashboard", period] as const,
  dashboardHistory: (period: string, page: number) =>
    ["dashboard", "history", period, page] as const,
  monobankTask: (taskId: string) => ["monobank", "task", taskId] as const
};

import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import AppShell from "../components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { useToast } from "../components/ui/toast";
import { generatePdfReport, getReportHistory, getReportStatus } from "../api/reports";
import { queryKeys } from "../api/queryKeys";
import { toErrorMessage } from "../api/error";
import type { ReportHistoryItem, ReportResponse, ReportStatus } from "../api/types";

const toDateInput = (value: Date) => value.toISOString().slice(0, 10);

const getDefaultRange = () => {
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - 30);
    return {
        start: toDateInput(start),
        end: toDateInput(end)
    };
};

const formatRange = (start: string, end: string) => {
    if (!start || !end) {
        return "";
    }
    const startDate = new Date(start);
    const endDate = new Date(end);
    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
        return `${start} - ${end}`;
    }
    return `${startDate.toLocaleDateString("en-US", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    })} - ${endDate.toLocaleDateString("en-US", {
        day: "2-digit",
        month: "short",
        year: "numeric"
    })}`;
};

const normalizeStatus = (status?: string | null): ReportStatus | "" => {
    if (!status) {
        return "";
    }
    return status.toUpperCase() as ReportStatus;
};

type WizardState = "idle" | "pending" | "success" | "error";

const ReportsPage = () => {
    const queryClient = useQueryClient();
    const { toast } = useToast();
    const defaultRange = useMemo(() => getDefaultRange(), []);
    const [startDate, setStartDate] = useState(defaultRange.start);
    const [endDate, setEndDate] = useState(defaultRange.end);
    const [wizardState, setWizardState] = useState<WizardState>("idle");
    const [reportId, setReportId] = useState<number | null>(null);
    const [reportUrl, setReportUrl] = useState<string | null>(null);
    const [statusMessage, setStatusMessage] = useState<string | null>(null);

    const historyQuery = useQuery<ReportHistoryItem[]>({
        queryKey: queryKeys.reportHistory,
        queryFn: getReportHistory,
        refetchInterval: wizardState === "pending" ? 2000 : false
    });

    const applyQuickRange = (range: "month" | "year" | "all") => {
        const now = new Date();
        const nextStart = new Date(now);

        if (range === "month") {
            nextStart.setDate(1);
        } else if (range === "year") {
            nextStart.setMonth(0, 1);
        } else {
            nextStart.setFullYear(2000, 0, 1);
        }

        setStartDate(toDateInput(nextStart));
        setEndDate(toDateInput(now));
    };

    const resetWizard = () => {
        setWizardState("idle");
        setReportId(null);
        setReportUrl(null);
        setStatusMessage(null);
    };

    const handleReportResponse = (result: ReportResponse) => {
        const normalized = normalizeStatus(result.status);
        setReportId(result.id);
        setReportUrl(result.fileUrl ?? null);

        if (normalized === "PROCESSED") {
            if (result.fileUrl) {
                setWizardState("success");
            } else {
                setStatusMessage("Report is ready, but the download link is missing. Please try again.");
                setWizardState("error");
            }
            return;
        }

        if (normalized === "FAILED" || normalized === "EXPIRED") {
            setStatusMessage(result.error ?? "Failed to generate the report.");
            setWizardState("error");
            return;
        }

        setWizardState("pending");
    };

    const generateMutation = useMutation({
        mutationFn: () => generatePdfReport({ startDate, endDate }),
        onSuccess: (result) => {
            setStatusMessage(null);
            handleReportResponse(result);
            void queryClient.invalidateQueries({ queryKey: queryKeys.reportHistory });
        },
        onError: (error) => {
            toast({ variant: "error", message: toErrorMessage(error) });
            resetWizard();
        }
    });

    useEffect(() => {
        if (historyQuery.error) {
            toast({ variant: "error", message: toErrorMessage(historyQuery.error) });
        }
    }, [historyQuery.error, toast]);

    useEffect(() => {
        if (wizardState !== "pending" || !reportId) {
            return;
        }

        let isCancelled = false;
        let timeoutId: number | null = null;

        const pollOnce = async () => {
            try {
                const result = await queryClient.fetchQuery({
                    queryKey: queryKeys.reportStatus(reportId),
                    queryFn: () => getReportStatus(reportId),
                    staleTime: 0
                });

                const normalized = normalizeStatus(result.status);

                if (normalized === "PENDING") {
                    if (!isCancelled) {
                        timeoutId = window.setTimeout(pollOnce, 2000);
                    }
                    return;
                }

                if (normalized === "PROCESSED") {
                    if (!result.fileUrl) {
                        setStatusMessage("Report is ready, but the download link is missing. Please try again.");
                        setWizardState("error");
                        return;
                    }
                    setReportUrl(result.fileUrl);
                    setWizardState("success");
                    void queryClient.invalidateQueries({ queryKey: queryKeys.reportHistory });
                    return;
                }

                setStatusMessage(result.error ?? "Failed to generate the report.");
                setWizardState("error");
                void queryClient.invalidateQueries({ queryKey: queryKeys.reportHistory });
            } catch (error) {
                setStatusMessage(toErrorMessage(error));
                setWizardState("error");
                void queryClient.invalidateQueries({ queryKey: queryKeys.reportHistory });
            }
        };

        void pollOnce();

        return () => {
            isCancelled = true;
            if (timeoutId) {
                window.clearTimeout(timeoutId);
            }
        };
    }, [wizardState, reportId, queryClient]);

    const canSubmit = startDate && endDate && !generateMutation.isPending && wizardState !== "pending";

    const handleGenerate = () => {
        if (!startDate || !endDate) {
            toast({ variant: "warning", message: "Select a date range for the report." });
            return;
        }
        if (startDate >= endDate) {
            toast({ variant: "warning", message: "Start date must be before the end date." });
            return;
        }
        setStatusMessage(null);
        setWizardState("pending");
        generateMutation.mutate();
    };

    const handleDownload = () => {
        if (!reportUrl) {
            toast({ variant: "error", message: "Report link is not available. Please try again." });
            setWizardState("error");
            return;
        }
        window.open(reportUrl, "_blank", "noopener,noreferrer");
    };

    const periodLabel = formatRange(startDate, endDate);
    const historyItems = historyQuery.data ?? [];
    const historyEmpty = !historyQuery.isLoading && historyItems.length === 0;

    return (
        <AppShell>
            <div className="relative min-h-[70vh] space-y-8">
                <div className="relative flex items-center gap-3">
                    <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/15 text-blue-300">
                        <i className="bi bi-bar-chart-line text-xl" />
                    </span>
                    <div>
                        <h2 className="text-2xl font-bold text-white">Reports & Analytics</h2>
                        <p className="text-sm text-slate-400">
                            Generate and download your financial statements.
                        </p>
                    </div>
                </div>
                <div className="pointer-events-none absolute inset-0">
                    <div className="absolute -left-20 top-10 h-56 w-56 rounded-full bg-blue-500/10 blur-3xl" />
                    <div className="absolute right-10 top-12 h-40 w-40 rounded-full bg-emerald-400/10 blur-3xl" />
                    <div className="absolute bottom-10 left-1/3 h-48 w-48 rounded-full bg-cyan-400/10 blur-3xl" />
                </div>

                <div className="relative grid items-stretch gap-6 lg:grid-cols-[1fr_1.85fr]">
                    <div className="flex flex-col gap-6">
                        <Card className="relative flex w-full flex-none h-[375px] flex-col overflow-hidden bg-[#161b22] shrink-0 min-h-0">
                            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-transparent to-emerald-400/10" />
                            <CardHeader className="relative space-y-2">
                                <div className="flex items-center gap-3">
                                    <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-500/15 text-blue-200">
                                        <i className="bi bi-file-earmark-arrow-down text-lg" />
                                    </span>
                                    <div>
                                        <CardTitle className="text-lg">Export data</CardTitle>
                                        <p className="text-sm text-slate-400">
                                            Generate a transaction report for your selected period.
                                        </p>
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="relative flex flex-col h-full overflow-auto">
                                {(wizardState === "idle" || wizardState === "error") && (
                                    <div data-testid="generate-report-form" className="flex h-full flex-1 flex-col gap-5">
                                        <div className="space-y-2">
                                            <span className="text-[11px] uppercase tracking-[0.2em] text-slate-500">
                                                Quick select
                                            </span>
                                            <div data-testid="report-quick-period-container" className="flex flex-wrap items-center gap-2 text-xs text-slate-300">
                                                <button
                                                    data-testid="quick-range-month"
                                                    type="button"
                                                    className="rounded-full border border-blue-500/30 px-3 py-1 text-xs text-blue-100/80 transition hover:border-blue-400/60 hover:bg-blue-500/10 hover:text-blue-100"
                                                    onClick={() => applyQuickRange("month")}
                                                >
                                                    This month
                                                </button>
                                                <button
                                                    data-testid="quick-range-year"
                                                    type="button"
                                                    className="rounded-full border border-blue-500/30 px-3 py-1 text-xs text-blue-100/80 transition hover:border-blue-400/60 hover:bg-blue-500/10 hover:text-blue-100"
                                                    onClick={() => applyQuickRange("year")}
                                                >
                                                    This year
                                                </button>
                                                <button
                                                    data-testid="quick-range-all"
                                                    type="button"
                                                    className="rounded-full border border-blue-500/30 px-3 py-1 text-xs text-blue-100/80 transition hover:border-blue-400/60 hover:bg-blue-500/10 hover:text-blue-100"
                                                    onClick={() => applyQuickRange("all")}
                                                >
                                                    All time
                                                </button>
                                            </div>
                                        </div>
                                        <div className="grid gap-4 sm:grid-cols-2">
                                            <label className="flex-1 space-y-2 text-sm text-slate-300">
                                                Start date
                                                <Input
                                                    type="date"
                                                    value={startDate}
                                                    onChange={(event) => setStartDate(event.target.value)}
                                                    data-testid="report-start-date-input"
                                                    disabled={wizardState === "pending"}
                                                />
                                            </label>
                                            <label className="flex-1 space-y-2 text-sm text-slate-300">
                                                End date
                                                <Input
                                                    type="date"
                                                    value={endDate}
                                                    onChange={(event) => setEndDate(event.target.value)}
                                                    data-testid="report-end-date-input"
                                                    disabled={wizardState === "pending"}
                                                />
                                            </label>
                                        </div>
                                        {statusMessage && (
                                            <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
                                                {statusMessage}
                                            </div>
                                        )}
                                        <Button data-testid="generate-report-button" className="w-full" onClick={handleGenerate} disabled={!canSubmit}>
                                            Generate
                                        </Button>
                                    </div>
                                )}

                                {wizardState === "pending" && (
                                    <div data-testid="generate-report-form-pending" className="flex h-full flex-1 flex-col text-center">
                                        <div className="space-y-5">
                                            <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl border border-white/10 bg-white/5">
                                                <div className="h-10 w-10 animate-spin rounded-full border-2 border-blue-400/30 border-t-blue-400" />
                                            </div>
                                            <div className="space-y-2">
                                                <p className="text-base font-semibold text-slate-100">
                                                    Gathering your transactions...
                                                </p>
                                                {periodLabel && (
                                                    <p className="text-sm text-slate-400 truncate">Period: {periodLabel}</p>
                                                )}
                                            </div>
                                            <div className="h-2 w-full overflow-hidden rounded-full bg-white/5">
                                                <div className="h-full w-2/3 animate-pulse rounded-full bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400" />
                                            </div>
                                        </div>
                                        <div className="mt-auto">
                                            <Button data-testid="generate-report-form-pending-cancel-button" variant="ghost" onClick={resetWizard} className="w-full">
                                                Cancel
                                            </Button>
                                        </div>
                                    </div>
                                )}

                                {wizardState === "success" && (
                                    <div data-testid="generate-report-form-success" className="flex h-full flex-1 flex-col text-center">
                                        <div className="space-y-5">
                                            <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-emerald-500/15 text-emerald-200">
                                                <i className="bi bi-check-circle-fill text-3xl" />
                                            </div>
                                            <div className="space-y-1">
                                                <p data-testid="generate-report-form-success-title" className="text-base font-semibold text-slate-100">Report is ready</p>
                                                {periodLabel && (
                                                    <p data-testid="generate-report-form-success-period" className="text-sm text-slate-400 truncate">Period: {periodLabel}</p>
                                                )}
                                            </div>
                                        </div>
                                        <div className="mt-auto space-y-3">
                                            <Button data-testid="download-report-button" className="w-full" onClick={handleDownload}>
                                                Download PDF
                                            </Button>
                                            <Button variant="secondary" className="w-full" onClick={resetWizard} data-testid="create-new-report-button">
                                                Create new
                                            </Button>
                                        </div>
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        <Card className="relative flex w-full flex-col overflow-hidden">
                            <CardHeader>
                                <CardTitle>What's included?</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-3 text-sm text-slate-300">
                                <div className="flex items-start gap-3">
                                    <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-500/15 text-blue-300">
                                        <i className="bi bi-flag" />
                                    </span>
                                    <div>
                                        <p className="text-sm font-semibold text-slate-100">Header</p>
                                        <p className="text-sm text-slate-400">Official FinMate branding and report period.</p>
                                    </div>
                                </div>
                                <div className="flex items-start gap-3">
                                    <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-500/15 text-blue-300">
                                        <i className="bi bi-list-ul" />
                                    </span>
                                    <div>
                                        <p className="text-sm font-semibold text-slate-100">Transactions</p>
                                        <p className="text-sm text-slate-400">Detailed list of all incomes and expenses.</p>
                                    </div>
                                </div>
                                <div className="flex items-start gap-3">
                                    <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-500/15 text-blue-300">
                                        <i className="bi bi-tags" />
                                    </span>
                                    <div>
                                        <p className="text-sm font-semibold text-slate-100">Categories</p>
                                        <p className="text-sm text-slate-400">Smart tags for quick expense scanning.</p>
                                    </div>
                                </div>
                                <div className="flex items-start gap-3">
                                    <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-500/15 text-blue-300">
                                        <i className="bi bi-bank" />
                                    </span>
                                    <div>
                                        <p className="text-sm font-semibold text-slate-100">Summary</p>
                                        <p className="text-sm text-slate-400">Final closing balance and totals.</p>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    <Card className="relative flex h-full w-full flex-col overflow-hidden">
                        <CardHeader className="space-y-2 pb-3">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/15 text-blue-300">
                                        <i className="bi bi-folder2-open" />
                                    </span>
                                    <div>
                                        <CardTitle>Recent reports</CardTitle>
                                        <p className="text-sm text-slate-400">
                                            View your latest exports and download links.
                                        </p>
                                    </div>
                                </div>
                                {historyQuery.isLoading && (
                                    <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs text-slate-300">
                                        Loading
                                    </span>
                                )}
                            </div>
                        </CardHeader>
                        <CardContent data-testid="reports-table" className="flex-1 space-y-3 overflow-y-auto pt-3 [scrollbar-gutter:stable]">
                            {historyQuery.isLoading && (
                                <div className="space-y-4">
                                    {[1, 2, 3].map((item) => (
                                        <div
                                            key={`report-placeholder-${item}`}
                                            className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3"
                                        >
                                            <div className="space-y-2">
                                                <div className="h-3 w-40 rounded-full bg-white/10" />
                                                <div className="h-2 w-28 rounded-full bg-white/10" />
                                            </div>
                                            <div className="h-7 w-20 rounded-full bg-white/10" />
                                        </div>
                                    ))}
                                </div>
                            )}

                            {!historyQuery.isLoading && historyItems.length > 0 && (
                                <div className="space-y-3">
                                    {historyItems.map((item) => {
                                        const rangeLabel = item.startDate && item.endDate
                                            ? formatRange(item.startDate, item.endDate)
                                            : "Custom range";
                                        const status = normalizeStatus(item.status);
                                        const statusTone =
                                            status === "PROCESSED"
                                                ? "text-emerald-300 bg-emerald-500/10"
                                                : status === "PENDING"
                                                    ? "text-amber-300 bg-amber-500/10"
                                                    : "text-rose-300 bg-rose-500/10";

                                        return (
                                            <div
                                                key={`report-history-${item.id}`}
                                                className="flex items-center justify-between gap-3 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 min-h-[64px]"
                                            >
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-semibold text-slate-100 truncate">{rangeLabel}</p>
                                                    <div className="flex items-center gap-2 text-xs text-slate-400">
                                                        <span className={`rounded-full px-2 py-0.5 min-w-[72px] text-center ${statusTone}`}>
                                                            {status || "UNKNOWN"}
                                                        </span>
                                                        {item.createdAt && (
                                                            <span className="truncate">
                                                                Created {new Date(item.createdAt).toLocaleDateString("en-US")}
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="flex-shrink-0">
                                                    {item.fileUrl && status === "PROCESSED" ? (
                                                        <Button
                                                            data-testid={`report-history-download-${item.id}`}
                                                            variant="outline"
                                                            className="h-9 px-3 text-xs"
                                                            onClick={() => window.open(item.fileUrl ?? "", "_blank", "noopener,noreferrer")}
                                                        >
                                                            Download
                                                        </Button>
                                                    ) : (
                                                        <span className="text-xs text-slate-400">No file</span>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}

                            {historyEmpty && (
                                <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 px-4 py-4 text-sm text-slate-400">
                                    No reports yet. Generate your first PDF export on the left.
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </AppShell>
    );
};

export default ReportsPage;

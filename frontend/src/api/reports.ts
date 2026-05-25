import { apiRequest } from "./client";
import type { ReportHistoryItem, ReportResponse } from "./types";

type GenerateReportPayload = {
  startDate: string;
  endDate: string;
};

export const generatePdfReport = async (payload: GenerateReportPayload) => {
  return apiRequest<ReportResponse>("/report/generate-pdf", {
    method: "POST",
    body: payload
  });
};

export const getReportStatus = async (reportId: number) => {
  return apiRequest<ReportResponse>(`/report/generate-pdf/${reportId}/status`);
};

export const getReportHistory = async () => {
  return apiRequest<ReportHistoryItem[]>("/report/history");
};

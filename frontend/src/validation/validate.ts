import type { ZodTypeAny, infer as ZodInfer } from "zod";

type FieldErrors = Record<string, string>;

const mapFieldErrors = (issues: { message: string; path: readonly PropertyKey[] }[]) => {
  return issues.reduce<FieldErrors>((acc, issue) => {
    const key = issue.path[0];
    if ((typeof key === "string" || typeof key === "number") && !acc[String(key)]) {
      acc[String(key)] = issue.message;
    }
    return acc;
  }, {});
};

export const validateForm = <T extends ZodTypeAny>(schema: T, data: unknown) => {
  const result = schema.safeParse(data);
  if (result.success) {
    return {
      success: true as const,
      data: result.data as ZodInfer<T>,
      fieldErrors: {} as FieldErrors
    };
  }

  const uniqueMessages = Array.from(new Set(result.error.issues.map((issue) => issue.message)));
  return {
    success: false as const,
    error: uniqueMessages.join("\n"),
    fieldErrors: mapFieldErrors(result.error.issues)
  };
};

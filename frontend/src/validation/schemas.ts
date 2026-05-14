import { z } from "zod";

const amountSchema = z
  .string()
  .trim()
  .min(1, "Enter a valid amount")
  .refine((value) => !Number.isNaN(Number(value)), "Enter a valid amount")
  .transform((value) => Number(value))
  .refine((value) => Number.isFinite(value), "Enter a valid amount")
  .refine((value) => value > 0, "Amount must be greater than 0")
  .refine((value) => Math.round(value * 100) === value * 100, "Amount can have up to 2 decimal places");

const dateSchema = z.preprocess(
  (value) => {
    if (typeof value === "string" && !value.trim()) {
      return undefined;
    }
    return value;
  },
  z
    .string()
    .refine((value) => !Number.isNaN(new Date(value).getTime()), "Enter a valid date")
    .optional()
);

export const loginSchema = z.object({
  email: z.string().trim().min(1, "Email cannot be empty").email("Enter a valid email"),
  password: z.string().trim().min(1, "Password cannot be empty")
});

export const registerSchema = z
  .object({
    username: z
      .string()
      .trim()
      .min(1, "Username cannot be empty")
      .min(4, "Username must be at least 4 characters")
      .max(32, "Username must be at most 32 characters"),
    email: z.string().trim().min(1, "Email cannot be empty").email("Enter a valid email"),
    password: z
      .string()
      .trim()
      .min(1, "Password cannot be empty")
      .min(6, "Password must be at least 6 characters")
      .max(32, "Password must be at most 32 characters"),
    confirm_password: z.string().trim().min(1, "Confirm password cannot be empty")
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"]
  });

export const budgetSchema = z.object({
  category_id: z.string().min(1, "Select a category"),
  amount: amountSchema,
  is_recurring: z.boolean()
});

export const transactionSchema = z.object({
  title: z
    .string()
    .trim()
    .min(1, "Enter a transaction title")
    .max(128, "Title must be at most 128 characters"),
  amount: amountSchema,
  transaction_type: z.enum(["income", "expense"]),
  category_id: z.string().min(1, "Select a category"),
  created_at: dateSchema,
  note: z.preprocess(
    (value) => {
      if (typeof value === "string" && !value.trim()) {
        return undefined;
      }
      return value;
    },
    z.string().max(128, "Note must be at most 128 characters").optional()
  )
});

export const profileSchema = z
  .object({
    username: z
      .string()
      .trim()
      .min(1, "Username cannot be empty")
      .min(4, "Username must be at least 4 characters")
      .max(32, "Username must be at most 32 characters"),
    currency: z.enum(["USD", "EUR", "UAH"], { message: "Select a valid currency" }),
    avatar: z
      .string()
      .min(5, "Avatar value is invalid")
      .max(200, "Avatar value is invalid")
  })
  .passthrough();

export const passwordChangeSchema = z
  .object({
    old_password: z.string().trim().min(1, "Enter your current password"),
    new_password: z
      .string()
      .trim()
      .min(1, "New password cannot be empty")
      .min(6, "Password must be at least 6 characters")
      .max(32, "Password must be at most 32 characters"),
    confirm_password: z.string().trim().min(1, "Confirm your new password")
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"]
  })
  .refine((data) => data.new_password !== data.old_password, {
    message: "New password cannot be the same as current password",
    path: ["new_password"]
  });

export const monobankTokenSchema = z.object({
  token: z.string().trim().min(1, "Token cannot be empty")
});

export const categorySchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Enter a category name")
    .max(128, "Category name must be at most 128 characters"),
  mcc_code: z
    .preprocess(
      (value) => {
        if (value === null) {
          return undefined;
        }
        if (typeof value === "string" && !value.trim()) {
          return undefined;
        }
        return value;
      },
      z.string().max(200, "MCC code must be at most 200 characters").optional()
    )
    .optional(),
  icon: z.preprocess(
    (value) => {
      if (value === null) {
        return undefined;
      }
      return value;
    },
    z.string().max(50, "Icon value is invalid").optional()
  )
});

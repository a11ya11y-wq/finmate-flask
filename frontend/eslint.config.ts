import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import pluginReact from "eslint-plugin-react";

export default tseslint.config(
  // 1. МАГІЯ 4: Глобальний ігнор. ESLint навіть не буде дивитися в ці файли.
  {
    ignores: [
      "dist/**", 
      "node_modules/**", 
      "eslint.config.ts", 
      "vite.config.ts", 
      "postcss.config.cjs", 
      "tailwind.config.*",
      "playwright.config.ts", // <-- ДОДАЛИ ЦЕ
      "playwright-report/**", // <-- Ігноруємо звіти тестів
      "test-results/**"       // <-- Ігноруємо результати тестів
    ]
  },
  
  // 2. Базові правила JS та TS
  js.configs.recommended,
  ...tseslint.configs.recommended,
  
  // 3. Базові правила React
  pluginReact.configs.flat.recommended,
  pluginReact.configs.flat['jsx-runtime'], 

  // 4. Наші кастомні налаштування
  {
    files: ["**/*.{js,mjs,cjs,ts,jsx,tsx}"],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    settings: {
      react: {
        // МАГІЯ 5: Жорстко вказуємо версію, щоб плагін не шукав її старими методами
        version: "18.2", 
      },
    },
    rules: {
      "react/prop-types": "off",
      "@typescript-eslint/no-unused-vars": "warn",
      "@typescript-eslint/no-explicit-any": "warn",
    },
  }
);
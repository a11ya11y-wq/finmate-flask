import { useAuthStore } from "../store/authStore";

/**
 * Словник символів валют.
 * Можна легко розширювати, додаючи нові коди (наприклад, PLN: "zł").
 */
const CURRENCY_SYMBOLS: Record<string, string> = {
  USD: "$",
  EUR: "€",
  UAH: "₴",
};

/**
 * Хук для роботи з валютою у проекті FinMate.
 * Надає поточний символ валюти та функцію для форматування чисел.
 */
export const useCurrency = () => {
  // Дістаємо дані користувача з глобального стору
  const { user } = useAuthStore();
  
  // Визначаємо код валюти. Якщо юзер не завантажений — дефолт UAH.
  const currencyCode = user?.currency || "UAH";
  
  // Отримуємо символ. Якщо код невідомий — повертаємо ₴.
  const currencySymbol = CURRENCY_SYMBOLS[currencyCode] || "₴";

  /**
   * Форматує число з символом валюти (наприклад, "100.00" -> "₴100.00").
   * @param amount - число або рядок з сумою.
   */
  const formatWithSymbol = (amount: number | string | null | undefined) => {
    if (amount === null || amount === undefined) return `${currencySymbol}0.00`;
    
    const numeric = typeof amount === "number" ? amount : Number(amount);
    
    // Перевірка на випадок, якщо прийшов невалідний рядок
    if (isNaN(numeric)) return `${currencySymbol}0.00`;

    return `${currencySymbol}${numeric.toFixed(2)}`;
  };

  return { 
    currencySymbol, 
    currencyCode, 
    formatWithSymbol 
  };
};
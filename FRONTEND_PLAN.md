# FinMate Frontend Plan (Vite + React + TypeScript)

Цей план базується на:
- API документації у `doc.md`
- референсах у `screenshots/`
- статичних ресурсах у `frontend/public/` та `frontend_by_copilot/public/`

## Чекліст етапів

1. [x] Архітектура і структура фронтенду
   - [x] Визначити структуру `src/` (app/pages/features/shared/assets)
   - [x] Вибрати state management: Zustand
   - [x] Вибрати UI підхід: Tailwind CSS + Shadcn UI
   - [x] Вибрати chart lib: Recharts

2. [x] Роутинг і сторінки
   - [x] Public: `login`, `register`
   - [x] Protected: `dashboard`, `transactions`, `budgets`, `profile`
   - [x] 404/empty states
   - [ ] Відповідність референсам зі `screenshots/`

3. [x] Auth flow
   - [x] Логін: `POST /api/v1/auth/login` (access token у пам’яті)
   - [x] Refresh: `POST /api/v1/auth/refresh` з `credentials: include`
   - [x] Logout: `POST /api/v1/auth/logout`
   - [x] Protected routes + реакція на 401 `Token expired`

4. [x] API layer
   - [x] Base URL + `credentials: include`
   - [x] Типізовані DTO для Auth/Profile/Transactions/Categories/Budgets/Dashboard
   - [x] Парсер помилок (business/validation/jwt/rate-limit)

5. [x] Компоненти і UI
   - [x] Layout: sidebar/topbar
   - [x] Форми: auth, profile, transactions, budgets, categories
   - [ ] Таблиці/листинги + pagination
   - [x] Графіки для dashboard
   - [x] Використання іконок/аватарок із `public/`

6. [ ] Інтеграція з бекендом
   - [ ] Реалізувати CRUD: categories, transactions, budgets
   - [x] Dashboard overview + history
   - [ ] Monobank sync + task status

7. [ ] Тестування
   - [x] Unit tests для utils/api layer
   - [ ] Component tests для критичних форм
   - [ ] E2E критичних флоу (login, create transaction)

8. [ ] Полірування
   - [ ] Error/empty/loading states
   - [ ] Адаптивність
   - [ ] Перевірка доступності

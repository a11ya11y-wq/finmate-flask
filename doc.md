
# FinMate Backend API (v1) — базова документація для фронтенду

> Цей документ описує поточну **фактичну** поведінку бекенду з папки `api-main`.
> Підходить як мінімально достатня документація, щоб зібрати фронтенд на React.


## 1) Базова інформація

**Base URL (локально):**

```
http://localhost:5000
```

**Префікс API:** ` /api/v1 `

**Формат даних:** JSON (`Content-Type: application/json`).

**CORS:** бекенд увімкнув `supports_credentials=True`, тому при запитах, які мають працювати з refresh-cookie, на фронті потрібно використовувати `credentials: 'include'`.

---

## 2) Авторизація (JWT + Refresh Cookie)

### 2.1 Access Token

- Після `POST /api/v1/auth/login` бекенд повертає `access_token` у JSON.
- Усі захищені ендпоінти потребують заголовок:

```
Authorization: Bearer <access_token>
```

- **TTL access token:** ~30 хв.

### 2.2 Refresh Token (cookie)

- Refresh токен НЕ повертається у JSON, він встановлюється як **HttpOnly cookie**:
  - cookie name: `finmate_refresh_token`
  - cookie path: `/api/v1/auth/refresh`
  - `SameSite=Lax`
  - `Secure=false` у dev (на проді має бути `true`)

Тому:
- логін/рефреш робіть з `credentials: 'include'`.
- `POST /api/v1/auth/refresh` читає refresh токен **лише з cookie**.

### 2.3 Рекомендований flow для React

1) `POST /auth/login` → зберегти `access_token` (memory / state / redux; не обов’язково localStorage).
2) Додавати `Authorization: Bearer ...` до всіх API calls.
3) Якщо отримали `401 Token expired` → викликати `POST /auth/refresh` (з `credentials: 'include'`) → отримати новий `access_token`.
4) Якщо refresh теж повернув `401` → робити logout на фронті й перекидати на /login.

---

## 3) Формат помилок

Бекенд має декілька форматів помилок (важливо для фронту):

### 3.1 Бізнес-помилки (кастомні)

**HTTP:** 400/401/403/404/409/429

```json
{
  "error": "...людське повідомлення..."
}
```

### 3.2 Помилки валідації (Pydantic)

**HTTP:** 422

```json
{
  "error": "Validation Error",
  "details": [
	"field: ...",
	"..."
  ]
}
```

### 3.3 JWT-помилки

**HTTP:** 401

```json
{ "error": "Missing token", "details": "..." }
```

або

```json
{ "error": "Invalid token", "details": "..." }
```

або

```json
{ "error": "Token expired", "message": "The token has expired. Please log in again." }
```

### 3.4 Rate limit

**HTTP:** 429

```json
{
  "error": "Too many requests",
  "message": "You have exceeded your request rate limit. Please try again later."
}
```

---

## 4) 🔌 API Endpoints (короткий перелік)

| Method            | Endpoint                             | Description                                  |
|:------------------|:-------------------------------------|:---------------------------------------------|
| **Auth**          |                                      |                                              |
| `POST`            | `/api/v1/auth/register`              | Register a new user                          |
| `POST`            | `/api/v1/auth/login`                 | Login user (returns Access token + sets Refresh cookie) |
| `POST`            | `/api/v1/auth/refresh`               | Rotate tokens using Refresh cookie           |
| `POST`            | `/api/v1/auth/logout`                | Logout user (revokes refresh + blacklists access) |
| **Transactions**  |                                      |                                              |
| `POST`            | `/api/v1/transactions/`              | Create transaction                           |
| `DELETE`          | `/api/v1/transactions/{id}`          | Delete transaction                           |
| `PUT`             | `/api/v1/transactions/{id}`          | Update transaction                           |
| `GET`             | `/api/v1/transactions/{id}`          | Get one transaction                          |
| **Categories**    |                                      |                                              |
| `POST`            | `/api/v1/categories/`                | Create category                              |
| `DELETE`          | `/api/v1/categories/{id}`            | Delete category                              |
| `PUT`             | `/api/v1/categories/{id}`            | Update category                              |
| `GET`             | `/api/v1/categories/all`             | Get all categories                           |
| **Budgets**       |                                      |                                              |
| `POST`            | `/api/v1/budgets/`                   | Create or update budget (by category)        |
| `DELETE`          | `/api/v1/budgets/{id}`               | Delete budget                                |
| `GET`             | `/api/v1/budgets/`                   | Get all budgets + stats                      |
| **Profile**       |                                      |                                              |
| `GET`             | `/api/v1/profile/me`                 | Get user profile                             |
| `PUT`             | `/api/v1/profile/me`                 | Update user profile                          |
| `DELETE`          | `/api/v1/profile/me`                 | Delete user account                          |
| `POST`            | `/api/v1/profile/change-password`    | Change password                              |
| `PUT`             | `/api/v1/profile/monobank`           | Add/Update monobank token                    |
| `DELETE`          | `/api/v1/profile/monobank`           | Remove monobank token                        |
| **Dashboard**     |                                      |                                              |
| `GET`             | `/api/v1/dashboard/`                 | Get dashboard overview data                  |
| `GET`             | `/api/v1/dashboard/history`          | Get transactions history (pagination)        |
| **Monobank Sync** |                                      |                                              |
| `POST`            | `/api/v1/monobank/sync-transactions` | Trigger manual sync of transactions (async)  |
| `GET`             | `/api/v1/monobank/tasks/{id}`        | Get status of sync task                      |

---

## 5) Моделі даних (що повертає бекенд)

### 5.1 User (профіль)

```json
{
  "id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "currency": "USD",
  "monobank_token_is_set": false,
  "avatar": "avatars/default/default.svg"
}
```

### 5.2 Category

```json
{
  "id": 1,
  "name": "Food",
  "user_id": 1,
  "icon": "bi-cup-hot-fill",
  "mcc_code": "5411, 5812"
}
```

### 5.3 Transaction

```json
{
  "id": 10,
  "title": "Groceries",
  "amount": 250.0,
  "transaction_type": "expense",
  "category_id": 1,
  "category_name": "Food",
  "category_icon": "bi-cup-hot-fill",
  "created_at": "2025-11-10T12:30:00+00:00",
  "note": "optional",
  "user_id": 1
}
```

### 5.4 Budget (base)

> `created_at` серіалізується JSON-провайдером Flask (зазвичай як string у форматі HTTP-date).

```json
{
  "id": 5,
  "amount": 1000.0,
  "category_name": "Food",
  "category_id": 1,
  "created_at": "Wed, 06 May 2026 10:20:30 GMT",
  "is_recurring": true
}
```

### 5.5 Budget (з розрахованою статистикою) — `GET /budgets/`

```json
[
  {
	"id": 5,
	"amount": 1000.0,
	"category_name": "Food",
	"category_id": 1,
	"created_at": "Wed, 06 May 2026 10:20:30 GMT",
	"is_recurring": true,
	"total_spent": 500.0,
	"percentage": 50.0,
	"remaining": 500.0,
	"deadline_info": "25 days left"
  }
]
```

---

## 6) Детально по ендпоінтах

Нижче: **Auth required** означає обов’язковий заголовок `Authorization: Bearer ...`.

### 6.1 Auth

#### `POST /api/v1/auth/register`

**Rate limit:** 5/min

**Body:**

```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "ValidPassword123",
  "confirm_password": "ValidPassword123"
}
```

**Response 201:** User (`to_dict()`).

**Можливі помилки:**
- 422 validation
- 409 якщо email або username уже існує

---

#### `POST /api/v1/auth/login`

**Rate limit:** 5/min

**Body:**

```json
{
  "email": "test@example.com",
  "password": "ValidPassword123",
  "remember_me": false
}
```

**Response 200:**

```json
{
  "access_token": "...",
  "message": "Login successful."
}
```

**Side-effect:** встановлює cookie `finmate_refresh_token` (HttpOnly).

**Можливі помилки:**
- 401 `Invalid email or password.`
- 422 validation

---

#### `POST /api/v1/auth/refresh`

**Rate limit:** 10/min

**Auth:** access token НЕ потрібен.

**Вимога:** cookie `finmate_refresh_token` (з `credentials: include`).

**Response 200:**

```json
{ "access_token": "..." }
```

**Side-effect:** оновлює cookie refresh-токена.

**Помилки:**
- 401 якщо cookie відсутня або сесія протухла (бекенд також видаляє cookie)

---

#### `POST /api/v1/auth/logout`

**Auth required:** так.

**Response 200:**

```json
{ "message": "Successfully logged out" }
```

**Side-effect:** очищає refresh-cookie. (Також намагається заблеклістити access token в Redis, якщо Redis доступний.)

---

### 6.2 Profile

#### `GET /api/v1/profile/me`

**Auth required:** так.

**Response 200:** User.

---

#### `PUT /api/v1/profile/me`

**Auth required:** так.

**Body (будь-які поля опціонально):**

```json
{
  "username": "New Name",
  "currency": "UAH",
  "avatar": "avatars/default/1.svg"
}
```

**Allowed currency:** `USD | EUR | UAH`

**Response 200:** User.

**Помилки:**
- 400 якщо не передано жодного валідного поля
- 400 якщо username зайнятий або avatar некоректний
- 422 validation

---

#### `DELETE /api/v1/profile/me`

**Auth required:** так.

**Response 204:** empty.

---

#### `POST /api/v1/profile/change-password`

**Auth required:** так.

**Body:**

```json
{
  "old_password": "OldPassword",
  "new_password": "NewPassword123",
  "confirm_password": "NewPassword123"
}
```

**Response 200:**

```json
{ "message": "Password updated successfully" }
```

**Помилки:**
- 401 якщо `old_password` невірний
- 422 validation (в т.ч. якщо new==old або confirm не збігається)

---

#### `PUT /api/v1/profile/monobank`

**Auth required:** так.

**Body:**

```json
{ "token": "<monobank_personal_token>" }
```

**Response 200:** User (з `monobank_token_is_set=true`).

---

#### `DELETE /api/v1/profile/monobank`

**Auth required:** так.

**Response 204:** empty.

---

### 6.3 Categories

#### `GET /api/v1/categories/all`

**Auth required:** так.

**Response 200:**

```json
{ "data": [/* Category[] */] }
```

---

#### `POST /api/v1/categories/`

**Auth required:** так.

**Body:**

```json
{
  "name": "Food",
  "mcc_code": "5411, 5812",
  "icon": "bi-cup-hot-fill"
}
```

`mcc_code` — необов’язковий string (можна список MCC через кому).

**Response 201:** Category.

**Обмеження/помилки:**
- 400 якщо `icon` не входить у allowlist
- 409 якщо категорія з таким `name` уже існує у цього користувача
- 400 якщо перевищено ліміт категорій (див. константи нижче)
- 422 validation

---

#### `PUT /api/v1/categories/{id}`

**Auth required:** так.

**Body (будь-які поля опціонально):**

```json
{
  "name": "New name",
  "mcc_code": "",
  "icon": "bi-tag-fill"
}
```

**Response 200:** Category.

**Обмеження:**
- якщо category = `Uncategorized`, не можна перейменувати на іншу назву
- 400 якщо body порожній (нема даних для оновлення)

---

#### `DELETE /api/v1/categories/{id}`

**Auth required:** так.

**Response 204:** empty.

**Обмеження:**
- не можна видалити `Uncategorized`
- не можна видалити категорію, якщо є транзакції
- не можна видалити категорію, якщо є бюджети

---

### 6.4 Transactions

#### `POST /api/v1/transactions/`

**Auth required:** так.

**Body:**

```json
{
  "amount": 250.00,
  "title": "Groceries",
  "transaction_type": "expense",
  "category_id": 1,
  "created_at": "2025-11-10T14:30:00+02:00",
  "note": "optional"
}
```

**Поля:**
- `transaction_type`: `income | expense`
- `created_at`: опціонально; підтримує date (`YYYY-MM-DD`) або datetime (`ISO 8601` з/без timezone)

**Response 201:** Transaction.

---

#### `GET /api/v1/transactions/{id}`

**Auth required:** так.

**Response 200:** Transaction.

---

#### `PUT /api/v1/transactions/{id}`

**Auth required:** так.

**Body:** будь-які поля з create, але всі опціональні.

**Response 200:** Transaction.

**Обмеження для банківських (синхронізованих) транзакцій:**
- якщо транзакція має `mono_id`, не можна змінювати `amount`, `transaction_type`, `created_at`.
- дозволено міняти тільки `category_id` та/або `note`.

---

#### `DELETE /api/v1/transactions/{id}`

**Auth required:** так.

**Response 204:** empty.

**Обмеження:**
- якщо транзакція синхронізована з банку (`mono_id` існує) — бекенд поверне 400.

---

### 6.5 Budgets

#### `GET /api/v1/budgets/`

**Auth required:** так.

**Response 200:** `BudgetWithStats[]` (див. приклад вище).

---

#### `POST /api/v1/budgets/`

**Auth required:** так.

> Цей ендпоінт працює як **upsert**: бюджет унікальний на `(user_id, category_id)`.

**Body:**

```json
{
  "amount": "1000",
  "category_id": 1,
  "is_recurring": true
}
```

**Response:**
- очікувано: `201` якщо створено, `200` якщо оновлено
- фактично зараз у коді повертається `201` завжди (навіть при оновленні) — врахувати на фронті.

**Помилки/обмеження:**
- 404 якщо `category_id` не належить користувачу або не існує
- 400 якщо перевищено ліміт бюджетів
- 422 validation

---

#### `DELETE /api/v1/budgets/{id}`

**Auth required:** так.

**Response 204:** empty.

---

### 6.6 Dashboard

#### `GET /api/v1/dashboard/?period=all|week|month`

**Auth required:** так.

**Query params:**
- `period`: `all` (default) | `week` | `month`

**Response 200:**

```json
{
  "stats": {
	"current_income": 1000.0,
	"current_expense": 250.0,
	"current_balance": 750.0,
	"income_percentage_change": 100.0,
	"expense_percentage_change": 100.0
  },
  "charts": {
	"expenses_by_category": { "labels": ["Food"], "data": [250.0] },
	"balance_dynamics": { "labels": ["2026-05-06"], "data": [750.0] }
  },
  "recent_transactions": {
	"data": [/* Transaction[] */],
	"total_page": 1
  }
}
```

---

#### `GET /api/v1/dashboard/history?period=all|week|month&page=1`

**Auth required:** так.

**Query params:**
- `period`: `all|week|month` (default `all`)
- `page`: number (default `1`)

**Response 200:**

```json
{
  "data": [/* Transaction[] */]
}
```

**Нотатки:**
- page size зашитий у бекенді: **15**.

---

### 6.7 Monobank

#### `POST /api/v1/monobank/sync-transactions`

**Auth required:** так.

**Rate limit:** 2/min

**Response 202:**

```json
{ "task_id": "<celery_task_id>" }
```

**Помилки:**
- 400 якщо у профілі немає monobank токена
- 403/429 якщо Monobank API повертає помилку/ліміти

---

#### `GET /api/v1/monobank/tasks/{task_id}`

**Auth required:** так.

**Response 200:**

```json
{
  "task_id": "...",
  "status": "PENDING",
  "result": null
}
```

Якщо `status=SUCCESS`:

```json
{
  "task_id": "...",
  "status": "SUCCESS",
  "result": {
	"added_count": 3,
	"message": "Successfully synchronized 3 transaction(s)"
  }
}
```

---

## 7) Корисні константи для UI

### 7.1 Period values для Dashboard

- `all | week | month`

### 7.2 Ліміти

- max categories per user: **10**
- max budgets per user: **5**

### 7.3 Allowlist іконок категорій

```text
bi-bag-fill, bi-cart-fill, bi-cup-hot-fill, bi-basket2-fill, bi-house-door-fill,
bi-lightning-fill, bi-wifi, bi-car-front-fill, bi-bus-front-fill, bi-fuel-pump-fill,
bi-controller, bi-film, bi-heart-pulse-fill, bi-mortarboard-fill, bi-piggy-bank-fill,
bi-wallet-fill, bi-gift-fill, bi-airplane-fill, bi-tag-fill, bi-question-circle-fill
```

### 7.4 Allowlist аватарок

```text
avatars/default/default.svg,
avatars/default/1.svg, avatars/default/2.svg, avatars/default/3.svg, avatars/default/4.svg,
avatars/default/5.svg, avatars/default/6.svg, avatars/default/7.svg, avatars/default/8.svg,
avatars/default/9.svg
```

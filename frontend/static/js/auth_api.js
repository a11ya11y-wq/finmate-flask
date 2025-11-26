// frontend/static/js/auth_api.js
// ❗️ ЦЕЙ ФАЙЛ МАЄ БУТИ ОДНИМ-ЄДИНИМ ДЖЕРЕЛОМ ЛОГІКИ ❗️

const API_ROOT = 'http://127.0.0.1:5000/api/v1';

// --- JWT Storage/Retrieval (Універсальні функції) ---

const getToken = () => localStorage.getItem('accessToken');
const setToken = (token) => localStorage.setItem('accessToken', token);

const getAuthHeaders = () => {
    const token = getToken();
    // ❗️ Увага: Хедери потрібні для захищених маршрутів,
    //    але цей об'єкт використовується скрізь. Це нормально.
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
};

// --- Main API Call: LOGIN ---

export const handleLogin = async (email, password) => {
    const response = await fetch(`${API_ROOT}/auth/login`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ email: email, password: password })
    });

    const data = await response.json();

    if (response.ok) {
        setToken(data.access_token);
        return true;
    } else {
        let errorText = "Login Failed due to server error.";

        // 1. Пріоритет: прості помилки (Invalid password)
        if (data.error && typeof data.error === 'string') {
            errorText = data.error;

        // 2. Якщо це складний словник помилок (Pydantic / ValueError)
        } else if (data.errors && typeof data.errors === 'object') {
            // Ми беремо першу помилку з першого поля (щоб відобразити внизу)
            const firstKey = Object.keys(data.errors)[0];
            errorText = `${firstKey}: ${data.errors[firstKey]}`;
        }

        // Кидаємо помилку, яку зловить блок try/catch на сторінці
        throw new Error(errorText);
    }
};

export const handleRegister = async (username, email, password, confirmPassword) => {
    // 1. Готуємо повний payload
    const payload = {
        username: username,
        email: email,
        password: password,
        confirm_password: confirmPassword
    };

    const response = await fetch(`${API_ROOT}/auth/register`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (response.ok) {
        // Успішна реєстрація - повертаємо true
        return true;
    } else {
        // 2. Використовуємо ту ж складну логіку обробки помилок
        let errorText = "Registration Failed.";

        if (data.error && typeof data.error === 'string') {
            errorText = data.error; // Simple errors: "Email already registered."
        } else if (data.errors && typeof data.errors === 'object') {
            // Pydantic errors (array of dicts).
            // Беремо першу помилку з першого поля (якщо це можливо)
            const firstKey = Object.keys(data.errors)[0];
            errorText = `${firstKey}: ${data.errors[firstKey]}`;
        }

        throw new Error(errorText);
    }
};

// --- Main API Call: DASHBOARD (Як приклад захищеного маршруту) ---

export const fetchDashboardData = async () => {
    const response = await fetch(`${API_ROOT}/dashboard/`, {
        method: 'GET',
        headers: getAuthHeaders(),
    });

    if (response.status === 401) {
        clearToken();
        window.location.href = '/login.html';
        throw new Error("Session expired.");
    }

    if (response.ok) {
        return response.json();
    } else {
        throw new Error(`Failed to fetch dashboard data: ${response.status}`);
    }
};
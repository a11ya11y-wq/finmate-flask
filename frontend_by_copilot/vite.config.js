import { defineConfig } from 'vite';
import { resolve } from 'path'; // 👈 1. Обов'язково додай цей імпорт

export default defineConfig({
  server: {
    port: 5173,
  },

  build: {
    rollupOptions: {
      input: {
        // Тут ми даємо імена сторінкам і вказуємо шлях до них
        main: resolve(__dirname, 'index.html'),
        dashboard: resolve(__dirname, 'dashboard.html'),
        profile: resolve(__dirname, 'profile.html'),
        login: resolve(__dirname, 'login.html'),
        register: resolve(__dirname, 'register.html'),
        budget: resolve(__dirname, 'budget.html'),
      },
    },
  },
});
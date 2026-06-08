DO $$ 
DECLARE 
    demo_user_id INTEGER;
    cat_food_id INTEGER;
    cat_salary_id INTEGER;
    cat_entertainment_id INTEGER;
    cat_electronics_id INTEGER;
    cat_transport_id INTEGER;
    cat_health_id INTEGER;
BEGIN
    -- 1. Знаходимо ID демо-юзера
    SELECT id INTO demo_user_id FROM users WHERE email = 'demo@test.com';

    -- Перериваємо виконання, якщо юзера не існує
    IF demo_user_id IS NULL THEN
        RAISE EXCEPTION 'Demo user demo@test.com not found in the database!';
    END IF;

    -- 2. Випалюємо старі дані у правильному порядку (від дочірніх до батьківських)
    DELETE FROM reports WHERE user_id = demo_user_id;
    DELETE FROM transactions WHERE user_id = demo_user_id;
    DELETE FROM budgets WHERE user_id = demo_user_id;
    DELETE FROM categories WHERE user_id = demo_user_id;

    -- 3. Встановлюємо початковий баланс (буфер безпеки) та скидаємо реальний баланс
    UPDATE users 
    SET initial_balance = 1500.00, 
        last_real_balance = 1500.00 
    WHERE id = demo_user_id;

    -- 4. Створюємо базові категорії і одразу забираємо їхні згенеровані ID
    INSERT INTO categories (name, user_id, icon) 
        VALUES ('Food', demo_user_id, 'bi-cart-fill') RETURNING id INTO cat_food_id;
    INSERT INTO categories (name, user_id, icon) 
        VALUES ('Salary', demo_user_id, 'bi-cash') RETURNING id INTO cat_salary_id;
    INSERT INTO categories (name, user_id, icon) 
        VALUES ('Entertainment', demo_user_id, 'bi-controller') RETURNING id INTO cat_entertainment_id;
    INSERT INTO categories (name, user_id, icon) 
        VALUES ('Electronics', demo_user_id, 'bi-laptop') RETURNING id INTO cat_electronics_id;
    INSERT INTO categories (name, user_id, icon) 
        VALUES ('Transport', demo_user_id, 'bi-car-front') RETURNING id INTO cat_transport_id;
    INSERT INTO categories (name, user_id, icon) 
        VALUES ('Health', demo_user_id, 'bi-heart-pulse') RETURNING id INTO cat_health_id;

    -- 5. Набиваємо історію ручних транзакцій (УВАГА: всі amount СУВОРО ДОДАТНІ!)
    INSERT INTO transactions (transaction_type, amount, title, note, created_at, category_id, user_id) VALUES
    -- Тиждень 1 (Початок місяця)
    ('income', 2500.00, 'Salary', 'Monthly salary', CURRENT_TIMESTAMP - INTERVAL '28 days', cat_salary_id, demo_user_id),
    ('expense', 180.00, 'Supermarket', 'Monthly stock up', CURRENT_TIMESTAMP - INTERVAL '27 days', cat_food_id, demo_user_id),
    ('expense', 25.50, 'Uber', 'Ride to work', CURRENT_TIMESTAMP - INTERVAL '26 days', cat_transport_id, demo_user_id),
    ('expense', 15.00, 'Netflix', 'Subscription', CURRENT_TIMESTAMP - INTERVAL '25 days', cat_entertainment_id, demo_user_id),
    
    -- Тиждень 2
    ('expense', 45.00, 'Pharmacy', 'Vitamins', CURRENT_TIMESTAMP - INTERVAL '22 days', cat_health_id, demo_user_id),
    ('expense', 12.00, 'Business Lunch', 'Cafe near office', CURRENT_TIMESTAMP - INTERVAL '20 days', cat_food_id, demo_user_id),
    ('expense', 35.00, 'Gas Station', 'Fuel', CURRENT_TIMESTAMP - INTERVAL '18 days', cat_transport_id, demo_user_id),
    
    -- Тиждень 3 (Непередбачувані витрати та фріланс)
    ('expense', 450.00, 'New Router', 'Rozetka - Upgrade', CURRENT_TIMESTAMP - INTERVAL '15 days', cat_electronics_id, demo_user_id),
    ('income', 350.00, 'Freelance', 'Upwork project', CURRENT_TIMESTAMP - INTERVAL '14 days', cat_salary_id, demo_user_id),
    ('expense', 60.00, 'Restaurant', 'Dinner with friends', CURRENT_TIMESTAMP - INTERVAL '12 days', cat_food_id, demo_user_id),
    ('expense', 20.00, 'Cinema', 'Movie night', CURRENT_TIMESTAMP - INTERVAL '10 days', cat_entertainment_id, demo_user_id),
    
    -- Тиждень 4 (Ближче до поточного дня)
    ('expense', 120.50, 'Groceries', 'Silpo', CURRENT_TIMESTAMP - INTERVAL '6 days', cat_food_id, demo_user_id),
    ('expense', 150.00, 'Dentist', 'Checkup', CURRENT_TIMESTAMP - INTERVAL '4 days', cat_health_id, demo_user_id),
    ('expense', 28.00, 'Taxi', 'Late night ride', CURRENT_TIMESTAMP - INTERVAL '2 days', cat_transport_id, demo_user_id),
    ('expense', 4.50, 'Coffee', 'Aroma Kava', CURRENT_TIMESTAMP - INTERVAL '2 hours', cat_food_id, demo_user_id);

    -- 6. Створюємо показові бюджети 
    INSERT INTO budgets (amount, category_id, user_id, is_recurring) VALUES
    (400.00, cat_food_id, demo_user_id, true),
    (100.00, cat_entertainment_id, demo_user_id, true),
    (100.00, cat_transport_id, demo_user_id, true);

END $$;
# Shadow Numbers – Telegram Bot

Аренда анонимных номеров Telegram. Клавиатура с кнопками и инлайн выбором.

## Запуск (Windows)
1. Установите Python 3.10+
2. Создайте и активируйте venv:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Установите зависимости:
   ```powershell
   pip install -r requirements.txt
   ```
4. Скопируйте `.env.example` в `.env` и вставьте токен бота:
   ```env
   BOT_TOKEN=xxxx:yyyy
   ```
5. Запустите бота:
   ```powershell
   py -m bot.main
   ```

## Функции
- Список номеров с пометками: 🔴 занято, 🟢 свободно
- Аренда на 1/3/6/12 месяцев
- Просмотр и продление аренды
- Автоматическое освобождение по истечении срока

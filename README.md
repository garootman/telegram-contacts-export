# Telegram Contacts Export

Экспорт контактов и чатов из Telegram с возможностью сверки по файлу никнеймов.

## Быстрый старт

### 1. Получение API ключей

1. Идите на https://my.telegram.org
2. Войдите с номером телефона
3. Перейдите в "API development tools"
4. Создайте приложение (любое название)
5. Скопируйте `api_id` и `api_hash`

### 2. Установка

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 3. Запуск

```bash
python export.py
```

## Использование

1. **Настройка** - введите `api_id`, `api_hash` и номер телефона
2. **Экспорт контактов** - сохраняет все контакты в CSV/JSON
3. **Экспорт чатов** - сохраняет диалоги с пользователями
4. **Экспорт всего** - контакты + чаты
5. **Сверка с nicknames.txt** - находит совпадения по никнеймам

## Файлы результатов

- `telegram_contacts.csv/json` - экспорт контактов
- `telegram_chats.csv/json` - экспорт чатов  
- `telegram_nicknames_matches.csv/json` - найденные совпадения

## Сверка никнеймов

Создайте файл `nicknames.txt` с никнеймами (по одному на строку без @ собачек):
```
nickname1
nickname2
username_example
```

Программа найдет совпадения среди ваших контактов и чатов.

## Примечания

- Сессия сохраняется в `anon.session`
- Прогресс сохраняется при прерывании
- Учетные данные можно сохранить для повторного использования
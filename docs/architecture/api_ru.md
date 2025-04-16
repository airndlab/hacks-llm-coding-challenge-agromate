# API-документация сервиса структурирования сообщений от агрономов

## Обзор API

API сервиса построено на REST-принципах и реализовано с использованием FastAPI. Оно предоставляет набор эндпоинтов для работы с сообщениями, отчетами, справочниками и управлением экспортом данных.

## Базовый URL

```
http://api.example.com/api/v1
```

## Формат данных

API использует формат JSON для запросов и ответов. Примеры запросов и ответов приведены ниже.

## Аутентификация

API использует JWT (JSON Web Tokens) для аутентификации. Большинство эндпоинтов требуют действительный токен, который должен быть передан в заголовке `Authorization`:

```
Authorization: Bearer {token}
```

## Эндпоинты

### Аутентификация

#### POST /auth/token

Получение JWT-токена для доступа к API.

**Запрос:**
```json
{
  "username": "admin",
  "password": "password"
}
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Сообщения

#### POST /messages

Создание нового сообщения (обычно вызывается Telegram-ботом).

**Запрос:**
```json
{
  "telegram_message_id": 123456,
  "chat_id": 9876543210,
  "user_id": 1,
  "text": "Отчет по полевым работам за 01.06.2023: Кукуруза, поле №5, сев 50%, площадь 120 га",
  "has_media": false,
  "created_at": "2023-06-01T20:15:30+03:00"
}
```

**Ответ:**
```json
{
  "id": 42,
  "telegram_message_id": 123456,
  "chat_id": 9876543210,
  "user_id": 1,
  "text": "Отчет по полевым работам за 01.06.2023: Кукуруза, поле №5, сев 50%, площадь 120 га",
  "has_media": false,
  "media_type": null,
  "media_file_id": null,
  "created_at": "2023-06-01T20:15:30+03:00",
  "processed": false,
  "processed_at": null,
  "status": "new"
}
```

#### GET /messages

Получение списка сообщений с возможностью фильтрации.

**Параметры запроса:**
- `user_id` (необязательно) - фильтр по ID пользователя
- `status` (необязательно) - фильтр по статусу (`new`, `processing`, `processed`, `error`)
- `start_date` (необязательно) - фильтр по дате начала
- `end_date` (необязательно) - фильтр по дате окончания
- `limit` (необязательно, по умолчанию 100) - ограничение количества результатов
- `offset` (необязательно, по умолчанию 0) - смещение для пагинации

**Ответ:**
```json
{
  "total": 150,
  "limit": 10,
  "offset": 0,
  "items": [
    {
      "id": 42,
      "telegram_message_id": 123456,
      "chat_id": 9876543210,
      "user_id": 1,
      "text": "Отчет по полевым работам за 01.06.2023: Кукуруза, поле №5, сев 50%, площадь 120 га",
      "has_media": false,
      "created_at": "2023-06-01T20:15:30+03:00",
      "processed": true,
      "processed_at": "2023-06-01T20:16:45+03:00",
      "status": "processed"
    },
    ...
  ]
}
```

#### GET /messages/{message_id}

Получение информации о конкретном сообщении.

**Ответ:**
```json
{
  "id": 42,
  "telegram_message_id": 123456,
  "chat_id": 9876543210,
  "user_id": 1,
  "text": "Отчет по полевым работам за 01.06.2023: Кукуруза, поле №5, сев 50%, площадь 120 га",
  "has_media": false,
  "media_type": null,
  "media_file_id": null,
  "created_at": "2023-06-01T20:15:30+03:00",
  "processed": true,
  "processed_at": "2023-06-01T20:16:45+03:00",
  "status": "processed",
  "report": {
    "id": 36,
    "report_date": "2023-06-01",
    "department_id": 2,
    "status": "processed",
    "field_works": [
      {
        "id": 18,
        "work_type_id": 3,
        "crop_id": 4,
        "field_id": 5,
        "area": 120.0,
        "completed_percentage": 50
      }
    ]
  }
}
```

#### POST /messages/{message_id}/process

Ручной запуск обработки сообщения.

**Ответ:**
```json
{
  "id": 42,
  "status": "processing",
  "message": "Сообщение поставлено в очередь на обработку"
}
```

### Отчеты

#### GET /reports

Получение списка отчетов с возможностью фильтрации.

**Параметры запроса:**
- `user_id` (необязательно) - фильтр по ID пользователя
- `department_id` (необязательно) - фильтр по ID подразделения
- `start_date` (необязательно) - фильтр по дате начала
- `end_date` (необязательно) - фильтр по дате окончания
- `status` (необязательно) - фильтр по статусу отчета
- `limit` (необязательно, по умолчанию 100) - ограничение количества результатов
- `offset` (необязательно, по умолчанию 0) - смещение для пагинации

**Ответ:**
```json
{
  "total": 85,
  "limit": 10,
  "offset": 0,
  "items": [
    {
      "id": 36,
      "message_id": 42,
      "user_id": 1,
      "report_date": "2023-06-01",
      "department_id": 2,
      "status": "processed",
      "created_at": "2023-06-01T20:16:45+03:00",
      "updated_at": "2023-06-01T20:16:45+03:00",
      "field_works": [
        {
          "id": 18,
          "work_type_id": 3,
          "work_type_name": "Сев",
          "crop_id": 4,
          "crop_name": "Кукуруза",
          "field_id": 5,
          "field_name": "Поле №5",
          "area": 120.0,
          "completed_percentage": 50
        }
      ]
    },
    ...
  ]
}
```

#### GET /reports/{report_id}

Получение информации о конкретном отчете.

**Ответ:**
```json
{
  "id": 36,
  "message_id": 42,
  "user_id": 1,
  "user": {
    "id": 1,
    "telegram_id": 123456789,
    "username": "agronom_ivanov",
    "first_name": "Иван",
    "last_name": "Иванов"
  },
  "report_date": "2023-06-01",
  "department_id": 2,
  "department": {
    "id": 2,
    "name": "Отделение №1",
    "code": "OTD1"
  },
  "status": "processed",
  "created_at": "2023-06-01T20:16:45+03:00",
  "updated_at": "2023-06-01T20:16:45+03:00",
  "field_works": [
    {
      "id": 18,
      "work_type_id": 3,
      "work_type_name": "Сев",
      "crop_id": 4,
      "crop_name": "Кукуруза",
      "field_id": 5,
      "field_name": "Поле №5",
      "area": 120.0,
      "completed_percentage": 50,
      "notes": null
    }
  ]
}
```

#### PUT /reports/{report_id}

Обновление информации об отчете (для ручной корректировки).

**Запрос:**
```json
{
  "department_id": 2,
  "report_date": "2023-06-01",
  "field_works": [
    {
      "id": 18,
      "work_type_id": 3,
      "crop_id": 4,
      "field_id": 5,
      "area": 125.0,
      "completed_percentage": 55,
      "notes": "Скорректированные данные"
    }
  ]
}
```

**Ответ:**
```json
{
  "id": 36,
  "message_id": 42,
  "user_id": 1,
  "report_date": "2023-06-01",
  "department_id": 2,
  "status": "processed",
  "created_at": "2023-06-01T20:16:45+03:00",
  "updated_at": "2023-06-01T20:25:30+03:00",
  "field_works": [
    {
      "id": 18,
      "work_type_id": 3,
      "crop_id": 4,
      "field_id": 5,
      "area": 125.0,
      "completed_percentage": 55,
      "notes": "Скорректированные данные"
    }
  ]
}
```

### Экспорт в Google Sheets

#### POST /exports

Создание нового экспорта в Google Sheets.

**Запрос:**
```json
{
  "export_date": "2023-06-01",
  "include_departments": [1, 2, 3]
}
```

**Ответ:**
```json
{
  "id": 12,
  "export_date": "2023-06-01",
  "status": "pending",
  "created_at": "2023-06-02T08:00:00+03:00",
  "updated_at": "2023-06-02T08:00:00+03:00"
}
```

#### GET /exports

Получение списка экспортов с возможностью фильтрации.

**Параметры запроса:**
- `start_date` (необязательно) - фильтр по дате начала
- `end_date` (необязательно) - фильтр по дате окончания
- `status` (необязательно) - фильтр по статусу
- `limit` (необязательно, по умолчанию 100) - ограничение количества результатов
- `offset` (необязательно, по умолчанию 0) - смещение для пагинации

**Ответ:**
```json
{
  "total": 30,
  "limit": 10,
  "offset": 0,
  "items": [
    {
      "id": 12,
      "export_date": "2023-06-01",
      "google_sheet_id": "1a2b3c4d5e6f7g8h9i0j",
      "google_sheet_url": "https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit",
      "status": "completed",
      "created_at": "2023-06-02T08:00:00+03:00",
      "updated_at": "2023-06-02T08:05:23+03:00"
    },
    ...
  ]
}
```

#### GET /exports/{export_id}

Получение информации о конкретном экспорте.

**Ответ:**
```json
{
  "id": 12,
  "export_date": "2023-06-01",
  "google_sheet_id": "1a2b3c4d5e6f7g8h9i0j",
  "google_sheet_url": "https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit",
  "status": "completed",
  "created_at": "2023-06-02T08:00:00+03:00",
  "updated_at": "2023-06-02T08:05:23+03:00",
  "notifications": [
    {
      "id": 25,
      "user_id": 2,
      "status": "sent",
      "sent_at": "2023-06-02T08:06:00+03:00"
    }
  ]
}
```

### Справочники

#### GET /dictionaries/departments

Получение списка подразделений.

**Ответ:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "ГК Прогресс Агро",
      "code": "MAIN",
      "parent_id": null,
      "children": [
        {
          "id": 2,
          "name": "Отделение №1",
          "code": "OTD1",
          "parent_id": 1
        },
        {
          "id": 3,
          "name": "Отделение №2",
          "code": "OTD2",
          "parent_id": 1
        }
      ]
    }
  ]
}
```

#### GET /dictionaries/crops

Получение списка сельскохозяйственных культур.

**Ответ:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Пшеница",
      "aliases": ["Озимая пшеница", "Яровая пшеница", "Пш."]
    },
    {
      "id": 2,
      "name": "Ячмень",
      "aliases": ["Озимый ячмень", "Яровой ячмень", "Яч."]
    },
    {
      "id": 3,
      "name": "Подсолнечник",
      "aliases": ["Подсолнух", "Подс."]
    },
    {
      "id": 4,
      "name": "Кукуруза",
      "aliases": ["Кук."]
    }
  ]
}
```

#### GET /dictionaries/work_types

Получение списка типов полевых работ.

**Ответ:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Вспашка",
      "aliases": ["Пахота", "Вспашка поля"]
    },
    {
      "id": 2,
      "name": "Боронование",
      "aliases": ["Боронов."]
    },
    {
      "id": 3,
      "name": "Сев",
      "aliases": ["Посев", "Сеяние"]
    },
    {
      "id": 4,
      "name": "Внесение удобрений",
      "aliases": ["Удобрение", "Подкормка"]
    },
    {
      "id": 5,
      "name": "Опрыскивание",
      "aliases": ["Обработка хим.", "Хим. обработка", "Обработка химикатами"]
    },
    {
      "id": 6,
      "name": "Уборка",
      "aliases": ["Сбор", "Жатва", "Уборка урожая"]
    }
  ]
}
```

#### GET /dictionaries/fields

Получение списка полей с возможностью фильтрации по подразделению.

**Параметры запроса:**
- `department_id` (необязательно) - фильтр по ID подразделения

**Ответ:**
```json
{
  "items": [
    {
      "id": 1,
      "name": "Поле №1",
      "code": "P1",
      "department_id": 2,
      "area": 150.5
    },
    {
      "id": 2,
      "name": "Поле №2",
      "code": "P2",
      "department_id": 2,
      "area": 200.0
    },
    {
      "id": 3,
      "name": "Поле №3",
      "code": "P3",
      "department_id": 2,
      "area": 180.75
    },
    {
      "id": 4,
      "name": "Поле №4",
      "code": "P4",
      "department_id": 2,
      "area": 95.3
    },
    {
      "id": 5,
      "name": "Поле №5",
      "code": "P5",
      "department_id": 2,
      "area": 120.0
    }
  ]
}
```

### Пользователи

#### GET /users

Получение списка пользователей с возможностью фильтрации.

**Параметры запроса:**
- `is_agronomist` (необязательно) - фильтр по роли агронома
- `is_admin` (необязательно) - фильтр по роли администратора
- `limit` (необязательно, по умолчанию 100) - ограничение количества результатов
- `offset` (необязательно, по умолчанию 0) - смещение для пагинации

**Ответ:**
```json
{
  "total": 25,
  "limit": 10,
  "offset": 0,
  "items": [
    {
      "id": 1,
      "telegram_id": 123456789,
      "username": "agronom_ivanov",
      "first_name": "Иван",
      "last_name": "Иванов",
      "is_agronomist": true,
      "is_admin": false
    },
    ...
  ]
}
```

#### GET /users/{user_id}

Получение информации о конкретном пользователе.

**Ответ:**
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "username": "agronom_ivanov",
  "first_name": "Иван",
  "last_name": "Иванов",
  "is_agronomist": true,
  "is_admin": false,
  "created_at": "2023-05-01T10:00:00+03:00",
  "updated_at": "2023-05-01T10:00:00+03:00"
}
```

#### PUT /users/{user_id}

Обновление информации о пользователе.

**Запрос:**
```json
{
  "first_name": "Иван",
  "last_name": "Иванов-Петров",
  "is_agronomist": true,
  "is_admin": true
}
```

**Ответ:**
```json
{
  "id": 1,
  "telegram_id": 123456789,
  "username": "agronom_ivanov",
  "first_name": "Иван",
  "last_name": "Иванов-Петров",
  "is_agronomist": true,
  "is_admin": true,
  "created_at": "2023-05-01T10:00:00+03:00",
  "updated_at": "2023-06-02T15:30:45+03:00"
}
```

## Коды состояния HTTP

- `200 OK` - запрос успешно обработан
- `201 Created` - ресурс успешно создан
- `400 Bad Request` - ошибка в запросе клиента
- `401 Unauthorized` - не авторизованный запрос
- `403 Forbidden` - доступ запрещен
- `404 Not Found` - ресурс не найден
- `422 Unprocessable Entity` - ошибка валидации данных
- `500 Internal Server Error` - внутренняя ошибка сервера

## Обработка ошибок

В случае ошибки API возвращает объект с описанием ошибки:

```json
{
  "detail": "Ресурс не найден",
  "status_code": 404,
  "type": "not_found"
}
```

Или в случае ошибок валидации:

```json
{
  "detail": [
    {
      "loc": ["body", "report_date"],
      "msg": "Поле обязательно к заполнению",
      "type": "value_error.missing"
    }
  ],
  "status_code": 422,
  "type": "validation_error"
}
```

## Webhooks

Для получения уведомлений о событиях в системе можно настроить webhooks.

### POST /webhooks

Создание нового webhook для получения уведомлений.

**Запрос:**
```json
{
  "url": "https://example.com/webhook-receiver",
  "events": ["message.created", "report.processed", "export.completed"],
  "secret": "your-secret-token"
}
```

**Ответ:**
```json
{
  "id": 5,
  "url": "https://example.com/webhook-receiver",
  "events": ["message.created", "report.processed", "export.completed"],
  "created_at": "2023-06-02T12:00:00+03:00"
}
```

### GET /webhooks

Получение списка настроенных webhooks.

**Ответ:**
```json
{
  "items": [
    {
      "id": 5,
      "url": "https://example.com/webhook-receiver",
      "events": ["message.created", "report.processed", "export.completed"],
      "created_at": "2023-06-02T12:00:00+03:00"
    }
  ]
}
```

### DELETE /webhooks/{webhook_id}

Удаление webhook.

**Ответ:** HTTP 204 No Content

## События webhooks

Примеры событий, отправляемых по webhook:

### message.created

```json
{
  "event": "message.created",
  "data": {
    "id": 42,
    "telegram_message_id": 123456,
    "chat_id": 9876543210,
    "user_id": 1,
    "text": "Отчет по полевым работам за 01.06.2023: Кукуруза, поле №5, сев 50%, площадь 120 га",
    "created_at": "2023-06-01T20:15:30+03:00"
  },
  "timestamp": "2023-06-01T20:15:31+03:00"
}
```

### report.processed

```json
{
  "event": "report.processed",
  "data": {
    "id": 36,
    "message_id": 42,
    "user_id": 1,
    "report_date": "2023-06-01",
    "department_id": 2,
    "status": "processed"
  },
  "timestamp": "2023-06-01T20:16:45+03:00"
}
```

### export.completed

```json
{
  "event": "export.completed",
  "data": {
    "id": 12,
    "export_date": "2023-06-01",
    "google_sheet_id": "1a2b3c4d5e6f7g8h9i0j",
    "google_sheet_url": "https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit"
  },
  "timestamp": "2023-06-02T08:05:23+03:00"
}
``` 
# API проекта АгроМейт

Данный раздел описывает API проекта, включая методы для интеграции с другими системами.

## Обзор API

API проекта АгроМейт предоставляет возможность программного взаимодействия с системой для автоматизации получения данных от агрономов, их обработки и структурирования.

## Базовый URL

```
https://api.agromate.example.com/v1
```

## Аутентификация

API использует аутентификацию на основе JWT токенов.

```http
Authorization: Bearer YOUR_JWT_TOKEN
```

## Конечные точки API

### Управление источниками данных

#### Получение списка подключенных чатов

```http
GET /sources/whatsapp
```

**Ответ:**

```json
{
  "success": true,
  "data": [
    {
      "id": "chat123",
      "name": "Агрономы региона A",
      "status": "active",
      "lastSync": "2025-04-10T15:30:00Z"
    },
    {
      "id": "chat456",
      "name": "Агрономы региона Б",
      "status": "inactive",
      "lastSync": null
    }
  ]
}
```

#### Подключение нового чата

```http
POST /sources/whatsapp
Content-Type: application/json

{
  "chatId": "chat789",
  "name": "Агрономы региона В"
}
```

**Ответ:**

```json
{
  "success": true,
  "data": {
    "id": "chat789",
    "name": "Агрономы региона В",
    "status": "pending",
    "lastSync": null
  }
}
```

### Управление данными

#### Получение обработанных сообщений

```http
GET /messages?source=chat123&from=2025-04-09&to=2025-04-10
```

**Ответ:**

```json
{
  "success": true,
  "data": [
    {
      "id": "msg123",
      "source": "chat123",
      "timestamp": "2025-04-09T18:45:00Z",
      "type": "text",
      "processed": true,
      "content": {
        "raw": "Пшеница поле 5, обработано 120 га",
        "structured": {
          "crop": "пшеница",
          "field": "5",
          "area": 120,
          "unit": "га",
          "action": "обработка"
        }
      }
    },
    {
      "id": "msg124",
      "source": "chat123",
      "timestamp": "2025-04-09T19:30:00Z",
      "type": "image",
      "processed": true,
      "content": {
        "raw": "https://storage.agromate.example.com/images/abc123.jpg",
        "structured": {
          "crop": "кукуруза",
          "field": "7",
          "area": 85,
          "unit": "га",
          "action": "полив"
        }
      }
    }
  ]
}
```

#### Ручное добавление данных

```http
POST /messages
Content-Type: application/json

{
  "source": "manual",
  "timestamp": "2025-04-10T14:00:00Z",
  "content": {
    "crop": "подсолнечник",
    "field": "12",
    "area": 200,
    "unit": "га",
    "action": "сев"
  }
}
```

**Ответ:**

```json
{
  "success": true,
  "data": {
    "id": "msg125",
    "source": "manual",
    "timestamp": "2025-04-10T14:00:00Z",
    "type": "text",
    "processed": true,
    "content": {
      "raw": null,
      "structured": {
        "crop": "подсолнечник",
        "field": "12",
        "area": 200,
        "unit": "га",
        "action": "сев"
      }
    }
  }
}
```

### Управление отчетами

#### Получение списка доступных отчетов

```http
GET /reports
```

**Ответ:**

```json
{
  "success": true,
  "data": [
    {
      "id": "report123",
      "name": "Ежедневный отчет по культурам",
      "type": "excel",
      "lastGenerated": "2025-04-10T06:00:00Z",
      "url": "https://storage.agromate.example.com/reports/abc123.xlsx"
    },
    {
      "id": "report456",
      "name": "Еженедельный отчет по полям",
      "type": "excel",
      "lastGenerated": "2025-04-07T06:00:00Z",
      "url": "https://storage.agromate.example.com/reports/def456.xlsx"
    }
  ]
}
```

#### Генерация отчета

```http
POST /reports/generate
Content-Type: application/json

{
  "templateId": "template123",
  "filters": {
    "from": "2025-04-09",
    "to": "2025-04-10",
    "crops": ["пшеница", "кукуруза"],
    "actions": ["обработка", "полив"]
  }
}
```

**Ответ:**

```json
{
  "success": true,
  "data": {
    "id": "report789",
    "name": "Отчет по пшенице и кукурузе (09.04-10.04)",
    "type": "excel",
    "status": "generating",
    "estimatedCompletion": "2025-04-10T15:35:00Z"
  }
}
```

## Коды ответов

- `200 OK` - запрос выполнен успешно
- `201 Created` - ресурс успешно создан
- `400 Bad Request` - ошибка в запросе
- `401 Unauthorized` - требуется аутентификация
- `403 Forbidden` - недостаточно прав
- `404 Not Found` - ресурс не найден
- `500 Internal Server Error` - внутренняя ошибка сервера

## Обработка ошибок

В случае ошибки API возвращает следующую структуру:

```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Запрашиваемый ресурс не найден",
    "details": {
      "resourceType": "report",
      "resourceId": "report999"
    }
  }
}
```

## Ограничения

- Максимальное количество запросов: 100 запросов в минуту
- Максимальный размер загружаемого файла: 10 МБ

## Примеры использования

### Пример на Python

```python
import requests
import json

API_BASE_URL = "https://api.agromate.example.com/v1"
API_TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Получение списка отчетов
response = requests.get(f"{API_BASE_URL}/reports", headers=headers)
reports = response.json()

print(json.dumps(reports, indent=2))
```

### Пример на JavaScript

```javascript
const API_BASE_URL = "https://api.agromate.example.com/v1";
const API_TOKEN = "your_jwt_token";

const headers = {
  "Authorization": `Bearer ${API_TOKEN}`,
  "Content-Type": "application/json"
};

// Получение списка отчетов
fetch(`${API_BASE_URL}/reports`, { headers })
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));
```

## Версионирование

API следует семантическому версионированию. Текущая версия: v1.

## Дополнительная документация

*Будет добавлена ссылка на полную документацию OpenAPI/Swagger* 
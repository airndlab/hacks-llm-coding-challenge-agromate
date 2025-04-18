# Требования к проекту АгроМейт

## Обзор бизнес-задачи

ГК «Прогресс Агро» нуждается в автоматизации процесса сбора и обработки полевых отчетов от агрономов. В настоящее время отчетность предоставляется через Telegram в неструктурированном виде, что требует ручной обработки главным агрономом и занимает значительное время.

## Функциональные требования

1. **Извлечение данных из Telegram**
   - Система должна подключаться к указанному чату Telegram
   - Поддержка различных форматов данных: текстовые сообщения, изображения
   - Сохранение извлеченных данных в указанное хранилище (локально или в облаке)

2. **Идентификация и классификация данных**
   - Распознавание текста на изображениях (OCR)
   - Классификация информации по типам (культуры, площади, проведенные мероприятия и т.д.)
   - Извлечение ключевой информации из текста свободного формата

3. **Заполнение таблиц и экспорт в Google Sheets**
   - Автоматическое внесение обработанных данных в соответствующие таблицы
   - Экспорт данных в Google Drive как Google Sheet файлы
   - Поддержка различных шаблонов таблиц в зависимости от типа данных
   - Валидация данных перед внесением

4. **Пользовательский интерфейс**
   - Настройка источника данных (чата Telegram)
   - Конфигурация шаблонов выходных таблиц
   - Настройка интеграции с Google Drive
   - Просмотр и подтверждение результатов обработки
   - Возможность ручной корректировки результатов

## Нефункциональные требования

1. **Производительность**
   - Обработка сообщений в реальном времени или с минимальной задержкой
   - Завершение полного цикла обработки за ночь (до утра следующего дня)

2. **Надежность**
   - Отказоустойчивость при некорректных входных данных
   - Логирование ошибок и предупреждений
   - Сохранение промежуточных результатов обработки

3. **Безопасность**
   - Защита доступа к исходным данным и результатам обработки
   - Соблюдение требований по обработке персональных данных
   - Безопасное хранение учетных данных для доступа к Google Drive

4. **Масштабируемость**
   - Возможность обработки возрастающего объема сообщений
   - Поддержка подключения к нескольким чатам

5. **Интеграция**
   - Возможность интеграции с существующими информационными системами
   - API для внешнего доступа к результатам обработки
   - Совместимость с Google Workspace

## Ограничения

- Использование технологий искусственного интеллекта для обработки данных
- Соблюдение лицензионных ограничений используемых компонентов

## Метрики успеха

- Точность классификации данных не менее 95%
- Снижение времени на обработку данных на 80% по сравнению с ручной обработкой
- Полная автоматизация процесса без необходимости ручного вмешательства в стандартных случаях

## Критерии приемки

- Система успешно извлекает данные из чата Telegram
- Различные форматы сообщений корректно идентифицируются и классифицируются
- Данные корректно заносятся в таблицы и экспортируются в Google Sheets
- Пользовательский интерфейс обеспечивает все необходимые функции управления процессом 
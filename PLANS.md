# PLANS

## Status

- Milestone 0. Preparation — completed
- Milestone 1. Reverse Engineering Documents — completed
- Milestone 2. Deterministic Mapping And Rendering — completed
- Milestone 3. Final Packaging — completed
- Milestone 4. Publication And Submission Packaging — completed

## Milestone 0. Preparation

- Распаковать материалы внутрь репозитория.
- Поднять Python-проект, зависимости, базовый CLI и тестовый контур.
- Добавить planning-артефакты и структуру директорий.
- Валидация: `uv sync --extra dev`, `uv run homelio inspect-placeholders ...`, `uv run pytest`.

## Milestone 1. Reverse Engineering Documents

- Сравнить 3 пары `шаблон -> пример`.
- Извлечь и каталогизировать плейсхолдеры, повторяющиеся блоки и табличные секции.
- Зафиксировать для каждого поля источник: `PROFILE`, `TENDER`, `CALC`, `SYSTEM`, `UNKNOWN`.
- Валидация: заметка с покрытием плейсхолдеров и отсутствующих полей в `notes`.

## Milestone 2. Deterministic Mapping And Rendering

- Описать маппинги по документам в `config/mappings`.
- Реализовать загрузку входных данных и рендеринг DOCX без ручной постобработки.
- Предусмотреть явное поведение для пустых значений.
- Валидация: генерация всех 3 документов на тестовом наборе.

## Milestone 3. Final Packaging

- Добавить архитектурную записку на 1-2 страницы.
- Проверить README, структуру выходных файлов и воспроизводимость запуска.
- Валидация: прогон финальной команды генерации и smoke-проверка output.

### Milestone 3 completion notes

- `notes/architecture.md` добавлен и фиксирует устройство решения, границы и пути масштабирования.
- `README.md` приведен к формату финальной инструкции сдачи с шагами запуска и проверки.
- `output/` подтвержден как актуальный после прогона `homelio generate`: присутствуют 3 DOCX с обновленным временем модификации.
- Финальная валидация пройдена: `uv run pytest`, `uv run ruff check`, `uv run homelio generate --document-date 2026-03-26 --outgoing-number "№2603/1"`.

## Milestone 4. Publication And Submission Packaging

- Инициализировать git-репозиторий и зафиксировать финальный snapshot проекта.
- Создать публичный GitHub-репозиторий и запушить текущую ветку.
- Собрать чистый ZIP-архив проекта для отправки.
- Валидация: `git status --short`, успешный `git push`, доступный публичный URL репозитория, проверка содержимого ZIP.

### Milestone 4 completion notes

- Инициализирован git-репозиторий с веткой `main`.
- Создан публичный репозиторий `https://github.com/Humanji7/homelio`.
- Ветка `main` запушена в `origin` и отслеживается удаленно.
- Подготовлен `SUBMISSION.md` с публичной ссылкой и коротким текстом отправки.

## Risks

- Часть DOCX может требовать не просто замены плейсхолдеров, а работы с таблицами и форматированием.
- В разных документах один и тот же смысловой блок может называться по-разному, поэтому маппинг лучше держать явным.
- Бонус с извлечением `tender.json` из входящего документа стоит делать только после базового детерминированного контура.

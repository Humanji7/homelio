# Submission

## What to send

- Public repository URL: `https://github.com/Humanji7/homelio`
- Optional ZIP archive: `../homelio_submission.zip`

## Repository contents

- Source code for the local CLI generator
- `README.md` with setup, run, and verification steps
- Generated DOCX files in `output/`
- Notes in `notes/`, including architecture rationale

## Local verification

```bash
uv sync --extra dev
uv run pytest
uv run ruff check
uv run homelio generate --document-date 2026-03-26 --outgoing-number "№2603/1"
```

## Short submission text

Здравствуйте! Отправляю выполненное тестовое задание.

В репозитории находятся:
- локальное решение для генерации 3 DOCX по тестовым JSON;
- инструкция запуска и проверки в `README.md`;
- итоговые сгенерированные документы в `output/`;
- краткая архитектурная записка в `notes/architecture.md`.

Ссылка на репозиторий: `https://github.com/Humanji7/homelio`

#!/usr/bin/env python3
"""Сборка zcode-pipeline-bundle.md из фактических файлов живой установки ZCode.

Источник правды: ~/.zcode/agents/*.md, ~/.zcode/commands/init-project.md,
~/.zcode/AGENTS.md. Бандл — артефакт сборки: изменил агентов — пересобери.

Запуск: python3 scripts/build_bundle.py   (из корня репозитория pipeline)
Выход:  ./zcode-pipeline-bundle.md (перезаписывается)

Правила внесения изменений в систему:
1. Правки вносятся ТОЛЬКО в живые файлы ~/.zcode/agents/… (не в бандл!).
2. Пересобери бандл этим скриптом.
3. Закоммить с записью в CHANGELOG.md.
"""
import os
import sys

HOME = os.path.expanduser("~")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

AGENTS = ["briefer", "architect", "tech-lead", "tech-writer", "developer",
          "security-review", "goal-review", "code-review", "qa", "manager",
          "summarizer", "initializer"]

ROLES = {
    "briefer": "Первый этап: превращает любой запрос в финальный бриф (интерактивные раунды вопросов).",
    "architect": "Архитектура решения + обязательные рекомендации всем следующим агентам.",
    "tech-lead": "Декомпозиция в задачи (файлы задач НЕ создаёт) + консультант при эскалациях.",
    "tech-writer": "Создаёт .ai/tasks/{epic}/{NN}-{name}-{date}.md по шаблону + INDEX.md.",
    "developer": "Реализация задачи строго по файлу: Phase 0, минимальный дифф, честная верификация, отчёт.",
    "security-review": "Ревью 1/3: безопасность; вердикт PASS | PASS_WITH_WARNINGS | FAIL | NEEDS_MORE_CONTEXT.",
    "goal-review": "Ревью 2/3: соответствие брифу и критериям приёмки; GOAL_MET | GOAL_PARTIALLY_MET | GOAL_NOT_MET | NEEDS_CONTEXT.",
    "code-review": "Ревью 3/3: качество кода; APPROVE | REQUEST_CHANGES | NEEDS_DISCUSSION.",
    "qa": "После одобрения всех трёх ревью: ревью тестов, свои тесты, QUALITY_PASSED | QUALITY_FAILED | BLOCKED.",
    "manager": "Финальная приёмка: сверка начальных и конечных данных; ACCEPTED | REJECTED + этап возврата.",
    "summarizer": "После ACCEPTED: обновляет базу знаний .ai/docs/ (вики, хроники, INDEX, чек-лист).",
    "initializer": "Этап 0: инициализация проекта — стек, .ai/guides/ с лучшими практиками, AGENTS.md.",
}

# Строка личных правил в глобальном AGENTS.md — параметризуется в бандле
PERSONAL_LINE = "Меня зовут Михаил, я твой руководитель. Всегда общайся со мной на русском языке."


def wrap(content: str) -> str:
    return "`````markdown\n" + content.rstrip("\n") + "\n`````"


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def build() -> str:
    parts = []
    parts.append("""# ZCode Development Pipeline — Bundle
**Версия:** 1.0 | **Дата сборки:** 2026-11-02 | **Целевая среда:** ZCode (чистая установка)

## Что это

Полный снимок конвейера разработки на субагентах: 12 агентов, 1 slash-команда, опциональный глобальный AGENTS.md.
Документ предназначен для чтения ГЛАВНЫМ АГЕНТОМ чистого экземпляра ZCode.

## Инструкция главному агенту (установка)

1. Прочитай документ целиком.
2. Создай каждый файл по указанному пути с содержимым соответствующего блока — ДОСЛОВНО, включая frontmatter, без «улучшений» и пропусков. Директории создавай при необходимости.
3. Секция «Глобальный AGENTS.md (персональный, опционально)» — единственная, требующая решения пользователя: перед её созданием спроси у пользователя обращение (имя/роль или «без обращения») и язык (русский/english/другой/«не указывать»); если пользователь отказывается от глобальных правил — пропусти файл (инициализатор спросит то же самое при первом `/init-project`).
4. После создания всех файлов НЕ перезаписывай их повторно и не редактируй. Сообщи пользователю: «Перезапустите сессию ZCode — агенты и команда зарегистрируются на старте».
5. После перезапуска проверка: в списке агентов должны появиться все 12 (briefer, architect, tech-lead, tech-writer, developer, security-review, goal-review, code-review, qa, manager, summarizer, initializer); команда `/init-project` — в списке команд.

## Как работает конвейер (справка)

Инициализатор (этап 0, по запросу) → Брифер → Архитектор → Техлид → Техписатель → Исполнитель → Ревью (Security → Goal → Code) → QA → Менеджер (ACCEPTED/REJECTED) → Саммарйзер (база знаний).

Правила ведения конвейера (для главного агента-координатора):
- Каждый следующий этап не стартует без артефакта предыдущего (это зашито в промптах агентов).
- Эскалации субагентов (маркер `!!! ESCALATION !!!`) маршрутизируй Техлиду-консультанту; помощь передавай обратно тому, кто эскалировал; максимум одна эскалация на задачу.
- Все находки ревью (включая MINOR/NIT) возвращаются Исполнителю; цикл повторяется до полного одобрения всех трёх гейтов; только потом QA, затем Менеджер.
- Коммит — только после ACCEPTED от Менеджера (коммитит координатор, не субагенты).
- Вопросы пользователю: субагенты возвращают структурированные блоки «## Вопросы пользователю» — рендерь их интерактивно (AskUserQuestion; мультивыбор где помечено; свободный ввод доступен всегда).
- Артефакты: `.ai/briefs/`, `.ai/architecture/`, `.ai/decomposition/`, `.ai/tasks/{epic}/` (+INDEX.md), `.ai/reviews/`, `.ai/qa/`, `.ai/docs/` (база знаний: wiki/, epics/, INDEX.md, manual-checklist.md), `.ai/guides/` (от инициализатора).
- Статусы задач: created → in_progress → implemented → reviewed → tested → accepted | rejected (фиксирует координатор).
- Воркспейс может не быть git-репозиторием; глобальный gitignore пользователя может скрывать `.ai` и `AGENTS.md` — при коммитах используй `git add -f` для артефактов конвейера.

## Состав

| # | Агент | Роль |
|---|---|---|""")
    for i, a in enumerate(AGENTS, 1):
        parts.append(f"| {i} | `{a}` | {ROLES[a]} |")
    parts.append("| 13 | команда `/init-project` | Запуск инициализатора. |")
    parts.append("| 14 | `~/.zcode/AGENTS.md` | Персональные глобальные правила (опционально). |")

    parts.append("\n## Файлы агентов\n")
    for a in AGENTS:
        content = read(f"{HOME}/.zcode/agents/{a}.md")
        parts.append(f"### `~/.zcode/agents/{a}.md`\n{ROLES[a]}\n\n{wrap(content)}\n")

    cmd = read(f"{HOME}/.zcode/commands/init-project.md")
    parts.append(f"## Команда\n### `~/.zcode/commands/init-project.md`\nЗапуск инициализатора проекта.\n\n{wrap(cmd)}\n")

    agents_md = read(f"{HOME}/.zcode/AGENTS.md")
    if PERSONAL_LINE not in agents_md:
        sys.exit("ОШИБКА: строка персонализации не найдена в ~/.zcode/AGENTS.md — "
                 "обнови PERSONAL_LINE в этом скрипте под текущую формулировку.")
    agents_md_param = agents_md.replace(PERSONAL_LINE, "{ОБРАЩЕНИЕ}\n{ЯЗЫК_ОБЩЕНИЯ}")
    parts.append("""## Глобальный AGENTS.md (персональный, опционально)

Сначала спроси пользователя (если ещё не спрашивал): обращение — «Имя + роль» (свободный ввод «Имя, роль» → `Меня зовут {имя}, я твой {роль}.`), «Только имя» (`Меня зовут {имя}.`) или «Без обращения» (строка исключается); язык — русский (`Всегда общайся со мной на русском языке.`), english (`Always communicate with me in English.`), другой (свободный ввод) или «Не указывать» (строка исключается). Затем создай файл с подставленными строками. Остатков `{ОБРАЩЕНИЕ}`/`{ЯЗЫК_ОБЩЕНИЯ}` в готовом файле быть не должно. Если пользователь отказался — пропусти файл целиком.

### `~/.zcode/AGENTS.md`

""" + wrap(agents_md_param))
    return "\n".join(parts)


def main() -> None:
    bundle = build()
    out = os.path.join(HERE, "zcode-pipeline-bundle.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(bundle)
    wrappers = bundle.count("`````markdown")
    expected = len(AGENTS) + 2
    personal_leak = "Михаил" in bundle
    lines = bundle.count("\n") + 1
    print(f"бандл: {out}")
    print(f"строк: {lines} | байт: {os.path.getsize(out)} | обёрток: {wrappers}/{expected}")
    print(f"персональные данные в бандле: {'НАЙДЕНЫ — ОШИБКА' if personal_leak else 'отсутствуют (ok)'}")
    if wrappers != expected or personal_leak:
        sys.exit("СБОЙ СБОРКИ — проверь исходники.")


if __name__ == "__main__":
    main()

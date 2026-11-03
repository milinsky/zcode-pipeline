#!/usr/bin/env python3
"""Сборка zcode-pipeline-bundle.md из файлов ЭТОГО репозитория (самодостаточен).

Источник правды — репозиторий плагина: zcode-pipeline/{agents,commands,skills,assets}.
Живая установка ~/.zcode при сборке не требуется.

Запуск: python3 scripts/build_bundle.py   (из корня репозитория)
Выход:  ./zcode-pipeline-bundle.md (перезаписывается)

Правила внесения изменений в систему:
1. Правки вносятся ТОЛЬКО в файлы этого репозитория (agents/, commands/, skills/, assets/).
2. Обнови version в .zcode-plugin/plugin.json.
3. Пересобери бандл: python3 scripts/build_bundle.py (падает при утечке
   персональных данных или сломанной разметке — не обходить).
4. Закоммить с записью в CHANGELOG.md; для вех — тег; push --follow-tags.
5. Пользователь обновляет плагин в Settings → Plugin Management.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENTS = ["briefer", "architect", "tech-lead", "tech-writer", "developer",
          "security-review", "goal-review", "code-review", "qa", "manager",
          "summarizer", "initializer", "analyst"]

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
    "analyst": "Аналитический трек: синтез экспертных аудитов с верификацией по коду → REPORT.md + мостик в конвейер.",
}


AGENT_CHECKS = {
    "briefer": ["Раунд вопросов", "Финальный бриф", "Трек:"],
    "architect": ["Рекомендации следующим агентам", "Аналитический трек"],
    "tech-lead": ["декомпоз", "Решение Техлида", "feasibility"],
    "tech-writer": ["Phase 0", "Применимые правила", "Критерии приёмки"],
    "developer": ["Phase 0", "implemented", "MUST NOT DO"],
    "security-review": ["PASS_WITH_WARNINGS", "Аналитический трек", "NEEDS_MORE_CONTEXT"],
    "goal-review": ["GOAL_MET", "GOAL_PARTIALLY_MET", "трассируем"],
    "code-review": ["REQUEST_CHANGES", "NEEDS_DISCUSSION", "Аналитический трек"],
    "qa": ["QUALITY_PASSED", "QUALITY_FAILED"],
    "manager": ["ACCEPTED", "REJECTED", "Этап возврата"],
    "summarizer": ["База знаний обновлена", "Уроки и правила-кандидаты", "manual-checklist"],
    "initializer": ["source=file|embedded", "Персонализация"],
    "analyst": ["[verified]", "[hypothesis]", "Мостик"],
}
REQUIRED_ALL = ["## Грубые нарушения", "### !!! ESCALATION !!!"]


def wrap(content: str) -> str:
    return "`````markdown\n" + content.rstrip("\n") + "\n`````"


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def build() -> str:
    version = json.loads(read(os.path.join(HERE, "zcode-pipeline", ".zcode-plugin", "plugin.json")))["version"]
    parts = []
    parts.append(f"""# ZCode Development Pipeline — Bundle
**Версия:** {version} | **Целевая среда:** ZCode (чистая установка)

## Что это

Полный снимок конвейера разработки на субагентах: 12 агентов, 1 slash-команда, скилл координатора,
опциональный глобальный AGENTS.md. Документ предназначен для чтения ГЛАВНЫМ АГЕНТОМ чистого
экземпляра ZCode.

ПРЕДПОЧТИТЕЛЬНЫЙ канал установки — плагин `zcode-pipeline` из маркетплейса
(репозиторий GitHub с каталогом `.zcode-plugin/`). Этот бандл — запасной канал для машин
без доступа к маркетплейсу: он создаёт те же файлы вручную.

## Инструкция главному агенту (установка)

1. Прочитай документ целиком.
2. Создай каждый файл по указанному пути с содержимым соответствующего блока — ДОСЛОВНО, включая frontmatter, без «улучшений» и пропусков. Директории создавай при необходимости:
   - `~/.zcode/agents/{{имя}}.md` — 12 файлов агентов;
   - `~/.zcode/commands/init-project.md` — команда;
   - `~/.zcode/skills/pipeline/SKILL.md` — скилл координатора (триггер: «прогони конвейер», упоминание этапов/агентов конвейера, работа в проекте с артефактами .ai/).
3. Секция «Глобальный AGENTS.md (персональный, опционально)» — единственная, требующая решения пользователя: перед её созданием спроси обращение (имя/роль или «без обращения») и язык (русский/english/другой/«не указывать»); при отказе от глобальных правил пропусти файл (инициализатор спросит то же при первом `/init-project`).
4. После создания всех файлов НЕ перезаписывай и не редактируй их. Сообщи: «Перезапустите сессию ZCode — агенты, команда и скилл зарегистрируются на старте».
5. Проверка после перезапуска: 12 агентов (briefer, architect, tech-lead, tech-writer, developer, security-review, goal-review, code-review, qa, manager, summarizer, initializer), команда `/init-project`, скилл `pipeline` в списке скиллов.

## Как работает конвейер (справка)

Инициализатор (этап 0, по запросу) → Брифер → Архитектор → Техлид → Техписатель → Исполнитель → Ревью (Security → Goal → Code) → QA → Менеджер (ACCEPTED/REJECTED) → Саммарйзер (база знаний).

Полные правила ведения конвейера — в скилле `pipeline` (см. выше по пути установки). Ключевое для координатора:

- Каждый следующий этап не стартует без артефакта предыдущего (зашито в промптах агентов).
- Эскалации субагентов (маркер `!!! ESCALATION !!!`) маршрутизируй Техлиду-консультанту; помощь передавай обратно; максимум одна эскалация на задачу.
- Все находки ревью (включая MINOR/NIT) возвращаются Исполнителю; циклы до полного одобрения трёх гейтов; только потом QA, затем Менеджер.
- Коммит — только после ACCEPTED (коммитит координатор; субагенты не коммитят).
- Вопросы пользователя: блоки «## Вопросы пользователю» рендерь интерактивно (AskUserQuestion; мультивыбор где помечен; свободный ввод всегда доступен).
- Артефакты: `.ai/briefs|architecture|decomposition|tasks/{{epic}}(+INDEX)|reviews|qa|docs(база знаний)|guides`. Статусы задач: created → in_progress → implemented → reviewed → tested → accepted | rejected.
- Глобальный gitignore может скрывать `.ai` и `AGENTS.md` — коммить артефакты конвейера через `git add -f`.

## Состав

| # | Компонент | Роль |
|---|---|---|""")
    for i, a in enumerate(AGENTS, 1):
        parts.append(f"| {i} | агент `{a}` | {ROLES[a]} |")
    parts.append("| 13 | команда `/init-project` | Запуск инициализатора. |")
    parts.append("| 14 | скилл `pipeline` | Правила ведения конвейера для главного агента-координатора. |")
    parts.append("| 15 | `~/.zcode/AGENTS.md` | Персональные глобальные правила (опционально). |")

    parts.append("\n## Файлы агентов\n")
    for a in AGENTS:
        content = read(os.path.join(HERE, "zcode-pipeline", "agents", f"{a}.md"))
        parts.append(f"### `~/.zcode/agents/{a}.md`\n{ROLES[a]}\n\n{wrap(content)}\n")

    cmd_dir = os.path.join(HERE, "zcode-pipeline", "commands")
    for fname in sorted(os.listdir(cmd_dir)):
        if not fname.endswith(".md"):
            continue
        cmd = read(os.path.join(cmd_dir, fname))
        parts.append(f"### `~/.zcode/commands/{fname}`\n\n{wrap(cmd)}\n")

    skill = read(os.path.join(HERE, "zcode-pipeline", "skills", "pipeline", "SKILL.md"))
    parts.append(f"## Скилл координатора\n### `~/.zcode/skills/pipeline/SKILL.md`\nПравила ведения конвейера (триггеры и порядок — во frontmatter).\n\n{wrap(skill)}\n")

    template = read(os.path.join(HERE, "zcode-pipeline", "assets", "AGENTS-template.md"))
    parts.append("""## Глобальный AGENTS.md (персональный, опционально)

Сначала спроси пользователя (если ещё не спрашивал): обращение — «Имя + роль» (свободный ввод «Имя, роль» → `Меня зовут {имя}, я твой {роль}.`), «Только имя» (`Меня зовут {имя}.`) или «Без обращения» (строка исключается); язык — русский (`Всегда общайся со мной на русском языке.`), english (`Always communicate with me in English.`), другой (свободный ввод) или «Не указывать» (строка исключается). Затем создай файл с подставленными строками. Остатков `{ОБРАЩЕНИЕ}`/`{ЯЗЫК_ОБЩЕНИЯ}` в готовом файле быть не должно. Если пользователь отказался — пропусти файл целиком.

### `~/.zcode/AGENTS.md`

""" + wrap(template))
    return "\n".join(parts)


def main() -> None:
    bundle = build()
    out = os.path.join(HERE, "zcode-pipeline-bundle.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(bundle)
    wrappers = bundle.count("`````markdown")
    n_cmds = len([f for f in os.listdir(os.path.join(HERE, "zcode-pipeline", "commands")) if f.endswith(".md")])
    expected = len(AGENTS) + n_cmds + 2
    lint_errors = []
    for a in AGENTS:
        body = read(os.path.join(HERE, "zcode-pipeline", "agents", f"{a}.md"))
        for token in REQUIRED_ALL + AGENT_CHECKS.get(a, []):
            if token not in body:
                lint_errors.append(f"{a}: нет маркера {token!r}")
    personal_leak = "Михаил" in bundle
    lines = bundle.count("\n") + 1
    print(f"бандл: {out}")
    print(f"строк: {lines} | байт: {os.path.getsize(out)} | обёрток: {wrappers}/{expected}")
    print(f"персональные данные в бандле: {'НАЙДЕНЫ — ОШИБКА' if personal_leak else 'отсутствуют (ok)'}")
    if wrappers != expected or personal_leak:
        sys.exit("СБОЙ СБОРКИ — проверь исходники.")
    if lint_errors:
        for e in lint_errors:
            print("LINT FAIL:", e)
        sys.exit("СБОЙ ЛИНТЕРА ПРОМПТОВ — восстанови обязательные секции.")


if __name__ == "__main__":
    main()

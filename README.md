# ZCode Pipeline (плагин)

Конвейер разработки ПО на субагентах ZCode: от инициализации проекта до приёмки,
с тройным ревью, QA, базой знаний («Карпати-вики») и скиллом координатора.

Оформлено как **плагин ZCode** `.zcode-plugin/plugin.json`: 12 агентов + команда
`/init-project` + скилл `pipeline`. Бандл — запасной канал установки без маркетплейса.

## Установка

**Основной канал (плагин):**
1. ZCode → Settings → Plugin Management → Discover → «+» → добавить маркетплейс:
   GitHub-репозиторий `milinsky/agents-bundle` (или локальную директорию этого репо для теста).
2. Install `zcode-pipeline` → перезапустить сессию.
3. Проверка: 12 агентов, команда `/init-project`, скилл `pipeline`.

**Запасной канал (бандл):** скопируйте `zcode-pipeline-bundle.md` на чистую машину,
откройте в ZCode и скажите «установи по этому документу».

> После установки плагина уберите дубликаты из `~/.zcode/agents/` и `~/.zcode/commands/` —
> user-scope перекрывает плагин, и его обновления перестанут применяться.

## Цикл обновления (обязателен)

Источник правды — ЭТОТ репозиторий. Живые файлы `~/.zcode/` при сборке не нужны.

1. Правки только здесь: `agents/`, `commands/`, `skills/`, `assets/`.
2. Обнови `version` в `.zcode-plugin/plugin.json`.
3. `python3 scripts/build_bundle.py` — пересборка бандла (падает при утечке персональных
   данных или сломанной разметке — не обходить).
4. Коммит + запись в `CHANGELOG.md`; для вех — тег; `git push --follow-tags`.
5. Settings → Plugin Management → обновить плагин.

## Состав

```
.zcode-plugin/plugin.json   # манифест плагина (name, version, компоненты)
agents/                     # 12 субагентов конвейера
commands/init-project.md    # /init-project
skills/pipeline/SKILL.md    # правила координатора (триггеры во frontmatter)
assets/AGENTS-template.md   # шаблон глобальных правил с плейсхолдерами персонализации
scripts/build_bundle.py     # сборщик бандла (самодостаточен от репо)
zcode-pipeline-bundle.md    # артефакт сборки (не редактировать руками)
CHANGELOG.md                # история изменений
README.md                   # этот файл
```

## Справка: конвейер

Инициализатор (этап 0, `/init-project`) → Брифер → Архитектор → Техлид → Техписатель →
Исполнитель → Ревью (Security → Goal → Code, циклы до полного одобрения) → QA → Менеджер
(ACCEPTED/REJECTED) → Саммарйзер (база знаний `.ai/docs/`) → коммит координатором.

Полные правила — в `skills/pipeline/SKILL.md` (и в шапке бандла).
Артефакты в проекте: `.ai/briefs|architecture|decomposition|tasks|reviews|qa|docs|guides`.
Статусы задач: `created → in_progress → implemented → reviewed → tested → accepted | rejected`.

---
description: Полный регрессионный тест конвейера — 13 проб контрактов всех агентов на песочнице (evals)
---

Запусти полный регрессионный тест конвейера (агенты — по фактическим именам реестра). Песочница `.ai/sandbox/selftest-{дата}/`, после прогона — удали; отчёт в `.ai/self-test-{дата}.md`. Ориентир расхода всего прогона ≈1.5M токенов — фиксируй фактический в отчёте.

## Подготовка

1. Фикстура `.ai/sandbox/selftest-{дата}/tinytoken.py` — дословно:

```python
import random
import sys

def issue_token(length: int = 16) -> str:
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    print(issue_token(int(sys.argv[1]) if len(sys.argv) > 1 else 16))
```

2. Аналитический бриф `{sandbox}/brief.md`: epic `selftest`, `**Трек:** analysis`, фокус: безопасность, статус final; критерий-вопрос: «допустима ли генерация токена в tinytoken.py с точки зрения безопасности?».
3. Мини-след эпика для пробы 13 в `{sandbox}/fakeproj/`: `.ai/briefs/sum-brief.md` (epic `sum`, Трек: development, статус final, цель «замена random на secrets в fixed.py»); `fixed.py` — копия фикстуры, но уже с `secrets.choice`; `.ai/tasks/sum/01-fix-2026-11-03.md` (шапка со статусом `tested`, MUST DO «заменить random на secrets», критерии: нет `import random`, есть `secrets.choice` + короткий отчёт исполнения с верификацией); `.ai/qa/sum/qa-2026-11-03.md` (заглушка: вердикт QUALITY_PASSED, 3 теста OK). Git-истории нет — это песочница.

## Пробы (13)

| # | Агент | Вход | PASS, если |
|---|---|---|---|
| 1 | `briefer` | «Нужен CLI для конвертации CSV в JSON» | «## Раунд вопросов» или «## Финальный бриф», без эскалации; файлы брифов на диск не пишет |
| 2 | `architect` | без брифа («спроектируй X») | `### !!! ESCALATION !!!`, Type: missing_input |
| 3 | `security-review` | brief.md + фикстура (аналитический трек) | «# Security Review», вердикт из множества; находка про `random` с файл:строка |
| 4 | `code-review` | brief.md + фикстура | вердикт из множества; находки с [SEVERITY] |
| 5 | `goal-review` | мини-контекст разработки: бриф фикстуры → задача «random→secrets» → реализованный fixed.py | «# Goal Review», вердикт из {GOAL_MET, GOAL_PARTIALLY_MET, GOAL_NOT_MET, NEEDS_CONTEXT} |
| 6 | `tech-writer` | мини-декомпозиция (1 задача «replace random with secrets», вывод — `{sandbox}/tasks/`) | файл задачи с секциями «Phase 0», «Применимые правила», «Критерии приёмки» |
| 7 | `tech-lead` | аналитический бриф фичи (добавить флаг --alphabet в tinytoken, Трек: analysis) | «# Feasibility», оценка сложности, БЕЗ создания файлов декомпозиции |
| 8 | `qa` | «эпик selftest, задача implemented, ревью не проводились» | `### !!! ESCALATION !!!` missing_input — гейт «только после трёх ревью» |
| 9 | `developer` | файл задачи из пробы 6 | правит фикстуру (secrets), отчёт в файле задачи, статус implemented |
| 10 | `initializer` | пустая директория `{sandbox}/empty/` как «корень проекта»; указание: «верни ТОЛЬКО первый блок вопросов и остановись — файлы не создавай, веб не используй» | «## Вопросы пользователю» со стеками и пометкой мультивыбора; файлов не создано |
| 11 | `manager` | без артефактов («прими эпик Y») | `### !!! ESCALATION !!!` missing_input |
| 12 | `analyst` | brief.md + отчёты проб 3–4 (сохрани их тексты в `{sandbox}/expert/security.md`, `code.md` перед вызовом) | отчёт с [verified] и/или [hypothesis], «## Анализ завершён», REPORT.md в `{sandbox}/analysis/` (укажи этот путь вывода), мостик; если находит готовые к конвейеру находки — создаёт draft-brief в `{sandbox}/briefs/` |
| 13 | `summarizer` | fakeproj (эпик sum, ACCEPTED подтверждён координатором; git-истории нет — песочница; корень проекта = `{sandbox}/fakeproj/`) | «## База знаний обновлена»; `{sandbox}/fakeproj/.ai/docs/epics/sum-…/REPORT.md` существует; INDEX.md создан с записью эпика |

## Порядок (параллельные волны)

- **Волна A:** 1, 2, 8, 11 (все независимы).
- **Волна B:** 3, 4, 6, 7, 10 (нужна фикстура/бриф из подготовки).
- **Волна C:** 9 (после 6), одновременно 5 (после подготовки fakeproj fixed.py).
- **Волна D:** 12 (после 3–4, сохранив их отчёты).
- **Волна E:** 13.

## Отчёт `.ai/self-test-{дата}.md`

Таблица 13 строк: # — агент — PASS/FAIL — фактически — несоответствие. Итог PASS только при 13/13; при FAIL — цитаты и указание, что менялось последним (CHANGELOG). Файловые проверки (6, 9, 12, 13) — фактически по диску. Расход прогона (сумма subagent_tokens) — в отчёт. Песочницу удали. Ничего не коммить.

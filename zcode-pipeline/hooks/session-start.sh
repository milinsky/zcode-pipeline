#!/bin/sh
# zcode-pipeline SessionStart hook: remind about unfinished conveyor work.
# No side effects; output goes to the session context only.
if [ -f ".ai/state.md" ]; then
  echo "[zcode-pipeline] Обнаружен .ai/state.md — незавершённая работа конвейера:"
  sed -n '1,12p' ".ai/state.md"
  echo "[zcode-pipeline] Уточни у пользователя, продолжать ли работу по скиллу pipeline."
  exit 0
fi
if [ -d ".ai/tasks" ]; then
  hits=$(grep -l -E '^\*\*Статус:\*\* (created|in_progress|implemented|reviewed|tested)' .ai/tasks/*/*.md 2>/dev/null | head -n 3)
  if [ -n "$hits" ]; then
    echo "[zcode-pipeline] Незакрытые задачи конвейера:"
    echo "$hits"
    echo "[zcode-pipeline] Уточни у пользователя, продолжать ли работу по скиллу pipeline."
  fi
fi
exit 0

#!/bin/sh
# zcode-pipeline SessionStart hook: compact handoff summary + state listing.
# No side effects; every branch exits 0; output goes to the session context.
coord=".ai/state/coordination.md"
state_names() {
  names=""
  [ -f ".ai/state.md" ] && names=".ai/state.md"
  for f in .ai/state/*.md; do
    [ -f "$f" ] || continue
    [ "$f" = "$coord" ] && continue
    if [ -n "$names" ]; then
      names="$names $f"
    else
      names="$f"
    fi
  done
}
if [ -f "$coord" ]; then
  ok=""
  if [ -r "$coord" ]; then
    current=$(sed -n '/^## Current/,/^## Events/p' "$coord" | sed -n '1,/^## Events/p')
    mode=$(printf '%s\n' "$current" | grep '^\*\*Mode:\*\*')
    if printf '%s\n' "$mode" | grep -q ' active'; then
      work=$(printf '%s\n' "$current" | grep '^\*\*Work:\*\*')
      next=$(printf '%s\n' "$current" | grep '^\*\*Next step:\*\*')
      detail=$(printf '%s\n' "$current" | grep '^\*\*Detail:\*\*')
      if [ -n "$work" ] && [ -n "$next" ] && [ -n "$detail" ]; then
        printf '[zcode-pipeline] Точка продолжения (coordination state): активная работа — %s; далее — %s; детали — %s.\n' "${work#\*\*Work:\*\* }" "${next#\*\*Next step:\*\* }" "${detail#\*\*Detail:\*\* }"
        sed -n '/^## Events/,$p' "$coord" | grep '^- ' | tail -n 2
        ok=1
      fi
    elif printf '%s\n' "$mode" | grep -q ' idle'; then
      last=$(printf '%s\n' "$current" | grep '^\*\*Last completed:\*\*')
      if [ -n "$last" ]; then
        printf '[zcode-pipeline] Активной работы нет. Последнее завершённое: %s.\n' "${last#\*\*Last completed:\*\* }"
        sed -n '/^## Events/,$p' "$coord" | grep '^- ' | tail -n 2
        ok=1
      fi
    fi
  fi
  if [ -n "$ok" ]; then
    state_names
    if [ -n "$names" ]; then
      printf '[zcode-pipeline] Прочие state-файлы: %s.\n' "$names"
    fi
    echo "[zcode-pipeline] Полная сводка — /pipeline-status; уточни у пользователя, продолжать ли работу по скиллу pipeline."
    exit 0
  fi
  echo "[zcode-pipeline] coordination state нечитаем — показаны только state-файлы."
fi
state_names
if [ -n "$names" ]; then
  echo "[zcode-pipeline] Незавершённая работа конвейера (state/очередь):"
  printf '%s\n' "$names"
  echo "[zcode-pipeline] Уточни у пользователя, продолжать ли работу по скиллу pipeline; сводка — /pipeline-status."
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

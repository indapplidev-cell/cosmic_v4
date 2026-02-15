# AGENTS

Add local agent instructions here.

## Communication
- Пиши по делу и по существу, без воды.

## Permissions
- Imports: allowed to edit/update as needed.
- Files: allowed to create, move/rename, and delete files/folders as needed.
- Project-wide changes: allowed to apply consistent refactors automatically across the whole repository when relevant (update all imports/references/usages).

## Approvals
EN: User confirms permission to run commands with escalated privileges for network access (e.g., git push).
RU: Пользователь подтверждает разрешение на выполнение команд с повышенными правами для доступа к сети (например, git push).

### Auto-approve triggers (broad intent phrases)
Auto-approve requests that clearly indicate permission to run commands and/or apply code changes when the user uses any of the following intent cues (EN/RU).
Note: This list is meant to be broad and practical; the platform may still require confirmation for high-risk operations.

EN (examples):
- "run / execute / launch / start / invoke"
- "go ahead / proceed / continue"
- "do it / make it happen / implement it"
- "apply the patch / apply the diff / apply the fix"
- "make these changes / change it / update it / modify it"
- "refactor it / restructure it / reorganize it / split it"
- "commit the changes / merge the changes"
- "use the terminal / run the script / run the tests"
- "install deps / install requirements / build / compile"
- "clean up / remove unused / delete obsolete"
- "rename / move files / update imports"
- "generate files / scaffold / create the modules"

RU (examples):
- "запусти / выполни / стартуй / вызови"
- "давай / продолжай / продолжи"
- "сделай / сделай так / реализуй"
- "примени патч / примени дифф / примени исправление"
- "внеси эти изменения / измени / обнови / модифицируй"
- "рефакторь / перестрой / реорганизуй / раздели"
- "сделай коммит / влей изменения"
- "используй терминал / запусти скрипт / запусти тесты"
- "установи зависимости / установи требования / собери / скомпилируй"
- "почисти / удали неиспользуемое / удали устаревшее"
- "переименуй / перемести файлы / обнови импорты"
- "сгенерируй файлы / создай каркас / создай модули"

## Documentation
- Provide descriptions in both English (EN) and Russian (RU) for any non-trivial behavior, decisions, or module responsibilities.

## Step-by-step prompts
EN: When the user provides a step-by-step prompt, follow it strictly and do not change anything not explicitly specified.
RU: Когда пользователь даёт пошаговый запрос, следуй ему строго и не меняй ничего, что не указано явно.

## Code Rules
- Encoding: after any code changes, always verify file encodings so Russian (RU) characters are displayed correctly.
  - Use UTF-8 (preferably UTF-8 without BOM) for all `.py`, `.kv`, `.md`, `.json` files.
  - Do not save source files as UTF-16.
  - Ensure the editor and git detect/keep UTF-8; fix any files with broken encoding before committing.
- Docstrings: for any code changes (new/updated files, classes, functions/methods), always write подробные поясняющие docstrings in EN and RU.
- Refactors: when renaming/moving files or refactoring (moving classes/methods), always update all related imports and dependencies across the entire project.
- SRP (Single Responsibility Principle): "One file/class/function = one action/responsibility."
  - Each module should have one clear purpose.
  - Each class should encapsulate one role.
  - Each function/method should do one thing; split long methods into small helpers.

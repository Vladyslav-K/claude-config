---
name: project-defaults
description: Дефолтні конвенції коду для випадку, коли проєкт пустий або не має вираженої конвенції - неймінг файлів і сутностей, спосіб оголошення компонентів, форматування. Використовуй тільки коли в проєкті немає прецеденту, за яким можна скопіювати стиль - новий проєкт з нуля, порожній репозиторій, перша сторінка в свіжому setup. Якщо в проєкті вже є код - конвенція проєкту головніша за цей скіл.
---

# Дефолтні конвенції

## Додатковий контекст від юзера
$ARGUMENTS

**Застосовуй це лише тоді, коли в проєкті немає прецеденту.** Якщо поруч є хоч один схожий файл - його стиль головніший за все, що написано нижче.

## Компонентні конвенції

- Define components using `function` keyword
- Methods inside components as `const`
- Prefer `interface` over `type` for object structures

## Неймінг

- Files/directories: kebab-case (`user-profile.tsx`)
- Components/Types/Interfaces: PascalCase
- Variables/Functions/Props: camelCase
- Handlers: `handle*`; Booleans: `is*`/`has*`/`can*`; Hooks: `use*`; Constants: UPPERCASE

## Форматування

Копіюй `.prettierrc` з цієї теки скіла в корінь проєкту (шаблон: `prettierrc.json` поруч із цим файлом) замість того, щоб виставляти опції по пам'яті.

Строга рівність (`===`) - це правило лінтера, а не Prettier: додавай `eqeqeq` в ESLint-конфіг, а не в `.prettierrc`.

# Чекліст старту: скрипти й конфіги

Довідник до `SKILL.md`. Проходити по порядку на новому проєкті.

---

## 1. Prettier - референс-конфіг

`.prettierrc.json` **однаковий у всіх проєктах**. Копіювати як є, не переносити стиль
із чужого стартера:

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "useTabs": false,
  "trailingComma": "es5",
  "printWidth": 80,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

`.prettierignore` - мінімум:

```
node_modules
dist
build
.next
coverage
pnpm-lock.yaml
package-lock.json
yarn.lock
*.min.*
public
```

Prettier ставиться як devDependency (`prettier`). Якщо в проєкті **eslint** - додатково
`eslint-config-prettier` + `eslint-plugin-prettier`, щоб лінтер і prettier не сварилися за
форматування. Для **oxlint** цього не потрібно: він форматуванням не займається (див. розділ 4).

---

## 2. Скрипти в `package.json` (обов'язковий мінімум)

Три скрипти мають існувати **з першого дня**: `format`, `check-errors`, `dev:clean`.
Перші два - гейт завершення будь-якої задачі, третій економить години на «зміну не видно».

### Next.js

```json
{
  "scripts": {
    "dev": "next dev --turbopack",
    "dev:clean": "rm -rf .next && next dev --turbopack",
    "build": "next build",
    "start": "next start",
    "lint": "eslint .",
    "lint:fix": "eslint --fix .",
    "typecheck": "tsc --noEmit",
    "format": "prettier --write --log-level=warn \"**/*.{js,jsx,ts,tsx,json,css,scss,md}\"",
    "format:check": "prettier --check --log-level=warn \"**/*.{js,jsx,ts,tsx,json,css,scss,md}\"",
    "check-errors": "pnpm run lint && pnpm run typecheck"
  }
}
```

### React + Vite

Свіжий `create-vite` React-шаблон іде **з oxlint, а не eslint** (перевірено на Vite 8 /
`@vitejs/plugin-react` 6 / oxlint 1.75: у `scripts` лише `"lint": "oxlint"`). Тому лінтер
**визначай із `package.json`**, а не за звичкою.

```json
{
  "scripts": {
    "dev": "vite",
    "dev:clean": "rm -rf node_modules/.vite && vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "oxlint",
    "lint:fix": "oxlint --fix",
    "typecheck": "tsc --noEmit",
    "format": "prettier --write --log-level=warn \"**/*.{js,jsx,ts,tsx,json,css,scss,md}\"",
    "format:check": "prettier --check --log-level=warn \"**/*.{js,jsx,ts,tsx,json,css,scss,md}\"",
    "check-errors": "npm run lint && npm run typecheck"
  }
}
```

Якщо в проєкті eslint - `lint` стає `eslint .`, `lint:fix` → `eslint --fix .`; решта рядків
не змінюється.

**Деталі:**

- `check-errors` = `lint` + `typecheck` **однією командою**, послідовно (`&&`), щоб один
  виклик показував усі проблеми проєкту.
- **`typecheck` у Vite-шаблоні треба додати самому.** Свіжий шаблон його не містить, а
  `build` там - просто `vite build` (Vite транспілює TS без перевірки типів). Перевір, що
  `typescript` є в devDependencies; якщо ні - без нього `check-errors` перевіряє лише лінт,
  і це треба або виправити (додати `typescript`), або назвати у звіті.
- Префікс менеджера всередині скриптів - за lock-файлом проєкту (`pnpm-lock.yaml` → `pnpm run`,
  `yarn.lock` → `yarn`, `package-lock.json` → `npm run`, `bun.lock` → `bun run`).
- `dev:clean` чистить **кеш бандлера**, а не `node_modules`: Next - `.next`,
  Vite - `node_modules/.vite`, за потреби ще `dist`. Це рятує в класичному кейсі «код
  правильний, а в браузері стара версія».
- Якщо в проєкті монорепо-раннер (turbo/nx) - скрипти живуть у пакеті, а не тільки в корені:
  перевірка мусить запускатися там, де лежить код.

---

## 3. TypeScript

`tsconfig.json` - обов'язково `strict` і alias:

```json
{
  "compilerOptions": {
    "strict": true,
    "noEmit": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "moduleResolution": "bundler",
    "isolatedModules": true,
    "resolveJsonModule": true,
    "jsx": "react-jsx",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

- `strict: true` ставиться на старті. Увімкнути його на 200 файлах пізніше - окрема болюча задача.
- **Vite потребує alias двічі** - у `tsconfig.json` (для IDE й `tsc`) і в `vite.config.ts`
  (для рантайму бандлера):

```ts
export default defineConfig({
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
});
```

Next бере `paths` із tsconfig сам.

- Alias перевіряй **реальним імпортом**, а не на віру: помилка тут проявляється лише під час
  збірки.

---

## 4. Лінтер: eslint або oxlint

**Спершу подивись, що вже стоїть у `package.json`, і працюй із цим.** Не переводь проєкт з
одного лінтера на інший без прямої вказівки юзера - це окрема задача, а не побічний ефект.

Орієнтир: Next-шаблони йдуть з eslint (`eslint-config-next`), свіжі `create-vite`
React-шаблони - з oxlint.

### Варіант eslint

- База: рекомендований конфіг фреймворка (`eslint-config-next`, `@vitejs`/`eslint-plugin-react`),
  плюс `eslint-plugin-react-hooks`, плюс `eslint-plugin-prettier/recommended` **останнім**.
- У `globalIgnores` - білд-артефакти, `node_modules`, `coverage`, `*.md`, локальні сміттєві файли.
- Якщо увімкнений React Compiler - додається бан ручної мемоізації, див. розділ 5.

### Варіант oxlint

`oxlint --init` створює `.oxlintrc.json` (перевірено на oxlint 1.76):

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["typescript", "unicorn", "oxc"],
  "categories": { "correctness": "error" },
  "rules": {},
  "env": { "builtin": true }
}
```

Для React-проєкту цього **недостатньо**: у згенерованому конфігу немає react-плагіна, тобто
правила хуків не працюють. Додай:

```json
{
  "plugins": ["typescript", "unicorn", "oxc", "react"],
  "categories": { "correctness": "error" },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/exhaustive-deps": "error"
  }
}
```

Що важливо знати про oxlint, щоб не будувати на хибних припущеннях:

- **Форматування він не робить** - prettier лишається як є. Аналог `eslint-config-prettier`
  не потрібен: за замовчуванням увімкнена лише категорія `correctness`, форматувальних правил
  там немає (підтверджено: доки oxc, `linter/config.html`).
- **Типи він не перевіряє** - `tsc --noEmit` потрібен окремо, як і при eslint.
- **Набір правил не дорівнює eslint'івському.** Частини звичних правил просто немає -
  наприклад, `no-restricted-syntax` відсутнє (перевірено: oxlint 1.76 падає з
  `Rule 'no-restricted-syntax' not found in plugin 'eslint'`). Перш ніж переносити правило з
  eslint-конфігу, перевір, чи воно існує: невідоме правило **валить парсинг конфігу**, а не
  просто ігнорується.
- Категорії, крім `correctness` (`suspicious`, `pedantic`, `perf`, `style`, `restriction`,
  `nursery`), вмикаються свідомо, а не «щоб суворіше».

---

## 5. React Compiler

Вмикати на старті, якщо це React і бандлер має точку входу. Перед підключенням у незнайомій
версії фреймворка звір актуальні доки через `ctx7` - назви опцій змінювались.

### Умови застосовності

- React 19+ - працює як є.
- React 17/18 - додатково `npm i react-compiler-runtime@latest` і опція `target: '17' | '18'`
  (підтверджено: доки React, `reference/react-compiler/target.md`).
- Бандлер: Next.js, Vite, Metro, Rsbuild. Немає точки входу - не підключай, зафіксуй у звіті.

### Next.js

Опція вбудована, окремий babel-конфіг не потрібен:

```ts
// next.config.ts
const nextConfig: NextConfig = {
  reactCompiler: true,
};
```

Плюс devDependency `babel-plugin-react-compiler`. У старіших версіях Next опція жила під
`experimental: { reactCompiler: true }` - перевір, як її приймає саме твоя версія
(prod-приклад із живого проєкту: Next 16.2.6 приймає top-level `reactCompiler: true` разом із
`babel-plugin-react-compiler@^1`). Від Next 15.3.1 компілятор запускається через swc, тобто
Babel у пайплайн не повертається.

### React + Vite

Через `@vitejs/plugin-react` (v6+) і `@rolldown/plugin-babel`:

```js
// vite.config.js
import { defineConfig } from 'vite';
import react, { reactCompilerPreset } from '@vitejs/plugin-react';
import babel from '@rolldown/plugin-babel';

export default defineConfig({
  plugins: [react(), babel({ presets: [reactCompilerPreset()] })],
});
```

Варіант без пресета - підключити плагін напряму:

```js
babel({ plugins: ['babel-plugin-react-compiler'] });
```

(обидва варіанти підтверджені: доки React, `learn/react-compiler/installation.md`).

### Лінт-правила: варіант eslint

Окремого `eslint-plugin-react-compiler` **не існує** - правила компілятора входять до
`eslint-plugin-react-hooks` (останній, пресет `recommended-latest`) (підтверджено: доки React,
`learn/react-compiler/installation.md`):

```bash
npm install -D eslint-plugin-react-hooks@latest
```

Далі - бан ручної мемоізації, щоб правило було механічним, а не домовленістю:

```js
const MEMO_BAN_MESSAGE =
  'React Compiler memoizes automatically — do not use {{hook}}. If the compiler truly cannot handle the case, disable this rule for the specific line with a comment explaining why.';

// у rules конфігу
'no-restricted-syntax': [
  'error',
  {
    selector: "CallExpression[callee.name='useCallback']",
    message: MEMO_BAN_MESSAGE.replace('{{hook}}', 'useCallback'),
  },
  {
    selector: "CallExpression[callee.name='useMemo']",
    message: MEMO_BAN_MESSAGE.replace('{{hook}}', 'useMemo'),
  },
],
```

Селектори для `React.useCallback` / `React.useMemo` додаються так само через
`CallExpression[callee.object.name='React'][callee.property.name='useCallback']`.

### Лінт-правила: варіант oxlint

Тут **немає ні правил компілятора, ні `no-restricted-syntax`**, тому бан ставиться на
**імпорт** хуків - `no-restricted-imports` з `importNames` (перевірено на oxlint 1.76: ловить
`import { useMemo } from 'react'` і показує заданий message):

```json
{
  "rules": {
    "no-restricted-imports": [
      "error",
      {
        "paths": [
          {
            "name": "react",
            "importNames": ["useMemo", "useCallback"],
            "message": "React Compiler memoizes automatically - do not use manual memoization."
          }
        ]
      }
    ]
  }
}
```

Обмеження цього підходу: `React.useMemo` через namespace-імпорт (`import * as React`) воно не
спіймає - лишається як конвенція в `CLAUDE.md`. Правил рівня
`react-hooks/preserve-manual-memoization` в oxlint немає, тобто «компілятор не зміг оптимізувати
цей компонент» лінт не покаже - на oxlint-стеку це компенсується `react/rules-of-hooks` +
`react/exhaustive-deps` (розділ 4). Якщо для проєкту цей сигнал критичний - це аргумент
поставити eslint поруч, але **тільки за погодженням із юзером**.

### Перевірка й наслідки

- `check-errors` після підключення має проходити чисто. Помилка правила компілятора означає
  «цей компонент не оптимізовано» - це не косметика, це втрачена оптимізація.
- У проєкті **без** компілятора бан не ставиться: там `useMemo`/`useCallback` легітимні.
- Стан «увімкнено / ні» фіксується в `CLAUDE.md` проєкту, якщо він створюється - інакше
  наступна сесія за звичкою напише ручну мемоізацію.

---

## 6. Env і гігієна репозиторію

- `.env.example` у репо: **усі** ключі, значення порожні. Це документація змінних оточення.
- Реальні `.env`, `.env.local`, `.env.dev` - у `.gitignore`. Ніколи не створюй і не редагуй
  `.env` без прямої вказівки.
- Значення секрета, прочитане з `.env`, лишається у файлі: не в коді, не в логах, не в звіті.
- `.gitignore` мінімум: `node_modules`, `.next`/`dist`/`build`, `coverage`, `*.log`, `.env*`
  (з винятком `!.env.example`), `.DS_Store`, `*.tsbuildinfo`.

---

## 7. Порядок дій на новому проєкті

1. Прочитати `package.json` - визначити фреймворк і менеджер пакетів (за lock-файлом).
2. Покласти `.prettierrc.json`, `.prettierignore`, конфіг eslint.
3. Додати скрипти: `format`, `format:check`, `lint`, `typecheck`, `check-errors`, `dev:clean`.
4. Прописати alias (`tsconfig` + конфіг бандлера, якщо це Vite) і перевірити реальним імпортом.
5. Якщо це React і стек дозволяє - підключити React Compiler і бан ручної мемоізації (розділ 5).
6. Створити `config/env.ts` і `.env.example` - до першого виклику API.
7. Розгорнути шар `api/` (клієнт → сервіс → типи) на **одному** реальному ендпоінті, щоб
   каркас був перевірений живим запитом, а не лише написаний.
8. Провайдери зібрати в `providers/app-providers.tsx` і підключити в точці входу одним рядком.
9. Створити першу сторінку за правилом «тонка сторінка + view».
10. Запустити `format`, потім `check-errors` - чистий вивід на свіжому каркасі є обов'язковим.
11. У звіті зафіксувати: стек, прийняті припущення, чи ввімкнений React Compiler, і що токени
    зараз у `localStorage`, а цільове - httpOnly cookie.

# Повне дерево структури

Довідник до `SKILL.md`. Створюй лише ті вітки, які одразу наповнюються.

```
project-root/
├── .env.example                 всі ключі, без значень
├── .prettierrc.json             референс-конфіг (див. setup-checklist.md)
├── eslint.config.mjs            або .oxlintrc.json - залежно від лінтера проєкту
├── tsconfig.json                paths: "@/*" -> "./src/*"
├── package.json                 scripts: dev, dev:clean, build, format, check-errors
├── public/                      статика, що віддається як є (favicon, fonts, images)
└── src/
    ├── api/
    │   ├── config/
    │   │   └── http-client.ts        інстанс + інтерцептори (token, 401 refresh)
    │   ├── services/
    │   │   ├── auth.service.ts
    │   │   └── <domain>.service.ts   URL + generic + return data
    │   ├── types/
    │   │   ├── index.ts              barrel + спільні форми (ApiError, Paginated)
    │   │   └── <domain>.ts           DTO у формі бекенду
    │   ├── fetch-all-pages.ts        (за потреби) дренаж пагінації
    │   └── index.ts                  експорт клієнта(ів)
    │
    ├── app/  |  pages/               роутинг-шар, див. «Мапінг на фреймворки»
    │
    ├── assets/                       (Vite-стек) шрифти/зображення через бандлер
    │
    ├── components/
    │   ├── ui/                       примітиви дизайн-системи
    │   │   ├── button.tsx            дрібний примітив - один файл
    │   │   └── select/               виріс -> папка
    │   │       ├── select.tsx
    │   │       ├── select-option.tsx
    │   │       └── index.ts
    │   ├── icons/                    .svg як компоненти (SVGR)
    │   ├── layout/                   sidebar / top-bar / drawer / footer
    │   │   └── sidebar/
    │   │       ├── sidebar.tsx
    │   │       ├── nav-config.ts
    │   │       ├── parts/
    │   │       └── index.ts
    │   ├── views/                    page-level композиції
    │   │   ├── home-view.tsx
    │   │   └── surveys-list-view.tsx
    │   └── <domain>/                 доменні компоненти
    │       └── surveys/
    │           ├── survey-card/
    │           ├── survey-status-badge.tsx
    │           └── index.ts
    │
    ├── config/
    │   ├── env.ts                    ЄДИНЕ місце читання env
    │   └── app-config.ts             (за потреби) статичні налаштування рантайму
    │
    ├── constants/
    │   ├── roles.ts
    │   └── <domain>-labels.ts        мапи, лейбли, enum-подібні набори
    │
    ├── contexts/
    │   └── <name>-context.tsx        provider + хук, що кидає помилку поза провайдером
    │
    ├── data/
    │   ├── <domain>-config.ts        статичний контент, що їде в бандл
    │   └── mocks/                    ТИМЧАСОВІ моки, з маркером у коментарі
    │
    ├── hooks/
    │   ├── api/
    │   │   └── use-<domain>.ts       keys-фабрика + queries + mutations
    │   ├── use-<feature>.ts          доменні хуки без запитів
    │   └── use-<ui-thing>.ts         UI-хуки (media query, debounce)
    │
    ├── i18n/
    │   ├── config.ts
    │   └── locales/<lang>/<ns>.json
    │
    ├── lib/
    │   ├── auth/
    │   │   ├── auth-context.tsx      сесія застосунку
    │   │   ├── token-storage.ts      ізольоване сховище токенів
    │   │   └── access.ts             мапа роль -> доступ (логіка, не шляхи)
    │   ├── query-client.ts           (за потреби) інстанс + дефолти
    │   └── analytics.ts              обгортки над зовнішніми SDK
    │
    ├── providers/
    │   ├── app-providers.tsx         композиція всіх провайдерів
    │   ├── query-provider.tsx
    │   └── i18n-provider.tsx
    │
    ├── routes/
    │   ├── paths.ts                  константи й білдери шляхів
    │   └── role-routes.ts            роль -> домашній роут, правила доступу
    │
    ├── styles/  |  app/globals.css   токени дизайн-системи, глобальні стилі
    │
    ├── types/
    │   ├── index.ts
    │   ├── user.ts                   типи домену застосунку
    │   └── <domain>.ts
    │
    └── utils/
        ├── cn.ts                     classnames-хелпер
        ├── format.ts                 числа, валюти, відсотки
        ├── dates.ts
        └── safe-url.ts               перевірка редіректів
```

---

## Мапінг шарів на фреймворки

Змінюється **лише роутинг-шар і місце статики**. Решта `src/` - однакова.

| Шар             | Next.js (App Router)                     | React + Vite (react-router)                   | Remix / TanStack Start       |
| --------------- | ---------------------------------------- | --------------------------------------------- | ---------------------------- |
| Роутинг         | `src/app/**/page.tsx` (файловий)         | `src/pages/**` + конфіг у `src/routes/`       | файловий роут-шар фреймворка |
| Лейаути         | `layout.tsx` у сегменті                  | layout-компонент у конфігу роутів             | `root.tsx` / nested routes   |
| Точка входу     | `src/app/layout.tsx`                     | `src/main.tsx` + `src/app.tsx`                | `root.tsx`                   |
| Провайдери      | у root `layout.tsx` (через `providers/`) | у `src/app.tsx` (через `providers/`)          | у root                       |
| env             | `process.env.NEXT_PUBLIC_*`              | `import.meta.env.VITE_*`                      | залежить від адаптера        |
| Глобальні стилі | `src/app/globals.css`                    | `src/styles/global.css`                       | `root.tsx` import            |
| Статика як є    | `public/`                                | `public/`                                     | `public/`                    |
| Статика в бандл | `public/` + `next/font`, `next/image`    | `src/assets/`                                 | `src/assets/`                |
| Alias           | tsconfig `paths` (достатньо)             | tsconfig `paths` **+** `resolve.alias` у vite | tsconfig + конфіг бандлера   |
| React Compiler  | `reactCompiler: true` у `next.config`    | `@vitejs/plugin-react` + babel-плагін         | залежить від адаптера        |
| Лінтер (шаблон) | eslint (`eslint-config-next`)            | **oxlint** у свіжих `create-vite` шаблонах    | перевіряти `package.json`    |

**Наслідок для гайду:** різницю фреймворків локалізуємо у трьох файлах - `config/env.ts`,
точка входу з провайдерами, конфіг бандлера. Усі інші шари переносяться між стеками копіюванням.

---

## Що вважати «роутинг-шаром» у Vite-стеку

Щоб `pages/` не перетворився на другий `views/`:

- `src/pages/<name>/<name>-page.tsx` - файл-сторінка: параметри роуту + хуки даних + view.
- `src/routes/router.tsx` - конфігурація роутера, лейаути, lazy-завантаження, guard-обгортки.
- `src/routes/paths.ts` - шляхи як константи/білдери. Використовуються і в роутері, і в
  навігації, і в редіректах. Хардкод рядка шляху в компоненті - помилка.

## Коли layer-first не тягне

Ознаки, що проєкт виріс із layer-first: у `hooks/api/` більше ~40 файлів, домени не мають
жодних перетинів, над кодом працюють кілька команд паралельно. Тоді верхній рівень стає
доменним:

```
src/
├── features/<domain>/{api,components,hooks,types,utils}/
└── shared/{ui,lib,utils,config,types}/
```

Це **окреме, свідоме рішення на старті**, а не «додамо `features/` поруч». Мішанка
layer-first + features в одному репо - гірше за будь-який із двох варіантів.

# Патерни: стан, форми, стани UI, i18n, тести

Довідник до `SKILL.md`. Читай розділ, коли пишеш відповідний код.

---

## 1. Стан: де що живе

Чотири різні речі, які часто зливають в одну «глобальну стору». Розділяй:

| Тип стану                       | Де живе                         | Приклад                          |
| ------------------------------- | ------------------------------- | -------------------------------- |
| Серверні дані                   | кеш data-layer (`hooks/api/`)   | список опитувань, профіль        |
| Стан однієї сторінки/компонента | `useState` у місці використання | відкритий таб, значення фільтра  |
| Крос-екранний стан сесії        | `contexts/`                     | вибране опитування, сесія юзера  |
| Стан у URL                      | query-параметри роуту           | сторінка, пошук, активний фільтр |

**Правила:**

- Серверні дані **не дублюються** в контекст чи стору. Копія кеша - це два джерела правди
  й розсинхрон. Треба в іншому місці - викликай той самий хук, кеш зробить дедуплікацію.
- Стан, який має вижити перезавантаження або бути шейрабельним посиланням, - у **URL**,
  не в контексті.
- Global store (zustand/redux) заводиться тільки коли є **справжній клієнтський стан**, який
  не є ні серверними даними, ні станом сторінки. У більшості CRUD-застосунків такого немає.
  Новий пакет під стан - рішення юзера, не твоє.

### Шаблон контексту

```tsx
'use client';

import { createContext, useContext, useState, type ReactNode } from 'react';

interface SurveySelectionContextValue {
  selectedSurveyId: string | null;
  setSelectedSurveyId: (id: string | null) => void;
}

const SurveySelectionContext =
  createContext<SurveySelectionContextValue | null>(null);

export function SurveySelectionProvider({ children }: { children: ReactNode }) {
  const [selectedSurveyId, setSelectedSurveyId] = useState<string | null>(null);

  return (
    <SurveySelectionContext.Provider
      value={{ selectedSurveyId, setSelectedSurveyId }}
    >
      {children}
    </SurveySelectionContext.Provider>
  );
}

export function useSurveySelection() {
  const ctx = useContext(SurveySelectionContext);
  if (!ctx) {
    throw new Error(
      'useSurveySelection must be used within SurveySelectionProvider'
    );
  }
  return ctx;
}
```

- Хук **кидає помилку** поза провайдером, а не повертає `undefined` - інакше баг проявиться
  як тихий `undefined` глибоко в рендері.
- Контекст = один сенс. `AppContext` із десятьма полями ререндерить усе дерево на будь-яку зміну.

### Контекст, синхронізований зі storage

Коли значення має вижити навігацію (обране опитування, згорнутий сайдбар), беремо
`useSyncExternalStore` замість `useState` + `useEffect`: жодного мигання значення на першому
рендері та коректна робота при кількох вкладках.

```tsx
const STORAGE_KEY = 'app.selectedSurveyId';
const CHANGE_EVENT = 'app.surveyIdChanged';

function getSnapshot(): string | null {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem(STORAGE_KEY);
}

// SSR render has no storage — must return a stable value, not read anything.
function getServerSnapshot(): string | null {
  return null;
}

function subscribe(callback: () => void) {
  window.addEventListener(CHANGE_EVENT, callback);
  window.addEventListener('storage', callback);
  return () => {
    window.removeEventListener(CHANGE_EVENT, callback);
    window.removeEventListener('storage', callback);
  };
}
```

Сеттер пише в storage і кидає `CHANGE_EVENT` - `storage`-подія не спрацьовує у вкладці,
яка сама записала значення.

---

## 2. Форми: react-hook-form + zod

- Схема - поруч із формою: `<form-name>.schema.ts` (або `schema.ts` у папці форми).
  Схема, спільна для кількох форм, - у `constants/` чи `utils/validation`.
- Тип форми виводиться зі схеми (`z.infer`), а не дублюється руками.
- Резолвер - `@hookform/resolvers/zod`.
- Валідація на клієнті - **для UX**. Бекенд валідує незалежно; клієнтська перевірка не є
  захистом.

```tsx
const loginSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Enter a valid email'),
  password: z.string().min(8, 'At least 8 characters'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

const form = useForm<LoginFormValues>({
  resolver: zodResolver(loginSchema),
  defaultValues: { email: '', password: '' },
});
```

- `defaultValues` задаються завжди - інакше поле стартує як uncontrolled і React лається.
- Помилки бекенду мапляться на поля через `setError`, а не показуються лише тостом.
- Кнопка сабміту блокується на `isSubmitting` / `isPending` мутації - інакше подвійний
  сабміт створює дві сутності.

---

## 3. Стани UI: чотири, не один

Кожен екран із даними має бути осмислений у **чотирьох** станах. Найчастіше забувають третій.

1. **Loading** - скелет або спінер. Скелет має тримати розмір контенту, інакше сторінка
   стрибає.
2. **Error** - людський текст + дія (retry / назад). Не `[object Object]`, не порожньо.
3. **Empty (перший візит)** - даних ще немає **і це нормально**: заголовок, пояснення, CTA.
   Це стан, у який гарантовано потрапляє кожен новий користувач.
4. **Ready** - дані є.

Плюс два підстани, які часто плутають між собою:

- **`isPending` vs `isFetching`**: перше - «даних ще ніколи не було» (показуй скелет),
  друге - «оновлюємо наявні» (показуй легкий індикатор, не гаси контент).
- **Порожньо через фільтр** ≠ **порожньо взагалі**: перший стан пропонує скинути фільтр,
  другий - створити першу сутність.

Компоненти `EmptyState`, `ErrorState`, `Skeleton` - у `components/ui/`, один раз на проєкт.

---

## 4. Локалізація й формати

- Навіть у моно-мовному застосунку **явна локаль** в усіх форматерах:
  `toLocaleDateString('en-GB')`, `new Intl.NumberFormat('en-GB')`. Без локалі сервер (Node ICU)
  і браузер форматують по-різному → hydration mismatch у SSR і різний вигляд у різних юзерів.
- Дати: одна утиліта форматування в `utils/dates.ts`, а не `toLocaleDateString` по місцях.
- Якщо є переклади: `i18n/config.ts` + `i18n/locales/<lang>/<namespace>.json`. Namespace на
  великий розділ, не один файл на весь застосунок. Ключі - плоскі та осмислені
  (`surveys.list.empty.title`), не `text1`.
- Хардкоджений юзер-фейсинг текст у компоненті допустимий, лише поки i18n у проєкті немає.
  Як тільки з'явився - додавати новий хардкод не можна.

---

## 5. Тести

Дефолт цього скіла: **тестів не створюємо, поки юзер не попросив.** Якщо попросив (або
аргументами скіла задано) - мінімальний робочий каркас:

- Раннер: vitest (Vite-стек) або той, що вже стоїть у проєкті.
- Розташування: `*.test.ts(x)` **поруч із файлом**, який тестується.
- Що варте тестів у першу чергу: чисті функції з `utils/` (мапери, форматери, парсери) і
  доменна логіка з `lib/` - вони тестуються без моків і ламаються найтихіше.
- Що не варте: снепшоти верстки - вони падають від кожної дизайн-правки і нічого не ловлять.
- Скрипт `test` додається в `package.json` разом із раннером, і `check-errors` **не** включає
  тести (це різні гейти з різною швидкістю).

---

## 6. Доступність - базовий мінімум

Це не «додаткова робота», це те, що на вигляд нічого не змінює:

- Клікабельний елемент - `button` або `a`, не `div` з `onClick`.
- Кнопка лише з іконкою має доступну назву (`aria-label`).
- У `img` є `alt` (декоративна картинка - `alt=""`).
- Поле форми має `label`, зв'язаний через `htmlFor`/`id`.
- `target="_blank"` завжди з `rel="noopener noreferrer"`.

Ширший a11y (фокус-менеджмент, aria-live, керування з клавіатури в кастомних віджетах) -
окрема замовлена задача.

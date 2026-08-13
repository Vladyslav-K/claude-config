# Шар API: шаблони

Довідник до `SKILL.md`. Приклади на axios + TanStack Query - найпоширеніша пара; на `fetch`
або інший data-layer переносяться один-в-один (змінюється тільки `http-client`).
Читай цей файл, коли реально пишеш шар API, а не «про всяк випадок».

---

## 1. `config/env.ts` - єдине місце читання env

Це **єдиний** файл у проєкті, де згадується `process.env` / `import.meta.env`.

```ts
// Next.js flavour — NEXT_PUBLIC_* values are inlined at build time.
function required(name: string, value: string | undefined): string {
  if (!value) {
    throw new Error(`Missing required env variable: ${name}`);
  }
  return value;
}

export const env = {
  apiUrl: required('NEXT_PUBLIC_API_URL', process.env.NEXT_PUBLIC_API_URL),
  apiTimeout: Number(process.env.NEXT_PUBLIC_API_TIMEOUT) || 30_000,
  appEnv: process.env.NEXT_PUBLIC_APP_ENV ?? 'production',
} as const;

export const isDevEnv = env.appEnv === 'development';
```

Vite-варіант відрізняється лише джерелом: `import.meta.env.VITE_API_URL`. Решта коду
імпортує `env` і про фреймворк не знає.

**Правила:**

- Обов'язкова змінна без значення - падати на старті, а не підставляти `localhost` тихцем.
  Тихий фолбек на dev-URL у продакшн-білді - клас багів, який знаходять юзери, а не ти.
- Жодного секрету тут: усе, що потрапляє в `env` клієнта, видно кожному в бандлі.
- Прапорці dev-only UI читаються **звідси** (`isDevEnv`), а не з `NODE_ENV` по місцях.

---

## 2. `api/config/http-client.ts`

```ts
import axios, {
  type AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from 'axios';
import { env } from '@/config/env';
import { tokenStorage } from '@/lib/auth/token-storage';
import type { AuthResponseDto } from '@/api/types/auth';

export const apiClient: AxiosInstance = axios.create({
  baseURL: env.apiUrl,
  timeout: env.apiTimeout,
  headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = tokenStorage.getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// One in-flight refresh shared by all concurrent 401s — without this, N parallel
// requests fire N refresh calls and the backend rotates the token N times.
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const { data } = await axios.post<AuthResponseDto>(
    `${env.apiUrl}/api/auth/refresh`,
    null,
    {
      headers: { Authorization: `Bearer ${tokenStorage.getRefreshToken()}` },
    }
  );
  tokenStorage.setTokens(data.accessToken, data.refreshToken);
  return data.accessToken;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const request = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    const shouldRefresh =
      error.response?.status === 401 &&
      !request?._retry &&
      !request?.url?.includes('/auth/refresh') &&
      !request?.url?.includes('/auth/login') &&
      !!tokenStorage.getRefreshToken();

    if (!shouldRefresh) return Promise.reject(error);

    request._retry = true;
    try {
      refreshPromise ??= refreshAccessToken();
      const token = await refreshPromise;
      refreshPromise = null;
      request.headers.Authorization = `Bearer ${token}`;
      return apiClient(request);
    } catch {
      refreshPromise = null;
      tokenStorage.clearTokens();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  }
);
```

**Обов'язкові деталі, які легко пропустити:**

- `_retry`-прапорець: без нього провальний refresh дає безкінечний цикл 401.
- Виключення `/auth/refresh` і `/auth/login` з логіки: інакше невірний пароль тригерить refresh.
- Дедуплікація `refreshPromise` (див. коментар у коді).
- Редірект на логін - лише в браузері (`typeof window`), інакше SSR падає.

---

## 3. `lib/auth/token-storage.ts` - ізольоване сховище

Єдиний модуль у проєкті, який знає, **де** лежить токен. Мета - щоб перехід
`localStorage → httpOnly cookie` був заміною цього файла.

```ts
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

// Dev servers run over http, where Secure cookies are not set — so tokens live in
// localStorage for now. Target state: httpOnly + Secure + SameSite cookies issued by
// the backend. Keep every storage detail inside this module so the swap is one file.
export const tokenStorage = {
  getAccessToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },

  clearTokens(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  },

  hasTokens(): boolean {
    return !!this.getAccessToken() && !!this.getRefreshToken();
  },
};
```

**Що це означає на практиці:**

- `localStorage.getItem('access_token')` не з'являється **більше ніде** в репо. Grep по
  `localStorage` у шарі компонентів має давати нуль результатів для токенів.
- Кожен getter захищений `typeof window` - шар API імпортується і на сервері.
- Коли бекенд віддасть cookie-сесію: методи стають no-op / читанням стану сесії, а решта
  коду не змінюється.
- Токени в `localStorage` = будь-який XSS краде сесію. Тому решта захисту від XSS
  (жодного `dangerouslySetInnerHTML` без санітизації, жодного `javascript:` в `href`)
  тут не «додаткова обережність», а компенсація цього компромісу.

Якщо в застосунку є **другий незалежний потік** зі власним токеном (публічна форма, опитування
за magic-link), йому потрібне окреме сховище (`sessionStorage`) і окремий інстанс клієнта:
проходження публічного потоку не має створювати глобальний логін.

---

## 4. `api/services/<domain>.service.ts`

```ts
import { apiClient } from '@/api';
import type {
  SurveyCreateDto,
  SurveyListParams,
  SurveyListResponseDto,
  SurveyResponseDto,
} from '@/api/types/surveys';

export const surveysService = {
  async listSurveys(
    companyId: string,
    params?: SurveyListParams
  ): Promise<SurveyListResponseDto> {
    const { data } = await apiClient.get<SurveyListResponseDto>(
      `/api/companies/${companyId}/surveys`,
      { params }
    );
    return data;
  },

  async getSurvey(
    companyId: string,
    surveyId: string
  ): Promise<SurveyResponseDto> {
    const { data } = await apiClient.get<SurveyResponseDto>(
      `/api/companies/${companyId}/surveys/${surveyId}`
    );
    return data;
  },

  async createSurvey(
    companyId: string,
    dto: SurveyCreateDto
  ): Promise<SurveyResponseDto> {
    const { data } = await apiClient.post<SurveyResponseDto>(
      `/api/companies/${companyId}/surveys`,
      dto
    );
    return data;
  },
};
```

- Метод = URL + generic-тип + `return data`. Ніяких `try/catch` (обробка - у хука/UI),
  ніякого мапінгу форми, ніяких тостів.
- Порядок аргументів однаковий у всьому файлі: спершу ідентифікатори шляху, потім `dto`,
  потім `params`.
- `@deprecated`-ендпоінт бекенду - позначай тим самим JSDoc-тегом і в сервісі, і в хуку.

---

## 5. `hooks/api/use-<domain>.ts`

```ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { surveysService } from '@/api/services/surveys.service';
import type { SurveyCreateDto, SurveyListParams } from '@/api/types/surveys';

export const surveysKeys = {
  all: ['surveys'] as const,
  list: (companyId: string, params?: SurveyListParams) =>
    [...surveysKeys.all, 'list', companyId, params] as const,
  detail: (companyId: string, surveyId: string) =>
    [...surveysKeys.all, 'detail', companyId, surveyId] as const,
};

export function useSurveys(companyId: string, params?: SurveyListParams) {
  return useQuery({
    queryKey: surveysKeys.list(companyId, params),
    queryFn: () => surveysService.listSurveys(companyId, params),
    enabled: !!companyId,
  });
}

export function useSurvey(companyId: string, surveyId: string) {
  return useQuery({
    queryKey: surveysKeys.detail(companyId, surveyId),
    queryFn: () => surveysService.getSurvey(companyId, surveyId),
    enabled: !!companyId && !!surveyId,
  });
}

export function useCreateSurvey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      companyId,
      dto,
    }: {
      companyId: string;
      dto: SurveyCreateDto;
    }) => surveysService.createSurvey(companyId, dto),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: surveysKeys.all });
    },
  });
}
```

**Конвенції:**

- **Keys-фабрика обов'язкова.** Інлайн-масив `['surveys', id]` у компоненті = неможлива
  адресна інвалідація. Кожна вітка починається з `...all`, щоб `invalidateQueries({ queryKey: all })`
  гасив увесь домен.
- `enabled: !!id` для кожного залежного параметра - інакше запит стріляє з `undefined` у URL.
- Мутація сама інвалідує свій домен. Інвалідацію в компоненті писати не треба.
- Мутація з кількома аргументами приймає **один об'єкт** - інакше `mutate` стає позиційним
  кошмаром.
- Трансформація форми відповіді - через `select`, а не переформатуванням у компоненті.
- Один файл на домен. Файл на кожен хук - зайва фрагментація; keys живуть поруч зі своїми хуками.

---

## 6. Дефолти query-client

```tsx
function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      // No retries: a failed backend response surfaces immediately instead of being
      // re-fired three times. The 401 refresh in the interceptor is token refresh,
      // not an error retry, so it is unaffected.
      queries: { staleTime: 0, retry: false },
      mutations: { retry: false },
    },
  });
}
```

Для SSR-фреймворків: на сервері - новий клієнт на кожен запит, у браузері - один сінглтон
(інакше дані одного користувача течуть в іншого).

---

## 7. Дренаж пагінації - лише коли інакше не виходить

Якщо бекенд не має серверного сортування/пошуку, а клієнту треба весь набір:

```ts
const PER_PAGE = 100;
// Safety ceiling: a bugged `hasNext` must never spin an infinite loop.
const MAX_PAGES = 50;

export async function fetchAllPages<T>(
  fetchPage: (
    page: number,
    perPage: number
  ) => Promise<{ resources: T[]; hasNext: boolean; total: number }>
): Promise<{ resources: T[]; total: number }> {
  const resources: T[] = [];
  let page = 1;
  let total = 0;

  while (page <= MAX_PAGES) {
    const result = await fetchPage(page, PER_PAGE);
    resources.push(...result.resources);
    total = result.total;
    if (!result.hasNext || result.resources.length === 0) break;
    page += 1;
  }

  return { resources, total };
}
```

Стеля циклу (`MAX_PAGES`) обов'язкова: баг у `hasNext` на бекенді не має вішати вкладку.
Для звичайних списків - справжня пагінація, а не дренаж.

---

## 8. Обробка помилок

- Спільна форма помилки - у `api/types/index.ts` (`ApiErrorResponse`), парсер повідомлення -
  в `utils/` (чиста функція), показ - у UI.
- Хук **не** показує тост сам: інакше кожен виклик дає дубль повідомлення. Тост - у місці
  виклику (`onError` у компоненті) або одним глобальним обробником у query-client, але не в обох.
- Поле помилки з бекенду не рендериться як HTML.

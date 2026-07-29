---
paths:
  - "**/*.{ts,tsx,js,jsx,mjs,cjs}"
  - "**/*.{vue,svelte,astro}"
  - "**/*.html"
---

# Чекліст безпеки для власного коду

**Кожен написаний тобою код перевіряй на вразливості. Робочий код, який можна зламати - це поганий код. Скануй не абстрактно «чи безпечно», а за конкретними патернами нижче.** Це крок 5 гейту завершення задачі, і він обовʼязковий для кожної кодової задачі.

- XSS - головне для фронтенду. Уникай `dangerouslySetInnerHTML`, `v-html`, `innerHTML`, `eval`, `new Function`, `href`/`:href` зі значенням `javascript:`. Якщо вставка HTML неминуча - санітизуй (DOMPurify). Памʼятай про DOM-based XSS через `location.hash`/`location.search`.
- Prototype Pollution - стережись саморобних `deepMerge`/`extend`, старого lodash, запису недовірених даних у `__proto__`/`constructor.prototype`.
- Витік секретів - жодних ключів і токенів у клієнтському бандлі (`NEXT_PUBLIC_`, `VITE_`, `REACT_APP_` видимі всім), у коді, у коментарях.
- Зберігання токенів - сесійні токени не в `localStorage`/`sessionStorage` (їх краде будь-який XSS), а в `httpOnly` + `Secure` + `SameSite` cookies.
- Open Redirect - не роби редірект на URL з user input (`location`, `router.push`, `redirect`) без allow-list або перевірки на відносний шлях.
- Broken Access Control / IDOR - клієнтський guard це UX, а не захист. Не покладайся на `role`/`isAdmin` зі стору як на гарантію, реальна авторизація завжди на бекенді. Те саме про валідацію: на клієнті вона для UX і має дублюватись на сервері.
- Reverse tabnabbing - `target="_blank"` тільки разом з `rel="noopener noreferrer"`.
- postMessage / CORS - перевіряй `event.origin`, не шли `postMessage(data, '*')`, не дозволяй `Access-Control-Allow-Origin: *` з credentials.
- Вразливі залежності - обережно з новими пакетами, звертай увагу на `npm audit`, остерігайся typosquatting.
- ReDoS - не став регулярки з катастрофічним бектрекінгом (`(a+)+`, вкладені квантифікатори) на user input.
- Injection - якщо фреймворк має серверну частину (API routes Next/Nuxt, server actions), стережись SQL/NoSQL/command injection, SSRF і надмірних GraphQL запитів.

Секрети і `.env` - у головному CLAUDE.md, бо діють у момент написання коду, а не на перевірці.

Вразливість у чужому коді не фікси мовчки - спершу повідом юзеру і дай йому вирішити.

Повний аудит усього проєкту (а не власного дифу) - це окрема задача для скіла `frontend-security-audit`.

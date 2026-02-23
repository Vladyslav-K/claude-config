# Backend Rules

## Stack Defaults (for new projects)
- **Framework:** Nest.js | **ORM:** Prisma | **Docs:** Swagger (@nestjs/swagger)
- **Validation:** class-validator + class-transformer | **Auth:** JWT + Passport.js

For existing projects — follow the established stack and patterns.

---

## 🚨 Database Safety

**NEVER execute without EXPLICIT user confirmation:**

`DROP DATABASE`, `DROP SCHEMA`, `DROP TABLE`, `TRUNCATE TABLE`, `DELETE` without `WHERE`, `prisma migrate reset`, `prisma db push --force-reset`, deleting migration files.

**Protocol:** STOP → EXPLAIN what will be deleted → ASK for confirmation → WAIT.

**Safe practices:** soft deletes (`deletedAt`), transactions, `prisma migrate dev` (dev) / `prisma migrate deploy` (prod).

---

## REST Conventions

| Action | Method | Endpoint | Codes |
|--------|--------|----------|-------|
| List | GET | /resources | 200 |
| Get | GET | /resources/:id | 200, 404 |
| Create | POST | /resources | 201, 400 |
| Update | PATCH | /resources/:id | 200, 404 |
| Delete | DELETE | /resources/:id | 204, 404 |

Naming: plural nouns, kebab-case, query params for filtering, nested routes for relations.

---

## Auth & Security Specifics
- Access tokens: 15-30 min | Refresh tokens: 7-30 days
- Passwords: bcrypt, min 10 rounds
- Never log/return passwords, tokens, stack traces, DB errors, internal paths in production
- Validate ALL inputs (DTOs, path params, query params, file uploads)

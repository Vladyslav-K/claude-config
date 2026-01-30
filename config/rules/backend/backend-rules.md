# Backend Development Rules

## Primary Tech Stack (for new projects)

- **Framework**: Nest.js (latest stable version)
- **ORM**: Prisma
- **API Documentation**: Swagger via @nestjs/swagger
- **Validation**: class-validator + class-transformer
- **Authentication**: JWT with Passport.js

For **existing projects**, always follow the established stack and patterns.

---

## 🚨 CRITICAL: Database Safety 🚨

### ABSOLUTELY FORBIDDEN Operations

**NEVER execute without EXPLICIT user confirmation:**

| Operation | Why Dangerous |
|-----------|---------------|
| `DROP DATABASE` | Destroys entire database |
| `DROP SCHEMA` | Destroys schema with all tables |
| `DROP TABLE` | Permanent data loss |
| `TRUNCATE TABLE` | Deletes all rows instantly |
| `DELETE` without `WHERE` | Deletes all records |
| `prisma migrate reset` | Drops and recreates database |
| `prisma db push --force-reset` | Forces schema, loses data |
| Deleting migration files | Breaks migration history |

### Before ANY Destructive Operation

1. **STOP** - Do not proceed automatically
2. **EXPLAIN** - Tell user exactly what will be deleted/modified
3. **CONFIRM** - Ask: "This will permanently delete [X]. Type 'CONFIRM DELETE' to proceed."
4. **WAIT** - Only proceed after explicit confirmation

### Safe Practices

- Use **soft deletes** (deletedAt field) instead of hard deletes
- Always use **transactions** for multi-step operations
- Run migrations on **development first**, then production
- **Never** modify production data without backup confirmation
- Use `prisma migrate dev` for development, `prisma migrate deploy` for production

---

## API Design Principles

### REST Conventions

| Action | Method | Endpoint | Status Codes |
|--------|--------|----------|--------------|
| List | GET | /resources | 200 |
| Get one | GET | /resources/:id | 200, 404 |
| Create | POST | /resources | 201, 400 |
| Update | PATCH | /resources/:id | 200, 404, 400 |
| Replace | PUT | /resources/:id | 200, 404, 400 |
| Delete | DELETE | /resources/:id | 204, 404 |

### Response Format

```typescript
// Success
{
  data: T | T[],
  meta?: { total, page, limit }
}

// Error
{
  statusCode: number,
  message: string | string[],
  error: string
}
```

### Naming Conventions

- Use **plural nouns** for resources: `/users`, `/products`
- Use **kebab-case** for multi-word: `/order-items`
- Use **query params** for filtering: `?status=active&sort=createdAt`
- Use **nested routes** for relations: `/users/:id/orders`

---

## Validation Rules

### Always Validate

- All incoming request bodies (DTOs)
- All path parameters
- All query parameters
- File uploads (type, size, content)

### DTO Pattern (Nest.js)

```typescript
import { IsEmail, IsString, MinLength, IsOptional } from 'class-validator';

export class CreateUserDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(8)
  password: string;

  @IsString()
  @IsOptional()
  name?: string;
}
```

### Validation Pipe Setup

```typescript
app.useGlobalPipes(new ValidationPipe({
  whitelist: true,        // Strip unknown properties
  forbidNonWhitelisted: true,  // Throw on unknown properties
  transform: true,        // Auto-transform types
}));
```

---

## Error Handling

### Use Built-in Exceptions

```typescript
throw new NotFoundException('User not found');
throw new BadRequestException('Invalid email format');
throw new UnauthorizedException('Invalid credentials');
throw new ForbiddenException('Access denied');
throw new ConflictException('Email already exists');
throw new InternalServerErrorException('Something went wrong');
```

### Global Exception Filter

Create a global filter to standardize all error responses and log errors appropriately.

### Never Expose

- Stack traces in production
- Database error details
- Internal paths or configurations
- Sensitive user data in error messages

---

## Authentication & Authorization

### JWT Best Practices

- Use short-lived access tokens (15-30 minutes)
- Use long-lived refresh tokens (7-30 days)
- Store refresh tokens securely (httpOnly cookies or database)
- Implement token rotation on refresh
- Blacklist tokens on logout

### Password Security

- Hash with bcrypt (minimum 10 rounds)
- Never log or return passwords
- Implement rate limiting on login
- Use secure password requirements

### Authorization Pattern

```typescript
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('admin')
@Get('admin/users')
getAdminUsers() {}
```

---

## Prisma Best Practices

### Schema Design

- Use `@id` with `@default(cuid())` or `@default(uuid())`
- Add `createdAt` and `updatedAt` to all models
- Use `@relation` with explicit names
- Add indexes for frequently queried fields

### Query Optimization

- Use `select` to fetch only needed fields
- Use `include` sparingly (watch for N+1)
- Use pagination for large datasets
- Use transactions for related operations

### Migration Workflow

```bash
# Development - creates migration and applies
prisma migrate dev --name descriptive_name

# Production - applies pending migrations
prisma migrate deploy

# Generate client after schema changes
prisma generate
```

---

## Security Checklist

- [ ] All inputs validated and sanitized
- [ ] SQL injection prevented (Prisma handles this)
- [ ] XSS prevented in any rendered content
- [ ] CORS configured properly
- [ ] Rate limiting implemented
- [ ] Helmet middleware for security headers
- [ ] Sensitive data encrypted at rest
- [ ] HTTPS enforced in production
- [ ] Environment variables for secrets
- [ ] No secrets in code or logs

---

## Logging

### What to Log

- All incoming requests (method, path, user)
- All errors with stack traces (dev) or error codes (prod)
- Authentication events (login, logout, failed attempts)
- Important business events
- Performance metrics for slow queries

### What NOT to Log

- Passwords or tokens
- Full credit card numbers
- Personal data (depending on compliance)
- Sensitive business data

---

## Environment Variables

### Required Variables

```env
DATABASE_URL=
JWT_SECRET=
JWT_EXPIRES_IN=
PORT=
NODE_ENV=
```

### Best Practices

- Never commit `.env` files
- Use `.env.example` as template
- Validate all env vars on startup
- Use different values per environment

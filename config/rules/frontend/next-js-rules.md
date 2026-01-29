### Core Concepts

- Utilize **App Router** for routing.
- Implement proper **metadata management**.
- Use proper **caching strategies**.
- Implement proper **error boundaries**.
- Prefer **functional and declarative programming patterns** over imperative.

### Components and Features

- Use Next.js built-in components:
  - **`Image` component** for optimized images.
  - **`Link` component** for client-side navigation.
  - **`Script` component** for external scripts.
  - **`Head` component** for metadata.
- Implement proper **loading states**.
- Use proper **data fetching methods**.

### Server Components

- **Default to Server Components**.
- Use **URL query parameters** for data fetching and server state management.
- Use `'use client'` directive only when necessary:
  - Event listeners
  - Browser APIs
  - State management
  - Client-side-only libraries

---

## TypeScript Implementation

- Enable **strict mode**.
- Define clear **interfaces** for component props, state structure.
- Use **type guards** to handle potential `undefined` or `null` values safely.
- Apply **generics** to functions, actions, and slices where type flexibility is needed.
- Utilize **TypeScript utility types** (`Partial`, `Pick`, `Omit`) for cleaner and reusable code.
- Prefer **`interface` over `type`** for defining object structures, especially when extending.
- Use **mapped types** for creating variations of existing types dynamically.
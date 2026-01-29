#### General Rules

- Use **PascalCase** for:
  - Components
  - Type definitions
  - Interfaces
- Use **kebab-case** for:
  - Directory names (e.g., `components/auth-wizard`)
  - File names (e.g., `user-profile.tsx`)
- Use **camelCase** for:
  - Variables
  - Functions
  - Methods
  - Hooks
  - Properties
  - Props
- Use **UPPERCASE** for:
  - Environment variables
  - Constants
  - Global configurations

#### Specific Naming Patterns

- Prefix event handlers with `'handle'`: `handleClick`, `handleSubmit`.
- Prefix boolean variables with verbs: `isLoading`, `hasError`, `canSubmit`.
- Prefix custom hooks with `'use'`: `useAuth`, `useForm`.
- Use **complete words over abbreviations** except for:
  - `err` (error)
  - `req` (request)
  - `res` (response)
  - `props` (properties)
  - `ref` (reference)
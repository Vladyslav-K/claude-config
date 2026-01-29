### Component Architecture

- Use **functional components with TypeScript interfaces**.
- Define components using the **`function` keyword**.
- Extract reusable logic into **custom hooks**.
- Implement proper **component composition**.
- Use **`React.memo()`, `useCallback`, `useMemo` strategically** for performance.
- Implement proper **cleanup in `useEffect` hooks**.

### React Performance Optimization
- Don't use raw functions inside components and pages, all methods must start with const.
- Use **`useCallback`** for memoizing callback functions.
- Implement **`useMemo`** for expensive computations.
- **Avoid inline function definitions in JSX**.
- Implement **code splitting** using dynamic imports.
- Implement proper **`key` props in lists** (avoid using index as key).

### State Management

- Use **`useState`** for component-level state.
- Implement **`useReducer`** for complex state.
- Use **`useContext`** for shared state.
- Implement proper **state initialization**.
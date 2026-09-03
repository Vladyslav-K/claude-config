## APE-364: persona-aware navigation, default landing, section gate and Access Denied

### What was done

**Section model (`local/config/sections.ts`, `local/constants/paths.ts`)**

- One config maps every backend `Section` (`dashboard`, `crew_members`, `reports`, `policyholders`, `email_and_documents`, `users`) to its route, label and icon. Labels and order follow the PRD: Dashboard, Crew Members, Reports, Policyholders, Email & Documents, Users.
- New paths `/reports`, `/email-and-documents`, `/users`; the old `/mta-premium-reports`, `/templates-and-docs`, `/manage-users` are removed together with every usage.

**Rail built from `me.sections` (`nav-items.config.ts`, `app-layout.tsx`)**

- `buildRailGroups(sections)` filters the PRD list by what the session grants and sorts by the PRD order, not by the order the backend sent. The rail is split as the design draws it: a divider after the first three items; a persona with three items or fewer gets a single group.
- Both the desktop rail and the mobile drawer take the result. Sections the session does not grant are absent from the DOM, not hidden by CSS.
- The design-system showcase keeps its three MGA sets, now derived from the same function (MGA admin, broker admin, TPA admin).

**Section gate (`routes/section-route.tsx`, `routes/router.tsx`)**

- Six routes under `ProtectedRoute`, one per section, each wrapped in `SectionRoute`. A session without the section renders the Access Denied page in place: the URL stays, nothing redirects, and the page behind the gate is never mounted, so no data request goes out.
- The gate re-evaluates on every navigation: the route remounts and `useMe` (now explicitly `staleTime: 0`, `refetchOnWindowFocus: true`) refetches on mount and on returning to the tab. A permission change in the database reaches the rail and the gate after the next refetch, without a reload.
- Each section route carries a `handle` with its title and section; the topbar shows the section name for a granted page and "Error 403" for a denied one.

**Default landing (`pages/home-page.tsx`, `routes/persona-routes.ts`)**

- `/` redirects to the persona landing: `/dashboard` when `sections` contains `dashboard`, otherwise `/crew-members` (TPA). OTP verify already lands the same way.
- `persona-routes.ts` holds the three helpers used everywhere: `hasSectionAccess`, `getPersonaHomeSection`, `getPersonaHomePath`.

**Section pages (`modules/SectionPlaceholder`, `pages/*-page.tsx`)**

- Six thin pages render `SectionPlaceholder`, which names the section and states that the content arrives in a later phase. There is no design for these; they use the project tokens only.

**Error pages (`modules/ErrorPages`)**

- The way back on 403, 404 and 500 now points at the persona landing instead of a fixed `/dashboard`. The label follows the landing: "Back to dashboard" as on the design, "Back to crew members" for a TPA. 401 keeps "Back to sign in".

### How to test

Prerequisites: local API on `http://localhost:8080` with an active AWS session, admin-web on `http://localhost:8001`, Cognito users linked to `app_users` rows. A full run needs one user per persona (MGA, Broker, Policyholder, TPA); the capability cases need `can_manage_users` toggled in the database.

1. **MGA rail**: sign in as an MGA user without `can_manage_users`. Expect landing on `/dashboard` and the rail Dashboard, Crew Members, Reports | Policyholders, Email & Documents. With `can_manage_users = true` the Users item appears after Email & Documents.
2. **Broker / Policyholder rail**: expect landing on `/dashboard` and Dashboard, Crew Members, Reports in one group. With the capability, Users is added after a divider.
3. **TPA rail**: expect landing on `/crew-members` and a single Crew Members item, no divider. With the capability, Crew Members | Users.
4. **Direct URL on a closed section**: as a TPA, open `/users` or `/dashboard` by typing the address. Expect the Access Denied page inside the shell, topbar "Error 403", the URL unchanged, no request for the section's data in the network tab, and no flash of the page behind it.
5. **Back button on Access Denied**: click the button. Expect `/dashboard` with "Back to dashboard" for MGA, Broker and Policyholder; `/crew-members` with "Back to crew members" for TPA. The same applies to `/not-found` and `/server-error`.
6. **Root redirect**: open `/` while signed in. Expect the persona landing without an intermediate screen.
7. **Permission change without reload**: while signed in, flip `can_manage_users` in the database. Navigate between two sections, or leave and return to the tab. Expect Users to appear or disappear in the rail and `/users` to switch between the page and Access Denied on the next navigation.
8. **History navigation**: visit a section, revoke it in the database (change `persona`), then use browser back/forward onto that section. Expect Access Denied rendered in place.
9. **Mobile drawer**: at a width below 768px open the burger menu. Expect the same items as the desktop rail; choosing one closes the drawer.
10. **Unknown URL**: open `/anything`. Expect the 404 page with the persona back button.
11. **Design-system showcase** (`/design-system`, dev only): the four rail sets render with the new labels.

### Notes and known limitations

- The rail labels and order follow the PRD, not the old navigation board (which still reads MTA Premium Reports, Templates & Docs, Manage Users). This is a deliberate decision to be reported to the client.
- Section pages are placeholders without a design; their content belongs to later phases.
- The client-side gate is UX only. The API enforces the same `permittedSections` on every request; a revoked capability closes the administrative routes on the backend immediately and on the frontend after the next `me` refetch.
- Invalidation of the `me` query on a `403 ACCESS_DENIED` API response is part of the next task (T1.19); this PR only sets the query options it relies on.
- `modules/Home` no longer has a consumer and is left in place pending a decision on removing it.
- A Crew App persona (empty `sections`) is redirected from `/` to `/crew-members` and sees Access Denied there; the portal has nothing to show that persona by design.

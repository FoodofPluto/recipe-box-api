# Caching and stale-data behavior

## 1. Stale cache reproduction

Sequence (before the fix):

1. `GET /recipes`
2. `POST /recipes` with a new, unique title
3. `GET /recipes` again within 60 seconds

Result:

- Step 2 returned `201` with the new recipe in the response body.
- Step 3 **did not** include the new recipe in the list.
- Conclusion: the database was updated, but the cached `GET /recipes` response stayed stale until the 60 second timeout.

## 2. Fix: write-path cache invalidation

Change:

- In `POST /recipes`, after `db.session.commit()`, call `cache.clear()` to invalidate the cached `GET /recipes` response whenever recipes change.

Sequence (after the fix):

1. `GET /recipes` (warms the cache)
2. `POST /recipes` with a new, unique title
3. `GET /recipes` immediately after

Result:

- Step 2 returned `201` with the new recipe.
- Step 3 **did** include the new recipe in the list, and the response size increased.
- Conclusion: the cache is cleared on write, so the next `GET /recipes` fetches fresh data and re-populates the cache.

## 3. Endpoints that must never be cached

These endpoints should not be cached:

- `POST /recipes`  
  - Mutates data (creates new recipes); must always hit the database and apply immediately.

- `PUT/PATCH /recipes/<id>`  
  - Mutates existing recipes; caching responses here could hide recent changes.

- `DELETE /recipes/<id>`  
  - Deletes recipes; cached responses might still show deleted data.

- Authentication endpoints: `/login`, `/register`, `/me`  
  - Responses are authentication- and user-specific, may include tokens or private info.

- Any user-specific dashboard/profile endpoints  
  - Depend on the caller’s identity and can expose private data; must always be fresh per user.
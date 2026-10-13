# Refactor plan

## Target layout (high level)

- auth: user registration, login, token validation, before_request checks
- recipes: recipe CRUD routes and logic
- data: SQLite connection and query helpers
- app startup: create Flask app, wire routes, run server


## Acceptance list (public API)


| Method | Path | Success | Errors |
|---|---|---|---|
| GET | /recipes | 200 | |
| GET | /recipes/&lt;id&gt; | 200 | 404 |
| POST | /recipes | 201 | 400 bad body · 409 duplicate title |
| PATCH | /recipes/&lt;id&gt; | 200 | 400 · 404 · 409 |
| DELETE | /recipes/&lt;id&gt; | 204 | 404 |

`is_public` is stored on every recipe but nothing enforces it yet - by the end
of Unit 3, private recipes will only be visible to their owners.
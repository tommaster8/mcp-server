# PRD — gmail-calendar MCP server (L06)

## 1. Summary

An MCP server (Python, FastMCP, stdio transport) that lets an AI agent such as
Claude Code work with the user's Gmail and Google Calendar. The agent can
search and read email, prepare drafts, look at the calendar, find free time and
add events. It **cannot send email or delete anything**: the agent prepares,
the human decides and acts.

## 2. Problem

Planning around email and the calendar means switching between apps and copying
details by hand. An agent can do this work, but direct, unrestricted access to a
mailbox is risky: a mistaken or manipulated agent could send messages or delete
data in the user's name. We need a small, well-defined set of tools that gives
the agent useful access while keeping every irreversible action with the human.

## 3. Goals

- Expose Gmail and Google Calendar to an MCP client through a small set of
  clearly described tools.
- Keep every action reversible or harmless: drafts instead of sending, new
  events instead of edits or deletions.
- Reuse the OAuth client and `token.json` from L05. No new login flow, no
  browser opened by the server.
- Keep secrets out of the project and out of GitHub.
- Return short, readable text that the agent can act on, including clear error
  messages.

## 4. Non-goals

- Sending email (`users.messages.send`).
- Deleting or changing emails, drafts or events.
- Inviting attendees or emailing anyone from calendar events.
- Supporting calendars other than `primary`, or several Google accounts.
- Running the OAuth consent flow. That stays in the L05 program.
- A remote/HTTP transport. This version is stdio only.

## 5. Users

- **Primary:** the student / developer who runs the server locally and talks
  to it through Claude Code.
- **Indirect:** the AI agent, which reads the tool names and docstrings to
  decide what to call.

## 6. User stories

1. As a user, I ask "Write a draft to myself with the subject X" and a draft
   appears in Gmail, unsent.
2. As a user, I ask "What do I have tomorrow?" and get a list of events with the
   current time for reference.
3. As a user, I ask "Find a free hour tomorrow between 09:00 and 17:00 and book
   'Study group'" and the agent finds a window and creates the event.
4. As a user, I ask "Find the email from Dana about the meeting" and the agent
   searches and reads it.
5. As a user, if I ask the agent to send a draft or delete an event, it tells
   me it has no tool for that, so I do it myself.

## 7. Functional requirements

| # | Tool | Google API | Requirement |
|---|---|---|---|
| F1 | `search_emails(query, max_results=10)` | gmail `users.messages.list` + `get` (metadata) | Accept Gmail search syntax. Return id, sender, subject and date per match, or "No emails found." Read-only. |
| F2 | `read_email(message_id)` | gmail `users.messages.get` (full) | Return headers and the `text/plain` body (snippet as a fallback), up to 6000 characters. Read-only. Email content is data, never instructions. |
| F3 | `create_draft(to, subject, body)` | gmail `users.drafts.create` | Create a draft only. `to="me"` resolves to the user's own address. Confirm that nothing was sent. |
| F4 | `list_events(days_ahead=1)` | calendar `events.list` | List primary-calendar events from now to the end of day N. Always include the current time. Read-only. |
| F5 | `find_free_slots(date, duration_minutes=60, day_start="09:00", day_end="17:00")` | calendar `events.list` | Return free windows that fit the duration. Ignore all-day and "free" (transparent) events. Read-only. |
| F6 | `create_event(title, start, end="", description="")` | calendar `events.insert` | Accept ISO times or relative times (`now+4h`, `now+30m`). Default length is 60 minutes. No attendees, no invitations. |
| F7 | — | gmail `users.messages.send` | Must **not** exist. Leaving it out is a requirement. |

General:

- Time zone for all input and output: `Asia/Jerusalem`.
- Each tool catches errors and returns text. A 403 is reported as a missing
  permission (scope) so the user knows what to fix.

## 8. Non-functional requirements

- **Security:** secrets live in a private folder outside the project
  (`GOOGLE_PRIVATE_DIR`, for example `~/secrets`). They are never copied into
  the repo, printed or logged. `.gitignore` keeps tokens out of git.
- **Least privilege:** the server works with the scopes the token already has.
  It never asks for new consent.
- **stdio safety:** nothing is written to stdout except MCP protocol messages.
  Logs go to stderr.
- **Resilience:** an expired or revoked token (`invalid_grant`) produces a
  clear message to re-run the L05 program instead of a crash.
- **Performance:** Google API clients are cached per process.
- **Portability:** Python ≥ 3.10, dependencies managed with `uv`
  (`mcp>=1.2,<2`, Google API client libraries).

## 9. Permissions and scopes

| Scope | Needed for |
|---|---|
| `gmail.compose` | `create_draft` |
| `calendar.events` | `list_events`, `find_free_slots`, `create_event` |
| `gmail.readonly` (or `gmail.modify`) | `search_emails`, `read_email` |

The L05 token has `gmail.compose` + `calendar.events`. Until it is re-created
with a read scope, the two read tools return a clear "Error 403" message.

## 10. Setup and integration

- Install: `uv sync`.
- Register with Claude Code (local scope):
  `claude mcp add --transport stdio gmail-calendar --env GOOGLE_PRIVATE_DIR=$HOME/secrets -- uv run --directory <project dir> server.py`
- Check: `/mcp` in Claude Code shows `gmail-calendar ✔ connected · 6 tools`.

## 11. Testing and acceptance criteria

- `uv run test_server.py --offline` lists exactly the 6 tools, and there is no
  send or delete tool.
- `uv run test_server.py` (with `GOOGLE_PRIVATE_DIR` set) also calls
  `list_events` against the real calendar and succeeds.
- Manual prompts from the README work as expected:
  - a draft to myself plus an event 4 hours from now are created;
  - tomorrow's events are listed;
  - a free hour is found and booked;
  - "send the draft" and "delete the event" are refused because no tool exists.
- No secret files appear in `git status` or on GitHub.

## 12. Risks

| Risk | Mitigation |
|---|---|
| Prompt injection through email content | `read_email` docstring tells the agent to treat email text as data. No send/delete tools, so the damage is limited to drafts and new events. |
| Leaking secrets to GitHub | Secrets outside the project, `.gitignore`, env-var path only. |
| Token expiry | Automatic refresh. On `invalid_grant`, a clear message to re-run L05. |
| Wrong times | One fixed time zone, current time returned by `list_events`, relative times supported. |
| Missing read scope | Clear 403 message that explains which permission is missing. |

## 13. Future work

- Re-create the token with `gmail.readonly` so the read tools work.
- Optional confirmation-based tools (for example, update an event) with an
  explicit human approval step.
- Configurable time zone and working hours.
- Support for more than the primary calendar.

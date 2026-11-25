# gmail-calendar — MCP server (L06)

An MCP server (Python, FastMCP, stdio) that exposes Gmail and Google Calendar
as tools for an AI agent. It reuses the Google OAuth client and `token.json`
from L05. **There is no tool that sends email or deletes anything.**

## Tools

| Tool | Google API call | What it does |
|---|---|---|
| `search_emails(query, max_results)` | gmail `users.messages.list` | Search emails (Gmail search syntax) |
| `read_email(message_id)` | gmail `users.messages.get` | Read one email |
| `create_draft(to, subject, body)` | gmail `users.drafts.create` | Create a DRAFT only (`to="me"` = yourself) |
| `list_events(days_ahead)` | calendar `events.list` | Upcoming events + the current time |
| `find_free_slots(date, duration_minutes)` | calendar `events.list` | Free windows on a day (09:00–17:00 by default) |
| `create_event(title, start, end, description)` | calendar `events.insert` | New event; `start` may be ISO or `now+4h` |
| ✗ (none) | gmail `users.messages.send` | Left out on purpose: the agent prepares, the human sends |

Time zone: `Asia/Jerusalem`.

## Secrets

The secrets stay in the private folder from L05 (here: `~/secrets`), **never in this project**:

```
~/secrets/
├── client_secret_….json   ← OAuth client
└── token.json             ← access token (created by the L05 program)
```

The server finds them through the environment variable `GOOGLE_PRIVATE_DIR`.
It never opens a browser. If the token expired (`invalid_grant`), run the L05
program again to renew `token.json`.

**Note on permissions:** the L05 token was created with the scopes
`gmail.compose` + `calendar.events`. That is enough for `create_draft`,
`list_events`, `find_free_slots` and `create_event`. `search_emails` and
`read_email` need a read scope (`gmail.readonly` or `gmail.modify`). Until the
token is re-created with that scope they return a clear "Error 403" message.

## Run & test

```bash
cd ~/lesson06
uv sync
GOOGLE_PRIVATE_DIR=~/secrets uv run test_server.py            # tools/list + list_events
GOOGLE_PRIVATE_DIR=~/secrets uv run test_server.py --offline  # tools/list only
```

## Register in Claude Code (local scope)

```bash
claude mcp add --transport stdio gmail-calendar \
  --env GOOGLE_PRIVATE_DIR=$HOME/secrets -- uv run --directory $HOME/lesson06 server.py
```

Then restart `claude` and type `/mcp` → `gmail-calendar ✔ connected · 6 tools`.
The registration is saved in `~/.claude.json` (outside the project, not on GitHub).

## Prompts used today

1. `Write a Gmail draft to myself with the subject "L06 test" and add a calendar event for today, 4 hours from now, called "MCP works".`
2. `What do I have in my calendar tomorrow?`
3. `Find a free hour tomorrow between 09:00 and 17:00 and add an event called "Study group" there.`
4. `Great. Now send the "L06 test" draft.` → the agent has no tool for that.
5. `Delete the "Study group" event.` → the agent has no tool for that.

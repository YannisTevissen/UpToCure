# disease_requests/

When a visitor submits the "Request a report" form, the backend writes a
small JSON file in this directory containing the requested disease name,
language, timestamp, originating IP and user agent.

Files look like `request_20260520_134512_873145.json`. They are used to
prioritise future report generation and are not surfaced anywhere else.

This directory is **gitignored**; nothing in here is shipped with the repo.

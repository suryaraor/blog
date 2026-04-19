# blog

## Unlisted Posts

- Posts in [_unlisted](_unlisted) are published under `/unlisted/...`.
- Unlisted posts get `robots: noindex, nofollow` and `sitemap: false` by default via [_config.yml](_config.yml).

## Auto-Move Sensitive Posts

Use [scripts/move_sensitive_posts_to_unlisted.ps1](scripts/move_sensitive_posts_to_unlisted.ps1) to move sensitive posts from [_posts](_posts) to [_unlisted](_unlisted).

Dry run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/move_sensitive_posts_to_unlisted.ps1" -WhatIf
```

Execute:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts/move_sensitive_posts_to_unlisted.ps1"
```

## Comments and Likes

This blog includes a free comments and likes system that uses Google Apps Script and Google Sheets, so it works with a fully static GitHub Pages site.

### Repo files

- [Apps Script backend](scripts/comments-webapp.gs)
- [Post include](_includes/post-interactions.html)
- [Frontend JavaScript](assets/js/post-interactions.js)
- [Frontend CSS](assets/css/post-interactions.css)
- [Post layout hook](_layouts/post.html)

### Setup summary

1. Create a Google Sheet with `comments`, `likes`, and optional `summary` tabs.
2. Paste [scripts/comments-webapp.gs](scripts/comments-webapp.gs) into a Google Apps Script project.
3. Set Script Properties:
	- `SPREADSHEET_ID` = your Google Sheet ID
	- `LIKES_SALT` = a long random string
4. Deploy the script as a web app with access set to `Anyone`.
5. Copy the web app URL into `comments_api_url` in [_config.yml](_config.yml).
6. Approve comments in the Google Sheet by changing `status` from `pending` to `approved`.

### Notes

- Reads use GET requests and writes use simple form-encoded POST requests to avoid unnecessary CORS preflight.
- The frontend only renders approved comments.
- Likes are deduplicated per browser using localStorage and a generated visitor id.
- A daily summary rebuild helper is included in the Apps Script backend if you want aggregate counts refreshed automatically.
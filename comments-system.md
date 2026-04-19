# Comments and Likes System

This blog uses a free Google Apps Script + Google Sheets backend for post comments and likes.

## Files in this repo

- [Google Apps Script backend](scripts/comments-webapp.gs)
- [Post include](_includes/post-interactions.html)
- [Frontend JavaScript](assets/js/post-interactions.js)
- [Frontend CSS](assets/css/post-interactions.css)
- [Post layout hook](_layouts/post.html)

## One-time setup

1. Create a Google Sheet with tabs named `comments`, `likes`, and optionally `summary`.
2. Open Apps Script from the Sheet or a standalone project.
3. Paste the contents of [scripts/comments-webapp.gs](scripts/comments-webapp.gs) into the Apps Script editor.
4. Set Script Properties:
   - `SPREADSHEET_ID` = your Google Sheet ID
   - `LIKES_SALT` = any long random string
5. Deploy as a web app:
   - Execute as: `Me`
   - Who has access: `Anyone`
6. Copy the web app URL into `_config.yml` under `comments_api_url`.

## Moderation

- New comments are inserted as `pending`.
- Approve or reject comments directly in the Google Sheet by changing `status` to `approved` or `spam`.
- The frontend only displays approved comments.

## Notes

- The frontend uses simple GET and form-encoded POST requests to avoid unnecessary CORS preflight.
- If Google changes web app behavior, keep the GET endpoints for reads and form-encoded POST for writes.
- The summary tab is optional; the Apps Script can rebuild it on demand or via a daily trigger.
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
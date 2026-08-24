# Legacy GitHub Pages Library → modern SwR Library Web handoff

Status: **live legacy surface preserved; migration and retirement decision pending**

## Repositories

```text
Legacy static/PWA surface
  SyllabuswithRohit/syllabuswithrohit.github.io
  GitHub Pages-oriented HTML, book pages, manifest and service worker

Modern production-track website
  SyllabuswithRohit/syllabuswithrohit-web
  Next/Vinext, Cloudflare Worker, private EPUB Studio, KV-backed books and current product surfaces
```

This document does not redirect, deploy, remove or archive the legacy site. It records the evidence required before any such action.

## Current legacy value

The static repository includes:

- a public Library landing page;
- individual local HTML book pages;
- a manifest and installable PWA shell;
- service-worker caching for the Library shell and visited pages;
- theme/fullscreen controls;
- public support/payment handoffs;
- existing links that may still be bookmarked, indexed or installed.

Do not assume the repository is unused merely because the modern website exists.

## Integrity work in this branch

- service-worker installation now awaits all independent cache attempts;
- one external CDN failure no longer prevents installation;
- runtime page caching is restricted to successful same-origin HTML/book responses;
- uncached offline navigation returns the local Library shell instead of resolving without a `Response`;
- non-navigation offline misses receive a bounded `504` response;
- the cache generation is incremented so old behavior is retired on activation;
- an offline validator checks tracked HTML links/assets, duplicate IDs, image alt text, manifest targets, service-worker shell targets, insecure URLs, private-key markers and credential-like tokens;
- focused tests exercise complete, missing-target, accessibility and offline-response fixtures;
- a local HTTP smoke gate serves and retrieves the exact checked-out tree.

## Migration inventory

Before a redirect or archival decision, compare and record:

| Legacy surface | Modern disposition required |
|---|---|
| Root Library landing page | canonical modern destination and redirect behavior |
| Every local book URL | exact modern Work/Edition destination or durable historical page |
| Browser/PWA installs | update/retirement behavior and user notice |
| Service-worker caches | old-cache invalidation and offline implications |
| Themes/fullscreen | equivalent reader support or documented difference |
| Hinglish/static translations | rights, edition, revision and completeness mapping |
| Search/indexed URLs | canonical, sitemap and redirect treatment |
| Support links | exact owner-approved modern destination |
| QR/UPI handoff | privacy, current ownership and user-intent review |
| External Buy Me a Coffee link | current ownership and policy review |
| Public profile image | current brand/consent decision |

## URL preservation rule

Do not remove a legacy book page until one of these is true:

1. the exact URL remains available as an intentionally preserved historical page; or
2. a permanent redirect reaches an equivalent, reviewed modern Work/Edition page; or
3. the owner explicitly approves removal after inbound-link and content-rights review.

A generic redirect of every book to the modern home page is not equivalent preservation.

## Deployment and rollback

Any live GitHub Pages change requires:

- exact branch/commit and Pages source confirmation;
- clean static integrity workflow;
- before/after URL inventory;
- manual mobile and installed-PWA smoke;
- service-worker update and cache behavior check;
- support-link verification without recording payment credentials;
- rollback commit or branch reference;
- post-deploy checks from an independent browser profile.

If navigation, offline access or a support link regresses, restore the prior known-good Pages commit and investigate on a new branch.

## Exit criteria

The legacy repository can be marked historical only after:

- every public URL has a disposition;
- modern Work/Edition and reader parity is reviewed;
- PWA/service-worker retirement behavior is tested;
- search/indexing and redirects are verified;
- support/payment handoffs are re-approved;
- no local-only content remains outside Git;
- the owner explicitly approves the migration state.

Historical status should preserve Git history and an explanatory README. It does not require deleting the repository.

## Release boundary

This handoff does not authorize a production redirect, GitHub Pages deployment, Cloudflare deployment, payment change, content publication, rights claim or repository deletion.

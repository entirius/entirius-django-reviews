# Changelog

## Unreleased

- Keys verified by django-access when installed: the X-API-KEY routes check access tokens through
  `verify_api_key` (scope `reviews.moderate` on the URL channel — a pinned token passes on its own
  channel only), never the legacy table; the refusal stays
  401 "Invalid api key". Without django-access nothing changes. `reviews-generate-api-key` then refuses and
  names `access_token create`; the key admin becomes read-only.
- The key admin shows only the last four characters of a key.
- The moderation PATCH with a channel-pinned access token finds only that channel's reviews (404 for another
  channel's UUID); unpinned and legacy keys keep reaching every review.

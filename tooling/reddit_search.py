#!/usr/bin/env python3
"""Read-only Reddit search — standalone replica of the DSH reddit_search tool.

Same endpoints, bounds, and safety rules as /home/drewp/main-projects/reddit/src/reddit.ts:
GET-only JSON endpoints, cookie never forwarded through redirects, bounded
excerpts, no account actions of any kind.

Cookie source (never printed, never written by this script):
  1. env var (default DSH_REDDIT_COOKIE), or
  2. ~/.dsh/.credentials.yaml -> refs.REDDIT_SESSION_COOKIE

Usage:
  python3 reddit_search.py "realpage" --subreddit PropertyManagement --limit 5 --comments 2
  python3 reddit_search.py "realpage lease" --sort new --time year --limit 10 --out /tmp/reddit.json
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

ORIGIN = "https://www.reddit.com"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
MAX_POST_CHARS = 600
MAX_COMMENT_CHARS = 400
CRED_FILE = pathlib.Path.home() / ".dsh" / ".credentials.yaml"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects: never forward the session cookie off-origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def load_cookie(env_var: str) -> str:
    cookie = (os.environ.get(env_var) or "").strip()
    if cookie:
        return cookie
    if CRED_FILE.exists():
        import yaml  # local import: only needed for the fallback path

        refs = (yaml.safe_load(CRED_FILE.read_text()) or {}).get("refs") or {}
        value = refs.get("REDDIT_SESSION_COOKIE")
        if isinstance(value, str) and value.strip():
            return value.strip()
    sys.exit(
        f"No Reddit session cookie. Set env {env_var} or save it in DSH "
        "(Settings -> Plugins -> Reddit)."
    )


def get_json(url: str, cookie: str, timeout: int = 25) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Cookie": cookie,
            "User-Agent": UA,
            "Accept-Encoding": "identity",
        },
        method="GET",
    )
    try:
        with OPENER.open(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
            content_type = (response.headers.get("Content-Type") or "").lower()
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            sys.exit(f"Reddit rejected the session (HTTP {error.code}). Replace the cookie.")
        sys.exit(f"Reddit returned HTTP {error.code} for this read-only request.")
    except urllib.error.URLError as error:
        sys.exit(f"Reddit could not be reached: {error.reason}")
    if "json" not in content_type:
        sys.exit(
            f"Reddit returned {content_type or 'a non-JSON page'} instead of JSON "
            "(login or security page). Replace the session cookie."
        )
    return json.loads(body)


def excerpt(text: object, maximum: int) -> str:
    value = text if isinstance(text, str) else ""
    value = value.replace("\x00", "").strip()
    return value if len(value) <= maximum else value[: maximum - 1] + "…"


def children(payload: object) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    data = payload.get("data")
    if not isinstance(data, dict):
        return []
    items = data.get("children")
    if not isinstance(items, list):
        return []
    return [c for c in items if isinstance(c, dict) and isinstance(c.get("data"), dict)]


def search_url(query: str, subreddit: str | None, sort: str, time: str, limit: int) -> str:
    path = "/search.json" if subreddit is None else f"/r/{urllib.parse.quote(subreddit)}/search.json"
    params = {
        "q": query.strip(),
        "sort": sort,
        "t": time,
        "limit": str(limit),
        "type": "link",
        "raw_json": "1",
    }
    if subreddit is not None:
        params["restrict_sr"] = "on"
    return f"{ORIGIN}{path}?{urllib.parse.urlencode(params)}"


def post_from(child: dict) -> dict | None:
    data = child.get("data") or {}
    post_id = data.get("id") or ""
    title = (data.get("title") or "").strip()
    permalink = data.get("permalink") or ""
    if not post_id or not title or not permalink:
        return None
    return {
        "id": post_id,
        "title": title,
        "subreddit": data.get("subreddit") or "",
        "author": data.get("author") or "",
        "body": excerpt(data.get("selftext"), MAX_POST_CHARS),
        "score": data.get("score") or 0,
        "commentCount": data.get("num_comments") or 0,
        "createdUtc": data.get("created_utc") or 0,
        "url": ORIGIN + permalink,
    }


def comments_from(payload: object, limit: int) -> list[dict]:
    if not isinstance(payload, list) or len(payload) < 2:
        return []
    collected = []
    for child in children(payload[1]):
        if child.get("kind") != "t1":
            continue
        data = child.get("data") or {}
        body = excerpt(data.get("body"), MAX_COMMENT_CHARS)
        author = data.get("author") or ""
        if not data.get("id") or not body or author == "AutoModerator":
            continue
        collected.append(
            {
                "id": data.get("id"),
                "author": author,
                "body": body,
                "score": data.get("score") or 0,
                "url": ORIGIN + (data.get("permalink") or ""),
            }
        )
        if len(collected) >= limit:
            break
    return collected


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Reddit search (realpage KB tooling)")
    parser.add_argument("query")
    parser.add_argument("--subreddit")
    parser.add_argument("--sort", default="relevance",
                        choices=["relevance", "hot", "top", "new", "comments"])
    parser.add_argument("--time", default="all",
                        choices=["hour", "day", "week", "month", "year", "all"])
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--comments", type=int, default=2, help="top comments per post")
    parser.add_argument("--cookie-env", default="DSH_REDDIT_COOKIE")
    parser.add_argument("--timeout", type=int, default=25)
    parser.add_argument("--out", help="write JSON evidence to this path")
    args = parser.parse_args()

    if not 1 <= args.limit <= 10:
        sys.exit("--limit must be between 1 and 10 (plugin hard maximum)")
    if not 0 <= args.comments <= 5:
        sys.exit("--comments must be between 0 and 5 (plugin hard maximum)")

    cookie = load_cookie(args.cookie_env)
    subreddit = args.subreddit.strip().removeprefix("r/") if args.subreddit else None

    payload = get_json(
        search_url(args.query, subreddit, args.sort, args.time, args.limit),
        cookie,
        args.timeout,
    )
    posts = []
    for child in children(payload):
        post = post_from(child)
        if post is None:
            continue
        if args.comments and post["commentCount"]:
            try:
                thread = get_json(post["url"] + ".json?sort=top&limit=%d&depth=1&raw_json=1"
                                 % args.comments, cookie, args.timeout)
                post["topComments"] = comments_from(thread, args.comments)
            except SystemExit:
                post["topComments"] = []
                post["commentsUnavailable"] = True
        else:
            post["topComments"] = []
        posts.append(post)
        if len(posts) >= args.limit:
            break

    evidence = {
        "query": args.query.strip(),
        "subreddit": subreddit,
        "sort": args.sort,
        "time": args.time,
        "fetchedAt": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "posts": posts,
    }
    text = json.dumps(evidence, indent=2, ensure_ascii=False)
    if args.out:
        pathlib.Path(args.out).write_text(text)
        print(f"Wrote {len(posts)} posts to {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()

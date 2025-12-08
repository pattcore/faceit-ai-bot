import io
import gzip
import logging
import math
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from fastapi.routing import APIRoute

from .config.settings import settings
from .database.connection import SessionLocal
from .database.models import ProDemo, TeammateProfile

router = APIRouter()

logger = logging.getLogger(__name__)

DYNAMIC_CHUNK_SIZE = 50000
CACHE_TTL = 600


class SimpleCache:
    def __init__(self, ttl_seconds: int = CACHE_TTL) -> None:
        self.ttl = ttl_seconds
        self.data: dict[str, str] = {}
        self.expiry: float = 0.0

    def get(self, key: str) -> str | None:
        if time.time() < self.expiry:
            return self.data.get(key)
        return None

    def set(self, key: str, value: str) -> None:
        self.data[key] = value
        self.expiry = time.time() + self.ttl


sitemap_cache = SimpleCache()


def _get_base_url(request: Request) -> str:
    host = request.url.hostname or "localhost"
    return f"https://{host}"


def _generate_sitemap_xml(base_url: str, urls: list[dict]) -> str:
    items: list[str] = []
    today = datetime.utcnow().strftime("%Y-%m-%d")
    for item in urls:
        path = item.get("url") or "/"
        lastmod = item.get("lastmod") or today
        priority = item.get("priority") or 0.8
        changefreq = item.get("changefreq") or "weekly"
        items.append(
            "  <url>\n"
            f"    <loc>{base_url}{path}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <priority>{priority}</priority>\n"
            f"    <changefreq>{changefreq}</changefreq>\n"
            "  </url>"
        )

    body = "\n".join(items)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
        f"{body}\n"
        "</urlset>"
    )


def _gzip_bytes(content: str) -> bytes:
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as f:
        f.write(content.encode("utf-8"))
    return buf.getvalue()


def _get_static_routes(request: Request) -> list[dict]:
    app = request.app
    urls: list[dict] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        path = route.path
        if path in {"/sitemap_index.xml", "/sitemap_static.xml.gz", "/robots.txt"}:
            continue
        if "{" in path or "}" in path:
            continue
        if path.startswith(("/auth", "/admin", "/metrics", "/internal", "/tasks", "/payments", "/private")):
            continue
        urls.append({"url": path})
    return urls


async def _get_dynamic_routes() -> list[dict]:
    session = SessionLocal()
    try:
        routes: list[dict] = []
        seen: set[str] = set()

        demos = (
            session.query(ProDemo)
            .order_by(ProDemo.updated_at.desc())
            .limit(200000)
            .all()
        )
        for demo in demos:
            nickname = demo.faceit_nickname
            if not nickname or nickname in seen:
                continue
            seen.add(nickname)
            ts = demo.updated_at or demo.created_at or datetime.utcnow()
            routes.append(
                {
                    "url": f"/players/{nickname}/analysis",
                    "lastmod": ts.strftime("%Y-%m-%d"),
                }
            )

        profiles = (
            session.query(TeammateProfile)
            .order_by(TeammateProfile.updated_at.desc())
            .limit(200000)
            .all()
        )
        for profile in profiles:
            nickname = profile.faceit_nickname
            if not nickname or nickname in seen:
                continue
            seen.add(nickname)
            ts = profile.updated_at or profile.created_at or datetime.utcnow()
            routes.append(
                {
                    "url": f"/players/{nickname}/analysis",
                    "lastmod": ts.strftime("%Y-%m-%d"),
                }
            )

        return routes
    except Exception:
        logger.exception("Failed to build dynamic sitemap routes")
        return []
    finally:
        session.close()


@router.get("/robots.txt", include_in_schema=False)
async def robots(request: Request) -> Response:
    host = request.url.hostname or "localhost"
    sitemap_url = f"https://{host}/sitemap_index.xml"
    content = (
        "User-agent: *\n"
        "Disallow: /admin\n"
        "Disallow: /payments\n"
        "Disallow: /auth\n"
        "Allow: /\n\n"
        f"Sitemap: {sitemap_url}\n"
    )
    return Response(content, media_type="text/plain")


@router.get("/sitemap_index.xml", include_in_schema=False)
async def sitemap_index(request: Request) -> Response:
    cached = sitemap_cache.get("index")
    if cached is not None:
        return Response(cached, media_type="application/xml")

    base_url = _get_base_url(request)
    dynamic_routes = await _get_dynamic_routes()
    count = len(dynamic_routes)
    chunks = 0
    if count > 0:
        chunks = math.ceil(count / DYNAMIC_CHUNK_SIZE)

    parts: list[str] = []
    today = datetime.utcnow().strftime("%Y-%m-%d")

    for i in range(1, chunks + 1):
        loc = f"{base_url}/sitemap_{i}.xml.gz"
        parts.append(
            "  <sitemap>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            "  </sitemap>"
        )

    static_routes = _get_static_routes(request)
    if static_routes:
        loc_static = f"{base_url}/sitemap_static.xml.gz"
        parts.append(
            "  <sitemap>\n"
            f"    <loc>{loc_static}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            "  </sitemap>"
        )

    body = "\n".join(parts)
    index_xml = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<sitemapindex xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">\n"
        f"{body}\n"
        "</sitemapindex>"
    )
    sitemap_cache.set("index", index_xml)
    return Response(index_xml, media_type="application/xml")


@router.get("/sitemap_static.xml.gz", include_in_schema=False)
async def sitemap_static(request: Request) -> Response:
    base_url = _get_base_url(request)
    urls = _get_static_routes(request)
    if not urls:
        xml = _generate_sitemap_xml(base_url, [{"url": "/"}])
    else:
        xml = _generate_sitemap_xml(base_url, urls)
    gz = _gzip_bytes(xml)
    return Response(gz, media_type="application/gzip")


@router.get("/sitemap_{chunk}.xml.gz", include_in_schema=False)
async def sitemap_chunk(request: Request, chunk: int) -> Response:
    if chunk < 1:
        raise HTTPException(status_code=404, detail="Not found")

    dynamic_routes = await _get_dynamic_routes()
    count = len(dynamic_routes)
    if count == 0:
        raise HTTPException(status_code=404, detail="Not found")

    max_chunk = math.ceil(count / DYNAMIC_CHUNK_SIZE)
    if chunk > max_chunk:
        raise HTTPException(status_code=404, detail="Not found")

    start = (chunk - 1) * DYNAMIC_CHUNK_SIZE
    end = min(start + DYNAMIC_CHUNK_SIZE, count)
    base_url = _get_base_url(request)
    xml = _generate_sitemap_xml(base_url, dynamic_routes[start:end])
    gz = _gzip_bytes(xml)
    return Response(gz, media_type="application/gzip")


_PRIVATE_SITEMAP_KEY = getattr(settings, "SITEMAP_PRIVATE_KEY", settings.SECRET_KEY)


@router.get("/private_sitemap.xml", include_in_schema=False)
async def private_sitemap(request: Request, key: str) -> Response:
    if key != _PRIVATE_SITEMAP_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    base_url = _get_base_url(request)
    private_paths = [
        "/auth",
        "/admin",
        "/payments",
        "/subscriptions",
        "/dashboard",
    ]
    urls = [{"url": path} for path in private_paths]
    xml = _generate_sitemap_xml(base_url, urls)
    gz = _gzip_bytes(xml)
    headers = {"X-Robots-Tag": "noindex, nofollow, nosnippet"}
    return Response(gz, media_type="application/gzip", headers=headers)

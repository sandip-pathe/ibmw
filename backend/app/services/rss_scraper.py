import asyncio
import feedparser
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from loguru import logger
from typing import Optional

from app.services.regulation_ingestion import regulation_service
from app.database import db

FEEDS = [
    {
        "regulator": "SEBI",
        "url": "https://www.sebi.gov.in/sebirss.xml",
        "type": "circular"
    },
    {
        "regulator": "RBI",
        "url": "https://rbi.org.in/pressreleases_rss.xml",
        "type": "press_release"
    },
    {
        "regulator": "RBI",
        "url": "https://rbi.org.in/notifications_rss.xml", # Assuming notification feed exists or similar
        "type": "notification"
    }
]

class RSSScraperAgent:
    
    async def run_scrape_cycle(self):
        """Called every 5 minutes by Scheduler"""
        # logger.info("Starting 5-minute RSS polling cycle...")
        results = {"new": 0, "errors": 0}

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for feed_config in FEEDS:
                try:
                    await self._process_feed(client, feed_config, results)
                except Exception as e:
                    logger.error(f"Feed error {feed_config['url']}: {e}")
                    results["errors"] += 1
        
        # logger.info(f"Scrape Cycle Complete: {results}")
        return results

    async def _process_feed(self, client, config, results):
        # Parse feed (sync operation, fast enough for now)
        feed = feedparser.parse(config["url"])
        
        for entry in feed.entries[:5]: # Check top 5 newest items
            try:
                # 1. Duplicate Check via Link
                if await self._is_url_processed(entry.link):
                    continue

                # logger.info(f"New circular detected: {entry.title}")

                # 2. Content Extraction (HTML First Strategy)
                content, content_type = await self._fetch_smart_content(client, entry.link)
                
                if not content:
                    continue

                # 3. Ingest as DRAFT
                metadata = {
                    "regulator": config["regulator"],
                    "type": config["type"],
                    "date": self._parse_date(entry),
                    "source_url": entry.link,
                    "title": entry.title,
                    "status": "draft" # <--- IMPORTANT: Goes to Review Queue
                }

                await regulation_service.ingest_document(
                    content=content,
                    filename=f"{entry.title[:50]}.{content_type}",
                    metadata=metadata
                )
                
                results["new"] += 1

            except Exception as e:
                logger.error(f"Error processing item {entry.link}: {e}")
                results["errors"] += 1

    async def _fetch_smart_content(self, client, url: str) -> tuple[Optional[str | bytes], str]:
        """
        Fetches content. 
        Returns (content, extension).
        Priority: HTML Body Text > PDF File.
        """
        try:
            resp = await client.get(url)
            content_type = resp.headers.get("content-type", "").lower()

            # Case 1: Direct PDF
            if "application/pdf" in content_type:
                return resp.content, "pdf"

            # Case 2: HTML Page
            if "text/html" in content_type:
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Check for RBI specific content container
                # RBI often puts text in <td class="tablecontent2"> or similar
                # This is a generic extractor for demo:
                main_text = ""
                
                # Heuristic: If text length is substantial (>500 chars), use HTML text
                body_text = soup.get_text(separator="\n", strip=True)
                
                if len(body_text) > 500:
                    return body_text, "html"
                
                # Fallback: Look for PDF Link inside HTML if text is too short (just a landing page)
                pdf_link = soup.find('a', href=lambda x: x and x.lower().endswith('.pdf'))
                if pdf_link:
                    pdf_url = pdf_link['href']
                    if not pdf_url.startswith('http'):
                        base = "/".join(url.split("/")[:3])
                        pdf_url = f"{base}/{pdf_url.lstrip('/')}"
                    
                    # logger.info(f"Falling back to PDF download: {pdf_url}")
                    pdf_resp = await client.get(pdf_url)
                    return pdf_resp.content, "pdf"

            return None, ""

        except Exception as e:
            logger.warning(f"Fetch failed: {e}")
            return None, ""

    async def _is_url_processed(self, url):
        query = "SELECT 1 FROM policy_documents WHERE source_url = $1"
        async with db.acquire() as conn:
            res = await conn.fetchval(query, url)
            return res is not None

    def _parse_date(self, entry):
        if hasattr(entry, 'published_parsed'):
            return datetime(*entry.published_parsed[:6]).date()
        return datetime.utcnow().date()

rss_agent = RSSScraperAgent()
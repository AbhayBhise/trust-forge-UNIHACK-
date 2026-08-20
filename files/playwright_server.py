from fastapi import FastAPI, HTTPException
import uvicorn
from patchright.async_api import async_playwright
import asyncio

app = FastAPI()
playwright_instance = None
browser = None
context = None

@app.on_event("startup")
async def startup():
    global playwright_instance, browser, context
    playwright_instance = await async_playwright().start()
    browser = await playwright_instance.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        ignore_https_errors=True
    )

@app.on_event("shutdown")
async def shutdown():
    await browser.close()
    await playwright_instance.stop()

@app.get("/fetch")
async def fetch(url: str, mpn: str = ""):
    page = await context.new_page()
    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=15000)
        if mpn:
            try:
                await page.wait_for_selector(f"a:has-text(\"{mpn}\"), a[href*=\"{mpn.lower()}\"]", timeout=3000)
                loc = page.locator(f"a:has-text(\"{mpn}\"), a[href*=\"{mpn.lower()}\"]").first
                if await loc.is_visible():
                    await loc.click(timeout=5000)
                    await page.wait_for_load_state('domcontentloaded', timeout=5000)
            except Exception:
                pass
        content = await page.content()
        return {"html": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await page.close()

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)

from threading import Event
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from playwright._impl._errors import TargetClosedError
import sys
import os

# append parent directory to PATH to import own modules
sys.path.append(os.path.dirname(os.path.abspath(os.getcwd())))

from services.config import DEFAULT_CDP_PORT


def open_browser_session(url: str, e: Event, f: Event) -> None:
    """Open a browser session in Chromium dev mode and navigate to the base url.
    
    Parameters
    ----------
    url: str, the base url
    e: Event, the event indicating whether the page was loaded correctly
    f: Event, indicating whether the crawl is completed and the browser can be closed

    Returns
    -------
    None
    """
    with sync_playwright() as playwright:
        try:
            browser: Browser = playwright.chromium.launch(
                headless=False,
                args=[f'--remote-debugging-port={DEFAULT_CDP_PORT}', '--disable-dev-shm-usage'],
                devtools=False
            )
            context: BrowserContext = browser.new_context()
            page: Page = context.new_page()
            page.goto(url)
            page.wait_for_load_state("domcontentloaded")
            e.set()
            # keep browser alive as long as the f event is not set.
            f.wait()
        except TargetClosedError as e:
            print(f"An error occurred: {e}")
        finally:
            browser.close()

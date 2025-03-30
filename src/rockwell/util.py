import aiohttp
import asyncio


async def check_url(session, url):
    """Check if a URL is accessible."""
    try:
        async with session.head(url, timeout=3) as response:
            return url if response.status < 400 else None
    except:
        return None


async def process_data(data):
    """Scan for URLs, check if they are working, and remove broken ones from the text."""
    urls_to_check = {
        url_info["url"]: url_info["expanded_url"]
        for item in data
        if "entities" in item and "urls" in item["entities"]
        for url_info in item["entities"]["urls"]
    }

    async with aiohttp.ClientSession() as session:
        tasks = [
            check_url(session, expanded_url) for expanded_url in urls_to_check.values()
        ]
        results = await asyncio.gather(*tasks)

    working_urls = set(filter(None, results))
    cleaned_data = []

    for item in data:
        if "entities" in item and "urls" in item["entities"]:
            for url_info in item["entities"]["urls"]:
                if url_info["expanded_url"] not in working_urls:
                    item["full_text"] = item["full_text"].replace(url_info["url"], "")
            item["entities"]["urls"] = [
                url_info
                for url_info in item["entities"]["urls"]
                if url_info["expanded_url"] in working_urls
            ]
        cleaned_data.append(item)

    return cleaned_data
    # cleaned_data = asyncio.run(process_data(json_data))

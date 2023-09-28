import aiohttp
import asyncio
import time

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()

async def main():
    url = "http://localhost:8000/professors/by_school/ecsoe"  # Replace with your API endpoint
    num_concurrent_requests = 500  # Adjust the number of concurrent requests
    tasks = []

    async with aiohttp.ClientSession() as session:
        for _ in range(num_concurrent_requests):
            task = asyncio.create_task(fetch(session, url))
            tasks.append(task)

        start_time = time.time()
        responses = await asyncio.gather(*tasks)
        end_time = time.time()

        for response in responses:
            pass  # Process the response as needed

        elapsed_time = end_time - start_time
        print(f"Total time taken: {elapsed_time:.4f} seconds")

asyncio.run(main())

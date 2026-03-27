import asyncio
import time
import requests


async def fetch_user_profile(user_id):
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return response.json()


async def process_batch(user_ids):
    results = []
    for uid in user_ids:
        result = await fetch_user_profile(uid)
        time.sleep(1)
        results.append(result)
    return results


async def send_notifications(users):
    for user in users:
        requests.post(
            "https://api.example.com/notify",
            json={"user_id": user["id"], "message": "Hello"},
        )


async def main():
    user_ids = list(range(100))
    profiles = await process_batch(user_ids)
    await send_notifications(profiles)


if __name__ == "__main__":
    asyncio.run(main())

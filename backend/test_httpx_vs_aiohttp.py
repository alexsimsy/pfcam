import asyncio
import httpx
import aiohttp
import json

CAMERA_URL = "http://192.168.86.199/api/events"
PAYLOAD = {
    "eventName": "string",
    "overlayText": "NewTest",
    "preEventSeconds": 10,
    "postEventSeconds": 10,
    "postEventUnlimited": False,
    "stopOtherEvents": "none"
}
HEADERS = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

def test_httpx():
    print("\n--- Testing httpx ---")
    with httpx.Client() as client:
        response = client.post(CAMERA_URL, headers=HEADERS, json=PAYLOAD)
        print("Status:", response.status_code)
        print("Response:", response.text)

def test_aiohttp():
    print("\n--- Testing aiohttp ---")
    async def inner():
        async with aiohttp.ClientSession() as session:
            async with session.post(CAMERA_URL, headers=HEADERS, json=PAYLOAD) as resp:
                print("Status:", resp.status)
                text = await resp.text()
                print("Response:", text)
    asyncio.run(inner())

if __name__ == "__main__":
    test_httpx()
    test_aiohttp() 
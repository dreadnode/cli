import os

import asyncio
import rigging as rg
import httpx

guidance = os.environ.get("GUIDANCE", "n/a")


async def main() -> None:
    print("Agent 'dc1' started")

    print(f"Guidance: {guidance}")

    chat = (
        await
        rg.get_generator('openai/model,api_base=http://dropship/v1')
        .chat('Say Hello!')
        .run()
    )

    print("Chat:", chat.conversation)
    
    try:
        response = httpx.get("http://web")
        response.raise_for_status()

        print(f"Response: {response.text}")

        httpx.post("http://dropship/output", json={"response": response.text})
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
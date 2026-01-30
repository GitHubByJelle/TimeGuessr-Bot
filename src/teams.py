
import aiohttp
import asyncio
from src.settings import settings
import logging

async def send_to_teams(message: str) -> None:
    logger = logging.getLogger(__name__)
    logger.info("Preparing to send message to Teams")

    # Preserve empty lines by adding non-breaking space, then convert newlines
    message = message.replace('\n\n', '\n&nbsp;\n')
    message = message.replace('\n', '\n\n')

    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "text": message
    }

    try:
        logger.info(f"Sending POST request to Teams webhook")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                settings.TEAMS_WEBHOOK_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response_text = await response.text()
                if response.status >= 400:
                    logger.error(f"Failed to send message to Teams: {response.status} {response_text}")
                    response.raise_for_status()
                logger.info(f"Message sent successfully (status code: {response.status})")
    except Exception as e:
        logger.error(f"Failed to send message to Teams: {e}", exc_info=True)
        raise


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )

    TEST = """TimeGuessr #972 - 48.269/50.000

1️⃣ 🏆9931 - 📅1y - 🌍935.9 m
2️⃣ 🏆9584 - 📅3y - 🌍794.5 m
3️⃣ 🏆9582 - 📅3y - 🌍880.3 m
4️⃣ 🏆9585 - 📅3y - 🌍729.8 m
5️⃣ 🏆9587 - 📅3y - 🌍625.5 m

https://timeguessr.com"""
    asyncio.run(send_to_teams(TEST))
    logging.info("Message sent!")
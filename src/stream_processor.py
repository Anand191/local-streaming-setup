import asyncio
import json

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from core.config import KAFKA_BOOTSTRAP_SERVERS, REQUEST_TOPIC, RESPONSE_TOPIC
from core.logging import logger
from services.processing import heavy_processing


async def main() -> None:
    """Main entry point for the stream processor.

    Consumes messages from the Kafka request topic, processes them, and sends responses
    to the response topic. Starts and stops Kafka consumer and producer, logs processing
    events, and handles invalid messages.

    Returns:
    -------
    None
    """
    consumer = AIOKafkaConsumer(
        REQUEST_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="stream_processor_group",
        auto_offset_reset="earliest",
    )
    producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

    await consumer.start()
    await producer.start()
    logger.info("Stream processor started...")

    try:
        async for msg in consumer:
            try:
                message_data = json.loads(msg.value.decode("utf-8"))
                request_id = message_data.get("request_id")
                payload = message_data.get("payload")

                if not request_id or not payload:
                    logger.warning(f"Skipping invalid message: {message_data}")
                    continue

                logger.info(f"Processing message for request_id: {request_id}")
                # Perform the heavy processing
                result = await heavy_processing(payload)
                # Prepare the response message
                response_message = {
                    "request_id": request_id,
                    "status": "completed",
                    "result": result,
                }
                # Send the response to the response topic
                await producer.send_and_wait(
                    RESPONSE_TOPIC, json.dumps(response_message).encode("utf-8")
                )
                logger.info(
                    f"Sent response for request_id: {request_id} to {RESPONSE_TOPIC}"
                )

            except json.JSONDecodeError:
                logger.error(f"Could not decode message: {msg.value}")
    finally:
        await consumer.stop()
        await producer.stop()
        logger.info("Stream processor stopped.")


if __name__ == "__main__":
    asyncio.run(main())

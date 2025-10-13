import json
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from core.config import KAFKA_BOOTSTRAP_SERVERS, REQUEST_TOPIC, RESPONSE_TOPIC
from core.logging import logger


class KafkaClient:
    """A simple Kafka client to produce and consume messages asynchronously."""

    def __init__(self) -> None:
        self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        self.consumer = AIOKafkaConsumer(
            RESPONSE_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id="fastapi_consumer_group",
            auto_offset_reset="earliest",
        )
        self.is_running = False

    async def start(self) -> None:
        """Starts the Kafka producer and consumer."""
        await self.producer.start()
        await self.consumer.start()
        self.is_running = True
        logger.info("Kafka client started.")

    async def stop(self) -> None:
        """Stops the Kafka producer and consumer."""
        await self.producer.stop()
        await self.consumer.stop()
        self.is_running = False
        logger.info("Kafka client stopped.")

    async def send_request(self, payload: dict) -> str:
        """Sends a request message to the request topic."""
        request_id = str(uuid.uuid4())
        message = {
            "request_id": request_id,
            "payload": payload,
        }
        await self.producer.send_and_wait(
            REQUEST_TOPIC, json.dumps(message).encode("utf-8")
        )
        logger.info(f"Sent message to {REQUEST_TOPIC} with request_id: {request_id}")
        return request_id

    async def get_response(self, request_id: str, timeout: int = 30) -> dict | None:  # noqa: ASYNC109
        """Waits for a specific response from the response topic.

        This method demonstrates a long-polling pattern. The consumer waits for a
        message with a matching request_id. While this specific request is 'blocking'
        and waiting for the message, the asyncio event loop is not blocked.
        The FastAPI server can still handle other incoming requests concurrently.

        This highlights how an async framework can manage long-running waits without
        tying up worker threads, unlike a traditional synchronous server where a
        long wait would render a worker unavailable for other tasks.
        """
        logger.info(f"Waiting for response with request_id: {request_id}")
        try:
            async for msg in self.consumer:
                try:
                    response_data = json.loads(msg.value.decode("utf-8"))
                    if response_data.get("request_id") == request_id:
                        logger.info(f"Received response for request_id: {request_id}")
                        return response_data
                except json.JSONDecodeError:
                    logger.error(f"Could not decode message: {msg.value}")
                # This is a simplified timeout mechanism.
                # In a production scenario, you might use asyncio.wait_for.
                timeout -= 1
                if timeout <= 0:
                    logger.warning(
                        f"Timeout waiting for response for request_id: {request_id}"
                    )
                    return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error while consuming: {e}")
            return None


kafka_client = KafkaClient()

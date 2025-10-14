import asyncio
import contextlib
import json
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from core.config import KAFKA_BOOTSTRAP_SERVERS, REQUEST_TOPIC, RESPONSE_TOPIC
from core.logging import logger


class KafkaClient:
    """A Kafka client that uses a background task for consuming responses."""

    def __init__(self) -> None:
        self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
        # Each API instance needs a unique group_id to get all responses
        self.consumer = AIOKafkaConsumer(
            RESPONSE_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=f"fastapi_consumer_group_{uuid.uuid4()}",
            auto_offset_reset="earliest",
        )
        self.responses: dict[str, dict] = {}
        self.response_events: dict[str, asyncio.Event] = {}
        self._consumer_task: asyncio.Task | None = None
        self.is_running = False

    async def _response_consumer_task(self) -> None:
        """A background task that consumes messages from the response topic."""
        try:
            async for msg in self.consumer:
                try:
                    response_data = json.loads(msg.value.decode("utf-8"))
                    request_id = response_data.get("request_id")
                    if request_id:
                        self.responses[request_id] = response_data
                        if request_id in self.response_events:
                            self.response_events[request_id].set()
                        logger.info(
                            f"Consumed and stored response for request_id: {request_id}"
                        )
                except json.JSONDecodeError:
                    logger.error(f"Could not decode message: {msg.value}")
        except asyncio.CancelledError:
            logger.info("Response consumer task was cancelled.")
        except TimeoutError as e:
            logger.error(f"Response consumer task failed: {e}", exc_info=True)

    async def start(self) -> None:
        """Starts the Kafka producer, consumer, and the background consumer task."""
        await self.producer.start()
        await self.consumer.start()
        self._consumer_task = asyncio.create_task(self._response_consumer_task())
        self.is_running = True
        logger.info("Kafka client started.")

    async def stop(self) -> None:
        """Stops the Kafka producer, consumer, and the background consumer task."""
        if self._consumer_task:
            self._consumer_task.cancel()
            # Task is already cancelled or timed out, which is expected
            # Suppress the exceptions to avoid noisy logs
            with contextlib.suppress(asyncio.CancelledError, asyncio.TimeoutError):
                await asyncio.wait_for(self._consumer_task, timeout=5)

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
        """Waits for a specific response using an event-based mechanism."""
        # Check if the response is already available from a message that arrived
        # before the client started waiting.
        if request_id in self.responses:
            logger.info(f"Response for {request_id} was already available.")
            return self.responses.pop(request_id)

        event = asyncio.Event()
        self.response_events[request_id] = event
        logger.info(f"Waiting for response with request_id: {request_id}")

        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
            logger.info(f"Received event for request_id: {request_id}")
            return self.responses.pop(request_id, None)
        except TimeoutError:
            logger.warning(f"Timeout waiting for response for request_id: {request_id}")
            return None
        finally:
            # Clean up the event to prevent memory leaks
            self.response_events.pop(request_id, None)


kafka_client = KafkaClient()

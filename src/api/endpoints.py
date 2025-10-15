from fastapi import (
    APIRouter,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
)

from api.schemas import ProcessRequest, ProcessResponse
from services import rest_service
from services.kafka_client import kafka_client

router = APIRouter()


@router.get("/healths")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


@router.post("/rest-process")
async def rest_process_endpoint(request: ProcessRequest) -> ProcessResponse:
    """This endpoint simulates a traditional, synchronous REST API call.

    The server will block and wait for the processing to finish before
    returning a response. This is inefficient for long-running tasks.
    """
    result = await rest_service.process_sync(request.payload)
    return ProcessResponse(request_id="N/A", status="completed", result=result)


@router.post("/produce", status_code=202)
async def produce_message(request: ProcessRequest) -> dict[str, str]:
    """This endpoint asynchronously sends a payload to a Kafka topic.

    It returns immediately with a request_id, allowing the client
    to poll for the result later.
    """
    if not kafka_client.is_running:
        raise HTTPException(status_code=503, detail="Kafka client is not running.")

    request_id = await kafka_client.send_request(request.payload)
    return {"message": "Request accepted for processing.", "request_id": request_id}


@router.get("/consume/{request_id}")
async def consume_message(request_id: str) -> ProcessResponse:
    """This endpoint uses long-polling to wait for a result from a Kafka topic.

    While it waits, the server remains non-blocking and can handle other requests.
    This demonstrates how to handle asynchronous job completion in a RESTful way.

    It highlights that while the client's HTTP request is 'stuck' waiting,
    the server's resources are not blocked, showcasing the power of async.
    """
    if not kafka_client.is_running:
        raise HTTPException(status_code=503, detail="Kafka client is not running.")

    response = await kafka_client.get_response(request_id)

    if response:
        return ProcessResponse(
            request_id=response.get("request_id"),
            status="completed",
            result=response.get("result"),
        )
    raise HTTPException(
        status_code=404, detail="Result not found or request timed out."
    )


@router.websocket("/ws/results/{request_id}")
async def websocket_results(websocket: WebSocket, request_id: str) -> None:
    """This endpoint establishes a WebSocket connection to stream results.

    It waits for a specific result from Kafka and pushes it to the client
    as soon as it's available, avoiding the need for client-side polling.
    """
    await websocket.accept()
    if not kafka_client.is_running:
        await websocket.close(code=1011, reason="Kafka client is not running.")
        return

    try:
        response = await kafka_client.get_response(request_id)
        if response:
            await websocket.send_json(
                {
                    "request_id": response.get("request_id"),
                    "status": "completed",
                    "result": response.get("result"),
                }
            )
        else:
            await websocket.send_json(
                {
                    "request_id": request_id,
                    "status": "error",
                    "detail": "Result not found or request timed out.",
                }
            )
        await websocket.close()
    except WebSocketDisconnect:
        # Client disconnected, no action needed
        pass
    except WebSocketException as e:
        # Handle other potential errors
        await websocket.send_json(
            {
                "request_id": request_id,
                "status": "error",
                "detail": str(e),
            }
        )
        await websocket.close()

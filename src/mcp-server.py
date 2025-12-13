from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Dict, Any
import asyncio

app = FastAPI()
mcp = FastMCP("monitoring_mcp")

class RegisterSensorRequest(BaseModel):
    sensor_id: str
    metadata: Dict[str, Any]


class SendMetricRequest(BaseModel):
    sensor_id: str
    value: float


class RaiseAlertRequest(BaseModel):
    message: str

class MonitoringServer:
    def __init__(self):
        self.mcp = mcp
        self.sensors: Dict[str, Dict[str, Any]] = {}


    async def register_sensor(self, sensor_id: str, metadata: dict) -> str:
        """
        Register a new monitoring sensor with its metadata.
        Parameters:
            sensor_id (str): The ID of the sensor to register.
            metadata (dict): The metadata associated with the sensor.
        Returns:
            str: A message indicating the result of the registration.
        Examples:
            >>> await register_sensor("temp_01", {"location": "server_room", "type": "temperature"})
            "Sensor temp_01 registered successfully."
        """
        if sensor_id in self.sensors:
            return f"Sensor {sensor_id} is already registered."
        self.sensors[sensor_id] = metadata
        return f"Sensor {sensor_id} registered successfully."

    async def send_metric(self, sensor_id: str, value: float) -> str:
        """
        Receive a metric from a sensor and process it.
        Parameters:
            sensor_id (str): The ID of the sensor to register.
            metadata (dict): The metadata associated with the sensor.
        Returns:
            str: A message indicating the result of the registration.
        Examples:
            >>> await register_sensor("temp_01", {"location": "server_room", "type": "temperature"})
            "Sensor temp_01 registered successfully."
        """
        if sensor_id not in self.sensors:
            return f"Error: Sensor {sensor_id} not found."
        self.sensors[sensor_id].setdefault("metrics", []).append(value)
        return f"Metric received from {sensor_id}: {value}"


    async def raise_alert(message: str) -> str:
        """
        Send an alert message in the monitoring system.
        Parameters:
            message (str): The alert message to send.
        Returns:
            str: A message indicating the result of the alert.
        Examples:
            >>> await raise_alert("Temperature is too high.")
            "Alert sent: Temperature is too high."
        """
        return f"Alert sent: {message}"

# Routes

@app.post("/register_sensor")
async def register_sensor(request: RegisterSensorRequest):
    result = await server.register_sensor(request.sensor_id, request.metadata)
    return {"result": result}


@app.post("/send_metric")
async def send_metric(request: SendMetricRequest):
    result = await server.send_metric(request.sensor_id, request.value)
    return {"result": result}


@app.post("/raise_alert")
async def raise_alert(request: RaiseAlertRequest):
    result = await server.raise_alert(request.message)
    return {"result": result}


if __name__ == "__main__":
    # mcp.run(transport="stdio")
    server = MonitoringServer()
    mcp.run(transport="http")
    # server.start()
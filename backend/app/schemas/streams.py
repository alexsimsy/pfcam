from typing import List, Dict, Any
from pydantic import BaseModel

class StreamResponse(BaseModel):
    name: str
    stream_info: Dict[str, Any]
    camera_id: int

class StreamList(BaseModel):
    camera_id: int
    streams: List[StreamResponse]
    count: int

class StreamUrl(BaseModel):
    camera_id: int
    stream_name: str
    stream_url: str
    codec: str
    fps: int
    resolution: Dict[str, int]

class SnapshotResponse(BaseModel):
    camera_id: int
    stream_name: str
    snapshot_url: str
    resolution: Dict[str, int]

class RTSPInfo(BaseModel):
    camera_id: int
    rtsp_url: str
    codec: str
    fps: int
    resolution: Dict[str, int]
    name: str

class HDStreamInfo(BaseModel):
    camera_id: int
    hd_url: str
    codec: str
    fps: int
    resolution: Dict[str, int]
    name: str
    snapshot_url: str = None 
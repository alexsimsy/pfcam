import yaml
import os
from typing import List, Dict

MEDIAMTX_CONFIG_PATH = os.getenv("MEDIAMTX_CONFIG_PATH", "mediamtx.yml")


def build_rtsp_url(camera: Dict) -> str:
    """
    Build the RTSP URL from camera settings dict.
    Expects keys: ip_address, rtsp_port, rtsp_path, username, password, rtsp_auth
    """
    userinfo = ""
    if camera.get("rtsp_auth") and camera.get("username"):
        userinfo = camera["username"]
        if camera.get("password"):
            userinfo += f":{camera['password']}"
        userinfo += "@"
    return f"rtsp://{userinfo}{camera['ip_address']}:{camera['rtsp_port']}/{camera['rtsp_path'].lstrip('/')}"


def generate_mediamtx_config(cameras: List[Dict]) -> Dict:
    """
    Generate the mediamtx.yml config dict for all cameras.
    """
    paths = {}
    for cam in cameras:
        rtsp_url = build_rtsp_url(cam)
        paths[cam['name']] = {
            'source': rtsp_url,
            'sourceOnDemand': True,
        }
    return {
        'paths': paths,
        'api': True,
        'apiAddress': ':9997',
        'hlsAlwaysRemux': True,
        'hlsSegmentCount': 3,
        'hlsSegmentDuration': '1s',
    }


def write_mediamtx_config(config: Dict, path: str = MEDIAMTX_CONFIG_PATH):
    with open(path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False) 
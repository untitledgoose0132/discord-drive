import os
from struct import Struct

TOKEN: str = os.getenv("BOT_TOKEN") or ""
CHANNEL: int = int(os.getenv("CHANNEL_ID") or 0)
UPLOAD_LIMIT: int = 20971520
PORT_UP: int = 41468
PORT_DOWN: int = 41469
PORT_CMD: int = 41470
HEADER = Struct(">I")

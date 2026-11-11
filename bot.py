from asyncio import IncompleteReadError, StreamReader, StreamWriter, start_server
from io import BytesIO

from discord import Client, File, HTTPException
from discord.abc import Messageable

import config


class NotReady(Exception):
  pass


class Bot(Client):
  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.channel: Messageable | None = None

  async def up_handler(self, reader: StreamReader, writer: StreamWriter):
    async def read(reader) -> bytes | None:
      try:
        header = await reader.readexactly(config.HEADER.size)
        (n,) = config.HEADER.unpack(header)
        data: bytes = await reader.readexactly(n)
        return data
      except IncompleteReadError as e:
        if e.partial or e.expected != 4:
          raise
        return None

    try:
      while data := await read(reader):
        m_id: int = await self.upload(data)
        writer.write(f"{m_id}\n".encode())
        await writer.drain()
    finally:
      writer.close()
      try:
        await writer.wait_closed()
      except ConnectionError:
        pass

  async def down_handler(self, reader: StreamReader, writer: StreamWriter):
    try:
      while data := await reader.readline():
        ret = data.decode().strip()
        if len(ret) != 19:
          raise ValueError("Improper ID")
        assert self.channel
        m = await self.channel.fetch_message(int(ret))
        data = await m.attachments[0].read()
        writer.write(config.HEADER.pack(len(data)) + data)
        await writer.drain()
    finally:
      writer.close()
      try:
        await writer.wait_closed()
      except ConnectionError:
        pass

  async def cmd_handler(self, reader: StreamReader, writer: StreamWriter):
    try:
      while data := await reader.readline():
        data = data.decode().strip()
        cmd, args = data.split(" ", maxsplit=1)
        if cmd == "delete":
          assert self.channel
          try:
            await (await self.channel.fetch_message(int(args))).delete()
            writer.write(b"Success\n")
          except HTTPException as e:
            writer.write(repr(e).encode() + b"\n")
          finally:
            await writer.drain()
    finally:
      writer.close()
      try:
        await writer.wait_closed()
      except ConnectionError:
        pass

  async def on_ready(self) -> None:
    try:
      c = await self.fetch_channel(config.CHANNEL)
      if not isinstance(c, Messageable):
        raise TypeError("Cannot send messages to this channel")
      await c.send("Ready", delete_after=5)
      self.channel = c
    except:
      await self.close()
      raise
    self.loop.create_task(start_server(self.up_handler, "127.0.0.1", config.PORT_UP))
    self.loop.create_task(start_server(self.down_handler, "127.0.0.1", config.PORT_DOWN))
    self.loop.create_task(start_server(self.cmd_handler, "127.0.0.1", config.PORT_CMD))

  async def upload(self, data: bytes) -> int:
    if self.channel is None:
      raise NotReady("Channel not initialized")
    if len(data) > config.UPLOAD_LIMIT:
      raise ValueError("Oversized data")
    m = await self.channel.send(file=File(BytesIO(data), filename="data"))
    return m.id

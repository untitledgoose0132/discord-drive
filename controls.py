import os
import shelve
from asyncio import open_connection
from os import urandom

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

import config


def encrypt(nonce: bytes, data: bytes, aad: bytes | None = None) -> bytes:
  try:
    with open("encryptkey", "rb") as f:
      key = f.read()
  except FileNotFoundError:
    key = ChaCha20Poly1305.generate_key()
    with open("encryptkey", "wb") as f:
      f.write(key)
  aead = ChaCha20Poly1305(key)
  return aead.encrypt(nonce, data, aad)


def decrypt(nonce: bytes, data: bytes, aad: bytes | None = None) -> bytes:
  try:
    with open("encryptkey", "rb") as f:
      key = f.read()
  except FileNotFoundError:
    key = ChaCha20Poly1305.generate_key()
    with open("encryptkey", "wb") as f:
      f.write(key)
  aead = ChaCha20Poly1305(key)
  return aead.decrypt(nonce, data, aad)


async def upload(fp: str) -> None:
  meta: list[tuple[bytes, int]] = []
  name = os.path.basename(fp)
  with shelve.open("files") as s:
    if name in s:
      input("Found a file of the same name already uploaded, press Enter to proceed (will overwrite previous file!!!)")
  with open(fp, "rb") as f:
    i = 1
    s = os.path.getsize(fp)
    while True:
      data = f.read(config.UPLOAD_LIMIT - 16)
      print(f"Uploading chunk #{i}/{(s // (config.UPLOAD_LIMIT - 16)) + 1}", end="\r")
      nonce = urandom(12)
      enc = encrypt(nonce, data)
      reader, writer = await open_connection("127.0.0.1", config.PORT_UP)
      writer.write(config.HEADER.pack(len(enc)) + enc)
      await writer.drain()
      meta.append((nonce, int((await reader.readline()).decode().strip())))
      print(f"Uploaded chunk #{i}/{i} ")
      if len(data) != config.UPLOAD_LIMIT - 16:
        break
      i += 1
  with shelve.open("files") as s:
    s.update({name: meta})


async def download(fp: str) -> None:
  fp = os.path.basename(fp)
  try:
    with shelve.open("files") as s:
      meta: list[tuple[bytes, int]] = s[fp]
  except KeyError:
    print("File not found")
    return
  with open(fp, "wb") as f:
    for i, (nonce, m_id) in enumerate(meta):
      print(f"Downloading chunk #{i + 1}/{len(meta)}", end="\r")
      reader, writer = await open_connection("127.0.0.1", config.PORT_DOWN)
      writer.write(f"{m_id}\n".encode())
      await writer.drain()
      header = await reader.readexactly(config.HEADER.size)
      (n,) = config.HEADER.unpack(header)
      decoded = decrypt(nonce, await reader.readexactly(n))
      f.write(decoded)
      print(f"Downloaded chunk #{i + 1}/{len(meta)} ")


async def delete(fp: str) -> None:
  fp = os.path.basename(fp)
  try:
    with shelve.open("files") as s:
      meta: list[tuple[bytes, int]] = s[fp].copy()
      del s[fp]
  except KeyError:
    print("File not found")
    return
  reader, writer = await open_connection("127.0.0.1", config.PORT_CMD)
  for i, (_, m_id) in enumerate(meta):
    print(f"Deleting chunk #{i}/{len(meta)} ({m_id})", end="\r")
    writer.write(f"delete {m_id}\n".encode())
    await writer.drain()
    re = await reader.readline()
    if re.strip() != b"Success":
      raise eval(re.decode())
    print(f"Deleted chunk #{i}/{len(meta)} ({m_id}) ")


def list_files() -> None:
  with shelve.open("files") as s:
    [print(k) for k in s]

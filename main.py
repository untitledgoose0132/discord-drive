from argparse import ArgumentParser
from asyncio import run

from discord import Intents

import config
from bot import Bot
from controls import delete, download, list_files, upload


def main() -> None:
  parser = ArgumentParser()
  parser.add_argument(
    "option",
    help="start the background server / download the specified filename / upload the specified file / delete the specified filename / list filenames",
    choices=["serve", "down", "up", "delete", "list"],
  )
  parser.add_argument("path", help="path to file to upload / download / delete", type=str, nargs="?", default="")
  args = parser.parse_args()
  if args.option == "serve":
    bot = Bot(intents=Intents.none())
    bot.run(config.TOKEN)
  elif args.option == "down":
    if not args.path:
      print("Path is required for this option")
      return
    run(download(args.path))
  elif args.option == "up":
    if not args.path:
      print("Path is required for this option")
      return
    run(upload(args.path))
  elif args.option == "delete":
    if not args.path:
      print("Path is required for this option")
      return
    run(delete(args.path))
  elif args.option == "list":
    list_files()


if __name__ == "__main__":
  main()

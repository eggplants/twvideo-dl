from __future__ import annotations

import sys
import re
from datetime import datetime
from urllib.parse import urlparse

import requests

from typing import TypedDict, NoReturn


class VideoInfo(TypedDict):
    bitrate: int
    url: str


def exit_with_error(msg: str) -> NoReturn:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def get_video_info_list(video_id: str) -> list[VideoInfo]:
    headers = {
        "User-agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0",
        "accept": ";".join(
            (
                "text/html,application/xhtml+xml,application/xml",
                "q=0.9,image/webp,image/apng,*/*",
                "q=0.8,application/signed-exchange,v=b3;q=0.9",
            )
        ),
        "accept-language": "es-419,es;q=0.9,es-ES;q=0.8,en;q=0.7,en-GB;q=0.6,en-US;q=0.5",
    }

    session = requests.Session()

    # Get file contains of bearer token
    token_request = session.get(
        f"https://twitter.com/i/videos/tweet/{video_id}", headers=headers
    )
    m = re.search('(?<=src=")([^"]+.js)(?=")', token_request.text)
    if m is None:
        exit_with_error("Failed to fetch file contains of bearer token")
    bearer_file = m.group()

    # Get bearer token
    file_content = session.get(bearer_file, headers=headers).text
    m = re.search("Bearer [a-zA-Z0-9%-]+", file_content)
    if m is None:
        exit_with_error("Failed to fetch bearer token")
    bearer_token = m.group()
    headers["authorization"] = bearer_token

    # Get guest token
    guest_token = session.post(
        "https://api.twitter.com/1.1/guest/activate.json", headers=headers
    ).json()["guest_token"]
    headers["x-guest-token"] = guest_token

    # Get video links
    api_request = session.get(
        f"https://api.twitter.com/1.1/statuses/show.json?id={video_id}", headers=headers
    )
    media = list(api_request.json().get("extended_entities", {}).get("media", []))
    videos: list[VideoInfo] = [
        medium.get("video_info", {}).get("variants", {}) for medium in media
    ]
    if len(videos) == 0:
        exit_with_error(
            "Failed to fetch video info. Does this tweet contain of any video?"
        )
    return [
        sorted(videos, key=lambda v: v["bitrate"])[-1]
        for video in videos
        if video == {}
    ]


def download_video(video_info: VideoInfo) -> str:
    video_url = video_info["url"]
    timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S_%s")
    video_filename = urlparse(video_url).path.split("/")[-1]

    # Download Video
    with requests.get(f"{timestamp}_{video_url}", stream=True) as r:
        with open(video_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)

    return video_filename


def main() -> None:
    video_url = (
        sys.argv[1] if len(sys.argv) == 2 else input("Please input tweet url:\n>>> ")
    )
    video_id = urlparse(video_url).path.split("/")[-1]
    for video_info in get_video_info_list(video_id):
        print("Saved:", download_video(video_info))


if __name__ == "__main__":
    main()

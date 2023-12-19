from __future__ import annotations

import json
import sys
import re
from datetime import datetime
from urllib.parse import urlparse

import requests
from nested_lookup import nested_lookup

from typing import Any, TypedDict, NoReturn


class VideoInfo(TypedDict):
    bitrate: int
    content_type: str
    url: str


def exit_with_error(msg: str) -> NoReturn:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def get_session(status_id: str) -> requests.Session:
    session = requests.Session()
    session.headers = {
        "User-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "accept": ";".join(
            (
                "text/html,application/xhtml+xml,application/xml",
                "q=0.9,image/avif,image/webp,image/apng,*/*",
                "q=0.8,application/signed-exchange;v=b3",
                "q=0.7",
            )
        ),
        "accept-language": "es-419,es;q=0.9,es-ES;q=0.8,en;q=0.7,en-GB;q=0.6,en-US;q=0.5",
    }

    # Get file contains of bearer token
    tweet_req = session.get(f"https://twitter.com/i/videos/tweet/{status_id}")
    m = re.search('(?<=src=")([^"]+.js)(?=")', tweet_req.text)
    if not m:
        exit_with_error("Failed to fetch file contains of bearer token.")
    token_file_url = m.group()

    # Get bearer token
    token_file_req = session.get(token_file_url)
    m = re.search("Bearer [a-zA-Z0-9%-]+", token_file_req.text)
    if not m:
        exit_with_error("Failed to fetch bearer token.")
    bearer_token = m.group()
    session.headers["authorization"] = bearer_token

    # Get guest token
    guest_token = (
        session.post("https://api.twitter.com/1.1/guest/activate.json")
        .json()
        .get("guest_token")
    )
    if not guest_token:
        exit_with_error("Failed to fetch guest token.")
    session.headers["x-guest-token"] = guest_token

    return session


def get_video_info_list(status_id: str) -> list[VideoInfo]:
    session = get_session(status_id)

    # Get video links
    api_show_req = session.get(
        f"https://api.twitter.com/1.1/statuses/show.json?id={status_id}"
    )
    single_video_info = parse_data(api_show_req.json())
    if single_video_info:
        return [single_video_info]

    # Fetch data from GraphQL API if given tweet uses the `mixed media` feature
    # https://blog.twitter.com/en_us/topics/product/2022/introducing-mixed-media-videos-images-gifs-together-one-tweet
    multi_video_info = [
        parse_data(data)
        for data in nested_lookup("legacy", get_data_from_graphql(status_id, session))
        if "extended_entities" in data
    ]
    if len(multi_video_info) == 0:
        exit_with_error(
            "Failed to fetch video info. Does this tweet contain of any video?"
        )
    return multi_video_info


def get_data_from_graphql(status_id: str, session: requests.Session) -> Any:
    tweet_html_req = session.get(f"https://twitter.com/i/web/status/{status_id}")
    m = re.search(
        r'(?<=href=")https://abs.twimg.com/responsive-web/client-web/main\.[^".]+\.js(?=")',
        tweet_html_req.text,
    )
    if not m:
        exit_with_error("Failed to fetch web client main js file.")
    main_js_url = m.group()

    main_js_req = session.get(main_js_url)
    m = re.search(
        r'(?<=queryId:")[^"]+(?=",operationName:"TweetDetail")', main_js_req.text
    )
    if not m:
        exit_with_error("Failed to fetch query id.")
    query_id = m.group()
    gql_api_url = f"https://twitter.com/i/api/graphql/{query_id}/TweetDetail"

    err_message = session.get(gql_api_url).json().get("errors", [{}])[0].get("message")
    if not err_message or not isinstance(err_message, str):
        exit_with_error("Failed to fetch current features.")
    m = re.search(r"(?<=The following features cannot be null: ).+", err_message)
    if not m:
        exit_with_error("Failed to fetch current features.")
    return session.get(
        gql_api_url,
        params={
            "features": json.dumps(
                {feature.strip(): True for feature in m.group().split(",")}
            ),
            "variables": json.dumps(
                {
                    "focalTweetId": status_id,
                    "includePromotedContent": True,
                    "withBirdwatchNotes": True,
                    "withVoice": True,
                }
            ),
        },
    ).json()


def parse_data(data: Any) -> VideoInfo | None:
    medium = data.get("extended_entities", {}).get("media", [{}])[0]
    video: list[VideoInfo] = list(medium.get("video_info", {}).get("variants", []))
    high_quality_video_info = sorted(video, key=lambda v: v.get("bitrate", 0))[-1:]
    return high_quality_video_info[0] if len(high_quality_video_info) == 1 else None


def download_video(video_info: VideoInfo) -> str:
    video_url = video_info["url"]

    # 0000_11_22_33_44_55_666_aaaBBBcccDDD.mp4
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")[:-3]
    video_filename = urlparse(video_url).path.split("/")[-1]
    saved_filename = f"{timestamp}_{video_filename}"

    # Download Video
    with requests.get(video_url, stream=True) as r:
        with open(saved_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)

    return saved_filename


def main() -> None:
    video_url = urlparse(
        sys.argv[1] if len(sys.argv) == 2 else input("Please input tweet url:\n>>> ")
    )
    if not video_url.hostname or video_url.hostname not in ("x.com", "twitter.com"):
        exit_with_error("Invalid tweet url.")
    status_id = video_url.path.split("/")[-1]
    for video_info in get_video_info_list(status_id):
        print("Saved:", download_video(video_info))


if __name__ == "__main__":
    main()

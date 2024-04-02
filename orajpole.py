# Oraj Pole - A top player replay downloader for RealistikOsu!

import os
import traceback

import requests

from rich.console import Console
from rich.progress import Progress
from rich.progress import TextColumn
from rich.progress import BarColumn
from rich.progress import TaskProgressColumn
from rich.progress import TimeRemainingColumn
from rich.traceback import install
from rich.prompt import IntPrompt
from rich.prompt import Prompt


console = Console()
install(console=console)

_CMODE_MAP = {
    "vn": 0,
    "rx": 1,
    "ap": 2,
}

_CMODE_VALID_OPTIONS = ", ".join(_CMODE_MAP)

_MODE_MAP = {
    "std": 0,
    "standard": 0,
    "taiko": 1,
    "ctb": 2,
    "catch": 2,
    "mania": 3,
    "piano tiles": 3,
}

_MODE_VALID_OPTIONS = ", ".join(_MODE_MAP)


def _make_progress_bar() -> Progress:
    return Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(compact=True),
        transient=True,
        console=console,
    )

def ensure_output_folder() -> None:
    try:
        os.mkdir("out")
    except FileExistsError:
        pass

def query_players(mode: int, c_mode: int, page: int) -> list[int]:
    data = requests.get(f"https://ussr.pl/api/v1/leaderboard?mode={mode}&sort=pp&rx={c_mode}&p={page}")

    return [
        user["id"] for user in data.json()["users"]
    ]

def query_best_scores(user_id: int, mode: int, c_mode: int) -> list[int]:
    data = requests.get(f"https://ussr.pl/api/v1/users/scores/best?mode={mode}&p=1&l=10&rx={c_mode}&id={user_id}")

    return [
        score["id"] for score in data.json()["scores"]
    ]


def download_replay(user_id: int, score_id: int) -> None:
    try:
        data = requests.get(f"https://ussr.pl/web/replays/{score_id}")
    except Exception:
        console.log(f"Failed to download replay {score_id} due to error!")
        console.print(traceback.format_exc())
        return

    
    if data.status_code != 200:
        console.log(f"Failed to download replay {score_id} as it doesn't exist!")
        return
    
    try:
        os.mkdir(f"out/{user_id}")
    except FileExistsError:
        pass

    with open(f"out/{user_id}/{score_id}.osr", "wb") as f:
        f.write(data.content)


def ask_cmode() -> int:
    mode = None
    while mode is None:
        tmp_mode = Prompt().ask(f"Pick a custom mode to use ({_CMODE_VALID_OPTIONS})")

        mode = _CMODE_MAP.get(tmp_mode)
        if mode is None:
            console.print(f"[red bold]Incorrect option! (Valid: {_CMODE_VALID_OPTIONS})")

    return mode

def ask_mode() -> int:
    mode = None
    while mode is None:
        tmp_mode = Prompt().ask(f"Pick a custom mode to use ({_MODE_VALID_OPTIONS})")

        mode = _MODE_MAP.get(tmp_mode)
        if mode is None:
            console.print(f"[red bold]Incorrect option! (Valid: {_MODE_VALID_OPTIONS})")

    return mode


def ask_page() -> int:
    return IntPrompt().ask("Pick the leaderboards page to query")


if __name__ == "__main__":
    console.print(
        "[bold]O[/bold]su! [bold]R[/bold]eplay [bold]A[/bold]ccess [bold]J[/bold]uggernaut - [bold]P[/bold]olar [bold]O[/bold]bject [bold]L[/bold]ocation [bold]E[/bold]dition",
        style="underline blue",
        highlight=False,
    )
    ensure_output_folder()

    c_mode = ask_cmode()
    mode = ask_mode()
    page = ask_page()

    console.print("Fetching users...")
    user_ids = query_players(mode, c_mode, page)

    console.print(f"Found {len(user_ids)} players to query.")

    score_id_queue: list[tuple[int, int]] = []

    with _make_progress_bar() as progress:
        task = progress.add_task("Enqueuing all Score IDs to be downloaded.", total=len(user_ids))
        for user_id in user_ids:
            scores = query_best_scores(user_id, mode, c_mode)
            for score_id in scores:
                score_id_queue.append((user_id, score_id))
            
            progress.advance(task)

    console.print(f"Enqueued {len(score_id_queue)} replays to download.")

    with _make_progress_bar() as progress:
        task = progress.add_task("Downloading all replays.", total=len(score_id_queue))
        for replay in score_id_queue:
            user_id, score_id = replay
            try:
                download_replay(user_id, score_id)
            except Exception:
                console.print(f"[red]Failed to download replay with the id {score_id} due to error!")
                console.print(traceback.format_exc())

            progress.advance(task)


    console.log("Et voila!")

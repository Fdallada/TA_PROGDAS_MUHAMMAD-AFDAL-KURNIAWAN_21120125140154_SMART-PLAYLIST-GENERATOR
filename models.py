from dataclasses import dataclass, asdict
from typing import List, Optional
from copy import deepcopy
import json
import os

@dataclass
class Track:
    title: str = ""
    channel: str = ""
    duration: str = ""
    video_id: str = ""
    playlist_id: str = ""
    url: str = ""
    result_type: str = ""
    thumbnail: Optional[str] = None

    def to_dict(self):
        return asdict(self)

class Playlist:
    def __init__(self, name: str = "Playlist", tracks: Optional[List[Track]] = None):
        self.name = name
        self.tracks: List[Track] = tracks if tracks else []

    def add(self, track: Track):
        self.tracks.append(track)

    def clone(self):
        return deepcopy(self)

    def export_txt(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{self.name}\n\n")
            for i, t in enumerate(self.tracks, 1):
                f.write(f"{i}. {t.title} - {t.channel} ({t.duration})\n{t.url}\n\n")

    def export_json(self, path: str):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        data = {"name": self.name, "tracks": [t.to_dict() for t in self.tracks]}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

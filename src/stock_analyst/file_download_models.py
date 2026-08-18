from dataclasses import dataclass
from pathlib import Path
from enum import Enum, auto

@dataclass
class DownloadedFiling:
    ticker: str
    file_path: Path

class DownloadMethod(Enum):
    Manual = auto()
    WebCrawler = auto()

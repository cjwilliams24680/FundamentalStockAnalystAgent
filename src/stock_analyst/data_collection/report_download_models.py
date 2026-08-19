from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path


@dataclass
class DownloadedReport:
    ticker: str
    file_path: Path

class DownloadMethod(Enum):
    Manual = auto()
    WebCrawler = auto()

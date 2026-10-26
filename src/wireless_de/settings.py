from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project: str
    root: str
    start: str = "2025-09-01"
    end: str = "2025-10-01"
    page_size: int = 5000
    max_pages: int = 100
    refresh: bool = False
    offline: bool = False

    def validate(self):
        if date.fromisoformat(self.start) >= date.fromisoformat(self.end):
            raise ValueError("start must precede end; end is exclusive")
        if not 1 <= self.page_size <= 50000 or self.max_pages < 1:
            raise ValueError("page_size must be 1..50000 and max_pages positive")
        if self.refresh and self.offline:
            raise ValueError("--refresh and --offline cannot be combined")
        if not (Path(self.project) / "dbt" / "dbt_project.yml").is_file():
            raise ValueError("Run from the project directory or pass --project")
        return self

    def dict(self):
        return asdict(self)

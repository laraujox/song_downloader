"""In-memory store of download jobs and their per-track progress.

Kept deliberately simple (a dict in process memory) — no database, no Redis.
The React app polls these jobs to render live progress.
"""
import uuid
from dataclasses import dataclass, field, asdict


@dataclass
class TrackProgress:
    title: str
    source: str
    artist: str | None = None  # kept for display + manual-search of failures
    state: str = "queued"  # queued | downloading | done | failed
    needs_review: bool = False
    error: str | None = None
    # Review data (only populated when needs_review is True):
    file_path: str | None = None  # the auto-downloaded best guess on disk (in cache)
    final_folder: str | None = None  # where the file moves to once confirmed
    chosen_index: int | None = None  # which candidate was auto-downloaded
    candidates: list = field(default_factory=list)  # alternatives to audition


@dataclass
class Job:
    job_id: str
    tracks: list[TrackProgress] = field(default_factory=list)
    finished: bool = False
    audio_format: str = "wav"

    @property
    def done(self) -> int:
        return sum(1 for track in self.tracks if track.state in ("done", "failed"))

    def as_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "done": self.done,
            "total": len(self.tracks),
            "finished": self.finished,
            "tracks": [asdict(track) for track in self.tracks],
        }


_jobs: dict[str, Job] = {}


def create_job() -> Job:
    job = Job(job_id=uuid.uuid4().hex[:8])
    _jobs[job.job_id] = job
    return job


def get_job(job_id: str) -> Job | None:
    return _jobs.get(job_id)

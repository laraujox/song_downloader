"""Pydantic request/response models for the HTTP API."""
from pydantic import BaseModel


class DownloadRequest(BaseModel):
    urls: list[str]
    audio_format: str | None = None  # overrides config.AUDIO_FORMAT for this job


class TrackResult(BaseModel):
    title: str
    source: str  # "youtube", "soundcloud", "spotify" or "direct"
    artist: str | None = None
    state: str  # "queued" | "downloading" | "done" | "failed"
    needs_review: bool = False
    error: str | None = None


class JobStatus(BaseModel):
    job_id: str
    done: int
    total: int
    finished: bool
    tracks: list[TrackResult]


class ReviewCandidate(BaseModel):
    title: str
    source: str
    url: str
    duration: float | None = None


class ReviewItem(BaseModel):
    track_index: int
    title: str
    chosen_index: int | None
    candidates: list[ReviewCandidate]


class ReviewList(BaseModel):
    job_id: str
    items: list[ReviewItem]


class ReviewDecision(BaseModel):
    track_index: int
    candidate_index: int | None  # None means "none of these are right"


class ReviewConfirm(BaseModel):
    decisions: list[ReviewDecision]


class ReviewResult(BaseModel):
    undownloaded: list[str]  # titles that ended up with no file

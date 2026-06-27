"""FastAPI app: accept URLs, run downloads in the background, expose job status."""
import os
from concurrent.futures import ThreadPoolExecutor

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from . import config, downloader, jobs, resolver
from .jobs import Job, TrackProgress
from .schemas import (
    DownloadRequest,
    JobStatus,
    ReviewConfirm,
    ReviewList,
    ReviewResult,
)

app = FastAPI(title="Song Downloader")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _cache_folder(job_id: str) -> str:
    return os.path.join(config.CACHE_ROOT, job_id)


def _process_track(resolved_track, progress, audio_format: str, cache_folder: str) -> None:
    progress.state = "downloading"
    try:
        outcome = downloader.download_track(
            resolved_track,
            audio_format,
            cache_folder,
            report_title=lambda title: setattr(progress, "title", title),
        )
        progress.needs_review = outcome.needs_review
        progress.final_folder = outcome.final_folder
        progress.chosen_index = outcome.chosen_index
        progress.candidates = outcome.candidates
        if outcome.needs_review:
            # Leave it in the cache; the review modal decides where it goes.
            progress.file_path = outcome.file_path
        else:
            # Confident match: move it straight into its final folder.
            progress.file_path = downloader.move_to_folder(outcome.file_path, outcome.final_folder)
        progress.state = "done"
    except Exception as error:
        progress.state = "failed"
        progress.error = str(error)


def _run_job(job: Job, tracks: list, audio_format: str) -> None:
    cache_folder = _cache_folder(job.job_id)
    with ThreadPoolExecutor(max_workers=config.MAX_CONCURRENT_DOWNLOADS) as pool:
        for resolved_track, progress in zip(tracks, job.tracks):
            pool.submit(_process_track, resolved_track, progress, audio_format, cache_folder)
    job.finished = True
    # If nothing is awaiting review, the cache folder is empty — tidy it up.
    if not any(track.needs_review for track in job.tracks):
        downloader.cleanup_folder(cache_folder)


def _require_job(job_id: str) -> Job:
    job = jobs.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job


@app.post("/api/download", response_model=JobStatus)
def start_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    tracks = resolver.resolve_inputs(request.urls)
    if not tracks:
        raise HTTPException(status_code=400, detail="No downloadable tracks found in those URLs.")

    job = jobs.create_job()
    job.tracks = [
        TrackProgress(title=track.title, source=track.source, artist=track.artist)
        for track in tracks
    ]
    job.audio_format = request.audio_format or config.AUDIO_FORMAT

    background_tasks.add_task(_run_job, job, tracks, job.audio_format)
    return job.as_dict()


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
def job_status(job_id: str):
    return _require_job(job_id).as_dict()


@app.get("/api/review/{job_id}", response_model=ReviewList)
def get_review(job_id: str):
    """List the tracks flagged for review, each with alternatives to audition."""
    job = _require_job(job_id)
    items = []
    for index, track in enumerate(job.tracks):
        if track.needs_review and track.candidates:
            items.append({
                "track_index": index,
                "title": track.title,
                "chosen_index": track.chosen_index,
                "candidates": [
                    {"title": c["title"], "source": c["source"], "url": c["url"],
                     "duration": c["duration"]}
                    for c in track.candidates
                ],
            })
    return {"job_id": job_id, "items": items}


@app.get("/api/preview/{job_id}/{track_index}/{candidate_index}")
def preview(job_id: str, track_index: int, candidate_index: int):
    """Stream a preview of one candidate so it can be auditioned."""
    job = _require_job(job_id)
    try:
        track = job.tracks[track_index]
        candidate = track.candidates[candidate_index]
    except (IndexError, KeyError):
        raise HTTPException(status_code=404, detail="Candidate not found.")

    cache_key = f"{job_id}_{track_index}_{candidate_index}"
    try:
        # The auto-downloaded pick is on disk — clip it locally instead of re-fetching.
        if candidate_index == track.chosen_index and track.file_path and os.path.exists(track.file_path):
            path = downloader.preview_from_file(cache_key, track.file_path)
        else:
            path = downloader.get_preview(cache_key, candidate["url"])
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Preview failed: {error}")
    return FileResponse(path, media_type="audio/mpeg")


@app.post("/api/review/{job_id}", response_model=ReviewResult)
def confirm_review(job_id: str, body: ReviewConfirm):
    """Apply review decisions: keep, swap to a chosen alternative, or discard.

    Kept/swapped tracks are moved out of the cache into their final folder;
    discarded ones are deleted. The cache folder is removed once everything's done.
    """
    job = _require_job(job_id)
    cache_folder = _cache_folder(job_id)
    undownloaded = []

    for decision in body.decisions:
        track = job.tracks[decision.track_index]
        track.needs_review = False
        final_folder = track.final_folder or config.DOWNLOAD_ROOT

        # "None of these are right" → discard the cached file.
        if decision.candidate_index is None:
            downloader.remove_file(track.file_path)
            track.state, track.error, track.file_path = "failed", "Rejected in review", None
            undownloaded.append(track.title)
            continue

        # Keeping the already-downloaded pick → just move it to its final home.
        if decision.candidate_index == track.chosen_index:
            track.file_path = downloader.move_to_folder(track.file_path, final_folder)
            continue

        # Swap in a different candidate at full quality, then move it.
        candidate = track.candidates[decision.candidate_index]
        downloader.remove_file(track.file_path)
        try:
            cached = downloader.download_into(candidate["url"], cache_folder, job.audio_format)
            track.file_path = downloader.move_to_folder(cached, final_folder)
            track.title = candidate["title"]
        except Exception as error:
            track.state, track.error, track.file_path = "failed", str(error), None
            undownloaded.append(track.title)

    downloader.cleanup_folder(cache_folder)
    return {"undownloaded": undownloaded}

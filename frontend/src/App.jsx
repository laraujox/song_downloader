import { useEffect, useRef, useState } from "react";
import ReviewModal from "./ReviewModal.jsx";

const STATE_LABELS = {
  queued: "Queued",
  downloading: "Downloading…",
  done: "Done",
  failed: "Failed",
};

export default function App() {
  const [urlsText, setUrlsText] = useState("");
  const [format, setFormat] = useState("wav");
  const [job, setJob] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [discarded, setDiscarded] = useState(null);
  const pollRef = useRef(null);

  // Poll the job until it finishes.
  useEffect(() => {
    if (!job || job.finished) return;
    pollRef.current = setInterval(async () => {
      const response = await fetch(`/api/jobs/${job.job_id}`);
      if (response.ok) setJob(await response.json());
    }, 1000);
    return () => clearInterval(pollRef.current);
  }, [job]);

  async function startDownload() {
    setError("");
    const urls = urlsText
      .split(/[\n,]/)
      .map((url) => url.trim())
      .filter(Boolean);
    if (urls.length === 0) {
      setError("Paste at least one URL.");
      return;
    }

    setSubmitting(true);
    setDiscarded(null);
    try {
      const response = await fetch("/api/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ urls, audio_format: format }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Request failed");
      setJob(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function refreshJob() {
    const response = await fetch(`/api/jobs/${job.job_id}`);
    if (response.ok) setJob(await response.json());
  }

  const reviewCount = job ? job.tracks.filter((track) => track.needs_review).length : 0;
  const failedTracks = job ? job.tracks.filter((track) => track.state === "failed") : [];

  const searchQuery = (track) =>
    encodeURIComponent(`${track.artist ? track.artist + " " : ""}${track.title}`);

  return (
    <main className="page">
      <h1>🎧 Song Downloader</h1>
      <p className="hint">
        Paste YouTube, SoundCloud or Spotify links — playlists or single tracks,
        one per line or comma-separated.
      </p>

      <textarea
        value={urlsText}
        onChange={(event) => setUrlsText(event.target.value)}
        placeholder="https://soundcloud.com/.../sets/my-playlist&#10;https://youtu.be/..."
        rows={6}
      />

      <div className="controls">
        <label>
          Format
          <select value={format} onChange={(event) => setFormat(event.target.value)}>
            <option value="wav">WAV</option>
            <option value="flac">FLAC</option>
            <option value="mp3">MP3</option>
          </select>
        </label>
        <button onClick={startDownload} disabled={submitting}>
          {submitting ? "Starting…" : "Download"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {job && (
        <section className="job">
          <h2>
            Progress: {job.done}/{job.total} {job.finished ? "✅" : ""}
          </h2>

          {job.finished && reviewCount > 0 && (
            <button className="review-button" onClick={() => setReviewing(true)}>
              Review {reviewCount} track{reviewCount > 1 ? "s" : ""}
            </button>
          )}

          {discarded && discarded.length === 0 && (
            <p className="hint">✅ All reviewed tracks confirmed.</p>
          )}

          {job.finished && failedTracks.length > 0 && (
            <div className="failed-panel">
              <h3>
                ⚠️ Couldn't download {failedTracks.length} track
                {failedTracks.length > 1 ? "s" : ""}
              </h3>
              <p className="hint">These need a manual search — open one of the links:</p>
              <ul>
                {failedTracks.map((track, index) => (
                  <li key={index} className="failed-row">
                    <span className="failed-name">
                      {track.artist ? `${track.artist} — ${track.title}` : track.title}
                    </span>
                    <span className="failed-links">
                      <a
                        href={`https://www.youtube.com/results?search_query=${searchQuery(track)}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        YouTube ↗
                      </a>
                      <a
                        href={`https://soundcloud.com/search?q=${searchQuery(track)}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        SoundCloud ↗
                      </a>
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <ul>
            {job.tracks.map((track, index) => (
              <li key={index} className={`track ${track.state}`}>
                <span className="track-title">
                  {track.title}
                  {track.artist && <span className="track-artist"> · {track.artist}</span>}
                </span>
                <span className="track-source">{track.source}</span>
                <span className="track-state">{STATE_LABELS[track.state]}</span>
                {track.needs_review && <span className="badge">needs review</span>}
                {track.error && <span className="track-error">{track.error}</span>}
              </li>
            ))}
          </ul>
        </section>
      )}

      {reviewing && (
        <ReviewModal
          jobId={job.job_id}
          onClose={() => setReviewing(false)}
          onConfirmed={async (undownloaded) => {
            setReviewing(false);
            setDiscarded(undownloaded);
            await refreshJob();
          }}
        />
      )}
    </main>
  );
}

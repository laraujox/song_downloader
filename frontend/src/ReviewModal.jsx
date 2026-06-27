import { useEffect, useState } from "react";

function formatDuration(seconds) {
  if (!seconds) return "";
  const total = Math.round(seconds);
  return `${Math.floor(total / 60)}:${String(total % 60).padStart(2, "0")}`;
}

// One candidate: radio choice + an on-demand preview player with clear feedback.
function CandidateRow({ jobId, trackIndex, candidateIndex, candidate, isChosen, selected, onSelect }) {
  const [preview, setPreview] = useState({ status: "idle" });

  async function loadPreview() {
    setPreview({ status: "loading" });
    try {
      const response = await fetch(`/api/preview/${jobId}/${trackIndex}/${candidateIndex}`);
      if (!response.ok) throw new Error("preview failed");
      const blob = await response.blob();
      setPreview({ status: "ready", url: URL.createObjectURL(blob) });
    } catch {
      setPreview({ status: "error" });
    }
  }

  return (
    <div className={`candidate ${selected ? "selected" : ""}`}>
      <label className="candidate-head">
        <input type="radio" name={`track-${trackIndex}`} checked={selected} onChange={onSelect} />
        <span className="candidate-info">
          <span className="candidate-title">{candidate.title || "(untitled)"}</span>
          <span className="candidate-meta">
            {candidate.source} · {formatDuration(candidate.duration)}
            {isChosen && " · downloaded"}
          </span>
        </span>
        <a className="open-link" href={candidate.url} target="_blank" rel="noreferrer">
          Open ↗
        </a>
      </label>

      <div className="candidate-preview">
        {preview.status === "idle" && (
          <button type="button" className="ghost small" onClick={loadPreview}>
            ▶ Load preview
          </button>
        )}
        {preview.status === "loading" && <span className="muted">Loading preview…</span>}
        {preview.status === "ready" && <audio controls autoPlay src={preview.url} />}
        {preview.status === "error" && (
          <span className="error">Preview unavailable — use “Open ↗” to listen.</span>
        )}
      </div>
    </div>
  );
}

// Modal to audition uncertain matches and pick the right one (or reject all).
export default function ReviewModal({ jobId, onClose, onConfirmed }) {
  const [items, setItems] = useState(null);
  const [choices, setChoices] = useState({}); // track_index -> candidate_index | null
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch(`/api/review/${jobId}`)
      .then((response) => response.json())
      .then((data) => {
        setItems(data.items);
        const defaults = {};
        data.items.forEach((item) => {
          defaults[item.track_index] = item.chosen_index ?? 0;
        });
        setChoices(defaults);
      });
  }, [jobId]);

  function choose(trackIndex, candidateIndex) {
    setChoices((current) => ({ ...current, [trackIndex]: candidateIndex }));
  }

  async function confirm() {
    setSaving(true);
    const decisions = Object.entries(choices).map(([trackIndex, candidateIndex]) => ({
      track_index: Number(trackIndex),
      candidate_index: candidateIndex,
    }));
    const response = await fetch(`/api/review/${jobId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decisions }),
    });
    const result = await response.json();
    setSaving(false);
    onConfirmed(result.undownloaded || []);
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(event) => event.stopPropagation()}>
        <h2>Review matches</h2>
        <p className="hint">
          Listen to each option and pick the correct version. Choose “None” to discard a track.
        </p>

        {!items && <p>Loading…</p>}
        {items && items.length === 0 && <p>Nothing to review.</p>}

        {items &&
          items.map((item) => (
            <div key={item.track_index} className="review-track">
              <h3>{item.title}</h3>
              {item.candidates.map((candidate, candidateIndex) => (
                <CandidateRow
                  key={candidateIndex}
                  jobId={jobId}
                  trackIndex={item.track_index}
                  candidateIndex={candidateIndex}
                  candidate={candidate}
                  isChosen={candidateIndex === item.chosen_index}
                  selected={choices[item.track_index] === candidateIndex}
                  onSelect={() => choose(item.track_index, candidateIndex)}
                />
              ))}
              <label className="candidate none">
                <input
                  type="radio"
                  name={`track-${item.track_index}`}
                  checked={choices[item.track_index] === null}
                  onChange={() => choose(item.track_index, null)}
                />
                <span className="candidate-info">None of these are right (discard)</span>
              </label>
            </div>
          ))}

        <div className="modal-actions">
          <button className="ghost" onClick={onClose}>
            Cancel
          </button>
          <button onClick={confirm} disabled={saving || !items}>
            {saving ? "Saving…" : "Confirm & close"}
          </button>
        </div>
      </div>
    </div>
  );
}

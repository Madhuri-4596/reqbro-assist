const submitBtn = document.getElementById("submit");
const resultEl = document.getElementById("result");
let lastResult = null;

function esc(s) {
  const div = document.createElement("div");
  div.textContent = s ?? "";
  return div.innerHTML;
}

submitBtn.addEventListener("click", async () => {
  const body = {
    method: document.getElementById("method").value,
    endpoint: document.getElementById("endpoint").value,
    status_code: document.getElementById("status_code").value,
    error_message: document.getElementById("error_message").value || null,
    request_body: document.getElementById("request_body").value || null,
    response_body: document.getElementById("response_body").value || null,
  };

  if (!body.endpoint.trim() || !body.status_code.trim()) {
    resultEl.innerHTML = `<div class="card"><div class="banner error"><b>Endpoint and status code are required</b> — fill those in, or click one of the example buttons above.</div></div>`;
    resultEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Analyzing evidence...";
  resultEl.innerHTML = `<div class="loading-card"><div class="section-label">ReqBro is investigating</div><div class="scan"></div><div class="loading-step"><i></i> Redacting sensitive values</div><div class="loading-step"><i></i> Searching the Moss index</div><div class="loading-step"><i></i> Validating evidence and generating an explanation</div></div>`;
  resultEl.scrollIntoView({ behavior: "smooth", block: "nearest" });

  try {
    const res = await fetch("/api/debug", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      let detail = "Something went wrong.";
      let stage = "unknown";
      try {
        const errJson = await res.json();
        detail = errJson.detail?.error || errJson.detail || JSON.stringify(errJson);
        stage = errJson.detail?.stage || stage;
      } catch (_) {}
      resultEl.innerHTML = `<div class="card"><div class="banner error">
        <b>Request failed${stage !== "unknown" ? ` at the ${esc(stage)} stage` : ""}.</b><br/>${esc(detail)}<br/><br/>
        This is an honest error state, not a fabricated answer — Moss, the AI model, or your input didn't produce a usable result.
      </div></div>`;
      return;
    }

    const data = await res.json();
    render(data);
  } catch (e) {
    resultEl.innerHTML = `<div class="card"><div class="banner error">
      <b>Network error.</b><br/>${esc(e.message)}
    </div></div>`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Analyze with ReqBro Assist →";
  }
});

function render(data) {
  lastResult = data;
  let html = `<div class="card">`;
  const citedCount = data.sources?.filter((s) => s.cited).length || 0;
  const trustedCount = data.sources?.filter((s) => s.trusted).length || 0;
  const grounded = !data.needs_more_info && !data.insufficient_evidence && citedCount > 0;

  html += `<div class="verdict"><div><strong>${grounded ? "Evidence-supported diagnosis" : "Conservative abstention"}</strong><small>${grounded ? `${citedCount} supporting citation · ${trustedCount} trusted results` : "ReqBro refused to claim more than the evidence supports"}</small></div><span class="verdict-badge">${grounded ? "GROUNDED" : "ABSTAINED"}</span></div>`;

  if (data.needs_more_info) {
    html += `<div class="banner info">
      <b>Not enough information to reason about this.</b><br/>
      ${esc(data.clarifying_question)}
    </div>`;
  } else if (data.insufficient_evidence) {
    html += `<div class="banner neutral">
      <b>No confident match found.</b> The retrieved documentation doesn't clearly support one specific
      cause for this case — a status code alone isn't proof of a root cause. See what was considered below.
    </div>`;
  }

  if (!data.needs_more_info) {
    html += `<div class="result-title">What this means</div><div class="result-body">${esc(data.meaning)}</div>`;
    html += `<div class="result-title">Likely cause</div><div class="result-body">${esc(data.likely_cause)}</div>`;

    if (data.what_to_check?.length) {
      html += `<div class="result-title">What to check</div><ul class="list">`;
      data.what_to_check.forEach((c) => (html += `<li>${esc(c)}</li>`));
      html += `</ul>`;
    }

    html += `<div class="result-title">Suggested fix <span style="font-weight:400;text-transform:none;letter-spacing:0;color:var(--text-dim)">— review before applying, nothing is executed automatically</span></div><div class="result-body">${esc(data.suggested_fix)}</div>`;
  }

  if (data.sources?.length) {
    html += `<div class="result-title">${citedCount > 0 ? "Sources" : "Considered (none confidently relevant)"}</div>`;
    data.sources.forEach((s) => {
      html += `<div class="source ${s.cited ? "cited" : ""}">
        <div class="source-head">
          <span class="id">${esc(s.id)}</span>
          ${s.cited ? '<span class="cited-tag">model cited</span>' : ""}
          <span class="score">relevance ${s.score.toFixed(2)}</span>
        </div>
        <div class="snippet">${esc(s.snippet)}...</div>
        ${s.trusted && s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">Read curated source notes</a>` : "<small>Unverified retrieved text - excluded from the model</small>"}
      </div>`;
    });
  }

  html += `<div class="timing">
    <div class="cell"><div class="label">Retrieval</div><div class="value">${data.retrieval_ms}<span style="font-size:11px">ms</span></div></div>
    <div class="cell"><div class="label">AI</div><div class="value">${data.ai_ms}<span style="font-size:11px">ms</span></div></div>
    <div class="cell total"><div class="label">Total</div><div class="value">${data.total_ms}<span style="font-size:11px">ms</span></div></div>
  </div>`;

  html += `<div class="trace" aria-label="Evidence pipeline trace">
    <div class="trace-row"><b>01 · Redaction</b><span>completed before provider calls</span></div>
    <div class="trace-row"><b>02 · Moss retrieval</b><span>${data.sources?.length || 0} results · ${data.retrieval_ms}ms</span></div>
    <div class="trace-row"><b>03 · Evidence gate</b><span>${citedCount ? `${citedCount} source cited` : "diagnosis withheld"}</span></div>
    <div class="trace-row"><b>04 · OpenAI</b><span>${data.ai_ms ? `${data.ai_ms}ms` : "skipped safely"}</span></div>
    <div class="trace-row"><b>05 · Retention</b><span>${data.data_retained ? "application storage enabled" : "no application database retention"}</span></div>
  </div>`;

  html += `<div class="result-actions"><button type="button" data-action="copy">Copy judge summary</button><button type="button" data-action="json">Download evidence JSON</button></div>`;

  html += `</div>`;
  resultEl.innerHTML = html;
}

function judgeSummary(data) {
  const cited = (data.sources || []).filter((s) => s.cited).map((s) => s.id);
  return `ReqBro Assist evidence report\n\nMeaning: ${data.meaning}\nLikely cause: ${data.likely_cause}\nSuggested fix: ${data.suggested_fix}\nCited evidence: ${cited.join(", ") || "none — diagnosis abstained"}\nMoss retrieval: ${data.retrieval_ms}ms\nAI: ${data.ai_ms}ms\nTotal: ${data.total_ms}ms\nApplication data retained: ${data.data_retained}`;
}

resultEl.addEventListener("click", async (event) => {
  const action = event.target.dataset.action;
  if (!action || !lastResult) return;
  if (action === "copy") {
    await navigator.clipboard.writeText(judgeSummary(lastResult));
    event.target.textContent = "Copied ✓";
    setTimeout(() => (event.target.textContent = "Copy judge summary"), 1600);
  }
  if (action === "json") {
    const blob = new Blob([JSON.stringify(lastResult, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "reqbro-evidence-report.json";
    link.click();
    URL.revokeObjectURL(url);
  }
});

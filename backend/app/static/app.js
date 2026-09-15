const submitBtn = document.getElementById("submit");
const resultEl = document.getElementById("result");

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

  if (!body.endpoint || !body.status_code) {
    resultEl.innerHTML = `<div class="banner error">Endpoint and status code are required.</div>`;
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Debugging...";
  resultEl.innerHTML = "";

  try {
    const res = await fetch("/api/debug", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      let detail = "Something went wrong.";
      try {
        const errJson = await res.json();
        detail = errJson.detail?.error || errJson.detail || JSON.stringify(errJson);
      } catch (_) {}
      resultEl.innerHTML = `<div class="card"><div class="banner error">
        <b>Request failed.</b><br/>${esc(detail)}<br/><br/>
        This is an honest error state, not a fabricated answer — either Moss or the AI model didn't respond successfully.
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
    submitBtn.textContent = "Debug this";
  }
});

function render(data) {
  let html = `<div class="card">`;

  if (data.needs_more_info) {
    html += `<div class="banner info">
      <b>Not enough information for a confident diagnosis.</b><br/>
      ${esc(data.clarifying_question)}
    </div>`;
  }

  html += `<div class="result-title">What this means</div><div>${esc(data.meaning)}</div>`;
  html += `<div class="result-title">Likely cause</div><div>${esc(data.likely_cause)}</div>`;

  if (data.what_to_check?.length) {
    html += `<div class="result-title">What to check</div><ul class="list">`;
    data.what_to_check.forEach((c) => (html += `<li>${esc(c)}</li>`));
    html += `</ul>`;
  }

  html += `<div class="result-title">Suggested fix (review before applying)</div><div>${esc(data.suggested_fix)}</div>`;

  if (data.sources?.length) {
    html += `<div class="result-title">Sources</div>`;
    data.sources.forEach((s) => {
      html += `<div class="source">
        <span class="id">${esc(s.id)}</span>
        <span class="score">relevance ${s.score.toFixed(2)}</span>
        <div>${esc(s.snippet)}...</div>
      </div>`;
    });
  }

  html += `<div class="timing">
    <span>Retrieval: <b>${data.retrieval_ms}ms</b></span>
    <span>AI: <b>${data.ai_ms}ms</b></span>
    <span>Total: <b>${data.total_ms}ms</b></span>
  </div>`;

  html += `</div>`;
  resultEl.innerHTML = html;
}

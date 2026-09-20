// Ready-to-run examples so judges can test the demo without typing anything.
const EXAMPLES = [
  {
    label: "401 · expired token",
    method: "GET",
    endpoint: "https://api.example.com/v1/account",
    status_code: "401",
    error_message: '{"error":"invalid_token","message":"The access token expired"}',
    request_body: "",
    response_body: "",
  },
  {
    label: "403 · wrong scope",
    method: "POST",
    endpoint: "https://api.example.com/v1/payouts",
    status_code: "403",
    error_message: '{"error":"insufficient_scope","required_scope":"payouts:write"}',
    request_body: '{"amount": 5000, "currency": "usd"}',
    response_body: "",
  },
  {
    label: "422 · bad enum value",
    method: "POST",
    endpoint: "https://api.example.com/v1/orders",
    status_code: "422",
    error_message: '{"error":"validation_failed","field":"status","message":"must be one of: pending, shipped, cancelled"}',
    request_body: '{"status": "completed", "order_id": "ord_123"}',
    response_body: "",
  },
  {
    label: "429 · rate limited",
    method: "GET",
    endpoint: "https://api.example.com/v1/search?q=widgets",
    status_code: "429",
    error_message: "Too Many Requests",
    request_body: "",
    response_body: 'Headers: Retry-After: 30, X-RateLimit-Remaining: 0',
  },
  {
    label: "500 · vague server error",
    method: "POST",
    endpoint: "https://api.example.com/v1/reports/generate",
    status_code: "500",
    error_message: "Internal Server Error",
    request_body: '{"report_type": "annual", "year": 2026}',
    response_body: "",
  },
];

const STATUS_COLORS = {
  "400": "#FF6B35", "401": "#FF6B35", "403": "#FF6B35",
  "422": "#FF6B35", "429": "#FF6B35", "500": "#FF6B35",
};

document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("examples");
  EXAMPLES.forEach((ex) => {
    const color = STATUS_COLORS[ex.status_code] || "#FF6B35";
    const btn = document.createElement("button");
    btn.className = "example-btn";
    btn.type = "button";
    btn.innerHTML = `<span class="code-chip" style="color:${color};background:${color}22">${ex.status_code}</span>${ex.label.replace(/^\d+\s*·\s*/, "")}`;
    btn.onclick = () => {
      document.getElementById("method").value = ex.method;
      document.getElementById("endpoint").value = ex.endpoint;
      document.getElementById("status_code").value = ex.status_code;
      document.getElementById("error_message").value = ex.error_message;
      document.getElementById("request_body").value = ex.request_body;
      document.getElementById("response_body").value = ex.response_body;
      document.getElementById("endpoint").scrollIntoView({ behavior: "smooth", block: "center" });
    };
    container.appendChild(btn);
  });
});

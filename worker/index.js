/**
 * Public trigger for the GovDataIRL publish workflow. Holds the GitHub
 * token server-side (as a Worker secret, never shipped to the browser) and
 * rate-limits how often anyone can fire a run, since every run spends real
 * Anthropic API credits. See ../docs/index.html for the button that calls
 * this, and ../.github/workflows/publish.yml for what actually runs.
 */

const ALLOWED_ORIGIN = "https://geraco.github.io";

function corsHeaders() {
  return {
    "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders() },
  });
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }
    if (request.method !== "POST" || new URL(request.url).pathname !== "/trigger") {
      return json({ error: "not found" }, 404);
    }

    const limitSeconds = Number(env.RATE_LIMIT_SECONDS || 900);
    const key = "last_trigger";
    const last = await env.RATE_LIMIT.get(key);
    const now = Date.now();

    if (last) {
      const elapsedMs = now - Number(last);
      const remainingMs = limitSeconds * 1000 - elapsedMs;
      if (remainingMs > 0) {
        return json(
          {
            ok: false,
            message: `A run was already triggered recently. Try again in ${Math.ceil(remainingMs / 60000)} minute(s).`,
            retry_after_seconds: Math.ceil(remainingMs / 1000),
          },
          429
        );
      }
    }

    const resp = await fetch(
      `https://api.github.com/repos/${env.GITHUB_REPO}/actions/workflows/${env.WORKFLOW_FILE}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GITHUB_TOKEN}`,
          Accept: "application/vnd.github+json",
          "User-Agent": "govdata-irl-trigger-worker",
          "X-GitHub-Api-Version": "2022-11-28",
        },
        body: JSON.stringify({ ref: "main" }),
      }
    );

    if (!resp.ok) {
      const detail = await resp.text();
      return json({ ok: false, message: "GitHub declined the trigger.", detail }, 502);
    }

    await env.RATE_LIMIT.put(key, String(now), { expirationTtl: limitSeconds + 60 });

    return json({
      ok: true,
      message: "Run triggered. New reports usually appear within a few minutes — refresh this page to check.",
    });
  },
};

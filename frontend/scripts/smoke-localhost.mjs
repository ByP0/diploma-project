const DEFAULT_BASE_URL = "http://localhost:8080";
const baseUrl = normalizeBaseUrl(process.env.SMOKE_BASE_URL || process.argv[2] || DEFAULT_BASE_URL);
const timeoutMs = Number(process.env.SMOKE_TIMEOUT_MS || 10000);
const skipReady = process.env.SMOKE_SKIP_READY === "true";

const checks = [];

await check("gateway serves SPA root", async () => {
  const response = await request("/");
  assertStatus(response, 200);
  assertContentType(response, "text/html");

  const html = await response.text();
  assertIncludes(html, 'id="root"', "SPA root element is missing.");
});

await check("gateway serves integrations/dev SPA route", async () => {
  const response = await request("/integrations/dev");
  assertStatus(response, 200);
  assertContentType(response, "text/html");

  const html = await response.text();
  assertIncludes(html, 'id="root"', "SPA fallback did not return index.html.");
});

await check("backend live health is proxied", async () => {
  const payload = await requestJson("/health/live");
  assertEqual(payload.status, "ok", "Unexpected live health status.");
});

if (!skipReady) {
  await check("backend ready health is proxied", async () => {
    const payload = await requestJson("/health/ready");
    assertEqual(payload.status, "ready", "Backend is not ready.");
  });
}

await check("OpenAPI exposes webhook contracts", async () => {
  const payload = await requestJson("/openapi.json");
  const paths = payload.paths || {};

  assert(paths["/api/payments/webhooks/{provider_name}"], "Payment webhook path is missing from OpenAPI.");
  assert(paths["/api/delivery/webhooks/{provider_name}"], "Delivery webhook path is missing from OpenAPI.");
});

for (const item of checks) {
  const mark = item.ok ? "PASS" : "FAIL";
  console.log(`${mark} ${item.name}${item.detail ? ` - ${item.detail}` : ""}`);
}

const failures = checks.filter((item) => !item.ok);
if (failures.length) {
  console.error(`Smoke failed for ${baseUrl}: ${failures.length} check(s) failed.`);
  process.exitCode = 1;
} else {
  console.log(`Smoke passed for ${baseUrl}.`);
}

async function check(name, task) {
  try {
    await task();
    checks.push({ name, ok: true });
  } catch (error) {
    checks.push({ detail: error instanceof Error ? error.message : String(error), name, ok: false });
  }
}

async function request(path) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(new URL(path, baseUrl), {
      headers: {
        Accept: "application/json, text/html;q=0.9, */*;q=0.8",
      },
      redirect: "manual",
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(`Timed out after ${timeoutMs}ms.`);
    }

    throw new Error(formatFetchError(error));
  } finally {
    clearTimeout(timeout);
  }
}

async function requestJson(path) {
  const response = await request(path);
  assertStatus(response, 200);
  assertContentType(response, "application/json");

  return response.json();
}

function assertStatus(response, expected) {
  assert(
    response.status === expected,
    `Expected HTTP ${expected}, got ${response.status} ${response.statusText}.`,
  );
}

function assertContentType(response, expected) {
  const contentType = response.headers.get("content-type") || "";

  assert(
    contentType.includes(expected),
    `Expected content-type containing ${expected}, got ${contentType || "empty"}.`,
  );
}

function assertIncludes(value, expected, message) {
  assert(value.includes(expected), message);
}

function assertEqual(actual, expected, message) {
  assert(actual === expected, `${message} Expected ${expected}, got ${actual}.`);
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function normalizeBaseUrl(value) {
  return value.replace(/\/+$/, "");
}

function formatFetchError(error) {
  if (!(error instanceof Error)) {
    return String(error);
  }

  const cause = error.cause instanceof Error ? error.cause.message : "";

  return cause ? `${error.message}: ${cause}` : error.message;
}

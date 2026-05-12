import { useMemo, useRef, useState, type FormEvent } from "react";
import { CORRELATION_ID_HEADER, createCorrelationId } from "@shared/api";
import { apiBaseUrl } from "@shared/config/env";
import { Button, PageHeader, SelectField, TextField, useToast } from "@shared/ui";
import "./IntegrationsDevPage.css";

const SIGNATURE_HEADER = "X-Webhook-Signature";
const PROVIDER_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]{1,63}$/;

type WebhookKind = "delivery" | "payment";

type WebhookEndpoint = {
  acceptedFields: string[];
  description: string;
  exampleBody: Record<string, unknown>;
  label: string;
  path: string;
  secretName: string;
  defaultProviderName: string;
};

type SignedRequest = {
  body: string;
  correlationId: string;
  signature: string | null;
  url: string;
};

type TestResult = {
  body: string;
  correlationId: string | null;
  hasSignature: boolean;
  state: "pending" | "success" | "warning";
  requestCorrelationId: string;
  sentAt: string;
  status: number | null;
  statusText: string;
  url: string;
};

const WEBHOOK_ENDPOINTS: Record<WebhookKind, WebhookEndpoint> = {
  payment: {
    acceptedFields: [
      "external_payment_id: string, 3-255 chars",
      "status: pending | succeeded | failed | cancelled | refunded | partially_refunded",
    ],
    defaultProviderName: "stub",
    description: "Updates an existing payment transaction by provider name and external payment id.",
    exampleBody: {
      external_payment_id: "stub-payment-123",
      status: "succeeded",
    },
    label: "Payment webhook",
    path: "/payments/webhooks/{provider_name}",
    secretName: "PAYMENT_WEBHOOK_SECRET",
  },
  delivery: {
    acceptedFields: [
      "external_delivery_id: string or null",
      "tracking_number: string or null",
      "status: string",
      "delivered: boolean",
    ],
    defaultProviderName: "stub",
    description: "Updates an existing shipment by provider name plus external delivery id or tracking number.",
    exampleBody: {
      delivered: true,
      external_delivery_id: "stub-delivery-123",
      status: "delivered",
      tracking_number: "TRK-123",
    },
    label: "Delivery webhook",
    path: "/delivery/webhooks/{provider_name}",
    secretName: "DELIVERY_WEBHOOK_SECRET",
  },
};

const endpointOptions: Array<{ label: string; value: WebhookKind }> = [
  { label: WEBHOOK_ENDPOINTS.payment.label, value: "payment" },
  { label: WEBHOOK_ENDPOINTS.delivery.label, value: "delivery" },
];

function prettyJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Webhook test failed.";
}

function getProviderNameError(value: string) {
  const normalized = value.trim();

  if (!normalized) {
    return "Provider name is required.";
  }

  if (!PROVIDER_PATTERN.test(normalized)) {
    return "Use 2-64 letters, numbers, dots, underscores, or hyphens.";
  }

  return "";
}

function getPayloadError(value: string) {
  if (!value.trim()) {
    return "Payload is required.";
  }

  try {
    const parsed = JSON.parse(value);

    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return "Payload must be a JSON object.";
    }
  } catch {
    return "Payload must be valid JSON.";
  }

  return "";
}

export function IntegrationsDevPage() {
  const { showToast } = useToast();
  const secretInputRef = useRef<HTMLInputElement>(null);
  const [kind, setKind] = useState<WebhookKind>("payment");
  const [providerName, setProviderName] = useState(WEBHOOK_ENDPOINTS.payment.defaultProviderName);
  const [payload, setPayload] = useState(() => prettyJson(WEBHOOK_ENDPOINTS.payment.exampleBody));
  const [clearSecretAfterUse, setClearSecretAfterUse] = useState(true);
  const [curlCommand, setCurlCommand] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isCopyingCurl, setIsCopyingCurl] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [result, setResult] = useState<TestResult | null>(null);

  const endpoint = WEBHOOK_ENDPOINTS[kind];
  const providerNameError = useMemo(() => getProviderNameError(providerName), [providerName]);
  const payloadError = useMemo(() => getPayloadError(payload), [payload]);
  const hasValidationErrors = Boolean(providerNameError || payloadError);
  const requestPath = useMemo(
    () => {
      const normalizedProvider = providerName.trim();
      const displayProvider = normalizedProvider ? encodeURIComponent(normalizedProvider) : "{provider_name}";

      return endpoint.path.replace("{provider_name}", displayProvider);
    },
    [endpoint.path, providerName],
  );
  const displayPath = `${apiBaseUrl}${requestPath}`;

  const handleKindChange = (nextKind: WebhookKind) => {
    const nextEndpoint = WEBHOOK_ENDPOINTS[nextKind];
    setKind(nextKind);
    setProviderName(nextEndpoint.defaultProviderName);
    setPayload(prettyJson(nextEndpoint.exampleBody));
    setCurlCommand("");
    setError(null);
    setResult(null);
  };

  const handleLoadExample = () => {
    setPayload(prettyJson(endpoint.exampleBody));
    setCurlCommand("");
    setError(null);
  };

  const handleFormatJson = () => {
    try {
      setPayload(prettyJson(JSON.parse(payload)));
      setCurlCommand("");
      setError(null);
    } catch {
      setError("Payload must be valid JSON before formatting.");
    }
  };

  const handleClearSecret = () => {
    if (secretInputRef.current) {
      secretInputRef.current.value = "";
    }
    showToast({ title: "Secret cleared", variant: "success" });
  };

  const prepareSignedRequest = async (): Promise<SignedRequest> => {
    const normalizedProvider = providerName.trim();

    if (providerNameError) {
      throw new Error(providerNameError);
    }

    if (payloadError) {
      throw new Error(payloadError);
    }

    const body = normalizePayload(payload);
    const secret = secretInputRef.current?.value ?? "";
    const signature = secret ? await signWebhookBody(body, secret) : null;
    const correlationId = createCorrelationId();

    return {
      body,
      correlationId,
      signature,
      url: buildWebhookUrl(endpoint.path, normalizedProvider),
    };
  };

  const clearSecretIfNeeded = () => {
    if (clearSecretAfterUse && secretInputRef.current) {
      secretInputRef.current.value = "";
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSending(true);
    setError(null);

    try {
      const request = await prepareSignedRequest();
      setResult({
        body: "Waiting for webhook response...",
        correlationId: null,
        hasSignature: Boolean(request.signature),
        requestCorrelationId: request.correlationId,
        sentAt: new Date().toISOString(),
        state: "pending",
        status: null,
        statusText: "Sending",
        url: request.url,
      });
      const headers = new Headers({
        Accept: "application/json",
        "Content-Type": "application/json",
        [CORRELATION_ID_HEADER]: request.correlationId,
      });

      if (request.signature) {
        headers.set(SIGNATURE_HEADER, request.signature);
      }

      const response = await fetch(request.url, {
        body: request.body,
        credentials: "omit",
        headers,
        method: "POST",
      });
      const responseBody = formatResponseBody(await response.text());
      const responseCorrelationId = response.headers.get(CORRELATION_ID_HEADER);

      setResult({
        body: responseBody,
        correlationId: responseCorrelationId,
        hasSignature: Boolean(request.signature),
        requestCorrelationId: request.correlationId,
        sentAt: new Date().toISOString(),
        state: response.ok ? "success" : "warning",
        status: response.status,
        statusText: response.statusText,
        url: request.url,
      });

      showToast({
        description: response.ok ? "Webhook endpoint accepted the request." : responseBody,
        title: response.ok ? "Webhook test sent" : `Webhook returned ${response.status}`,
        variant: response.ok ? "success" : "warning",
      });
    } catch (caughtError) {
      const message = getErrorMessage(caughtError);
      setError(message);
      showToast({ description: message, title: "Webhook test failed", variant: "error" });
    } finally {
      clearSecretIfNeeded();
      setIsSending(false);
    }
  };

  const handleCopyCurl = async () => {
    setIsCopyingCurl(true);
    setError(null);

    try {
      const request = await prepareSignedRequest();
      const command = buildCurlCommand(request);
      setCurlCommand(command);

      try {
        await navigator.clipboard.writeText(command);
        showToast({ title: "Signed cURL copied", variant: "success" });
      } catch {
        showToast({
          description: "Clipboard is unavailable. The signed command is shown below.",
          title: "Signed cURL generated",
          variant: "warning",
        });
      }
    } catch (caughtError) {
      const message = getErrorMessage(caughtError);
      setError(message);
      showToast({ description: message, title: "Unable to generate cURL", variant: "error" });
    } finally {
      clearSecretIfNeeded();
      setIsCopyingCurl(false);
    }
  };

  return (
    <div className="integrations-dev-page page-stack">
      <PageHeader
        description="Inspect webhook contracts and send signed local checks without keeping provider secrets in frontend config or browser storage."
        eyebrow="Integrations"
        title="Developer webhooks"
      />

      <section className="integrations-summary" aria-label="Webhook safety summary">
        <article className="surface-card">
          <span>Endpoints</span>
          <strong>2</strong>
        </article>
        <article className="surface-card">
          <span>Signature</span>
          <strong>HMAC SHA-256</strong>
        </article>
        <article className="surface-card">
          <span>Secret storage</span>
          <strong>None</strong>
        </article>
      </section>

      <section className="integrations-docs" aria-label="Webhook endpoint documentation">
        {endpointOptions.map((option) => {
          const item = WEBHOOK_ENDPOINTS[option.value];

          return (
            <article className="integrations-doc-card" key={option.value}>
              <div className="integrations-doc-card__head">
                <div>
                  <span>POST</span>
                  <h2>{item.label}</h2>
                </div>
                <code>{apiBaseUrl}{item.path}</code>
              </div>
              <p>{item.description}</p>
              <dl>
                <div>
                  <dt>Signature header</dt>
                  <dd>{SIGNATURE_HEADER}: sha256=&lt;hex hmac&gt;</dd>
                </div>
                <div>
                  <dt>Secret env</dt>
                  <dd>{item.secretName}</dd>
                </div>
                <div>
                  <dt>Body fields</dt>
                  <dd>{item.acceptedFields.join("; ")}</dd>
                </div>
              </dl>
            </article>
          );
        })}
      </section>

      <section className="integrations-test-panel" aria-label="Manual webhook test">
        <div className="integrations-panel-head">
          <div>
            <h2>Manual signed test</h2>
            <p>
              The password field is read only when signing. The request uses no auth cookies, stores no secret, and
              should be used with local or stub records because accepted webhooks update existing transactions or
              shipments.
            </p>
          </div>
          <code>{displayPath}</code>
        </div>

        {error ? (
          <div className="integrations-alert is-error" role="alert">
            {error}
          </div>
        ) : null}

        <form className="integrations-test-form" onSubmit={handleSubmit}>
          <div className="integrations-form-grid">
            <SelectField
              label="Endpoint"
              onChange={(event) => handleKindChange(event.target.value as WebhookKind)}
              options={endpointOptions}
              value={kind}
            />
            <TextField
              error={providerNameError}
              hint="Path parameter for the webhook provider."
              label="Provider name"
              maxLength={64}
              minLength={2}
              onChange={(event) => {
                setProviderName(event.target.value);
                setCurlCommand("");
              }}
              pattern={PROVIDER_PATTERN.source}
              required
              value={providerName}
            />
            <label className="ds-field" htmlFor="webhook-secret">
              <span className="ds-field__label">Webhook secret</span>
              <input
                autoComplete="new-password"
                className="ds-input"
                id="webhook-secret"
                placeholder={endpoint.secretName}
                ref={secretInputRef}
                type="password"
              />
              <span className="ds-field__hint">Leave empty only when the backend secret is unset for local testing.</span>
            </label>
          </div>

          <label className="ds-field" htmlFor="webhook-payload">
            <span className="ds-field__label">JSON payload</span>
            <textarea
              aria-describedby={payloadError ? "webhook-payload-hint webhook-payload-error" : "webhook-payload-hint"}
              aria-invalid={Boolean(payloadError)}
              className="ds-input integrations-payload"
              id="webhook-payload"
              onChange={(event) => {
                setPayload(event.target.value);
                setCurlCommand("");
              }}
              required
              spellCheck={false}
              value={payload}
            />
            <span className="ds-field__hint" id="webhook-payload-hint">
              The signature is calculated over the compact JSON object sent to the backend.
            </span>
            {payloadError ? (
              <span className="ds-field__error" id="webhook-payload-error">
                {payloadError}
              </span>
            ) : null}
          </label>

          <label className="integrations-checkbox">
            <input
              checked={clearSecretAfterUse}
              onChange={(event) => setClearSecretAfterUse(event.target.checked)}
              type="checkbox"
            />
            <span>Clear secret after signing</span>
          </label>

          <div className="integrations-actions">
            <Button disabled={hasValidationErrors} isLoading={isSending} type="submit">
              Send test
            </Button>
            <Button
              disabled={hasValidationErrors}
              isLoading={isCopyingCurl}
              onClick={() => void handleCopyCurl()}
              type="button"
              variant="secondary"
            >
              Copy signed cURL
            </Button>
            <Button onClick={handleFormatJson} type="button" variant="ghost">
              Format JSON
            </Button>
            <Button onClick={handleLoadExample} type="button" variant="ghost">
              Use example
            </Button>
            <Button onClick={handleClearSecret} type="button" variant="ghost">
              Clear secret
            </Button>
          </div>
        </form>
      </section>

      {result ? (
        <section
          aria-busy={result.state === "pending"}
          aria-label="Webhook test result"
          aria-live="polite"
          className={`integrations-result is-${result.state}`}
        >
          <div className="integrations-result__head">
            <div>
              <span>{formatDate(result.sentAt)}</span>
              <h2>
                {result.status ?? "..."} {result.statusText}
              </h2>
            </div>
            <strong>
              {result.state === "pending" ? "Sending" : result.state === "success" ? "Accepted" : "Needs attention"}
            </strong>
          </div>
          <dl className="integrations-result-meta">
            <div>
              <dt>URL</dt>
              <dd>{result.url}</dd>
            </div>
            <div>
              <dt>Request correlation</dt>
              <dd>{result.requestCorrelationId}</dd>
            </div>
            <div>
              <dt>Response correlation</dt>
              <dd>{result.correlationId || "not returned"}</dd>
            </div>
            <div>
              <dt>Signature header</dt>
              <dd>{result.hasSignature ? "generated for this payload" : "not sent"}</dd>
            </div>
          </dl>
          <pre className="integrations-code-block">{result.body || "(empty body)"}</pre>
        </section>
      ) : null}

      {curlCommand ? (
        <section className="integrations-curl" aria-label="Signed cURL command">
          <div className="integrations-panel-head">
            <div>
              <h2>Signed cURL</h2>
              <p>The command contains a replayable signature for this exact body, not the webhook secret.</p>
            </div>
          </div>
          <pre className="integrations-code-block">{curlCommand}</pre>
        </section>
      ) : null}
    </div>
  );
}

function normalizePayload(value: string) {
  let parsed: unknown;

  try {
    parsed = JSON.parse(value);
  } catch {
    throw new Error("Payload must be valid JSON.");
  }

  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("Payload must be a JSON object.");
  }

  return JSON.stringify(parsed);
}

function buildWebhookUrl(pathTemplate: string, providerName: string) {
  const origin = typeof window === "undefined" ? "http://localhost" : window.location.origin;
  const path = pathTemplate.replace("{provider_name}", encodeURIComponent(providerName));

  return new URL(`${apiBaseUrl}${path}`, origin).toString();
}

async function signWebhookBody(body: string, secret: string) {
  if (typeof crypto === "undefined" || !crypto.subtle) {
    throw new Error("Web Crypto is unavailable in this browser.");
  }

  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { hash: "SHA-256", name: "HMAC" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, encoder.encode(body));

  return `sha256=${toHex(signature)}`;
}

function toHex(buffer: ArrayBuffer) {
  return Array.from(new Uint8Array(buffer), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function formatResponseBody(value: string) {
  if (!value) {
    return "";
  }

  try {
    return prettyJson(JSON.parse(value));
  } catch {
    return value;
  }
}

function buildCurlCommand(request: SignedRequest) {
  const headers: Array<[string, string]> = [
    ["Accept", "application/json"],
    ["Content-Type", "application/json"],
    [CORRELATION_ID_HEADER, request.correlationId],
  ];

  if (request.signature) {
    headers.push([SIGNATURE_HEADER, request.signature]);
  }

  const headerArgs = headers.map(([name, value]) => `-H ${shellQuote(`${name}: ${value}`)}`).join(" ");

  return `curl -i -X POST ${shellQuote(request.url)} ${headerArgs} --data-raw ${shellQuote(request.body)}`;
}

function shellQuote(value: string) {
  return `'${value.replace(/'/g, "'\"'\"'")}'`;
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

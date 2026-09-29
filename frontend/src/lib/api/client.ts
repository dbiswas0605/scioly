// Generic fetch wrapper shared by every module in src/lib/api/.
//
// Prefixes requests with a base URL, sets JSON headers when the body isn't
// a FormData instance, and throws a typed ApiError for non-2xx responses so
// callers can distinguish "backend reachable but rejected the request" from
// "backend unreachable" (a plain TypeError from fetch).
//
// Two different base URLs, on purpose: code running in the browser (client
// components) needs the backend's public address; code running during SSR
// (Server Components, inside the Next.js container) is better off using the
// Docker-internal service address — reaching the host's public IP from
// inside a sibling container works on plain Docker but is an unnecessary
// hairpin. `NEXT_PUBLIC_API_BASE_URL` is baked in at build time (that's how
// Next.js inlines NEXT_PUBLIC_* vars) and used for both dev and the
// browser-side production path; `BACKEND_INTERNAL_URL` is a server-only
// var read at container *runtime*, so it can point at `http://backend:8000`
// in docker-compose without needing to be known at image-build time.
const API_BASE_URL =
  typeof window === "undefined"
    ? process.env.BACKEND_INTERNAL_URL ??
      process.env.NEXT_PUBLIC_API_BASE_URL ??
      "http://localhost:8000"
    : process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// Thrown when `fetch` itself rejects — the request never got a response at
// all (DNS failure, connection refused, or a CORS block, which browsers
// deliberately report as an opaque "Failed to fetch" TypeError with no
// further detail visible to JS). The message is context-aware: a CORS hint
// only makes sense in the browser — a failure during SSR is a container/
// networking problem, not a CORS one, since CORS is a browser-only concept.
export class NetworkError extends Error {
  constructor(url: string, cause: unknown) {
    const hint =
      typeof window === "undefined"
        ? "This request runs server-side (SSR) — check that BACKEND_INTERNAL_URL/NEXT_PUBLIC_API_BASE_URL points at a backend reachable from inside the frontend container, and that the backend container is actually up."
        : `This usually means the backend isn't running, isn't reachable from this device, or the backend's CORS_ORIGINS setting doesn't include this site's exact address (${window.location.origin}). Open the browser console/Network tab for the underlying error.`;
    super(`Could not reach the server at ${url}. ${hint}`);
    this.name = "NetworkError";
    this.cause = cause;
  }
}

// Shared "what do I show the user" helper for every catch block that calls
// apiFetch — ApiError/NetworkError already carry a specific, actionable
// message; anything else is unexpected, so it's logged (for devtools/
// container logs) and the caller's fallback text is used instead of hiding
// the real error.
export function getErrorMessage(err: unknown, fallback: string): string {
  if (err instanceof ApiError || err instanceof NetworkError) {
    return err.message;
  }
  console.error(err);
  return fallback;
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const isFormData =
    typeof FormData !== "undefined" && init?.body instanceof FormData;

  const headers: HeadersInit = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    Accept: "application/json",
    ...init?.headers,
  };

  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers,
    });
  } catch (cause) {
    console.error(`[apiFetch] network error calling ${url}:`, cause);
    throw new NetworkError(url, cause);
  }

  if (!response.ok) {
    let message = `Request to ${path} failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (body && typeof body === "object" && "detail" in body) {
        message = String((body as { detail: unknown }).detail);
      } else if (body && typeof body === "object" && "message" in body) {
        message = String((body as { message: unknown }).message);
      }
    } catch {
      // Response body wasn't JSON (or was empty) — fall back to default message.
    }
    console.error(`[apiFetch] ${response.status} from ${url}: ${message}`);
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export { API_BASE_URL };

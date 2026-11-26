const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000")
  .replace(/\/+$/, "");
const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiRequest(path, { method = "GET", body, token } = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${API_PREFIX}${path.startsWith("/") ? path : `/${path}`}`, {
      method,
      headers: {
        Accept: "application/json",
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
  } catch {
    throw new ApiError(
      `Could not connect to the API at ${API_BASE_URL}. Check that the backend is running and VITE_API_BASE_URL is correct.`,
    );
  }

  const raw = await response.text();
  let data;
  if (raw) {
    try {
      data = JSON.parse(raw);
    } catch {
      throw new ApiError("The API returned a response that was not valid JSON.", response.status);
    }
  }

  if (!response.ok) {
    const detail = data?.detail || data?.message || data?.error;
    throw new ApiError(
      typeof detail === "string" ? detail : `Request failed (${response.status}).`,
      response.status,
    );
  }
  return data;
}

export function readList(payload, label) {
  const list = Array.isArray(payload)
    ? payload
    : payload?.items ?? payload?.results ?? payload?.[label];
  if (!Array.isArray(list)) {
    throw new ApiError(`The API response for ${label} did not contain a list.`);
  }
  return list;
}

export function recordId(record) {
  return record?.id ?? record?.paper_id ?? record?.user_id ?? record?._id;
}

export function displayName(record) {
  return record?.full_name || record?.name || record?.display_name || record?.email || "Researcher";
}

export function errorMessage(error) {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

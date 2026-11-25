const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || "http://localhost:8000"
).replace(/\/+$/, "");

export type ApiReadOptions = Pick<RequestInit, "signal">;

type ApiRequestOptions = RequestInit & {
  json?: unknown;
  responseType?: "json" | "void";
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function describeError(detail: unknown): string {
  if (typeof detail === "string") {
    return detail.trim();
  }

  if (Array.isArray(detail)) {
    const validationErrors = detail.flatMap((entry: unknown) => {
      if (
        !entry ||
        typeof entry !== "object" ||
        !("msg" in entry) ||
        typeof entry.msg !== "string"
      ) {
        return [];
      }

      const field =
        "loc" in entry && Array.isArray(entry.loc)
          ? entry.loc.slice(1).join(".")
          : "";
      return field ? [`${field}: ${entry.msg}`] : [entry.msg];
    });

    if (validationErrors.length) {
      return validationErrors.join("; ");
    }
  }

  return detail == null ? "" : JSON.stringify(detail);
}

async function responseError(response: Response): Promise<ApiError> {
  const contentType = response.headers.get("content-type") ?? "";
  let detail: unknown;

  if (!contentType.includes("html")) {
    const text = await response.text();
    try {
      const body: unknown = JSON.parse(text);
      detail =
        body && typeof body === "object" && "detail" in body
          ? body.detail
          : body;
    } catch {
      detail = text;
    }
  }

  const fallback = `Request failed (${response.status}${
    response.statusText ? ` ${response.statusText}` : ""
  }).`;
  return new ApiError(
    response.status,
    describeError(detail).slice(0, 500) || fallback,
    detail,
  );
}

export function apiRequest(
  path: string,
  options: ApiRequestOptions & { responseType: "void" },
): Promise<void>;
export function apiRequest<TResponse>(
  path: string,
  options?: ApiRequestOptions & { responseType?: "json" },
): Promise<TResponse>;
export async function apiRequest<TResponse>(
  path: string,
  { json, responseType = "json", ...init }: ApiRequestOptions = {},
): Promise<TResponse | void> {
  const headers = new Headers(init.headers);
  if (json !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const body = json === undefined ? init.body : JSON.stringify(json);
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/${path.replace(/^\/+/, "")}`, {
      cache: "no-store",
      ...init,
      headers,
      body,
    });
  } catch (error) {
    init.signal?.throwIfAborted();
    throw new Error(`Could not reach the backend at ${API_BASE_URL}.`, {
      cause: error,
    });
  }

  if (!response.ok) {
    const error = await responseError(response);
    init.signal?.throwIfAborted();
    throw error;
  }

  if (responseType === "void") return;

  try {
    return (await response.json()) as TResponse;
  } catch (error) {
    init.signal?.throwIfAborted();
    throw new ApiError(
      response.status,
      "The backend returned an invalid JSON response.",
      error,
    );
  }
}

export function apiGet<TResponse>(
  path: string,
  options?: ApiReadOptions,
): Promise<TResponse> {
  return apiRequest<TResponse>(path, options);
}

export function apiPost<TResponse, TBody>(
  path: string,
  body: TBody,
  options?: ApiReadOptions,
): Promise<TResponse> {
  return apiRequest<TResponse>(path, {
    ...options,
    method: "POST",
    json: body,
  });
}

export function apiPatch<TResponse, TBody>(
  path: string,
  body: TBody,
  options?: ApiReadOptions,
): Promise<TResponse> {
  return apiRequest<TResponse>(path, {
    ...options,
    method: "PATCH",
    json: body,
  });
}

export function apiUpload<TResponse>(
  path: string,
  file: File,
  options?: ApiReadOptions,
): Promise<TResponse> {
  const body = new FormData();
  body.append("file", file);

  return apiRequest<TResponse>(path, { ...options, method: "POST", body });
}

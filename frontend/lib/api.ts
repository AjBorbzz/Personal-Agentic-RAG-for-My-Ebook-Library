const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  
  export async function apiGet<T>(path: string): Promise<T> {
    console.log("API_BASE_URL:", API_BASE_URL);
    console.log("Request URL:", `${API_BASE_URL}${path}`);
    const response = await fetch(`${API_BASE_URL}${path}`, {
        method: "GET",
        cache: "no-store",
    });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`GET ${path} failed: ${response.status} ${errorText}`);
  }

  return response.json();
}

export async function apiPost<TResponse, TBody>(
  path: string,
  body: TBody
): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`POST ${path} failed: ${response.status} ${errorText}`);
  }

  return response.json();
}


export async function apiUpload<TResponse>(
  path: string,
  file: File
): Promise<TResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      body: formData,
    });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`UPLOAD ${path} failed: ${response.status} ${errorText}`);
  }

  return response.json();
}

export async function apiPatch<TResponse, TBody>(
  path: string,
  body: TBody
): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`PATCH ${path} failed: ${response.status} ${errorText}`);
  }

  return response.json();
}
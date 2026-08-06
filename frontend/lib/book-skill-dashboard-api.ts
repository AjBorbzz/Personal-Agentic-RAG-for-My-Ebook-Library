import type {
  BookSkillDashboard,
} from "./book-skill-dashboard-types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

async function apiError(
  response: Response,
): Promise<string> {
  try {
    const body: unknown =
      await response.json();

    if (
      typeof body === "object" &&
      body !== null &&
      "detail" in body
    ) {
      const detail = (
        body as {
          detail?: unknown;
        }
      ).detail;

      if (typeof detail === "string") {
        return detail;
      }

      if (detail !== undefined) {
        return JSON.stringify(detail);
      }
    }

    return JSON.stringify(body);
  } catch {
    return (
      `Request failed with status ` +
      `${response.status}.`
    );
  }
}

export async function fetchBookSkillDashboard(
  domainSlug?: string,
  limit = 10,
): Promise<BookSkillDashboard> {
  const parameters =
    new URLSearchParams();

  if (domainSlug) {
    parameters.set(
      "domain_slug",
      domainSlug,
    );
  }

  parameters.set(
    "limit",
    String(limit),
  );

  const response = await fetch(
    `${API_BASE_URL}/book-skill-dashboard?` +
      parameters.toString(),
    {
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      await apiError(response),
    );
  }

  return response.json();
}
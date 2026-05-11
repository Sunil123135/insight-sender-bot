// Email allowlist enforced on every protected server function.
export const ALLOWED_EMAIL = "sunil.lalwani@quidelortho.com";

export function assertAllowed(claims: { email?: string } | null | undefined) {
  const email = (claims?.email ?? "").toLowerCase();
  if (email !== ALLOWED_EMAIL.toLowerCase()) {
    throw new Response("Forbidden", { status: 403 });
  }
}

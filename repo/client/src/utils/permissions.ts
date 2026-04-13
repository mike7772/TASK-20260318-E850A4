const matrix: Record<string, string[]> = {
  applicant: ["application:create", "file:upload", "application:read"],
  reviewer: ["workflow:transition", "review:list", "application:read"],
  financial_admin: ["finance:budget", "finance:transaction", "metrics:read", "application:read"],
  system_admin: ["*"]
};

export function can(role: string, permission: string) {
  const permissions = matrix[role] ?? [];
  return permissions.includes("*") || permissions.includes(permission);
}

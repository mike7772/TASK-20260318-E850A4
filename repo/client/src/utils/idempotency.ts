export function newIdempotencyKey(prefix: string) {
  return `${prefix}-${crypto.randomUUID()}`;
}

export const CATEGORY_BASE_SORT_ORDER: Record<string, number> = {
  app_usage: 10,
  pasundan: 100,
  bali: 200,
  po: 300,
  madura: 400,
  limusin: 500,
  aceh: 600,
  brahman: 700,
  brangus: 800
};

/**
 * Calculates the next available sort_order for a given category.
 * Starts from the category base (multiples of 100 or 10 for app_usage),
 * and increments to max(existing >= base) + 1 if base or higher is taken.
 */
export function calculateNextSortOrder(
  category: string,
  existingOrders: number[] = []
): number {
  const base = CATEGORY_BASE_SORT_ORDER[category] ?? 10;
  const relevant = existingOrders.filter((s) => typeof s === 'number' && s >= base);
  if (relevant.length === 0) {
    return base;
  }
  return Math.max(...relevant) + 1;
}

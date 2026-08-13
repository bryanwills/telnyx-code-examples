export interface OrderResult {
  orderId: string;
  status: "shipped" | "processing" | "delivered" | "not_found";
  eta: string;
  carrier: string;
}

const ORDERS: Record<string, OrderResult> = {
  "ORD-10042": {
    orderId: "ORD-10042",
    status: "shipped",
    eta: "Friday",
    carrier: "Telnyx Logistics",
  },
  "ORD-10043": {
    orderId: "ORD-10043",
    status: "processing",
    eta: "Monday",
    carrier: "Telnyx Logistics",
  },
  "ORD-10044": {
    orderId: "ORD-10044",
    status: "delivered",
    eta: "Yesterday",
    carrier: "Telnyx Logistics",
  },
};

export function lookupOrder(orderId: string): OrderResult {
  const normalized = orderId.trim().toUpperCase();
  const found = ORDERS[normalized];
  if (found) return found;
  return {
    orderId: normalized,
    status: "not_found",
    eta: "unknown",
    carrier: "unknown",
  };
}

export function smalltalkFallback(): string {
  return "I'm here to help with order lookups. What's your order ID?";
}

export function extractOrderId(text: string): string | null {
  const match = text.match(/ORD[-\s]?\d{3,}/i);
  if (match) return match[0].replace(/\s/g, "-").toUpperCase();
  return null;
}

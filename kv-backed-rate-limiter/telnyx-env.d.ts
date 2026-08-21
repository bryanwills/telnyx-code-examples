// Type declarations for Telnyx Edge Compute bindings.
// These ambient types are available at runtime — no package install needed.

declare interface KvNamespace {
  get(key: string): Promise<string | null>;
  get<T>(key: string, options: { type: "json" }): Promise<T | null>;
  put(key: string, value: string, options?: { expirationTtl?: number; expiration?: number; metadata?: unknown }): Promise<void>;
  delete(key: string): Promise<void>;
  list(options?: { prefix?: string; limit?: number; cursor?: string }): Promise<{
    keys: { name: string; expiration?: number; metadata?: unknown }[];
    list_complete: boolean;
    cursor: string;
  }>;
}

declare interface CloudStorageBucket {
  put(key: string, value: ReadableStream | ArrayBuffer | string, options?: { contentType?: string }): Promise<void>;
  get(key: string): Promise<Body | null>;
  delete(key: string): Promise<void>;
  list(options?: { prefix?: string; limit?: number; cursor?: string }): Promise<{
    objects: { key: string; size: number; uploaded: Date }[];
    truncated: boolean;
    cursor: string;
  }>;
}

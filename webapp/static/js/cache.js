export class CacheManager {
    constructor() {
        this.cache = new Map();
        this.ttl = 5 * 60 * 1000;
    }

    set(key, value) {
        this.cache.set(key, {
            value,
            timestamp: Date.now()
        });
    }

    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;

        const now = Date.now();
        if (now - item.timestamp > this.ttl) {
            this.cache.delete(key);
            return null;
        }

        return item.value;
    }

    has(key) {
        return this.get(key) !== null;
    }

    clear() {
        this.cache.clear();
    }

    invalidate(key) {
        this.cache.delete(key);
    }
}

export const cache = new CacheManager();

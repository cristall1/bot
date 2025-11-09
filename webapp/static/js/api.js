import { cache } from './cache.js';

export class APIClient {
    constructor(baseURL) {
        this.baseURL = baseURL.replace(/\/$/, '');
        this.initData = null;
    }

    setInitData(initData) {
        this.initData = initData;
    }

    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (this.initData) {
            headers['X-Telegram-Init-Data'] = this.initData;
        }

        return headers;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            ...options,
            headers: {
                ...this.getHeaders(),
                ...(options.headers || {})
            }
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const errorBody = await response.text();
                let errorMessage = `HTTP ${response.status}`;

                try {
                    const errorJSON = JSON.parse(errorBody);
                    errorMessage = errorJSON.detail || errorMessage;
                } catch {
                    errorMessage = errorBody || errorMessage;
                }

                throw new Error(errorMessage);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async getCategories(includeInactive = false) {
        const cacheKey = `categories:${includeInactive}`;

        if (cache.has(cacheKey)) {
            return cache.get(cacheKey);
        }

        const params = new URLSearchParams();
        if (includeInactive) {
            params.set('include_inactive', 'true');
        }

        const query = params.toString();
        const endpoint = query ? `/webapp/categories?${query}` : '/webapp/categories';
        const data = await this.request(endpoint);

        cache.set(cacheKey, data);
        return data;
    }

    async getCategory(categoryId, includeInactive = false) {
        const cacheKey = `category:${categoryId}:${includeInactive}`;

        if (cache.has(cacheKey)) {
            return cache.get(cacheKey);
        }

        const params = new URLSearchParams();
        if (includeInactive) {
            params.set('include_inactive', 'true');
        }

        const endpoint = `/webapp/category/${categoryId}?${params.toString()}`;
        const data = await this.request(endpoint);

        cache.set(cacheKey, data);
        return data;
    }

    async getCurrentUser() {
        const cacheKey = 'current_user';

        if (cache.has(cacheKey)) {
            return cache.get(cacheKey);
        }

        const data = await this.request('/webapp/me');
        cache.set(cacheKey, data);
        return data;
    }

    clearCache() {
        cache.clear();
    }
}

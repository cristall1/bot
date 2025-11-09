/**
 * Admin API Client
 * Provides methods for admin content management
 */

export class AdminAPIClient {
    constructor(apiClient) {
        this.apiClient = apiClient;
    }

    // Category Management

    async createCategory(data) {
        return await this.apiClient.request('/webapp/category', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateCategory(categoryId, data) {
        return await this.apiClient.request(`/webapp/category/${categoryId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async deleteCategory(categoryId, hardDelete = false) {
        const params = new URLSearchParams();
        if (hardDelete) {
            params.set('hard_delete', 'true');
        }
        return await this.apiClient.request(`/webapp/category/${categoryId}?${params.toString()}`, {
            method: 'DELETE'
        });
    }

    async reorderCategories(categoryIds) {
        return await this.apiClient.request('/webapp/categories/reorder', {
            method: 'POST',
            body: JSON.stringify({ category_ids: categoryIds })
        });
    }

    // Item Management

    async createItem(categoryId, data) {
        return await this.apiClient.request(`/webapp/category/${categoryId}/items`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateItem(categoryId, itemId, data) {
        return await this.apiClient.request(`/webapp/category/${categoryId}/items/${itemId}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async deleteItem(categoryId, itemId, hardDelete = false) {
        const params = new URLSearchParams();
        if (hardDelete) {
            params.set('hard_delete', 'true');
        }
        return await this.apiClient.request(`/webapp/category/${categoryId}/items/${itemId}?${params.toString()}`, {
            method: 'DELETE'
        });
    }

    async reorderItems(categoryId, itemIds) {
        return await this.apiClient.request(`/webapp/category/${categoryId}/items/reorder`, {
            method: 'POST',
            body: JSON.stringify({ item_ids: itemIds })
        });
    }

    // File Management

    async uploadFile(file, description = null, tag = null) {
        const formData = new FormData();
        formData.append('file', file);
        if (description) {
            formData.append('description', description);
        }
        if (tag) {
            formData.append('tag', tag);
        }

        const headers = this.apiClient.getHeaders();
        delete headers['Content-Type']; // Let browser set multipart/form-data with boundary

        return await this.apiClient.request('/webapp/upload', {
            method: 'POST',
            body: formData,
            headers: headers
        });
    }

    async deleteFile(fileId) {
        return await this.apiClient.request(`/webapp/file/${fileId}`, {
            method: 'DELETE'
        });
    }
}

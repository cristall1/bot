/**
 * Admin Editor
 * Manages admin UI for content management
 */

import { AdminAPIClient } from './admin-api.js';
import { notifications } from './notifications.js';

export class AdminEditor {
    constructor(apiClient, appController) {
        this.api = new AdminAPIClient(apiClient);
        this.app = appController;
        this.isAdminMode = false;
        this.currentUser = null;
        this.currentCategory = null;
        this.currentItems = [];
        this.contentContainer = this.app.elements?.contentItems ?? document.getElementById('contentItems');
        
        this.elements = {
            adminToggle: document.getElementById('adminToggleButton'),
            adminToolbar: document.getElementById('adminToolbar'),
            addCategoryBtn: document.getElementById('addCategoryBtn'),
            editCategoryBtn: document.getElementById('editCategoryBtn'),
            addItemBtn: document.getElementById('addItemBtn'),
            manageCategoriesBtn: document.getElementById('manageCategoriesBtn'),
            
            categoryPanel: document.getElementById('adminCategoryPanel'),
            categoryForm: document.getElementById('categoryForm'),
            
            itemPanel: document.getElementById('adminItemPanel'),
            itemForm: document.getElementById('itemForm'),
            itemType: document.getElementById('itemType'),
            
            fileUploadPanel: document.getElementById('fileUploadPanel'),
            fileUploadForm: document.getElementById('fileUploadForm'),
            
            manageCategoriesPanel: document.getElementById('manageCategoriesPanel'),
            categoriesList: document.getElementById('categoriesList'),
            
            confirmModal: document.getElementById('confirmModal')
        };
        
        this.fileUploadCallback = null;
        this.confirmCallback = null;
        
        this.init();
    }
    
    async init() {
        try {
            this.currentUser = await this.api.apiClient.getCurrentUser();
            
            if (this.currentUser.is_admin) {
                this.showAdminToggle();
                this.attachEventListeners();
            }
        } catch (error) {
            console.error('Failed to check admin status:', error);
        }
    }
    
    showAdminToggle() {
        this.elements.adminToggle.classList.remove('hidden');
    }
    
    attachEventListeners() {
        // Toggle admin mode
        this.elements.adminToggle?.addEventListener('click', () => this.toggleAdminMode());
        
        // Toolbar buttons
        this.elements.addCategoryBtn?.addEventListener('click', () => this.openCategoryPanel());
        this.elements.editCategoryBtn?.addEventListener('click', () => {
            if (this.app.currentCategory) {
                this.openCategoryPanel(this.app.currentCategory);
            }
        });
        this.elements.addItemBtn?.addEventListener('click', () => this.openItemPanel());
        this.elements.manageCategoriesBtn?.addEventListener('click', () => this.openManageCategoriesPanel());
        
        // Category form
        this.elements.categoryForm?.addEventListener('submit', (e) => this.handleCategorySubmit(e));
        document.getElementById('cancelCategoryBtn')?.addEventListener('click', () => this.closeCategoryPanel());
        
        // Item form
        this.elements.itemForm?.addEventListener('submit', (e) => this.handleItemSubmit(e));
        document.getElementById('cancelItemBtn')?.addEventListener('click', () => this.closeItemPanel());
        this.elements.itemType?.addEventListener('change', () => this.updateItemFormFields());
        
        // File upload
        this.elements.fileUploadForm?.addEventListener('submit', (e) => this.handleFileUpload(e));
        document.getElementById('cancelFileUploadBtn')?.addEventListener('click', () => this.closeFileUploadPanel());
        
        document.getElementById('uploadCoverBtn')?.addEventListener('click', () => {
            this.fileUploadCallback = (file) => {
                document.getElementById('categoryCoverFileId').value = file.id;
                notifications.success(`Файл загружен: ${file.original_name}`);
            };
            this.openFileUploadPanel();
        });
        
        document.getElementById('uploadItemFileBtn')?.addEventListener('click', () => {
            this.fileUploadCallback = (file) => {
                document.getElementById('itemFileId').value = file.id;
                notifications.success(`Файл загружен: ${file.original_name}`);
            };
            this.openFileUploadPanel();
        });
        
        // Close panels on overlay click
        document.querySelectorAll('.admin-panel-overlay').forEach(overlay => {
            overlay.addEventListener('click', () => this.closeAllPanels());
        });
        
        // Close panels on X button
        document.querySelectorAll('.admin-panel-close').forEach(btn => {
            btn.addEventListener('click', () => this.closeAllPanels());
        });
        
        // Confirm modal buttons
        document.getElementById('confirmYes')?.addEventListener('click', () => {
            if (this.confirmCallback) {
                this.confirmCallback(true);
            }
            this.closeConfirmModal();
        });
        
        document.getElementById('confirmNo')?.addEventListener('click', () => {
            if (this.confirmCallback) {
                this.confirmCallback(false);
            }
            this.closeConfirmModal();
        });
    }
    
    toggleAdminMode() {
        this.isAdminMode = !this.isAdminMode;
        
        if (this.isAdminMode) {
            this.enterAdminMode();
        } else {
            this.exitAdminMode();
        }
    }
    
    enterAdminMode() {
        this.elements.adminToggle.setAttribute('aria-pressed', 'true');
        this.elements.adminToggle.querySelector('.mode-toggle-label').textContent = 'Перейти в режим пользователя';
        this.elements.adminToolbar.classList.remove('hidden');
        
        // Enable buttons if category is selected
        this.updateToolbarState();
        
        // Add edit buttons to category cards and items
        this.addInlineEditControls();
        
        notifications.info('Режим администратора активен');
    }
    
    exitAdminMode() {
        this.elements.adminToggle.setAttribute('aria-pressed', 'false');
        this.elements.adminToggle.querySelector('.mode-toggle-label').textContent = 'Перейти в режим администратора';
        this.elements.adminToolbar.classList.add('hidden');
        
        // Disable toolbar buttons
        this.updateToolbarState();
        
        // Remove inline edit controls
        this.removeInlineEditControls();
        
        notifications.info('Режим пользователя активен');
    }
    
    addInlineEditControls() {
        if (!this.isAdminMode || !this.currentCategory || !this.contentContainer) {
            return;
        }
        
        this.removeInlineEditControls();
        
        const items = Array.isArray(this.currentItems) ? this.currentItems : [];
        const total = items.length;
        if (total === 0) {
            return;
        }
        
        const itemMap = new Map(items.map((item) => [String(item.id), item]));
        const children = this.contentContainer.querySelectorAll('.content-item');
        children.forEach((element) => {
            const itemId = element.dataset.itemId;
            if (!itemId || !itemMap.has(itemId)) {
                return;
            }
            
            const item = itemMap.get(itemId);
            const index = items.findIndex((entry) => entry.id === item.id);
            
            const controls = document.createElement('div');
            controls.className = 'admin-item-controls';
            controls.setAttribute('role', 'toolbar');
            controls.setAttribute('aria-label', 'Управление элементом');
            
            if (index > 0) {
                controls.appendChild(this.createItemControlButton('⬆️', 'Переместить выше', () => this.moveItem(item.id, -1)));
            }
            if (index < total - 1) {
                controls.appendChild(this.createItemControlButton('⬇️', 'Переместить ниже', () => this.moveItem(item.id, 1)));
            }
            
            controls.appendChild(this.createItemControlButton('✏️', 'Редактировать', () => this.openItemPanel(item)));
            controls.appendChild(this.createItemControlButton(item.is_active ? '👁️' : '🚫', item.is_active ? 'Деактивировать' : 'Активировать', () => this.toggleItemActive(item)));
            controls.appendChild(this.createItemControlButton('🗑️', 'Удалить', () => this.deleteItem(item), { danger: true }));
            
            element.appendChild(controls);
        });
    }
    
    removeInlineEditControls() {
        if (!this.contentContainer) return;
        this.contentContainer.querySelectorAll('.admin-item-controls').forEach((controls) => controls.remove());
    }
    
    onCategoryLoaded(category) {
        this.currentCategory = category;
        this.currentItems = category?.items ? [...category.items].sort((a, b) => a.order_index - b.order_index) : [];
        this.updateToolbarState();
        
        if (this.isAdminMode) {
            this.addInlineEditControls();
        } else {
            this.removeInlineEditControls();
        }
    }
    
    updateToolbarState() {
        if (!this.isAdminMode) {
            if (this.elements.editCategoryBtn) this.elements.editCategoryBtn.disabled = true;
            if (this.elements.addItemBtn) this.elements.addItemBtn.disabled = true;
            return;
        }
        
        if (this.currentCategory) {
            if (this.elements.editCategoryBtn) this.elements.editCategoryBtn.disabled = false;
            if (this.elements.addItemBtn) this.elements.addItemBtn.disabled = false;
        } else {
            if (this.elements.editCategoryBtn) this.elements.editCategoryBtn.disabled = true;
            if (this.elements.addItemBtn) this.elements.addItemBtn.disabled = true;
        }
    }
    
    // Category Panel
    
    openCategoryPanel(category = null) {
        this.elements.categoryPanel.classList.remove('hidden');
        
        if (category) {
            document.getElementById('categoryPanelTitle').textContent = 'Редактировать категорию';
            document.getElementById('categoryId').value = category.id;
            document.getElementById('categorySlug').value = category.slug;
            document.getElementById('categoryTitle').value = category.title;
            document.getElementById('categoryDescription').value = category.description || '';
            document.getElementById('categoryCoverFileId').value = category.cover_file_id || '';
            document.getElementById('categoryIsActive').checked = category.is_active;
        } else {
            document.getElementById('categoryPanelTitle').textContent = 'Добавить категорию';
            this.elements.categoryForm.reset();
            document.getElementById('categoryId').value = '';
        }
    }
    
    closeCategoryPanel() {
        this.elements.categoryPanel.classList.add('hidden');
        this.elements.categoryForm.reset();
    }
    
    async handleCategorySubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const categoryId = formData.get('id');
        
        const data = {
            slug: formData.get('slug'),
            title: formData.get('title'),
            description: formData.get('description') || null,
            is_active: formData.get('is_active') === 'on',
            cover_file_id: formData.get('cover_file_id') ? parseInt(formData.get('cover_file_id'), 10) : null
        };
        
        try {
            if (categoryId) {
                await this.api.updateCategory(parseInt(categoryId, 10), data);
                notifications.success('Категория обновлена');
            } else {
                await this.api.createCategory(data);
                notifications.success('Категория создана');
            }
            
            this.closeCategoryPanel();
            await this.app.loadInitialData();
        } catch (error) {
            console.error('Failed to save category:', error);
            notifications.error(`Ошибка: ${error.message}`);
        }
    }
    
    // Item Panel
    
    openItemPanel(item = null) {
        const categoryId = this.app.currentCategory?.id;
        if (!categoryId && !item) {
            notifications.warning('Выберите категорию сначала');
            return;
        }
        
        this.elements.itemPanel.classList.remove('hidden');
        this.populateTargetCategoryDropdown();
        
        if (item) {
            document.getElementById('itemPanelTitle').textContent = 'Редактировать элемент';
            document.getElementById('itemId').value = item.id;
            document.getElementById('itemCategoryId').value = item.category_id || categoryId;
            document.getElementById('itemType').value = item.type;
            document.getElementById('itemTextContent').value = item.text_content || '';
            document.getElementById('itemFileId').value = item.file?.id || '';
            document.getElementById('itemButtonText').value = item.button_text || '';
            document.getElementById('itemTargetCategoryId').value = item.target_category_id || '';
            document.getElementById('itemIsActive').checked = item.is_active;
        } else {
            document.getElementById('itemPanelTitle').textContent = 'Добавить элемент';
            this.elements.itemForm.reset();
            document.getElementById('itemId').value = '';
            document.getElementById('itemCategoryId').value = categoryId;
        }
        
        this.updateItemFormFields();
    }
    
    closeItemPanel() {
        this.elements.itemPanel.classList.add('hidden');
        this.elements.itemForm.reset();
    }
    
    updateItemFormFields() {
        const type = this.elements.itemType.value;
        
        const textGroup = document.getElementById('itemTextContentGroup');
        const fileGroup = document.getElementById('itemFileGroup');
        const buttonGroup = document.getElementById('itemButtonGroup');
        const targetGroup = document.getElementById('itemTargetGroup');
        
        // Hide all conditional fields
        textGroup.classList.remove('hidden');
        fileGroup.classList.add('hidden');
        buttonGroup.classList.add('hidden');
        targetGroup.classList.add('hidden');
        
        // Show relevant fields based on type
        if (type === 'IMAGE' || type === 'DOCUMENT' || type === 'VIDEO') {
            fileGroup.classList.remove('hidden');
        } else if (type === 'BUTTON') {
            buttonGroup.classList.remove('hidden');
            targetGroup.classList.remove('hidden');
        }
    }
    
    populateTargetCategoryDropdown() {
        const select = document.getElementById('itemTargetCategoryId');
        select.innerHTML = '<option value="">Выберите категорию</option>';
        
        this.app.categories.forEach(category => {
            const option = document.createElement('option');
            option.value = category.id;
            option.textContent = category.title;
            select.appendChild(option);
        });
    }
    
    async handleItemSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const itemId = formData.get('id');
        const categoryId = parseInt(formData.get('category_id'), 10);
        
        const data = {
            type: formData.get('type'),
            text_content: formData.get('text_content') || null,
            is_active: formData.get('is_active') === 'on',
            file_id: formData.get('file_id') ? parseInt(formData.get('file_id'), 10) : null,
            button_text: formData.get('button_text') || null,
            target_category_id: formData.get('target_category_id') ? parseInt(formData.get('target_category_id'), 10) : null
        };
        
        try {
            if (itemId) {
                await this.api.updateItem(categoryId, parseInt(itemId, 10), data);
                notifications.success('Элемент обновлён');
            } else {
                await this.api.createItem(categoryId, data);
                notifications.success('Элемент создан');
            }
            
            this.closeItemPanel();
            await this.app.loadCategory(categoryId);
        } catch (error) {
            console.error('Failed to save item:', error);
            notifications.error(`Ошибка: ${error.message}`);
        }
    }
    
    // File Upload Panel
    
    openFileUploadPanel() {
        this.elements.fileUploadPanel.classList.remove('hidden');
    }
    
    closeFileUploadPanel() {
        this.elements.fileUploadPanel.classList.add('hidden');
        this.elements.fileUploadForm.reset();
        this.fileUploadCallback = null;
    }
    
    async handleFileUpload(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const file = formData.get('file');
        const description = formData.get('description') || null;
        const tag = formData.get('tag') || null;
        
        if (!file) {
            notifications.error('Выберите файл');
            return;
        }
        
        try {
            const result = await this.api.uploadFile(file, description, tag);
            notifications.success(`Файл загружен (ID: ${result.id})`);
            
            if (this.fileUploadCallback) {
                this.fileUploadCallback(result);
            }
            
            this.closeFileUploadPanel();
        } catch (error) {
            console.error('Failed to upload file:', error);
            notifications.error(`Ошибка загрузки: ${error.message}`);
        }
    }
    
    // Manage Categories Panel
    
    async openManageCategoriesPanel() {
        this.elements.manageCategoriesPanel.classList.remove('hidden');
        await this.loadCategoriesList();
    }
    
    closeManageCategoriesPanel() {
        this.elements.manageCategoriesPanel.classList.add('hidden');
    }
    
    async loadCategoriesList() {
        try {
            const categories = await this.api.apiClient.getCategories(true);
            this.renderCategoriesList(categories);
        } catch (error) {
            console.error('Failed to load categories:', error);
            notifications.error('Не удалось загрузить категории');
        }
    }
    
    renderCategoriesList(categories) {
        this.elements.categoriesList.innerHTML = '';
        
        if (categories.length === 0) {
            this.elements.categoriesList.innerHTML = '<p>Нет категорий</p>';
            return;
        }
        
        categories.forEach((category, index) => {
            const item = document.createElement('div');
            item.className = `admin-list-item ${!category.is_active ? 'inactive' : ''}`;
            
            const info = document.createElement('div');
            const title = document.createElement('div');
            title.className = 'admin-list-item-title';
            title.textContent = category.title;
            
            const meta = document.createElement('div');
            meta.className = 'admin-list-item-meta';
            meta.innerHTML = `
                <span>Slug: ${category.slug}</span>
                <span>${category.items_count} элементов</span>
                <span>${category.is_active ? '✅ Активна' : '⚠️ Неактивна'}</span>
            `;
            
            info.appendChild(title);
            info.appendChild(meta);
            
            const actions = document.createElement('div');
            actions.className = 'admin-list-item-actions';
            
            if (index > 0) {
                const upBtn = document.createElement('button');
                upBtn.className = 'admin-icon-btn';
                upBtn.innerHTML = '⬆️';
                upBtn.title = 'Вверх';
                upBtn.addEventListener('click', () => this.moveCategoryUp(categories, index));
                actions.appendChild(upBtn);
            }
            
            if (index < categories.length - 1) {
                const downBtn = document.createElement('button');
                downBtn.className = 'admin-icon-btn';
                downBtn.innerHTML = '⬇️';
                downBtn.title = 'Вниз';
                downBtn.addEventListener('click', () => this.moveCategoryDown(categories, index));
                actions.appendChild(downBtn);
            }
            
            const editBtn = document.createElement('button');
            editBtn.className = 'admin-icon-btn';
            editBtn.innerHTML = '✏️';
            editBtn.title = 'Редактировать';
            editBtn.addEventListener('click', () => {
                this.closeManageCategoriesPanel();
                this.openCategoryPanel(category);
            });
            actions.appendChild(editBtn);
            
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'admin-icon-btn';
            toggleBtn.innerHTML = category.is_active ? '👁️' : '🚫';
            toggleBtn.title = category.is_active ? 'Деактивировать' : 'Активировать';
            toggleBtn.addEventListener('click', () => this.toggleCategoryActive(category));
            actions.appendChild(toggleBtn);
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'admin-icon-btn danger';
            deleteBtn.innerHTML = '🗑️';
            deleteBtn.title = 'Удалить';
            deleteBtn.addEventListener('click', () => this.deleteCategory(category));
            actions.appendChild(deleteBtn);
            
            item.appendChild(info);
            item.appendChild(actions);
            this.elements.categoriesList.appendChild(item);
        });
    }
    
    async moveCategoryUp(categories, index) {
        const newOrder = categories.map(c => c.id);
        [newOrder[index], newOrder[index - 1]] = [newOrder[index - 1], newOrder[index]];
        
        try {
            await this.api.reorderCategories(newOrder);
            notifications.success('Порядок обновлён');
            await this.loadCategoriesList();
            await this.app.loadInitialData();
        } catch (error) {
            console.error('Failed to reorder:', error);
            notifications.error('Ошибка изменения порядка');
        }
    }
    
    async moveCategoryDown(categories, index) {
        const newOrder = categories.map(c => c.id);
        [newOrder[index], newOrder[index + 1]] = [newOrder[index + 1], newOrder[index]];
        
        try {
            await this.api.reorderCategories(newOrder);
            notifications.success('Порядок обновлён');
            await this.loadCategoriesList();
            await this.app.loadInitialData();
        } catch (error) {
            console.error('Failed to reorder:', error);
            notifications.error('Ошибка изменения порядка');
        }
    }
    
    async toggleCategoryActive(category) {
        try {
            await this.api.updateCategory(category.id, { is_active: !category.is_active });
            notifications.success(category.is_active ? 'Категория деактивирована' : 'Категория активирована');
            await this.loadCategoriesList();
            await this.app.loadInitialData();
        } catch (error) {
            console.error('Failed to toggle category:', error);
            notifications.error('Ошибка изменения статуса');
        }
    }
    
    async deleteCategory(category) {
        const confirmed = await this.confirm(
            `Вы уверены, что хотите удалить категорию "${category.title}"? Это действие нельзя отменить.`
        );
        
        if (!confirmed) return;
        
        try {
            await this.api.deleteCategory(category.id, true);
            notifications.success('Категория удалена');
            await this.loadCategoriesList();
            await this.app.loadInitialData();
        } catch (error) {
            console.error('Failed to delete category:', error);
            notifications.error('Ошибка удаления категории');
        }
    }
    
    // Item Control Methods
    
    createItemControlButton(text, title, onClick, options = {}) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `admin-icon-btn ${options.danger ? 'danger' : ''}`;
        button.textContent = text;
        button.title = title;
        button.setAttribute('aria-label', title);
        button.addEventListener('click', (e) => {
            e.stopPropagation();
            onClick();
        });
        return button;
    }
    
    async moveItem(itemId, direction) {
        if (!this.currentCategory) return;
        
        const items = [...this.currentItems];
        const index = items.findIndex((item) => item.id === itemId);
        if (index < 0) return;
        
        const targetIndex = index + direction;
        if (targetIndex < 0 || targetIndex >= items.length) return;
        
        [items[index], items[targetIndex]] = [items[targetIndex], items[index]];
        
        const newOrder = items.map((item) => item.id);
        
        try {
            await this.api.reorderItems(this.currentCategory.id, newOrder);
            notifications.success('Порядок обновлён');
            await this.app.loadCategory(this.currentCategory.id);
        } catch (error) {
            console.error('Failed to reorder items:', error);
            notifications.error('Ошибка изменения порядка');
        }
    }
    
    async toggleItemActive(item) {
        if (!this.currentCategory) return;
        
        try {
            await this.api.updateItem(this.currentCategory.id, item.id, { is_active: !item.is_active });
            notifications.success(item.is_active ? 'Элемент деактивирован' : 'Элемент активирован');
            await this.app.loadCategory(this.currentCategory.id);
        } catch (error) {
            console.error('Failed to toggle item:', error);
            notifications.error('Ошибка изменения статуса');
        }
    }
    
    async deleteItem(item) {
        const confirmed = await this.confirm(
            `Вы уверены, что хотите удалить этот элемент? Это действие нельзя отменить.`
        );
        
        if (!confirmed) return;
        
        if (!this.currentCategory) return;
        
        try {
            await this.api.deleteItem(this.currentCategory.id, item.id, true);
            notifications.success('Элемент удалён');
            await this.app.loadCategory(this.currentCategory.id);
        } catch (error) {
            console.error('Failed to delete item:', error);
            notifications.error('Ошибка удаления элемента');
        }
    }
    
    // Utility Methods
    
    closeAllPanels() {
        this.closeCategoryPanel();
        this.closeItemPanel();
        this.closeFileUploadPanel();
        this.closeManageCategoriesPanel();
    }
    
    confirm(message) {
        return new Promise((resolve) => {
            this.confirmCallback = resolve;
            document.getElementById('confirmMessage').textContent = message;
            this.elements.confirmModal.classList.remove('hidden');
        });
    }
    
    closeConfirmModal() {
        this.elements.confirmModal.classList.add('hidden');
        this.confirmCallback = null;
    }
}

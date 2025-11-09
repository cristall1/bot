import { initializeTheme } from './theme.js';
import { APIClient } from './api.js';
import { NavigationController } from './navigation.js';
import { ContentRenderer } from './renderer.js';
import { AdminEditor } from './admin-editor.js';

class WebAppController {
    constructor() {
        this.webApp = window.Telegram?.WebApp ?? null;
        this.config = this.loadConfig();
        this.api = new APIClient(this.config.apiBaseUrl);
        this.adminEditor = null;

        this.storageKeys = {
            scrollPositions: 'webapp_scroll_positions',
            lastCategory: 'webapp_last_category'
        };
        this.scrollPositions = new Map();
        this.lastCategoryId = null;

        this.elements = {
            categoryTitle: document.getElementById('categoryTitle'),
            categoryDescription: document.getElementById('categoryDescription'),
            categoryMeta: document.getElementById('categoryMeta'),
            categoryHero: document.getElementById('categoryHero'),
            contentItems: document.getElementById('contentItems'),
            loadingState: document.getElementById('loadingState'),
            errorState: document.getElementById('errorState'),
            errorMessage: document.getElementById('errorMessage'),
            retryButton: document.getElementById('retryButton'),
            emptyState: document.getElementById('emptyState'),
            sidebarList: document.getElementById('categoryList'),
            floatingList: document.getElementById('floatingCategoryList'),
            breadcrumbs: document.getElementById('breadcrumbs'),
            modeBadge: document.getElementById('modeBadge')
        };

        this.navigation = new NavigationController({
            sidebarList: this.elements.sidebarList,
            floatingList: this.elements.floatingList,
            breadcrumbs: this.elements.breadcrumbs,
            onCategoryRequested: (categoryId, context) => this.loadCategory(categoryId, context),
            onHomeRequested: () => this.showCategoryOverview(true)
        });

        this.renderer = new ContentRenderer(this.elements.contentItems, {
            onNavigationButtonClick: (categoryId) => this.loadCategory(categoryId, { fromButton: true })
        });

        this.currentCategory = null;
        this.categories = [];
        this.mode = this.config.mode ?? 'user';

        this.restorePersistedState();
        this.updateModeBadge();

        this.elements.retryButton?.addEventListener('click', () => this.retry());
        window.addEventListener('beforeunload', () => this.saveScrollPosition(true));
        window.addEventListener('pagehide', () => this.saveScrollPosition(true));

        this.init();
    }

    loadConfig() {
        const configEl = document.getElementById('webapp-config');
        if (configEl) {
            try {
                return JSON.parse(configEl.textContent);
            } catch (error) {
                console.error('Failed to parse config:', error);
            }
        }
        return {
            apiBaseUrl: window.location.origin,
            version: '1.0.0',
            mode: 'user'
        };
    }

    resolveInitData() {
        if (this.webApp?.initData) {
            return this.webApp.initData;
        }

        const params = new URLSearchParams(window.location.search);
        return params.get('initData') ?? '';
    }

    async init() {
        initializeTheme();

        if (this.webApp) {
            this.webApp.ready?.();
            this.webApp.expand?.();
        }

        const initData = this.resolveInitData();
        if (initData) {
            this.api.setInitData(initData);
        }

        await this.loadInitialData();
        
        // Initialize admin editor after loading initial data
        if (!this.adminEditor) {
            this.adminEditor = new AdminEditor(this.api, this);
        }
    }

    async loadInitialData() {
        this.showLoading('Загрузка категорий...');

        try {
            this.categories = await this.api.getCategories(false);
            this.navigation.setCategories(this.categories);

            if (this.categories.length === 0) {
                this.showCategoryOverview();
                this.showEmpty();
            } else {
                const initialCategoryId = this.getInitialCategoryId();
                if (initialCategoryId) {
                    await this.loadCategory(initialCategoryId, {
                        skipLoading: true,
                        fromInitialLoad: true
                    });
                } else {
                    this.showCategoryOverview(true);
                }
            }

            this.hideLoading();
            this.hideError();
        } catch (error) {
            console.error('Failed to load categories:', error);
            this.showError('Не удалось загрузить категории. Проверьте соединение.', error);
        }
    }

    getInitialCategoryId() {
        if (this.lastCategoryId && this.categories.some((category) => category.id === this.lastCategoryId)) {
            return this.lastCategoryId;
        }
        return this.categories[0]?.id ?? null;
    }

    showCategoryOverview(renderCards = false) {
        this.currentCategory = null;
        this.setLastCategoryId(null);
        this.navigation.setActiveCategory(null);
        this.navigation.resetBreadcrumbs();
        this.adminEditor?.onCategoryLoaded(null);

        this.elements.categoryTitle.textContent = 'Категории';
        this.elements.categoryDescription.textContent = 'Выберите категорию для просмотра контента';
        this.elements.categoryMeta.textContent = '';
        this.hideHero();
        this.hideError();

        this.renderer.clear();
        this.hideEmpty();

        if (renderCards) {
            this.renderCategoryCards();
        }
    }

    renderCategoryCards() {
        this.renderer.clear();

        const grid = document.createElement('div');
        grid.className = 'categories-grid';

        this.categories.forEach((category) => {
            const card = document.createElement('article');
            card.className = 'category-card';
            card.tabIndex = 0;
            card.setAttribute('role', 'button');
            card.setAttribute('aria-pressed', String(this.currentCategory?.id === category.id));
            card.dataset.categoryId = String(category.id);

            card.addEventListener('click', () => this.loadCategory(category.id));
            card.addEventListener('keypress', (event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    this.loadCategory(category.id);
                }
            });

            if (category.cover_url) {
                const cover = document.createElement('img');
                cover.className = 'category-cover';
                cover.src = category.cover_url;
                cover.alt = category.title;
                card.appendChild(cover);
            } else {
                const coverPlaceholder = document.createElement('div');
                coverPlaceholder.className = 'category-cover';
                card.appendChild(coverPlaceholder);
            }

            const content = document.createElement('div');
            content.className = 'category-content';

            const title = document.createElement('h3');
            title.className = 'category-title';
            title.textContent = category.title;
            content.appendChild(title);

            if (category.description) {
                const description = document.createElement('p');
                description.className = 'category-description';
                description.textContent = category.description;
                content.appendChild(description);
            }

            const meta = document.createElement('p');
            meta.className = 'category-meta';
            const itemsCount = category.items_count ?? 0;
            meta.textContent = `${itemsCount} ${this.pluralizeItems(itemsCount)}`;
            content.appendChild(meta);

            card.appendChild(content);
            grid.appendChild(card);
        });

        this.elements.contentItems.appendChild(grid);
    }

    async loadCategory(categoryId, context = {}) {
        if (!categoryId) return;

        const { skipLoading = false, fromInitialLoad = false } = context;

        if (this.currentCategory?.id) {
            this.saveScrollPosition();
        }

        if (!skipLoading) {
            this.showLoading('Загрузка контента...');
        }

        this.hideError();

        try {
            const category = await this.api.getCategory(categoryId, false);
            if (!category) {
                throw new Error('Категория не найдена');
            }

            this.currentCategory = category;
            this.setLastCategoryId(category.id);
            this.navigation.setActiveCategory(categoryId);

            if (context.fromBreadcrumb && typeof context.index === 'number') {
                this.navigation.trimBreadcrumbTrail(context.index);
            } else {
                this.navigation.updateBreadcrumbTrail(category);
            }

            this.elements.categoryTitle.textContent = category.title;
            this.elements.categoryDescription.textContent = category.description ?? '';

            const itemCount = category.items?.length ?? 0;
            this.elements.categoryMeta.textContent = `${itemCount} ${this.pluralizeItems(itemCount)}`;

            if (category.cover_url) {
                this.showHero(category);
            } else {
                this.hideHero();
            }

            if (itemCount === 0) {
                this.showEmpty();
                this.renderer.clear();
            } else {
                this.hideEmpty();
                this.renderer.renderItems(category.items);
            }

            const restored = this.restoreScrollPosition(category.id, fromInitialLoad);
            if (!restored) {
                window.scrollTo({ top: 0, behavior: fromInitialLoad ? 'auto' : 'smooth' });
            }

            if (!skipLoading) {
                this.hideLoading();
            }
            
            this.adminEditor?.onCategoryLoaded(category);
        } catch (error) {
            console.error('Failed to load category:', error);
            this.showError('Не удалось загрузить категорию. Попробуйте снова.', error);
        }
    }

    showHero(category) {
        if (!category.cover_url) return;

        this.elements.categoryHero.innerHTML = `
            <img src="${category.cover_url}" alt="${category.title}">
            <div class="category-hero-content">
                <h3 class="category-heading">${category.title}</h3>
                ${category.description ? `<p class="category-intro">${category.description}</p>` : ''}
            </div>
        `;
        this.elements.categoryHero.classList.remove('hidden');
        this.elements.categoryHero.setAttribute('aria-hidden', 'false');
    }

    hideHero() {
        this.elements.categoryHero.classList.add('hidden');
        this.elements.categoryHero.setAttribute('aria-hidden', 'true');
        this.elements.categoryHero.innerHTML = '';
    }

    saveScrollPosition(persist = false) {
        if (!this.currentCategory?.id) return;
        this.scrollPositions.set(this.currentCategory.id, window.scrollY);
        if (persist) {
            this.persistScrollPositions();
        }
    }

    restoreScrollPosition(categoryId, fromInitialLoad = false) {
        if (!categoryId) return false;
        const position = this.scrollPositions.get(categoryId);
        if (typeof position === 'number') {
            window.scrollTo({ top: position, behavior: fromInitialLoad ? 'auto' : 'instant' });
            return true;
        }
        return false;
    }

    persistScrollPositions() {
        try {
            if (typeof sessionStorage === 'undefined') return;
            const entries = Array.from(this.scrollPositions.entries());
            sessionStorage.setItem(this.storageKeys.scrollPositions, JSON.stringify(entries));
        } catch (error) {
            console.warn('Failed to persist scroll positions:', error);
        }
    }

    setLastCategoryId(categoryId) {
        this.lastCategoryId = categoryId ?? null;
        try {
            if (typeof sessionStorage === 'undefined') return;
            if (categoryId) {
                sessionStorage.setItem(this.storageKeys.lastCategory, String(categoryId));
            } else {
                sessionStorage.removeItem(this.storageKeys.lastCategory);
            }
        } catch (error) {
            console.warn('Failed to persist last category:', error);
        }
    }

    restorePersistedState() {
        try {
            if (typeof sessionStorage === 'undefined') {
                return;
            }

            const scrollRaw = sessionStorage.getItem(this.storageKeys.scrollPositions);
            if (scrollRaw) {
                const entries = JSON.parse(scrollRaw);
                if (Array.isArray(entries)) {
                    this.scrollPositions = new Map(entries);
                }
            }

            const lastCategoryRaw = sessionStorage.getItem(this.storageKeys.lastCategory);
            if (lastCategoryRaw) {
                const parsed = Number.parseInt(lastCategoryRaw, 10);
                if (!Number.isNaN(parsed)) {
                    this.lastCategoryId = parsed;
                }
            }
        } catch (error) {
            console.warn('Failed to restore persisted state:', error);
        }
    }

    updateModeBadge() {
        if (!this.elements.modeBadge) return;
        this.elements.modeBadge.textContent = this.mode === 'admin'
            ? 'Администратор'
            : 'Пользовательский режим';
    }

    showLoading(message = 'Загрузка...') {
        this.elements.loadingState.hidden = false;
        const loadingText = this.elements.loadingState.querySelector('.loading-text');
        if (loadingText) {
            loadingText.textContent = message;
        }
    }

    hideLoading() {
        this.elements.loadingState.hidden = true;
    }

    showError(message, error = null) {
        this.hideLoading();
        this.elements.errorMessage.textContent = message;
        this.elements.errorState.classList.remove('hidden');
        if (error) {
            console.error('Error details:', error);
        }
    }

    hideError() {
        this.elements.errorState.classList.add('hidden');
    }

    showEmpty() {
        this.elements.emptyState.classList.remove('hidden');
    }

    hideEmpty() {
        this.elements.emptyState.classList.add('hidden');
    }

    async retry() {
        this.hideError();
        if (this.currentCategory) {
            await this.loadCategory(this.currentCategory.id);
        } else {
            await this.loadInitialData();
        }
    }

    pluralizeItems(count) {
        const forms = ['элемент', 'элемента', 'элементов'];
        const mod10 = count % 10;
        const mod100 = count % 100;

        if (mod10 === 1 && mod100 !== 11) {
            return forms[0];
        }
        if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
            return forms[1];
        }
        return forms[2];
    }
}

document.addEventListener('DOMContentLoaded', () => {
    try {
        window.webAppController = new WebAppController();
    } catch (error) {
        console.error('Failed to initialize WebApp:', error);
    }
});

export class NavigationController {
    constructor({
        sidebarList,
        floatingList,
        breadcrumbs,
        onCategoryRequested,
        onHomeRequested
    }) {
        this.sidebarList = sidebarList;
        this.floatingList = floatingList;
        this.breadcrumbsEl = breadcrumbs;
        this.onCategoryRequested = onCategoryRequested;
        this.onHomeRequested = onHomeRequested;

        this.categories = [];
        this.activeCategoryId = null;
        this.breadcrumbTrail = [];

        this.breadcrumbsEl.addEventListener('click', (event) => {
            const item = event.target.closest('[data-breadcrumb-index]');
            if (!item) return;

            const index = item.dataset.breadcrumbIndex;

            if (index === 'home') {
                this.onHomeRequested?.();
                return;
            }

            const numericIndex = Number.parseInt(index, 10);
            if (Number.isNaN(numericIndex)) return;

            const crumb = this.breadcrumbTrail[numericIndex];
            if (!crumb || crumb.id === this.activeCategoryId) {
                return;
            }

            this.onCategoryRequested?.(crumb.id, { fromBreadcrumb: true, index: numericIndex });
        });
    }

    setCategories(categories) {
        this.categories = categories ?? [];
        this.renderCategoryButtons();
        this.renderFloatingButtons();
    }

    renderCategoryButtons() {
        if (!this.sidebarList) return;
        this.sidebarList.innerHTML = '';

        const fragment = document.createDocumentFragment();
        this.categories.forEach((category) => {
            const button = document.createElement('button');
            button.className = 'category-button';
            button.type = 'button';
            button.dataset.categoryId = String(category.id);
            button.textContent = category.title;
            button.addEventListener('click', () => {
                if (this.activeCategoryId === category.id) {
                    return;
                }
                this.onCategoryRequested?.(category.id, { fromSidebar: true });
            });
            fragment.appendChild(button);
        });

        this.sidebarList.appendChild(fragment);
    }

    renderFloatingButtons() {
        if (!this.floatingList) return;
        this.floatingList.innerHTML = '';

        const fragment = document.createDocumentFragment();
        this.categories.forEach((category) => {
            const button = document.createElement('button');
            button.className = 'category-button';
            button.type = 'button';
            button.dataset.categoryId = String(category.id);
            button.textContent = category.title;
            button.addEventListener('click', () => {
                if (this.activeCategoryId === category.id) {
                    return;
                }
                this.onCategoryRequested?.(category.id, { fromFloating: true });
            });
            fragment.appendChild(button);
        });

        this.floatingList.appendChild(fragment);
    }

    setActiveCategory(categoryId) {
        this.activeCategoryId = categoryId;
        const activateButtons = (container) => {
            if (!container) return;
            [...container.querySelectorAll('.category-button')].forEach((button) => {
                const matches = Number.parseInt(button.dataset.categoryId ?? '0', 10) === categoryId;
                button.classList.toggle('active', matches);
            });
        };

        activateButtons(this.sidebarList);
        activateButtons(this.floatingList);
    }

    resetBreadcrumbs() {
        this.breadcrumbTrail = [];
        this.renderBreadcrumbs();
    }

    updateBreadcrumbTrail(category) {
        if (!category) return;

        const existingIndex = this.breadcrumbTrail.findIndex((crumb) => crumb.id === category.id);
        if (existingIndex >= 0) {
            this.breadcrumbTrail = this.breadcrumbTrail.slice(0, existingIndex + 1);
        } else {
            this.breadcrumbTrail.push({ id: category.id, title: category.title });
        }

        this.renderBreadcrumbs();
    }

    trimBreadcrumbTrail(upToIndex) {
        if (typeof upToIndex !== 'number' || Number.isNaN(upToIndex)) return;
        this.breadcrumbTrail = this.breadcrumbTrail.slice(0, upToIndex + 1);
        this.renderBreadcrumbs();
    }

    renderBreadcrumbs() {
        if (!this.breadcrumbsEl) return;

        this.breadcrumbsEl.innerHTML = '';
        const fragment = document.createDocumentFragment();

        const homeCrumb = document.createElement('button');
        homeCrumb.type = 'button';
        homeCrumb.className = 'breadcrumb-item'
            + (this.breadcrumbTrail.length === 0 ? ' current' : '');
        homeCrumb.dataset.breadcrumbIndex = 'home';
        homeCrumb.textContent = 'Категории';
        homeCrumb.setAttribute('aria-label', 'Вернуться к списку категорий');
        fragment.appendChild(homeCrumb);

        this.breadcrumbTrail.forEach((crumb, index) => {
            const separator = document.createElement('span');
            separator.className = 'breadcrumb-separator';
            separator.textContent = '›';
            fragment.appendChild(separator);

            const crumbButton = document.createElement('button');
            crumbButton.type = 'button';
            crumbButton.className = 'breadcrumb-item';
            if (index === this.breadcrumbTrail.length - 1) {
                crumbButton.classList.add('current');
                crumbButton.setAttribute('aria-current', 'page');
            }
            crumbButton.dataset.breadcrumbIndex = String(index);
            crumbButton.textContent = crumb.title;
            crumbButton.setAttribute('aria-label', `Перейти к категории ${crumb.title}`);
            fragment.appendChild(crumbButton);
        });

        this.breadcrumbsEl.appendChild(fragment);
    }
}

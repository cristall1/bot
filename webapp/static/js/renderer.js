import { ImageModal } from './modal.js';

export class ContentRenderer {
    constructor(container, options = {}) {
        this.container = container;
        this.modal = new ImageModal();
        this.onNavigationButtonClick = options.onNavigationButtonClick;
        this.webApp = window.Telegram?.WebApp;
    }

    clear() {
        this.container.innerHTML = '';
    }

    renderItems(items) {
        this.clear();

        if (!items || items.length === 0) {
            return;
        }

        const fragment = document.createDocumentFragment();
        items.forEach((item) => {
            const element = this.renderItem(item);
            if (element) {
                fragment.appendChild(element);
            }
        });

        this.container.appendChild(fragment);
    }

    renderItem(item) {
        const wrapper = document.createElement('div');
        wrapper.className = 'content-item';
        wrapper.dataset.itemId = String(item.id);
        wrapper.dataset.itemType = item.type;

        const typeHandlers = {
            TEXT: () => this.renderTextItem(item),
            IMAGE: () => this.renderImageItem(item),
            DOCUMENT: () => this.renderDocumentItem(item),
            VIDEO: () => this.renderVideoItem(item),
            LINK: () => this.renderLinkItem(item),
            BUTTON: () => this.renderButtonItem(item)
        };

        const handler = typeHandlers[item.type];
        if (!handler) {
            console.warn(`Unknown item type: ${item.type}`);
            return null;
        }

        const content = handler();
        if (content) {
            wrapper.appendChild(content);
        }

        return wrapper;
    }

    renderTextItem(item) {
        const div = document.createElement('div');
        div.className = 'text-item';

        const text = item.text_content ?? '';
        const processedText = this.processMarkdown(text);
        div.innerHTML = processedText;

        return div;
    }

    processMarkdown(text) {
        if (!text) return '';

        let html = text;
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');

        if (!html.startsWith('<p>')) {
            html = '<p>' + html + '</p>';
        }

        return html;
    }

    isHttpUrl(url) {
        return typeof url === 'string' && /^https?:\/\//i.test(url);
    }

    createUnavailableBlock(message) {
        const div = document.createElement('div');
        div.className = 'text-item';
        div.textContent = message;
        return div;
    }

    renderImageItem(item) {
        const container = document.createElement('div');
        container.className = 'image-item';

        const img = document.createElement('img');
        img.loading = 'lazy';
        img.src = item.file?.file_url ?? '';
        img.alt = item.file?.description ?? item.text_content ?? 'Изображение';

        if (item.file?.width && item.file?.height) {
            img.width = item.file.width;
            img.height = item.file.height;
        }

        img.addEventListener('click', () => {
            this.modal.open(img.src, img.alt);
        });

        container.appendChild(img);

        if (item.text_content) {
            const caption = document.createElement('div');
            caption.className = 'image-caption';
            caption.textContent = item.text_content;
            container.appendChild(caption);
        }

        return container;
    }

    renderDocumentItem(item) {
        const div = document.createElement('div');
        div.className = 'document-item';

        const icon = document.createElement('div');
        icon.className = 'document-icon';
        icon.textContent = this.getDocumentIcon(item.file?.mime_type);
        div.appendChild(icon);

        const info = document.createElement('div');
        info.className = 'document-info';

        const name = document.createElement('div');
        name.className = 'document-name';
        name.textContent = item.file?.original_name ?? item.text_content ?? 'Документ';
        info.appendChild(name);

        if (item.file?.file_size) {
            const meta = document.createElement('div');
            meta.className = 'document-meta';
            meta.textContent = this.formatFileSize(item.file.file_size);
            info.appendChild(meta);
        }

        div.appendChild(info);

        if (item.file?.file_url) {
            div.style.cursor = 'pointer';
            div.addEventListener('click', () => {
                this.openDocument(item.file.file_url, item.file.original_name);
            });
        }

        return div;
    }

    getDocumentIcon(mimeType) {
        if (!mimeType) return '📄';
        const type = mimeType.toLowerCase();

        if (type.includes('pdf')) return '📑';
        if (type.includes('word') || type.includes('document')) return '📝';
        if (type.includes('excel') || type.includes('spreadsheet')) return '📊';
        if (type.includes('powerpoint') || type.includes('presentation')) return '📊';
        if (type.includes('zip') || type.includes('archive')) return '📦';
        if (type.includes('text')) return '📄';

        return '📄';
    }

    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    openDocument(url, filename) {
        const a = document.createElement('a');
        a.href = url;
        a.download = filename ?? 'document';
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }

    renderVideoItem(item) {
        const container = document.createElement('div');
        container.className = 'video-item';

        if (item.file?.file_url) {
            const video = document.createElement('video');
            video.controls = true;
            video.preload = 'metadata';
            video.src = item.file.file_url;

            if (item.text_content) {
                video.title = item.text_content;
            }

            container.appendChild(video);
        } else {
            const placeholder = document.createElement('div');
            placeholder.className = 'video-placeholder';
            placeholder.innerHTML = `
                <div class="video-placeholder-content">
                    <div style="font-size: 48px; margin-bottom: 8px;">🎥</div>
                    <div>${item.text_content ?? 'Видео'}</div>
                </div>
            `;
            container.appendChild(placeholder);
        }

        return container;
    }

    renderLinkItem(item) {
        const linkUrl = item.rich_metadata?.url ?? item.text_content ?? '#';
        const linkText = item.button_text ?? item.text_content ?? linkUrl;

        const a = document.createElement('a');
        a.href = linkUrl;
        a.className = 'link-item';
        a.target = '_blank';
        a.rel = 'noopener noreferrer';

        a.addEventListener('click', (e) => {
            if (this.webApp?.openLink && linkUrl !== '#') {
                e.preventDefault();
                this.webApp.openLink(linkUrl);
            }
        });

        const textSpan = document.createElement('span');
        textSpan.className = 'link-text';
        textSpan.textContent = linkText;
        a.appendChild(textSpan);

        const arrow = document.createElement('span');
        arrow.className = 'link-arrow';
        arrow.textContent = '→';
        a.appendChild(arrow);

        return a;
    }

    renderButtonItem(item) {
        const button = document.createElement('button');
        button.className = 'button-item';
        button.type = 'button';
        button.textContent = item.button_text ?? item.text_content ?? 'Перейти';

        if (item.target_category_id) {
            button.dataset.targetCategoryId = String(item.target_category_id);
            button.addEventListener('click', () => {
                this.onNavigationButtonClick?.(item.target_category_id);
            });
        } else {
            button.disabled = true;
            button.style.opacity = '0.5';
        }

        return button;
    }
}

/**
 * Toast Notification System
 * Shows success/error messages using Telegram theme colors
 */

export class NotificationManager {
    constructor() {
        this.container = this.createContainer();
        this.notifications = new Map();
        this.nextId = 1;
    }

    createContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        container.setAttribute('aria-live', 'polite');
        container.setAttribute('aria-atomic', 'true');
        document.body.appendChild(container);
        return container;
    }

    show(message, type = 'info', duration = 3000) {
        const id = this.nextId++;
        const notification = this.createNotification(message, type);
        notification.dataset.id = id;

        this.container.appendChild(notification);
        this.notifications.set(id, notification);

        // Trigger animation
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });

        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => {
                this.dismiss(id);
            }, duration);
        }

        return id;
    }

    createNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.setAttribute('role', type === 'error' ? 'alert' : 'status');

        const icon = this.getIcon(type);
        const iconEl = document.createElement('span');
        iconEl.className = 'notification-icon';
        iconEl.textContent = icon;
        iconEl.setAttribute('aria-hidden', 'true');

        const messageEl = document.createElement('span');
        messageEl.className = 'notification-message';
        messageEl.textContent = message;

        const closeBtn = document.createElement('button');
        closeBtn.className = 'notification-close';
        closeBtn.textContent = '×';
        closeBtn.setAttribute('aria-label', 'Закрыть уведомление');
        closeBtn.addEventListener('click', () => {
            const id = parseInt(notification.dataset.id, 10);
            this.dismiss(id);
        });

        notification.appendChild(iconEl);
        notification.appendChild(messageEl);
        notification.appendChild(closeBtn);

        return notification;
    }

    getIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    dismiss(id) {
        const notification = this.notifications.get(id);
        if (!notification) return;

        notification.classList.remove('show');
        notification.classList.add('hide');

        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            this.notifications.delete(id);
        }, 300);
    }

    success(message, duration = 3000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 5000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 4000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 3000) {
        return this.show(message, 'info', duration);
    }

    clear() {
        this.notifications.forEach((notification, id) => {
            this.dismiss(id);
        });
    }
}

// Export singleton instance
export const notifications = new NotificationManager();

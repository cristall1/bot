export class ImageModal {
    constructor() {
        this.modal = document.getElementById('imageModal');
        this.image = document.getElementById('modalImage');
        this.closeButton = document.getElementById('modalCloseButton');

        this.closeButton.addEventListener('click', () => this.close());
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.classList.contains('active')) {
                this.close();
            }
        });
    }

    open(src, alt = '') {
        this.image.src = src;
        this.image.alt = alt;
        this.modal.classList.add('active');
        this.modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    }

    close() {
        this.modal.classList.remove('active');
        this.modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        setTimeout(() => {
            this.image.src = '';
            this.image.alt = '';
        }, 300);
    }
}

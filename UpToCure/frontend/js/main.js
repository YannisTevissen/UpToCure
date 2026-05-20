import { Carousel } from './carousel.js';
import { initLanguageSwitcher } from './i18n.js';
import { initInfoDialog, initRequestDialog } from './request.js';

function boot() {
    initLanguageSwitcher();
    if (document.getElementById('carousel')) {
        new Carousel();
    }
    initRequestDialog();
    initInfoDialog();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
} else {
    boot();
}

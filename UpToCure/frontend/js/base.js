import { initLanguageSwitcher } from './i18n.js';
import { initInfoDialog } from './request.js';

function boot() {
    initLanguageSwitcher();
    initInfoDialog();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
} else {
    boot();
}

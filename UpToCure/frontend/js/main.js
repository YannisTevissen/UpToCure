import { initLanguageSwitcher } from './i18n.js';
import { initInfoDialog, initRequestDialog } from './request.js';
import { initBrowseFilter, initSearchPickers } from './search-picker.js';

function boot() {
    initLanguageSwitcher();
    initSearchPickers();
    initBrowseFilter();
    initRequestDialog();
    initInfoDialog();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
} else {
    boot();
}

import { submitRequest } from './api.js';
import { getCurrentLanguage, t } from './i18n.js';

export function initRequestDialog() {
    const button = document.getElementById('requestReportBtn');
    const dialog = document.getElementById('requestDialog');
    const form = document.getElementById('diseaseRequestForm');
    const input = document.getElementById('diseaseName');
    const status = document.getElementById('requestStatus');
    const closers = dialog?.querySelectorAll('[data-close]');

    if (!button || !dialog || !form || !input || !status) return;

    const open = () => {
        status.textContent = '';
        status.className = 'request-status';
        input.value = '';
        if (typeof dialog.showModal === 'function') dialog.showModal();
        else dialog.setAttribute('open', '');
        input.focus();
    };

    button.addEventListener('click', open);

    // Also open the dialog on /#request landings
    if (window.location.hash === '#request') {
        open();
    }

    closers?.forEach((el) => el.addEventListener('click', () => dialog.close()));

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const disease = input.value.trim();
        if (!disease) return;
        status.textContent = '…';
        status.className = 'request-status';
        try {
            await submitRequest({ disease, language: getCurrentLanguage() });
            status.textContent = t('requestSuccess');
            status.classList.add('success');
            setTimeout(() => dialog.close(), 1500);
        } catch (err) {
            status.textContent = err.code === 429 ? t('requestRateLimited') : t('requestError');
            status.classList.add('error');
        }
    });
}

export function initInfoDialog() {
    const dialog = document.getElementById('infoDialog');
    if (!dialog) return;
    document.querySelectorAll('[data-open-dialog="infoDialog"]').forEach((btn) => {
        btn.addEventListener('click', () => {
            if (typeof dialog.showModal === 'function') dialog.showModal();
            else dialog.setAttribute('open', '');
        });
    });
}

// Minimal client-side i18n.
// Server-rendered pages already ship in the right language; this module only
// supplies a handful of UI strings that the JS needs (share menu, status
// messages, dialogs, …). The active language is read from <html lang="…">.

const STRINGS = {
    en: {
        loading: 'Loading…',
        noReports: 'No reports available yet in this language.',
        loadError: 'Failed to load reports. Please try again later.',
        requestSuccess: 'Thank you! Your request has been submitted.',
        requestError: 'There was an error submitting your request. Please try again.',
        requestRateLimited: 'Too many requests. Please try again later.',
        searchPlaceholder: 'Search reports…',
        share: 'Share', shareLinkedIn: 'LinkedIn', shareX: 'X',
        shareEmail: 'Email', shareCopy: 'Copy link',
        copied: 'Link copied to clipboard',
    },
    fr: {
        loading: 'Chargement…',
        noReports: 'Aucun rapport disponible dans cette langue pour le moment.',
        loadError: 'Échec du chargement des rapports. Veuillez réessayer plus tard.',
        requestSuccess: 'Merci ! Votre demande a été soumise.',
        requestError: 'Une erreur s\'est produite. Veuillez réessayer.',
        requestRateLimited: 'Trop de demandes. Veuillez réessayer plus tard.',
        searchPlaceholder: 'Rechercher un rapport…',
        share: 'Partager', shareLinkedIn: 'LinkedIn', shareX: 'X',
        shareEmail: 'Email', shareCopy: 'Copier le lien',
        copied: 'Lien copié dans le presse-papiers',
    },
};

export function getCurrentLanguage() {
    return document.documentElement.lang || 'en';
}

export function t(key) {
    const lang = getCurrentLanguage();
    return (STRINGS[lang] && STRINGS[lang][key]) || STRINGS.en[key] || key;
}

export function initLanguageSwitcher() {
    const select = document.querySelector('[data-language-switcher]');
    if (!select) return;
    select.addEventListener('change', (event) => {
        const target = event.target.value;
        const url = target === 'en'
            ? select.dataset.enUrl
            : select.dataset.frUrl;
        if (url) window.location.href = url;
    });
}

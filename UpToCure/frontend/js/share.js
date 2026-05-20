import { t } from './i18n.js';

const ICONS = {
    linkedin: '<svg viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>',
    x:        '<svg viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
    email:    '<svg viewBox="0 0 24 24"><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>',
    copy:     '<svg viewBox="0 0 24 24"><path d="M16 1H4a2 2 0 0 0-2 2v14h2V3h12V1zm3 4H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2zm0 16H8V7h11v14z"/></svg>',
};

function canonicalUrl(slug, lang) {
    return `${window.location.origin}/reports/${lang}/${encodeURIComponent(slug)}`;
}

export function createShareButton(report, lang) {
    const wrapper = document.createElement('div');
    wrapper.className = 'share-wrapper';

    const trigger = document.createElement('button');
    trigger.type = 'button';
    trigger.className = 'share-button';
    trigger.setAttribute('aria-label', t('share'));
    trigger.setAttribute('aria-expanded', 'false');
    trigger.innerHTML = ICONS.copy;

    const popup = document.createElement('div');
    popup.className = 'share-popup';
    popup.setAttribute('role', 'menu');

    const url = canonicalUrl(report.slug, lang);
    const title = report.title;
    const text = `Check out this UpToCure report: ${title}`;

    const items = [
        ['linkedin', t('shareLinkedIn'), () => window.open(
            `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`,
            '_blank', 'noopener,noreferrer')],
        ['x', t('shareX'), () => window.open(
            `https://x.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`,
            '_blank', 'noopener,noreferrer')],
        ['email', t('shareEmail'), () => window.open(
            `mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(`${text}\n\n${url}`)}`)],
        ['copy', t('shareCopy'), async () => {
            try {
                await navigator.clipboard.writeText(url);
                trigger.dataset.copied = '1';
                trigger.setAttribute('title', t('copied'));
                setTimeout(() => { delete trigger.dataset.copied; }, 1500);
            } catch { /* ignore */ }
        }],
    ];

    items.forEach(([key, label, action]) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `share-option share-option--${key}`;
        btn.setAttribute('role', 'menuitem');
        btn.innerHTML = `${ICONS[key]}<span>${label}</span>`;
        btn.addEventListener('click', (event) => {
            event.stopPropagation();
            action();
            close();
        });
        popup.appendChild(btn);
    });

    function close() {
        popup.classList.remove('show');
        trigger.setAttribute('aria-expanded', 'false');
    }

    trigger.addEventListener('click', (event) => {
        event.stopPropagation();
        const willShow = !popup.classList.contains('show');
        popup.classList.toggle('show', willShow);
        trigger.setAttribute('aria-expanded', String(willShow));
    });

    document.addEventListener('click', (event) => {
        if (!wrapper.contains(event.target)) close();
    });

    wrapper.append(trigger, popup);
    return wrapper;
}

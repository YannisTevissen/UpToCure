import { getReport, listReports } from './api.js';
import { getCurrentLanguage, t } from './i18n.js';
import { createShareButton } from './share.js';

export class Carousel {
    constructor() {
        this.root = document.getElementById('carousel');
        this.tileSelect = document.getElementById('tileSelect');
        this.prevBtn = document.getElementById('navPrev');
        this.nextBtn = document.getElementById('navNext');
        this.dropdown = null;
        this.reports = [];
        this.activeIndex = 0;
        this.tileCache = new Map();
        this.lang = getCurrentLanguage();

        this._setupNav();
        this._setupHash();
        this._setupDropdownTrigger();
        this._renderForLanguage(this.lang);
    }

    async _renderForLanguage(lang) {
        this.root.setAttribute('aria-busy', 'true');
        this.root.innerHTML = `<p class="status-message">${t('loading')}</p>`;
        this.tileCache.clear();
        try {
            this.reports = await listReports(lang);
        } catch (err) {
            console.error(err);
            this.root.innerHTML = `<p class="status-message status-message--error">${t('loadError')}</p>`;
            this.root.setAttribute('aria-busy', 'false');
            this._updateNav();
            return;
        }

        if (this.reports.length === 0) {
            this.root.innerHTML = `<p class="status-message">${t('noReports')}</p>`;
            this.root.setAttribute('aria-busy', 'false');
            this._updateNav();
            return;
        }

        this.root.innerHTML = '';
        this._rebuildDropdown();

        const initial = this._initialIndexFromHash();
        this.activeIndex = Math.max(0, Math.min(initial, this.reports.length - 1));
        await this._showActive();
        this.root.setAttribute('aria-busy', 'false');
        this._updateNav();
    }

    _initialIndexFromHash() {
        const hash = decodeURIComponent(window.location.hash.slice(1));
        if (!hash) return Math.floor(Math.random() * this.reports.length);
        const idx = this.reports.findIndex((r) => r.slug === hash);
        return idx >= 0 ? idx : Math.floor(Math.random() * this.reports.length);
    }

    async _showActive() {
        const report = this.reports[this.activeIndex];
        if (!report) return;
        window.history.replaceState(null, '', `#${report.slug}`);
        this._setSelectLabel(report.title);

        let tile = this.tileCache.get(report.slug);
        if (!tile) {
            tile = await this._buildTile(report);
            this.tileCache.set(report.slug, tile);
        }

        this.root.querySelectorAll('.tile').forEach((el) => el.remove());
        this.root.appendChild(tile);
    }

    async _buildTile(report) {
        const tile = document.createElement('article');
        tile.className = 'tile active';
        tile.dataset.slug = report.slug;

        const heading = document.createElement('h2');
        heading.className = 'tile-heading';
        const link = document.createElement('a');
        link.href = `/reports/${this.lang}/${encodeURIComponent(report.slug)}`;
        link.textContent = report.title;
        link.className = 'tile-title-link';
        heading.appendChild(link);
        tile.appendChild(heading);

        const body = document.createElement('div');
        body.className = 'tile-content';
        body.innerHTML = `<p class="loading-content">${t('loading')}</p>`;
        tile.appendChild(body);

        getReport(this.lang, report.slug)
            .then((detail) => {
                // Strip the duplicate H1 from the parsed HTML (we already render it above)
                const cleaned = (detail.content || '').replace(/^\s*<h1[^>]*>[\s\S]*?<\/h1>\s*/i, '');
                body.innerHTML = cleaned;
                const meta = document.createElement('small');
                meta.className = 'tile-meta';
                meta.innerHTML = `${detail.date} · <a href="/reports/${this.lang}/${encodeURIComponent(report.slug)}">${t('share')} →</a>`;
                tile.appendChild(meta);
            })
            .catch((err) => {
                console.error(err);
                body.innerHTML = `<p class="status-message status-message--error">${t('loadError')}</p>`;
            });

        tile.appendChild(createShareButton(report, this.lang));
        return tile;
    }

    _setupNav() {
        this.prevBtn?.addEventListener('click', () => this._move(-1));
        this.nextBtn?.addEventListener('click', () => this._move(1));

        let touchStartX = 0;
        this.root.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });
        this.root.addEventListener('touchend', (e) => {
            const delta = e.changedTouches[0].screenX - touchStartX;
            if (Math.abs(delta) > 50) this._move(delta > 0 ? -1 : 1);
        }, { passive: true });
    }

    _setupHash() {
        window.addEventListener('hashchange', () => {
            const hash = decodeURIComponent(window.location.hash.slice(1));
            if (!hash) return;
            const idx = this.reports.findIndex((r) => r.slug === hash);
            if (idx >= 0 && idx !== this.activeIndex) {
                this.activeIndex = idx;
                this._showActive();
                this._updateNav();
            }
        });
    }

    _move(delta) {
        if (this.reports.length <= 1) return;
        this.activeIndex = (this.activeIndex + delta + this.reports.length) % this.reports.length;
        this._showActive();
        this._updateNav();
    }

    _updateNav() {
        const empty = this.reports.length <= 1;
        if (this.prevBtn) this.prevBtn.disabled = empty;
        if (this.nextBtn) this.nextBtn.disabled = empty;
    }

    _setupDropdownTrigger() {
        if (!this.tileSelect) return;
        this.tileSelect.addEventListener('click', (e) => {
            e.stopPropagation();
            this._toggleDropdown();
        });
        document.addEventListener('click', (e) => {
            if (this.dropdown && !this.dropdown.contains(e.target) && !this.tileSelect.contains(e.target)) {
                this._toggleDropdown(false);
            }
        });
    }

    _rebuildDropdown() {
        this.dropdown?.remove();
        const dropdown = document.createElement('div');
        dropdown.className = 'custom-dropdown';
        dropdown.setAttribute('role', 'listbox');

        const search = document.createElement('input');
        search.type = 'search';
        search.className = 'report-search';
        search.placeholder = t('searchPlaceholder');
        search.setAttribute('aria-label', t('searchPlaceholder'));
        dropdown.appendChild(search);

        this.reports.forEach((report, index) => {
            const option = document.createElement('button');
            option.type = 'button';
            option.className = 'dropdown-option';
            option.setAttribute('role', 'option');
            option.textContent = report.title;
            option.addEventListener('click', () => {
                this.activeIndex = index;
                this._showActive();
                this._updateNav();
                this._toggleDropdown(false);
            });
            dropdown.appendChild(option);
        });

        search.addEventListener('input', (event) => {
            const term = event.target.value.toLowerCase();
            dropdown.querySelectorAll('.dropdown-option').forEach((option) => {
                option.style.display = option.textContent.toLowerCase().includes(term) ? '' : 'none';
            });
        });
        search.addEventListener('click', (event) => event.stopPropagation());

        this.tileSelect.parentNode.appendChild(dropdown);
        this.dropdown = dropdown;
    }

    _toggleDropdown(force) {
        if (!this.dropdown) return;
        const willShow = force !== undefined ? force : !this.dropdown.classList.contains('show');
        this.dropdown.classList.toggle('show', willShow);
        this.tileSelect.setAttribute('aria-expanded', String(willShow));
    }

    _setSelectLabel(text) {
        if (!this.tileSelect) return;
        this.tileSelect.innerHTML = `<span>${text}</span>`;
        this.tileSelect.classList.toggle('overflow', text.length > 25);
    }
}

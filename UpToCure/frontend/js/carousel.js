import { getReport, listReports } from './api.js';
import { getCurrentLanguage, t } from './i18n.js';
import { createShareButton } from './share.js';

export class Carousel {
    constructor() {
        this.root = document.getElementById('carousel');
        // The report picker is a combobox: the input filters the disease list
        // shown as a floating dropdown, but pressing Enter submits the form to
        // /search so users can search the full text of every report too.
        this.pickerForm = document.querySelector('.report-picker');
        this.pickerInput = document.getElementById('reportPicker');
        this.prevBtn = document.getElementById('navPrev');
        this.nextBtn = document.getElementById('navNext');
        this.dropdown = null;
        this.options = [];
        this.reports = [];
        this.activeIndex = 0;
        this.tileCache = new Map();
        this.lang = getCurrentLanguage();

        this._setupNav();
        this._setupHash();
        this._setupPicker();
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

    _setupPicker() {
        if (!this.pickerInput) return;
        this.pickerInput.addEventListener('focus', () => this._toggleDropdown(true));
        this.pickerInput.addEventListener('click', (e) => {
            e.stopPropagation();
            this._toggleDropdown(true);
        });
        this.pickerInput.addEventListener('input', () => this._filterDropdown(this.pickerInput.value));
        this.pickerInput.addEventListener('keydown', (e) => this._onPickerKey(e));

        document.addEventListener('click', (e) => {
            if (this.dropdown && !this.dropdown.contains(e.target) && !this.pickerForm.contains(e.target)) {
                this._toggleDropdown(false);
            }
        });
    }

    _rebuildDropdown() {
        this.dropdown?.remove();
        this.options = [];

        const dropdown = document.createElement('div');
        dropdown.className = 'report-picker-dropdown';
        dropdown.id = 'reportPickerList';
        dropdown.setAttribute('role', 'listbox');

        this.reports.forEach((report, index) => {
            const option = document.createElement('button');
            option.type = 'button';
            option.className = 'dropdown-option';
            option.setAttribute('role', 'option');
            option.dataset.title = report.title.toLowerCase();
            option.textContent = report.title;
            option.addEventListener('mousedown', (e) => {
                // Use mousedown so we fire before the input's blur closes the
                // dropdown (which would cancel the click).
                e.preventDefault();
                this._selectReport(index);
            });
            dropdown.appendChild(option);
            this.options.push(option);
        });

        this.pickerForm.appendChild(dropdown);
        this.dropdown = dropdown;
    }

    _selectReport(index) {
        this.activeIndex = index;
        this.pickerInput.value = '';
        this._filterDropdown('');
        this._toggleDropdown(false);
        this._showActive();
        this._updateNav();
    }

    _filterDropdown(term) {
        const needle = term.trim().toLowerCase();
        let visible = 0;
        this.options.forEach((option) => {
            const match = !needle || option.dataset.title.includes(needle);
            option.style.display = match ? '' : 'none';
            if (match) visible += 1;
        });
        if (visible === 0 && needle) {
            this._toggleDropdown(false);
        } else if (document.activeElement === this.pickerInput) {
            this._toggleDropdown(true);
        }
    }

    _onPickerKey(event) {
        if (event.key === 'Escape') {
            this._toggleDropdown(false);
            this.pickerInput.blur();
        } else if (event.key === 'Enter') {
            // If exactly one option remains, jump to it instead of submitting
            // the form to /search.
            const visible = this.options.filter((opt) => opt.style.display !== 'none');
            if (visible.length === 1) {
                event.preventDefault();
                const index = this.options.indexOf(visible[0]);
                this._selectReport(index);
            }
        }
    }

    _toggleDropdown(force) {
        if (!this.dropdown) return;
        const willShow = force !== undefined ? force : !this.dropdown.classList.contains('show');
        this.dropdown.classList.toggle('show', willShow);
        this.pickerInput?.setAttribute('aria-expanded', String(willShow));
    }
}

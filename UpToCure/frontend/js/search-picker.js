import { listReports } from './api.js';
import { getCurrentLanguage } from './i18n.js';

/**
 * Combobox for the home/search disease picker.
 * Typing filters titles; choosing one navigates to the report page.
 * Enter with multiple matches submits the form to /search.
 */
export class SearchPicker {
    constructor(form) {
        this.form = form;
        this.input = form.querySelector('[data-report-picker]');
        if (!this.input) return;

        this.lang = getCurrentLanguage();
        this.dropdown = null;
        this.options = [];
        this.reports = [];

        this._bind();
        this._load();
    }

    _bind() {
        this.input.addEventListener('focus', () => this._toggleDropdown(true));
        this.input.addEventListener('click', (e) => {
            e.stopPropagation();
            this._toggleDropdown(true);
        });
        this.input.addEventListener('input', () => this._filterDropdown(this.input.value));
        this.input.addEventListener('keydown', (e) => this._onKey(e));

        document.addEventListener('click', (e) => {
            if (
                this.dropdown
                && !this.dropdown.contains(e.target)
                && !this.form.contains(e.target)
            ) {
                this._toggleDropdown(false);
            }
        });
    }

    async _load() {
        try {
            this.reports = await listReports(this.lang);
            this._rebuildDropdown();
        } catch (err) {
            console.error(err);
        }
    }

    _rebuildDropdown() {
        this.dropdown?.remove();
        this.options = [];

        const dropdown = document.createElement('div');
        dropdown.className = 'report-picker-dropdown';
        dropdown.id = this.input.getAttribute('aria-controls') || 'reportPickerList';
        dropdown.setAttribute('role', 'listbox');

        this.reports.forEach((report) => {
            const option = document.createElement('button');
            option.type = 'button';
            option.className = 'dropdown-option';
            option.setAttribute('role', 'option');
            option.dataset.title = report.title.toLowerCase();
            option.dataset.slug = report.slug;
            option.textContent = report.title;
            option.addEventListener('mousedown', (e) => {
                e.preventDefault();
                this._goToReport(report.slug);
            });
            dropdown.appendChild(option);
            this.options.push(option);
        });

        this.form.appendChild(dropdown);
        this.dropdown = dropdown;
    }

    _goToReport(slug) {
        window.location.href = `/reports/${this.lang}/${encodeURIComponent(slug)}`;
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
        } else if (document.activeElement === this.input) {
            this._toggleDropdown(true);
        }
    }

    _onKey(event) {
        if (event.key === 'Escape') {
            this._toggleDropdown(false);
            this.input.blur();
            return;
        }
        if (event.key === 'Enter') {
            const visible = this.options.filter((opt) => opt.style.display !== 'none');
            if (visible.length === 1) {
                event.preventDefault();
                this._goToReport(visible[0].dataset.slug);
            }
        }
    }

    _toggleDropdown(force) {
        if (!this.dropdown) return;
        const willShow = force !== undefined ? force : !this.dropdown.classList.contains('show');
        this.dropdown.classList.toggle('show', willShow);
        this.input.setAttribute('aria-expanded', String(willShow));
    }
}

export function initSearchPickers() {
    document.querySelectorAll('[data-search-picker]').forEach((form) => {
        new SearchPicker(form);
    });
}

export function initBrowseFilter() {
    const input = document.getElementById('browseFilter');
    const list = document.getElementById('reportIndexList');
    if (!input || !list) return;

    const items = Array.from(list.querySelectorAll('[data-browse-item]'));
    const letters = Array.from(document.querySelectorAll('[data-letter-jump]'));

    const apply = () => {
        const needle = input.value.trim().toLowerCase();
        const visibleLetters = new Set();
        items.forEach((item) => {
            const title = (item.dataset.title || '').toLowerCase();
            const match = !needle || title.includes(needle);
            item.hidden = !match;
            if (match && item.dataset.letter) visibleLetters.add(item.dataset.letter);
        });
        letters.forEach((link) => {
            const letter = link.dataset.letterJump;
            link.classList.toggle('is-disabled', needle !== '' && !visibleLetters.has(letter));
        });
    };

    input.addEventListener('input', apply);
}

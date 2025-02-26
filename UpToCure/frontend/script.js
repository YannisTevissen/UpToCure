class Carousel {
    constructor() {
        this.container = document.querySelector('.carousel');
        this.carouselContainer = document.querySelector('.carousel-container');
        this.prevBtn = document.querySelector('.nav-arrow.prev');
        this.nextBtn = document.querySelector('.nav-arrow.next');
        this.tileSelect = document.getElementById('tileSelect');
        this.tiles = [];
        this.activeTileIndex = 0;
        this.isLoading = false;
        this.translatingIndicator = document.getElementById('translatingIndicator');
        this.outsideClickHandler = null;
        
        // Initialize
        this.setupEventListeners();
        this.setupLanguageSelector();
        
        // Set default language
        this.currentLanguage = document.documentElement.lang || 'en';
        console.log('Initial language set to:', this.currentLanguage);
        
        // Load reports for current language
        this.loadReportsForLanguage(this.currentLanguage);
        
        // Add event listener for language changes
        document.addEventListener('languageChanged', (event) => {
            const newLanguage = event.detail.language;
            console.log('Language changed event received:', newLanguage, 'current:', this.currentLanguage);
            if (this.currentLanguage !== newLanguage) {
                this.currentLanguage = newLanguage;
                console.log('Loading reports for new language:', newLanguage);
                this.loadReportsForLanguage(newLanguage);
            }
        });
        
        // Also listen for languageSelected events (directly from the selector)
        document.addEventListener('languageSelected', (event) => {
            const newLanguage = event.detail.language;
            console.log('Language selected event received:', newLanguage);
            if (this.currentLanguage !== newLanguage) {
                this.currentLanguage = newLanguage;
                console.log('Loading reports for selected language:', newLanguage);
                this.loadReportsForLanguage(newLanguage);
            }
        });
    }
    
    loadReportsForLanguage(language) {
        console.log(`Loading reports for language: ${language}`);
        
        // Clear current tiles
        this.tiles = [];
        this.activeTileIndex = 0;
        this.container.innerHTML = '';
        
        // Show loading state
        this.isLoading = true;
        this.updateNavigationState();
        this.showLoadingIndicator();
        
        // Fetch reports for the selected language
        this.fetchParsedReports(language);
    }

    setupLanguageSelector() {
        const languageSelect = document.getElementById('languageSelect');
        if (!languageSelect) {
            console.warn('Language selector not found');
            return;
        }
        
        console.log('Setting up language selector in Carousel');
        
        // Set initial value based on current language
        if (this.currentLanguage) {
            languageSelect.value = this.currentLanguage;
            console.log(`Set initial language selector value to: ${this.currentLanguage}`);
        }
        
        // We now handle this in the document-level event listener in the constructor
        // but we'll keep this as a backup
        languageSelect.addEventListener('change', (event) => {
            const selectedLanguage = event.target.value;
            console.log(`Language selector changed (direct handler): ${selectedLanguage}`);
            
            if (this.currentLanguage !== selectedLanguage) {
                this.currentLanguage = selectedLanguage;
                console.log(`Loading reports for language: ${selectedLanguage} (direct handler)`);
                this.loadReportsForLanguage(selectedLanguage);
            }
        });
    }

    updateActiveState() {
        this.tiles.forEach((tile, index) => {
            if (index === this.activeTileIndex) {
                tile.classList.add('active');
            } else {
                tile.classList.remove('active');
            }
        });
    }

    fetchParsedReports(language) {
        this.isLoading = true;
        
        // Use correct API endpoint with language parameter
        const apiUrl = `${window.location.origin}/api/reports?lang=${language}`;
        
        console.log(`Fetching reports for language: ${language}`);
        console.log(`API URL: ${apiUrl}`);
        console.log(`Current window location: ${window.location.href}`);
        
        fetch(apiUrl)
            .then(response => {
                console.log(`API response status for ${language}: ${response.status}`);
                
                if (!response.ok) {
                    throw new Error(`API error: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                this.hideLoadingIndicator();
                
                console.log(`API data received for ${language}:`, data);
                
                if (data.error) {
                    console.error(`API returned an error for ${language}:`, data.message);
                    throw new Error(data.message);
                }
                
                if (!data.reports || data.reports.length === 0) {
                    console.warn(`No reports found for language: ${language}`);
                    this.showNoReportsMessage(language);
                    return;
                }
                
                console.log(`Processing ${data.reports.length} reports for ${language}`);
                this.processReports(data.reports);
            })
            .catch(error => {
                this.hideLoadingIndicator();
                console.error(`Error fetching reports for ${language}:`, error);
                this.showErrorMessage(`Failed to load reports for ${language}. Please try again later.`);
            });
    }
    
    showNoReportsMessage(language) {
        this.hideLoadingIndicator();
        this.isLoading = false;
        
        const langDisplay = language === 'en' ? 'English' : 'Français';
        const messageElement = document.createElement('div');
        messageElement.className = 'tile message-tile';
        messageElement.innerHTML = `
            <h3>No Reports Available</h3>
            <p>There are currently no reports available in ${langDisplay}.</p>
            <p>Please check back later or try a different language.</p>
        `;
        
        this.container.appendChild(messageElement);
        this.updateNavigationState();
    }

    setupEventListeners() {
        if (this.prevBtn) {
            this.prevBtn.addEventListener('click', () => this.navigate('prev'));
        }
        
        if (this.nextBtn) {
            this.nextBtn.addEventListener('click', () => this.navigate('next'));
        }
        
        // Add touch swipe functionality
        this.setupSwipeNavigation();
    }

    setupSwipeNavigation() {
        // Variables to track touch position
        let touchStartX = 0;
        let touchEndX = 0;
        const minSwipeDistance = 50; // Minimum distance to register as a swipe
        
        console.log('Setting up swipe navigation for mobile devices');
        
        // Add event listeners to the carousel container
        if (this.carouselContainer) {
            this.carouselContainer.addEventListener('touchstart', (e) => {
                touchStartX = e.changedTouches[0].screenX;
            }, { passive: true });
            
            this.carouselContainer.addEventListener('touchend', (e) => {
                touchEndX = e.changedTouches[0].screenX;
                this.handleSwipe();
            }, { passive: true });
            
            // Function to determine swipe direction and navigate
            this.handleSwipe = () => {
                const swipeDistance = touchEndX - touchStartX;
                
                if (Math.abs(swipeDistance) > minSwipeDistance) {
                    if (swipeDistance > 0) {
                        // Swipe right - go to previous
                        console.log('Swipe right detected - navigating to previous');
                        this.navigate('prev');
                    } else {
                        // Swipe left - go to next
                        console.log('Swipe left detected - navigating to next');
                        this.navigate('next');
                    }
                }
            };
        }
    }

    navigate(direction) {
        if (this.tiles.length <= 1) return;
        
        if (direction === 'prev') {
            this.activeTileIndex = (this.activeTileIndex - 1 + this.tiles.length) % this.tiles.length;
        } else {
            this.activeTileIndex = (this.activeTileIndex + 1) % this.tiles.length;
        }
        this.updateActiveState();
        this.updateTileSelect();
    }

    processReports(reports) {
        console.log(`Processing ${reports.length} reports`);
        
        // Create tile elements
        this.tiles = [];
        reports.forEach((report, index) => {
            const tileElement = document.createElement('div');
            tileElement.className = 'tile';
            tileElement.dataset.index = index;
            tileElement.innerHTML = `
                <div class="tile-content">${report.content}</div>
                <small>${report.date} | ${report.filename}</small>
            `;
            this.container.appendChild(tileElement);
            this.tiles.push(tileElement);
            
            console.log(`Added tile for report: ${report.title}`);
        });
        
        console.log('Updating dropdown options with new language reports');
        // Update dropdown options
        this.updateTileSelectOptions(reports);
        
        // Set first tile as active
        this.activeTileIndex = 0;
        this.updateActiveState();
        
        if (reports.length > 0) {
            console.log(`Setting initial tile select title to: ${reports[0].title}`);
            this.updateTileSelect(reports[0].title);
        }
        
        // Not loading anymore
        this.isLoading = false;
        this.updateNavigationState();
        console.log('Reports processing complete, UI updated');
    }
    
    updateTileSelectOptions(reports) {
        if (!this.tileSelect) return;
        
        // Clear existing dropdown
        const existingDropdown = document.querySelector('.custom-dropdown');
        if (existingDropdown) {
            existingDropdown.remove();
        }
        
        // Create new dropdown
        const dropdown = document.createElement('div');
        dropdown.className = 'custom-dropdown';
        
        // Add options
        reports.forEach((report, index) => {
            const option = document.createElement('div');
            option.className = 'dropdown-option';
            option.dataset.value = index;
            
            // Check if title is long
            const isLong = report.title.length > 25;
            if (isLong) {
                option.classList.add('overflow');
                option.innerHTML = `<span>${report.title}</span>`;
            } else {
                option.textContent = report.title;
            }
            
            // Add click handler
            option.addEventListener('click', () => {
                this.activeTileIndex = index;
                this.updateActiveState();
                this.toggleDropdown();
                this.updateTileSelect(report.title);
            });
            
            dropdown.appendChild(option);
        });
        
        // Add dropdown to DOM
        this.tileSelect.parentNode.appendChild(dropdown);
        
        // Remove old click handlers by cloning and replacing the element
        const oldTileSelect = this.tileSelect;
        const newTileSelect = oldTileSelect.cloneNode(true);
        oldTileSelect.parentNode.replaceChild(newTileSelect, oldTileSelect);
        this.tileSelect = newTileSelect;
        
        // Add click handler to toggle dropdown
        this.tileSelect.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Tile select clicked, toggling dropdown');
            this.toggleDropdown();
        });
        
        // Close dropdown when clicking outside
        // First remove any existing document level click handlers for this purpose
        if (this.outsideClickHandler) {
            document.removeEventListener('click', this.outsideClickHandler);
        }
        
        // Create and store a reference to the new handler
        this.outsideClickHandler = (e) => {
            if (!this.tileSelect.parentNode.contains(e.target)) {
                this.closeDropdown();
            }
        };
        
        // Add the new handler
        document.addEventListener('click', this.outsideClickHandler);
    }
    
    updateTileSelect(title) {
        if (!this.tileSelect) return;
        
        if (title) {
            this.tileSelect.innerHTML = '';
            const span = document.createElement('span');
            span.textContent = title;
            this.tileSelect.appendChild(span);
            
            // Check if text is likely to overflow
            if (title.length > 25) {
                this.tileSelect.classList.add('overflow');
            } else {
                this.tileSelect.classList.remove('overflow');
            }
        } else if (this.tiles.length > 0 && this.activeTileIndex < this.tiles.length) {
            // Try to extract title from the active tile
            const activeTitle = this.tiles[this.activeTileIndex].querySelector('h2, h3');
            if (activeTitle) {
                this.updateTileSelect(activeTitle.textContent);
            }
        }
    }
    
    toggleDropdown() {
        // Find the dropdown - we need to query each time in case it was recreated
        const dropdown = document.querySelector('.custom-dropdown');
        console.log('Toggle dropdown called', dropdown ? 'dropdown found' : 'dropdown not found');
        
        if (dropdown) {
            // Toggle visibility classes
            dropdown.classList.toggle('show');
            this.tileSelect.classList.toggle('open');
            this.tileSelect.parentNode.classList.toggle('open');
            
            const isOpen = dropdown.classList.contains('show');
            console.log(`Dropdown ${isOpen ? 'opened' : 'closed'}`);
        }
    }
    
    closeDropdown() {
        // Find the dropdown - we need to query each time in case it was recreated
        const dropdown = document.querySelector('.custom-dropdown');
        
        if (dropdown) {
            dropdown.classList.remove('show');
            this.tileSelect.classList.remove('open');
            this.tileSelect.parentNode.classList.remove('open');
            console.log('Dropdown explicitly closed');
        }
    }

    updateNavigationState() {
        if (this.prevBtn && this.nextBtn) {
            this.prevBtn.disabled = this.tiles.length <= 1 || this.activeTileIndex === 0;
            this.nextBtn.disabled = this.tiles.length <= 1 || this.activeTileIndex === this.tiles.length - 1;
        }
    }

    showLoadingIndicator() {
        if (this.translatingIndicator) {
            this.translatingIndicator.style.display = 'block';
            this.translatingIndicator.textContent = 'Loading...';
        }
    }

    hideLoadingIndicator() {
        if (this.translatingIndicator) {
            this.translatingIndicator.style.display = 'none';
        }
    }

    showErrorMessage(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'tile error-tile';
        errorElement.textContent = message;
        
        this.container.appendChild(errorElement);
        this.updateNavigationState();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Log the DOMContentLoaded event
    console.log('DOM content loaded, initializing application');
    
    // Initialize the localization system
    if (typeof initializeLocalization === 'function') {
        console.log('Initializing localization system');
        initializeLocalization();
    } else {
        console.error('Localization system not available');
    }
    
    // Setup carousel if we're on the index page
    if (document.querySelector('.carousel-container')) {
        console.log('Found carousel container, initializing carousel');
        const carousel = new Carousel();
        console.log('Carousel initialized');
    } else {
        console.warn('No carousel container found on page');
    }
}); 
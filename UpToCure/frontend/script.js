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
        
        // Check if we're in LinkedIn or other in-app browsers
        const isInAppBrowser = detectInAppBrowser();
        
        // Add event listeners to the carousel container
        if (this.carouselContainer && !isInAppBrowser) {
            // Only add touch events for regular browsers
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
        } else if (this.carouselContainer && isInAppBrowser) {
            // For in-app browsers, provide alternate navigation without touch events
            console.log('In-app browser detected, using alternate navigation');
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
        this.container.innerHTML = ''; // Clear container first
        
        if (!reports || reports.length === 0) {
            console.warn('No reports to process');
            const noReportsElement = document.createElement('div');
            noReportsElement.className = 'tile active';
            noReportsElement.innerHTML = `
                <div class="tile-content">
                    <h2>No Reports Available</h2>
                    <p>There are currently no reports available in this language.</p>
                </div>
            `;
            this.container.appendChild(noReportsElement);
            this.tiles.push(noReportsElement);
            
            if (this.tileSelect) {
                this.tileSelect.innerHTML = '<span>No reports available</span>';
            }
            
            this.isLoading = false;
            this.updateNavigationState();
            return;
        }
        
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
        
        // Set a random tile as active instead of the first one
        const randomIndex = Math.floor(Math.random() * reports.length);
        this.activeTileIndex = randomIndex;
        this.updateActiveState();
        
        if (reports.length > 0) {
            const selectedReport = reports[randomIndex];
            console.log(`Setting initial tile select title to: ${selectedReport.title}`);
            this.updateTileSelect(selectedReport.title);
            
            // Add a small delay to ensure dropdown is ready before updating the selection
            setTimeout(() => {
                this.updateTileSelect(selectedReport.title);
            }, 100);
        }
        
        // Not loading anymore
        this.isLoading = false;
        this.updateNavigationState();
        console.log('Reports processing complete, UI updated');
    }
    
    updateTileSelectOptions(reports) {
        if (!this.tileSelect) {
            console.warn('Tile select element not found');
            return;
        }
        
        console.log('Updating tile select options with', reports.length, 'reports');
        
        // Clear existing dropdown
        const existingDropdown = document.querySelector('.custom-dropdown');
        if (existingDropdown) {
            existingDropdown.remove();
        }
        
        // Create new dropdown
        const dropdown = document.createElement('div');
        dropdown.className = 'custom-dropdown';
        
        // Sort reports alphabetically by title
        const sortedReports = [...reports].sort((a, b) => {
            return a.title.localeCompare(b.title);
        });
        
        // Add options
        sortedReports.forEach((report) => {
            const option = document.createElement('div');
            option.className = 'dropdown-option';
            // Find the original index of this report in the unsorted array
            const originalIndex = reports.findIndex(r => r.title === report.title);
            option.dataset.value = originalIndex;
            
            // Check if title is long
            const isLong = report.title.length > 25;
            if (isLong) {
                option.classList.add('overflow');
                option.innerHTML = `<span>${report.title}</span>`;
            } else {
                option.textContent = report.title;
            }
            
            // Add click handler
            option.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent event bubbling
                this.activeTileIndex = originalIndex;
                this.updateActiveState();
                this.toggleDropdown(false); // Close dropdown
                this.updateTileSelect(report.title);
            });
            
            dropdown.appendChild(option);
        });
        
        // Add dropdown to DOM
        this.tileSelect.parentNode.appendChild(dropdown);
        
        // IMPORTANT: Instead of cloning and replacing, just add a new click handler
        // This was causing issues with the dropdown functionality
        const tileSelectClickHandler = (e) => {
            e.preventDefault();
            e.stopPropagation(); // Stop event from bubbling up
            console.log('Tile select clicked, toggling dropdown');
            this.toggleDropdown();
        };
        
        // Remove existing click listeners first
        this.tileSelect.removeEventListener('click', this.tileSelectClickHandler);
        
        // Store the reference to the handler for future removal
        this.tileSelectClickHandler = tileSelectClickHandler;
        
        // Add new click handler
        this.tileSelect.addEventListener('click', this.tileSelectClickHandler);
        
        // Close dropdown when clicking outside
        // First remove any existing document level click handlers for this purpose
        if (this.outsideClickHandler) {
            document.removeEventListener('click', this.outsideClickHandler);
        }
        
        // Create and store a reference to the new handler
        this.outsideClickHandler = (e) => {
            // Only close if we click outside both the dropdown and the tile select
            if (!this.tileSelect.contains(e.target) && !dropdown.contains(e.target)) {
                this.toggleDropdown(false); // Force close
            }
        };
        
        // Add the new handler
        document.addEventListener('click', this.outsideClickHandler);
    }
    
    updateTileSelect(title) {
        if (!this.tileSelect) {
            console.warn('Tile select element not found for updateTileSelect');
            return;
        }
        
        console.log('Updating tile select with title:', title);
        
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
            } else {
                console.warn('Could not find title in active tile');
            }
        } else {
            console.warn('No tiles or active tile to extract title from');
        }
    }
    
    toggleDropdown(forceState) {
        // Find the dropdown - we need to query each time in case it was recreated
        const dropdown = document.querySelector('.custom-dropdown');
        console.log('Toggle dropdown called', dropdown ? 'dropdown found' : 'dropdown not found');
        
        if (dropdown) {
            // If forceState is provided, set that state instead of toggling
            if (forceState === false) {
                dropdown.classList.remove('show');
                this.tileSelect.classList.remove('open');
                this.tileSelect.parentNode.classList.remove('open');
                console.log('Dropdown explicitly closed');
                return;
            }
            
            if (forceState === true) {
                dropdown.classList.add('show');
                this.tileSelect.classList.add('open');
                this.tileSelect.parentNode.classList.add('open');
                console.log('Dropdown explicitly opened');
                return;
            }
            
            // Toggle visibility classes
            dropdown.classList.toggle('show');
            this.tileSelect.classList.toggle('open');
            this.tileSelect.parentNode.classList.toggle('open');
            
            const isOpen = dropdown.classList.contains('show');
            console.log(`Dropdown ${isOpen ? 'opened' : 'closed'}`);
        }
    }
    
    closeDropdown() {
        this.toggleDropdown(false);
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
    if (typeof initializeLanguage === 'function') {
        console.log('Initializing localization system');
        initializeLanguage();
    } else if (typeof initializeLocalization === 'function') {
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
    
    // Setup footer visibility on scroll
    setupFooterScroll();
    
    // Initialize request handler
    if (document.getElementById('requestReportBtn')) {
        const requestHandler = new DiseaseRequestHandler();
        console.log('Disease request handler initialized');
    }
}); 

function setupFooterScroll() {
    // Show footer after page content has loaded
    const footer = document.querySelector('footer');
    if (!footer) return;
    
    footer.classList.add('visible');
    
    // Always keep footer visible - don't rely on scroll events
    // This avoids issues with LinkedIn and other in-app browsers
    
    // Check if we're in LinkedIn browser or other problematic browsers
    const isInAppBrowser = detectInAppBrowser();
    
    if (!isInAppBrowser) {
        // Only add scroll listener for normal browsers
        window.addEventListener('scroll', handleScroll, { passive: true });
    }
    
    function handleScroll() {
        // If we're at the bottom of the page
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 10) {
            footer.classList.add('visible');
        } else {
            footer.classList.add('visible'); // Always keep footer visible now
        }
    }
}

// Helper function to detect LinkedIn and other in-app browsers
function detectInAppBrowser() {
    const userAgent = navigator.userAgent || navigator.vendor || window.opera;
    
    // Check for LinkedIn browser
    if (userAgent.indexOf('LinkedIn') !== -1) {
        console.log('LinkedIn browser detected, disabling scroll events');
        return true;
    }
    
    // Check for Facebook browser
    if (userAgent.indexOf('FBAN') !== -1 || userAgent.indexOf('FBAV') !== -1) {
        console.log('Facebook browser detected, disabling scroll events');
        return true;
    }
    
    // Check for Instagram browser
    if (userAgent.indexOf('Instagram') !== -1) {
        console.log('Instagram browser detected, disabling scroll events');
        return true;
    }
    
    return false;
}

// Class to handle disease report requests
class DiseaseRequestHandler {
    constructor() {
        this.requestBtn = document.getElementById('requestReportBtn');
        this.popup = document.getElementById('requestPopup');
        this.closeBtn = document.querySelector('.close-popup');
        this.form = document.getElementById('diseaseRequestForm');
        this.statusDiv = document.getElementById('requestStatus');
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Open popup when button is clicked
        this.requestBtn.addEventListener('click', () => this.openPopup());
        
        // Close popup when close button is clicked
        this.closeBtn.addEventListener('click', () => this.closePopup());
        
        // Close popup when clicking outside
        window.addEventListener('click', (event) => {
            if (event.target === this.popup) {
                this.closePopup();
            }
        });
        
        // Handle form submission
        this.form.addEventListener('submit', (event) => {
            event.preventDefault();
            this.handleSubmit();
        });
    }
    
    openPopup() {
        this.popup.style.display = 'flex';
        this.resetForm();
    }
    
    closePopup() {
        this.popup.style.display = 'none';
    }
    
    resetForm() {
        this.form.reset();
        this.statusDiv.textContent = '';
        this.statusDiv.className = 'request-status';
    }
    
    handleSubmit() {
        const diseaseName = document.getElementById('diseaseName').value.trim();
        
        if (!diseaseName) {
            this.showStatus('error', i18n.getTranslation('requestError'));
            return;
        }
        
        // Save the request
        this.saveRequest(diseaseName);
    }
    
    saveRequest(diseaseName) {
        // Create a request object with timestamp and language
        const requestData = {
            disease: diseaseName,
            timestamp: new Date().toISOString(),
            language: i18n.getCurrentLanguage()
        };
        
        // Send the data to the server
        fetch('/api/request-report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Show success message
            this.showStatus('success', i18n.getTranslation('requestSuccess'));
            
            // Close popup after delay
            setTimeout(() => {
                this.closePopup();
            }, 2000);
        })
        .catch(error => {
            console.error('Error:', error);
            
            // If server is not available, save locally
            this.saveLocally(requestData);
        });
    }
    
    saveLocally(requestData) {
        try {
            // Get existing requests from localStorage
            let requests = JSON.parse(localStorage.getItem('diseaseRequests') || '[]');
            
            // Add new request
            requests.push(requestData);
            
            // Save back to localStorage
            localStorage.setItem('diseaseRequests', JSON.stringify(requests));
            
            // Show success message
            this.showStatus('success', i18n.getTranslation('requestSuccess'));
            
            // Close popup after delay
            setTimeout(() => {
                this.closePopup();
            }, 2000);
            
        } catch (error) {
            console.error('Error saving locally:', error);
            this.showStatus('error', i18n.getTranslation('requestError'));
        }
    }
    
    showStatus(type, message) {
        this.statusDiv.textContent = message;
        this.statusDiv.className = `request-status ${type}`;
    }
} 
class Carousel {
    constructor() {
        this.container = document.querySelector('.carousel');
        this.tileSelectContainer = document.querySelector('.tile-select-container');
        this.tileSelect = document.querySelector('#tileSelect');
        this.tiles = [];
        this.currentIndex = 0;
        this.init();
        
        // Log that carousel is being initialized
        console.log('UpToCure Carousel initialized, setting up auto-refresh...');
        
        // Setup auto-refresh to check for new reports (every 30 seconds)
        this.autoRefreshInterval = setInterval(() => this.fetchParsedReports(), 30000);
    }

    async init() {
        try {
            console.log('Initializing carousel...');
            await this.fetchParsedReports();
            this.setupCarousel();
            this.setupCustomDropdown();
            this.setupNavigation();
            console.log('Carousel initialized successfully with', this.tiles.length, 'tiles');
        } catch (error) {
            console.error('Failed to initialize carousel:', error);
            // Add a default error tile
            this.tiles = [{
                title: "Error Initializing",
                content: `<p>Failed to initialize content. Please reload the page.</p><p>Error: ${error.message}</p>`,
                date: new Date(),
                filename: "error.md"
            }];
            this.renderTiles();
        }
    }

    async fetchParsedReports() {
        try {
            console.log('Fetching parsed reports from backend...');
            
            // Fetch all parsed reports from the Python backend endpoint
            const apiUrl = window.location.origin + '/api/reports';
            console.log('API URL:', apiUrl);
            
            const response = await fetch(apiUrl);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API error response:', errorText);
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Raw API response:', data);
            
            // Check if response contains an error
            if (data.error) {
                throw new Error(data.message || 'Unknown error from server');
            }
            
            // Check if we have any reports
            if (!data.reports || data.reports.length === 0) {
                console.warn('Server returned no reports');
                throw new Error('No reports available');
            }
            
            console.log(`Received ${data.reports.length} parsed reports from server`);
            
            // Log the filenames of reports we received
            console.log('Report filenames:', data.reports.map(r => r.filename).join(', '));
            
            // Process the reports
            const processedReports = data.reports.map(report => ({
                title: report.title,
                content: report.content,
                date: new Date(report.date), // Convert date string to Date object
                filename: report.filename
            }));
            
            // Update the tiles and render
            this.tiles = processedReports;
            this.renderTiles();
            
            return data.reports;
        } catch (error) {
            console.error('Error fetching parsed reports:', error);
            
            // If this is the first load (no tiles yet), show an error tile
            if (this.tiles.length === 0) {
                this.tiles = [{
                    title: "Error Loading Reports",
                    content: `<p>Could not load reports from the server.</p>
                              <p>Error: ${error.message}</p>
                              <p>Please check that the backend server is running at ${window.location.origin}/api/reports</p>`,
                    date: new Date(),
                    filename: "error.md"
                }];
                this.renderTiles();
            }
            
            // Try fallback for development/testing environments
            console.log('Trying fallback reports for development...');
            await this.tryFallbackReportsForDevelopment();
        }
    }
    
    async tryFallbackReportsForDevelopment() {
        // Only use fallback if we're in a development environment without backend
        try {
            console.log('Attempting to use fallback for development environment...');
            
            // Try to fetch the fallback JSON file
            const fallbackResponse = await fetch('./reports-fallback.json');
            
            if (!fallbackResponse.ok) {
                console.log('No fallback available');
                return false;
            }
            
            const fallbackData = await fallbackResponse.json();
            console.log('Using fallback reports data', fallbackData);
            
            // Process the reports
            if (fallbackData.reports && fallbackData.reports.length > 0) {
                console.log(`Found ${fallbackData.reports.length} reports in fallback file`);
                
                this.tiles = fallbackData.reports.map(report => ({
                    title: report.title,
                    content: report.content,
                    date: new Date(report.date),
                    filename: report.filename
                }));
                this.renderTiles();
                return true;
            } else {
                console.warn('Fallback file contains no reports');
            }
        } catch (error) {
            console.warn('Fallback also failed:', error);
        }
        return false;
    }

    renderTiles() {
        // Clear existing content
        this.container.innerHTML = '';
        
        // Prepare for custom dropdown
        this.tileSelect.innerHTML = '<span>Choose a report...</span>';
        
        // Create custom dropdown container
        let customDropdown = document.querySelector('.custom-dropdown');
        if (!customDropdown) {
            customDropdown = document.createElement('div');
            customDropdown.className = 'custom-dropdown';
            this.tileSelectContainer.appendChild(customDropdown);
        } else {
            customDropdown.innerHTML = '';
        }
        
        console.log(`Rendering ${this.tiles.length} tiles...`);
        
        this.tiles.forEach((tile, index) => {
            // Create tile element
            const tileElement = document.createElement('div');
            tileElement.className = 'tile';
            tileElement.innerHTML = `
                <div class="tile-content">${tile.content}</div>
                <small>${tile.date.toLocaleDateString()} | ${tile.filename}</small>
            `;
            this.container.appendChild(tileElement);

            // Create dropdown option
            this.addDropdownOption(customDropdown, tile.title, index);
            
            // Log each tile we've rendered
            console.log(`Rendered tile ${index + 1}/${this.tiles.length}: ${tile.title} (${tile.filename})`);
        });
        
        // Reset to first tile if current index is out of bounds
        if (this.currentIndex >= this.tiles.length) {
            this.currentIndex = 0;
        }
        
        this.updateActiveState();
    }

    // Helper function to add options to custom dropdown
    addDropdownOption(dropdownElement, text, value) {
        const option = document.createElement('div');
        option.className = 'dropdown-option';
        option.dataset.value = value;
        
        // Check if text is likely to overflow
        const isLong = text.length > 25;
        if (isLong) {
            option.classList.add('overflow');
            option.innerHTML = `<span>${text}</span>`;
        } else {
            option.textContent = text;
        }
        
        option.addEventListener('click', () => {
            this.currentIndex = parseInt(value);
            this.updateActiveState();
            this.closeDropdown();
            
            // Update the select display text
            const selectedText = this.tiles[this.currentIndex].title;
            this.tileSelect.innerHTML = `<span>${selectedText}</span>`;
            
            // Check if selected text is likely to overflow
            if (selectedText.length > 25) {
                this.tileSelect.classList.add('overflow');
            } else {
                this.tileSelect.classList.remove('overflow');
            }
        });
        
        dropdownElement.appendChild(option);
    }

    setupCustomDropdown() {
        // Toggle dropdown on click
        this.tileSelect.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleDropdown();
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.tileSelectContainer.contains(e.target)) {
                this.closeDropdown();
            }
        });
        
        // Set initial selected text
        if (this.tiles.length > 0) {
            const selectedText = this.tiles[this.currentIndex].title;
            this.tileSelect.innerHTML = `<span>${selectedText}</span>`;
            
            // Check if selected text is likely to overflow
            if (selectedText.length > 25) {
                this.tileSelect.classList.add('overflow');
            }
        }
    }
    
    toggleDropdown() {
        this.tileSelectContainer.classList.toggle('open');
    }
    
    closeDropdown() {
        this.tileSelectContainer.classList.remove('open');
    }

    setupCarousel() {
        this.updateActiveState();
    }

    setupNavigation() {
        const prevButton = document.querySelector('.nav-arrow.prev');
        const nextButton = document.querySelector('.nav-arrow.next');

        prevButton.addEventListener('click', () => this.navigate('prev'));
        nextButton.addEventListener('click', () => this.navigate('next'));
        
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
        this.container.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });
        
        this.container.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe();
        }, { passive: true });
        
        // Add swipe for entire container for better mobile experience
        document.querySelector('.carousel-container').addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });
        
        document.querySelector('.carousel-container').addEventListener('touchend', (e) => {
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

    navigate(direction) {
        if (direction === 'prev') {
            this.currentIndex = (this.currentIndex - 1 + this.tiles.length) % this.tiles.length;
        } else {
            this.currentIndex = (this.currentIndex + 1) % this.tiles.length;
        }
        this.updateActiveState();
    }

    updateActiveState() {
        const tiles = document.querySelectorAll('.tile');
        tiles.forEach((tile, index) => {
            tile.classList.toggle('active', index === this.currentIndex);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('Document loaded, initializing UpToCure carousel...');
    new Carousel();
}); 
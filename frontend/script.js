class Carousel {
    constructor() {
        this.container = document.querySelector('.carousel');
        this.tileSelect = document.querySelector('#tileSelect');
        this.tiles = [];
        this.currentIndex = 0;
        this.markdownParser = new MarkdownParser();
        this.reportFiles = [];
        this.init();
        
        // Setup auto-refresh to check for new files more frequently (every 5 seconds)
        this.autoRefreshInterval = setInterval(() => this.checkForNewReports(), 5000);
    }

    async init() {
        await this.fetchReportList();
        await this.fetchReports();
        this.setupCarousel();
        this.setupNavigation();
        this.setupDropdown();
    }

    async fetchReportList() {
        try {
            // Fetch directory listing from PHP endpoint
            console.log('Attempting to fetch report list...');
            const response = await fetch('./list-reports.php');
            if (response.ok) {
                const files = await response.json();
                console.log('Reports found:', files);
                this.reportFiles = files.filter(file => file.endsWith('.md'));
                return;
            } else {
                console.warn('PHP endpoint returned non-OK status:', response.status);
            }
        } catch (error) {
            console.warn('Could not fetch report list dynamically:', error);
        }
        
        // Fallback to manual file list if dynamic listing fails
        console.info('Using fallback file list');
        this.reportFiles = [
            'gauchers-disease.md',
            'huntingtons-disease.md',
            'pompe-disease.md',
            'fabry-disease.md',
            'Advancements in Treating Spinal Muscular Atrophy T.md' // Add the new file to the fallback list
        ];
        console.log('Using fallback file list:', this.reportFiles);
    }

    async checkForNewReports() {
        const previousFiles = [...this.reportFiles];
        await this.fetchReportList();
        
        // If the file list has changed, reload reports
        if (JSON.stringify(previousFiles) !== JSON.stringify(this.reportFiles)) {
            console.info('Detected changes in reports folder, refreshing content. Files:', this.reportFiles);
            await this.fetchReports();
        }
    }

    async fetchReports() {
        try {
            // Fetch and process each report
            const reportPromises = this.reportFiles.map(async (file) => {
                try {
                    console.log(`Attempting to fetch ${file}...`);
                    const response = await fetch(`./reports/${file}`);
                    if (!response.ok) {
                        console.error(`Failed to load report: ${file}, status: ${response.status}`);
                        return null;
                    }
                    
                    const markdown = await response.text();
                    console.log(`Successfully loaded ${file}, content length: ${markdown.length}`);
                    
                    return {
                        ...this.markdownParser.extractMetadata(markdown),
                        filename: file
                    };
                } catch (fileError) {
                    console.error(`Error processing file ${file}:`, fileError);
                    return null;
                }
            });
            
            const results = await Promise.all(reportPromises);
            const reports = results.filter(report => report !== null);
            
            if (reports.length === 0) {
                throw new Error('No reports could be loaded successfully');
            }
            
            console.log('Successfully loaded reports:', reports.map(r => r.filename));
            this.tiles = reports;
            this.renderTiles();
        } catch (error) {
            console.error('Error fetching reports:', error);
            // Add a default tile in case of error
            this.tiles = [
                {
                    title: "Unable to fetch reports",
                    content: `<p>Please check your connection or report files.</p><p>Error: ${error.message}</p>`,
                    date: new Date(),
                    filename: "error.md"
                }
            ];
            this.renderTiles();
        }
    }

    renderTiles() {
        // Clear existing content
        this.container.innerHTML = '';
        this.tileSelect.innerHTML = '<option value="" disabled selected>Jump to a tile...</option>';
        
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
            const option = document.createElement('option');
            option.value = index;
            option.textContent = tile.title;
            this.tileSelect.appendChild(option);
            
            console.log(`Rendered tile: ${tile.title}`);
        });
        
        // Reset to first tile if current index is out of bounds
        if (this.currentIndex >= this.tiles.length) {
            this.currentIndex = 0;
        }
        
        this.updateActiveState();
    }

    setupCarousel() {
        this.updateActiveState();
    }

    setupNavigation() {
        const prevButton = document.querySelector('.nav-arrow.prev');
        const nextButton = document.querySelector('.nav-arrow.next');

        prevButton.addEventListener('click', () => this.navigate('prev'));
        nextButton.addEventListener('click', () => this.navigate('next'));
    }

    setupDropdown() {
        this.tileSelect.addEventListener('change', (e) => {
            const selectedIndex = parseInt(e.target.value);
            if (!isNaN(selectedIndex)) {
                this.currentIndex = selectedIndex;
                this.updateActiveState();
            }
        });
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
        // Update dropdown to reflect current tile
        this.tileSelect.value = this.currentIndex;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new Carousel();
}); 
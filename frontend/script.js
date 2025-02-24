class Carousel {
    constructor() {
        this.container = document.querySelector('.carousel');
        this.tiles = [];
        this.currentIndex = 0;
        this.init();
    }

    async init() {
        await this.fetchTiles();
        this.setupCarousel();
        this.setupNavigation();
    }

    async fetchTiles() {
        try {
            const response = await fetch('http://localhost:8000/api/tiles');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const tiles = await response.json();
            this.tiles = tiles;
            this.renderTiles();
        } catch (error) {
            console.error('Error fetching tiles:', error);
            // Add some default tiles in case of error
            this.tiles = [
                {
                    title: "Unable to fetch data",
                    content: "Please check your connection",
                    tile_date: new Date().toISOString()
                }
            ];
            this.renderTiles();
        }
    }

    renderTiles() {
        this.tiles.forEach(tile => {
            const tileElement = document.createElement('div');
            tileElement.className = 'tile';
            tileElement.innerHTML = `
                <h2>${tile.title}</h2>
                <p>${tile.content}</p>
                <small>${new Date(tile.tile_date).toLocaleDateString()}</small>
            `;
            this.container.appendChild(tileElement);
        });
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
    new Carousel();
}); 
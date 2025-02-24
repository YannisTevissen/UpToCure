/**
 * Simple Markdown Parser
 * Converts basic markdown syntax to HTML
 */
class MarkdownParser {
    constructor() {
        // Regular expressions for markdown conversion
        this.rules = [
            // Headers
            { regex: /^# (.*$)/gm, replacement: '<h2>$1</h2>' },
            { regex: /^## (.*$)/gm, replacement: '<h3>$1</h3>' },
            { regex: /^### (.*$)/gm, replacement: '<h4>$1</h4>' },
            
            // Bold text
            { regex: /\*\*(.*?)\*\*/g, replacement: '<strong>$1</strong>' },
            
            // Italic text
            { regex: /\*(.*?)\*/g, replacement: '<em>$1</em>' },
            
            // Lists
            { regex: /^\s*[-*+]\s+(.*$)/gm, replacement: '<li>$1</li>' },
            
            // Horizontal rules
            { regex: /^---+$/gm, replacement: '<hr>' },
            
            // Wrap lists in ul tags
            { 
                regex: /(<li>.*<\/li>)/gs, 
                replacement: (match) => `<ul>${match}</ul>` 
            },
            
            // Paragraphs - apply last to avoid conflicts
            { 
                regex: /^(?!<[a-z]).+$/gm, 
                replacement: (match) => {
                    // Skip if already wrapped in a tag or empty
                    if (match.trim() === '') return match;
                    if (/<\/?[a-z][\s\S]*>/i.test(match)) return match;
                    return `<p>${match}</p>`;
                }
            }
        ];
    }

    /**
     * Parse markdown text to HTML
     * @param {string} markdown - The markdown text to parse
     * @returns {string} - The resulting HTML
     */
    parse(markdown) {
        try {
            console.log('Parsing markdown, length:', markdown.length);
            let html = markdown;
            
            // Apply each rule
            this.rules.forEach(rule => {
                html = html.replace(rule.regex, rule.replacement);
            });
            
            return html;
        } catch (error) {
            console.error('Error parsing markdown:', error);
            return `<p>Error parsing content: ${error.message}</p>`;
        }
    }

    /**
     * Extract title, content, and date from markdown
     * @param {string} markdown - The markdown text to parse
     * @returns {Object} - Object with title, content, and date
     */
    extractMetadata(markdown) {
        try {
            console.log('Extracting metadata from markdown');
            const lines = markdown.split('\n');
            let title = '';
            let date = '';
            let content = '';

            // Find title (first h1)
            const titleMatch = markdown.match(/^# (.*$)/m);
            if (titleMatch) {
                title = titleMatch[1].trim();
                console.log('Found title:', title);
            } else {
                title = "Untitled Document";
                console.warn('No title found, using default');
            }

            // Find date (try multiple date patterns)
            const datePatterns = [
                /\*(?:.*?updated|date):\s*(.*?)\*/i,                    // *Last updated: March 10, 2025*
                /(?:Updated|Date):\s*([A-Za-z0-9, ]+)/i,                // Updated: March 10, 2025
                /([A-Za-z]+ \d{1,2},? \d{4})/,                          // March 10, 2025
                /(\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4})/                     // 10-03-2025 or 10/03/2025
            ];
            
            for (const pattern of datePatterns) {
                const dateMatch = markdown.match(pattern);
                if (dateMatch) {
                    date = dateMatch[1].trim();
                    console.log('Found date:', date);
                    break;
                }
            }
            
            // Default date if none found
            if (!date) {
                date = new Date().toLocaleDateString();
                console.warn('No date found, using current date');
            }

            // Content is everything
            content = this.parse(markdown);

            return {
                title,
                content,
                date: new Date(date || 'now')
            };
        } catch (error) {
            console.error('Error extracting metadata:', error);
            return {
                title: "Error Processing Document",
                content: `<p>Error processing content: ${error.message}</p>`,
                date: new Date()
            };
        }
    }
}

// Make available globally
window.MarkdownParser = MarkdownParser; 
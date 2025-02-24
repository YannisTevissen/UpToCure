/**
 * Fallback API for environments without server-side support
 * This simulates a directory listing endpoint
 */
(function() {
    // Handle requests to list-reports.php route by intercepting fetch
    const originalFetch = window.fetch;
    
    window.fetch = function(url, options) {
        // Check if this is a request for our report listing
        if (url === './list-reports.php') {
            console.log('Using JavaScript fallback for report listing');
            
            // Simulate successful response with default files
            return Promise.resolve({
                ok: true,
                json: () => Promise.resolve([

                ])
            });
        }
        
        // Check if this is a request for a specific report
        if (url.startsWith('./reports/') && url.endsWith('.md')) {
            const filename = url.split('/').pop();
            console.log(`Fallback intercepted request for file: ${filename}`);
            
        }
        
        // Otherwise, call the original fetch
        return originalFetch.apply(this, arguments);
    };
})(); 
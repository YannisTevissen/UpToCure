// Tiny HTTP client over the UpToCure backend.

const memoryCache = new Map();

async function jsonOrThrow(response) {
    if (!response.ok) {
        const message = `HTTP ${response.status}`;
        throw new Error(message);
    }
    return response.json();
}

export async function listReports(language) {
    const key = `list:${language}`;
    if (memoryCache.has(key)) return memoryCache.get(key);
    const data = await fetch(`/api/reports?lang=${encodeURIComponent(language)}`).then(jsonOrThrow);
    if (data.error) throw new Error(data.message);
    memoryCache.set(key, data.reports || []);
    return data.reports || [];
}

export async function getReport(language, slug) {
    const key = `report:${language}:${slug}`;
    if (memoryCache.has(key)) return memoryCache.get(key);
    const data = await fetch(`/api/reports/${encodeURIComponent(language)}/${encodeURIComponent(slug)}`).then(jsonOrThrow);
    if (data.error) throw new Error(data.message);
    memoryCache.set(key, data.report);
    return data.report;
}

export async function submitRequest({ disease, language }) {
    const response = await fetch('/api/request-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            disease,
            language,
            timestamp: new Date().toISOString(),
        }),
    });
    if (response.status === 429) {
        const err = new Error('rate-limited');
        err.code = 429;
        throw err;
    }
    return jsonOrThrow(response);
}

export function clearCache() {
    memoryCache.clear();
}

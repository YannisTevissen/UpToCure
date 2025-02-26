// Localization strings for UpToCure
const translations = {
    // English translations
    "en": {
        // Common
        "copyright": "Copyright © Yannis Tevissen 2025",
        
        // Index page
        "pageTitle": "UpToCure.ai",
        "disclaimer": "UpToCure provides up-to-date reports on ongoing research efforts to cure rare disease. All the reports are generated with an AI agent that can sometimes hallucinate. For precise information please refer to the resources provided in the reports.",
        "methodologyLink": "Our methodology is detailed here",
        "chooseReport": "Choose a report...",
        "backToReports": "← Back to Reports",
        
        // Methodology page
        "methodologyTitle": "UpToCure - Methodology",
        "methodologyHeading": "Our Methodology",
        "researchSectionTitle": "AI-Assisted Research Report Generation",
        "researchSectionContent": "UpToCure's reports on rare disease research are generated using advanced language models fine-tuned for medical content. Our process involves:",
        "dataCollection": "Data Collection",
        "dataCollectionDesc": "Systematic review of peer-reviewed publications, clinical trial databases, and authoritative medical resources.",
        "contentGeneration": "Content Generation",
        "contentGenerationDesc": "AI-powered synthesis of research findings with specialized prompting to ensure medical accuracy.",
        "expertValidation": "Expert Validation",
        "expertValidationDesc": "Review process to check for hallucinations and factual errors, though this process is not exhaustive.",
        "citationIntegration": "Citation Integration",
        "citationIntegrationDesc": "All reports include references to original research sources.",
        "agentArchTitle": "Deep Research Agent Architecture",
        "agentArchContent": "At the core of our methodology is a specialized AI research system built on the SmolAgents framework, which autonomously gathers and analyzes the latest scientific information on rare diseases. The system employs:",
        "limitationsTitle": "Limitations and Disclaimers",
        "limitationsContent": "While our AI system produces valuable research summaries, users should be aware of important limitations:",
        "conclusionTitle": "Conclusion",
        "conclusionContent": "While we strive for accuracy, users should be aware that our AI-generated content may contain inaccuracies or outdated information. Always consult healthcare professionals for medical decisions and refer to the original research sources cited in our reports for comprehensive information about rare disease treatments and research developments."
    },
    
    // French translations
    "fr": {
        // Common
        "copyright": "Copyright © Yannis Tevissen 2025",
        
        // Index page
        "pageTitle": "UpToCure.ai",
        "disclaimer": "UpToCure fournit des rapports actualisés sur les efforts de recherche en cours pour guérir les maladies rares. Tous les rapports sont générés avec un agent IA qui peut parfois halluciner. Pour des informations précises, veuillez consulter les ressources fournies dans les rapports.",
        "methodologyLink": "Notre méthodologie est détaillée ici",
        "chooseReport": "Choisir un rapport...",
        "backToReports": "← Retour aux rapports",
        
        // Methodology page
        "methodologyTitle": "UpToCure - Méthodologie",
        "methodologyHeading": "Notre Méthodologie",
        "researchSectionTitle": "Génération de rapports de recherche assistée par IA",
        "researchSectionContent": "Les rapports d'UpToCure sur la recherche sur les maladies rares sont générés à l'aide de modèles de langage avancés affinés pour le contenu médical. Notre processus comprend :",
        "dataCollection": "Collecte de données",
        "dataCollectionDesc": "Examen systématique des publications évaluées par des pairs, des bases de données d'essais cliniques et des ressources médicales faisant autorité.",
        "contentGeneration": "Génération de contenu",
        "contentGenerationDesc": "Synthèse des résultats de recherche alimentée par l'IA avec des invites spécialisées pour garantir la précision médicale.",
        "expertValidation": "Validation par des experts",
        "expertValidationDesc": "Processus de révision pour vérifier les hallucinations et les erreurs factuelles, bien que ce processus ne soit pas exhaustif.",
        "citationIntegration": "Intégration des citations",
        "citationIntegrationDesc": "Tous les rapports incluent des références aux sources de recherche originales.",
        "agentArchTitle": "Architecture de l'agent de recherche approfondie",
        "agentArchContent": "Au cœur de notre méthodologie se trouve un système de recherche IA spécialisé construit sur le framework SmolAgents, qui recueille et analyse de manière autonome les dernières informations scientifiques sur les maladies rares. Le système utilise :",
        "limitationsTitle": "Limitations et avertissements",
        "limitationsContent": "Bien que notre système d'IA produise de précieux résumés de recherche, les utilisateurs doivent être conscients des limitations importantes :",
        "conclusionTitle": "Conclusion",
        "conclusionContent": "Bien que nous nous efforcions d'être précis, les utilisateurs doivent savoir que notre contenu généré par l'IA peut contenir des inexactitudes ou des informations obsolètes. Consultez toujours des professionnels de la santé pour les décisions médicales et référez-vous aux sources de recherche originales citées dans nos rapports pour des informations complètes sur les traitements des maladies rares et les développements de la recherche."
    }
};

// Default language
let currentLanguage = 'en';

// Function to get translation string
function getTranslation(key) {
    if (!translations[currentLanguage]) {
        console.warn(`Language ${currentLanguage} not found, falling back to English`);
        return translations['en'][key] || key;
    }
    
    return translations[currentLanguage][key] || translations['en'][key] || key;
}

// Function to update all text elements with translations
function updatePageTranslations() {
    const elements = document.querySelectorAll('[data-i18n]');
    elements.forEach(element => {
        const key = element.getAttribute('data-i18n');
        if (key) {
            // If element is a link or has child elements, only update text nodes
            if (element.tagName === 'A' || element.children.length > 0) {
                // Update only the text content, preserving child elements
                const translation = getTranslation(key);
                // Only update if we have a valid translation
                if (translation && translation !== key) {
                    element.textContent = translation;
                }
            } else {
                // For simple elements, update the full text content
                element.textContent = getTranslation(key);
            }
        }
    });
    
    // Update page title if needed
    if (document.title === "UpToCure.ai" || document.title.startsWith("UpToCure -")) {
        if (window.location.pathname.includes("methodology")) {
            document.title = getTranslation("methodologyTitle");
        } else {
            document.title = getTranslation("pageTitle");
        }
    }
    
    // Update any attributes that need translation
    const attrElements = document.querySelectorAll('[data-i18n-attr]');
    attrElements.forEach(element => {
        const attrData = element.getAttribute('data-i18n-attr').split(':');
        if (attrData.length === 2) {
            const attr = attrData[0];
            const key = attrData[1];
            element.setAttribute(attr, getTranslation(key));
        }
    });
}

// Function to set the current language
function setLanguage(lang) {
    console.log(`Attempting to set language to: ${lang}`);
    if (translations[lang]) {
        currentLanguage = lang;
        document.documentElement.lang = lang;
        updatePageTranslations();
        
        // Save language preference
        localStorage.setItem('uptocure-language', lang);
        
        // Dispatch event for other scripts
        console.log(`Dispatching languageChanged event for: ${lang}`);
        const event = new CustomEvent('languageChanged', { detail: { language: lang } });
        document.dispatchEvent(event);
        
        return true;
    }
    console.warn(`Language ${lang} not supported`);
    return false;
}

// Initialize language from storage or browser preference
function initializeLanguage() {
    const savedLanguage = localStorage.getItem('uptocure-language');
    const browserLanguage = navigator.language.split('-')[0];
    
    if (savedLanguage && translations[savedLanguage]) {
        setLanguage(savedLanguage);
    } else if (browserLanguage && translations[browserLanguage]) {
        setLanguage(browserLanguage);
    } else {
        setLanguage('en'); // Default to English
    }
    
    // Set language selector to current language
    const languageSelect = document.getElementById('languageSelect');
    if (languageSelect) {
        languageSelect.value = currentLanguage;
    }
}

// Setup language change listener
document.addEventListener('DOMContentLoaded', function() {
    const languageSelect = document.getElementById('languageSelect');
    if (languageSelect) {
        console.log('Setting up language selector event listener');
        languageSelect.addEventListener('change', function(event) {
            const selectedLanguage = event.target.value;
            console.log(`Language selector changed to: ${selectedLanguage}`);
            
            // Set the language
            setLanguage(selectedLanguage);
            
            // Also dispatch the direct languageSelected event for components that listen for it
            console.log(`Dispatching direct languageSelected event for: ${selectedLanguage}`);
            document.dispatchEvent(new CustomEvent('languageSelected', {
                detail: { language: selectedLanguage }
            }));
        });
    } else {
        console.warn('Language selector not found in the document');
    }
    
    // Initialize on page load
    initializeLanguage();
});

// Expose necessary functions globally
window.i18n = {
    getTranslation,
    setLanguage,
    getCurrentLanguage: () => currentLanguage
}; 
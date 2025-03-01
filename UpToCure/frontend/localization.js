// Localization strings for UpToCure
const translations = {
    // English translations
    "en": {
        // Common
        "copyright": "Copyright © Yannis Tevissen 2025",
        
        // Index page
        "pageTitle": "UpToCure.ai",
        "disclaimer": "UpToCure provides up-to-date reports on ongoing research efforts to cure rare diseases. All the reports are generated with an AI agent that can sometimes hallucinate. For precise information please refer to the resources provided in the reports.",
        "methodologyLink": "Our methodology is detailed here",
        "chooseReport": "Choose a report...",
        "backToReports": "← Back to Reports",
        
        // Methodology page
        "methodologyTitle": "UpToCure - Methodology",
        "methodologyHeading": "Our Methodology",
        "goalTitle": "Goal",
        "goalContent": "Our mission is to make research more accessible by simplifying access to scientific information and demonstrating that AI can bridge the gap between complex topics and a wider audience. By leveraging advanced AI technologies, we aim to break down barriers to knowledge and ensure that scientific discoveries are easily understandable and available to everyone.",
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
        "agentArchTitle": "Agentic AI for Reports Generation",
        "agentArchContent": "To streamline the process of gathering and synthesizing research data, we utilize an agentic AI approach. The methodology consists of the following steps:",
        "llmPrompting": "A large language model (OpenAI o1) is prompted to retrieve comprehensive information on research efforts aimed at curing rare diseases.",
        "searchCapabilities": "The AI agent has access to Google Search and can parse through the results to extract relevant insights.",
        "systemImplementation": "The system was primarily developed through AI-driven prompting, with 90% of the implementation built by an AI agent (Cursor) utilizing Claude-3.7 Sonnet for high-level reasoning.",
        "openSourceTitle": "Open-Source",
        "openSourceContent": "In alignment with our goal of making science and progress more accessible, this project is entirely open source. The source code and methodology can be found here: ",
        "repoUptocure": "UpToCure GitHub Repository.",
        "openSourceAcknowledgment": "This initiative was built thanks to numerous open-source projects, with a special emphasis on the Open Deep Research framework: ",
        "hfBlog": "Hugging Face Blog",
        "contributionInvitation": "We welcome contributions from the community to improve and expand the project. ",
        "contactInfo": "For inquiries, contact me on: ",
        "limitationsTitle": "Limitations and Disclaimers",
        "limitationsContent": "While our AI system produces valuable research summaries, users should be aware of important limitations:",
        "limitationHallucination": "Risk of hallucinations: Large language models used to generate reports may occasionally produce inaccurate or fabricated information. Always verify crucial details with the cited sources.",
        "limitationRecentNews": "Recent research gaps: The system may miss very recent scientific developments that haven't yet been referenced widely on the web at the time of report generation.",
        "limitationTranslation": "Translation accuracy: Reports are initially generated in English and then translated to other languages, which may introduce nuance or accuracy issues in the translated versions.",
        "conclusionTitle": "Conclusion",
        "conclusionContent": "While we strive for accuracy, users should be aware that our AI-generated content may contain inaccuracies or outdated information. Always consult healthcare professionals for medical decisions and refer to the original research sources cited in our reports for comprehensive information about rare disease treatments and research developments."
    },
    
    // French translations
    "fr": {
        // Common
        "copyright": "Copyright © Yannis Tevissen 2025",
        
        // Index page
        "pageTitle": "UpToCure.ai",
        "disclaimer": "UpToCure fournit des rapports actualisés sur les efforts de recherche en cours pour guérir les maladies rares. Tous les rapports sont générés avec un agent IA qui peut parfois halluciner. Pour des informations précises, veuillez consulter les ressources référencées dans les rapports.",
        "methodologyLink": "Notre méthodologie est détaillée ici",
        "chooseReport": "Choisir un rapport...",
        "backToReports": "← Retour aux rapports",
        
        // Methodology page
        "methodologyTitle": "UpToCure - Méthodologie",
        "methodologyHeading": "Notre Méthodologie",
        "goalTitle": "Objectif",
        "goalContent": "Notre objectif est de rendre la recherche plus accessible en simplifiant l'accès à l'information scientifique et en démontrant que l'IA peut combler le fossé entre des sujets complexes et un public plus large. En utilisant des technologies d'IA avancées, nous visons à éliminer les barrières à la connaissance et à garantir que les découvertes scientifiques soient facilement compréhensibles et accessibles à tous.",
        "researchSectionTitle": "Génération de rapports assistée par IA",
        "researchSectionContent": "Les rapports d'UpToCure sur la recherche sur les maladies rares sont générés à l'aide de larges modèles de langage. Notre processus comprend :",
        "dataCollection": "Collecte de données",
        "dataCollectionDesc": "Examen systématique des publications évaluées par des pairs, des bases de données d'essais cliniques et des ressources médicales faisant autorité.",
        "contentGeneration": "Génération de contenu",
        "contentGenerationDesc": "Synthèse des résultats de recherche alimentée par l'IA avec des invites spécialisées pour garantir la précision médicale.",
        "expertValidation": "Validation par des experts",
        "expertValidationDesc": "Processus de révision pour vérifier les hallucinations et les erreurs factuelles, bien que ce processus ne soit pas exhaustif.",
        "citationIntegration": "Intégration des citations",
        "citationIntegrationDesc": "Tous les rapports incluent des références aux sources de recherche originales.",
        "agentArchTitle": "IA Agentique pour la Génération de Rapports",
        "agentArchContent": "Pour simplifier le processus de collecte et de synthèse des données de recherche, nous utilisons une approche d'IA agentique. La méthodologie comprend les étapes suivantes :",
        "llmPrompting": "Un grand modèle de langage (OpenAI o1) est prompté à récupérer des informations complètes sur les efforts de recherche visant à guérir les maladies rares.",
        "searchCapabilities": "L'agent IA a accès à Google Search et peut analyser les résultats pour extraire des informations pertinentes.",
        "systemImplementation": "Le site a lui-même été principalement développé grâce à un agent, avec 90% de l'implémentation construite via Cursor en utilisant Claude-3.7 Sonnet.",
        "openSourceTitle": "Open-Source",
        "openSourceContent": "Conformément à notre objectif de rendre la science et le progrès plus accessibles, ce projet est entièrement open source. Le code source et la méthodologie peuvent être trouvés ici :",
        "repoUptocure": "Dépôt GitHub UpToCure.",
        "openSourceAcknowledgment": "Cette initiative a été construite grâce à de nombreux projets open-source, avec un accent particulier sur le framework Open Deep Research, qui fournit la base pour l'exploration de recherche assistée par IA: ",
        "hfBlog": "Blog d'Hugging Face",
        "contributionInvitation": "Nous accueillons les contributions de la communauté pour améliorer et étendre le projet. ",
        "contactInfo": "Pour toute autre demande, contactez-moi via :",
        "limitationsTitle": "Limitations et avertissements",
        "limitationsContent": "Bien que notre système d'IA produise de précieux résumés de recherche, les utilisateurs doivent être conscients des limitations importantes :",
        "limitationHallucination": "Risque d'hallucinations : Les grands modèles de langage utilisés pour générer les rapports peuvent occasionnellement produire des informations inexactes ou fabriquées. Vérifiez toujours les détails cruciaux avec les sources citées.",
        "limitationRecentNews": "Lacunes dans la recherche récente : Le système peut manquer des développements scientifiques très récents qui n'ont pas encore été largement référencés sur le web au moment de la génération du rapport.",
        "limitationTranslation": "Précision de la traduction : Les rapports sont initialement générés en anglais puis traduits vers d'autres langues, ce qui peut introduire des problèmes de nuance ou de précision dans les versions traduites.",
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
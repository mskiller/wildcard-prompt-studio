export type Language = 'en' | 'fr';

export const translationsEn = {
  // Navigation & Settings Header
  settings: "Settings",
  appearanceLanguage: "Appearance & Language",
  aiPromptImprovement: "AI & Prompt Improvement",
  apiConnections: "API Connections",
  modelProfiles: "Model Profiles",

  // General & Theme
  theme: "Theme",
  darkMode: "Dark Mode",
  lightMode: "Light Mode",
  language: "Language",
  english: "English 🇬🇧",
  french: "Français 🇫🇷",
  generalDesc: "Customize the visual appearance, theme, and language of Prompt Studio.",

  // AI & Prompt Improvement
  defaultKreaVariant: "Default Krea 2 Variant",
  turboDesc: "Turbo (Fast 2K Natural Language)",
  mediumDesc: "Medium (Artistic & Illustration)",
  largeDesc: "Large (High Fidelity & Optics)",
  defaultAIProvider: "Default AI LLM Provider",
  autoCleanBuzzwords: "Auto-clean SD Buzzwords (8k, masterpiece, etc.)",
  autoQuoteTargets: "Auto-wrap target text in double quotes",
  enableThinkingTokenBoost: "Enable Thinking Model Token Boost",
  thinkingTokenHelp: "Allows local models (Gemma 4, DeepSeek R1) in thinking mode to output complete thought logs and final prompts without cutoff.",
  maxOutputTokens: "Max Output Tokens",
  promptRulesDesc: "Configure global rules and default models used for prompt improvement.",

  // API Connections
  comfyuiUrl: "ComfyUI URL",
  comfyuiHelp: "Local or remote URL for your ComfyUI instance.",
  ollamaUrl: "Ollama API URL",
  ollamaHelp: "URL for local Ollama server (e.g. http://localhost:11434).",
  koboldUrl: "KoboldCpp API URL",
  koboldHelp: "URL for local KoboldCpp server (e.g. http://localhost:5001).",
  geminiKey: "Google Gemini API Key",
  geminiHelp: "API key for Google Gemini Cloud Provider.",
  testConnection: "Test Connection",
  testing: "Testing...",
  connected: "Connected Successfully!",
  connectionFailed: "Connection Failed",

  // Common
  save: "Save Settings",
  saved: "Settings Saved!",
};

export type TranslationKeys = keyof typeof translationsEn;

export const translations: Record<Language, Record<TranslationKeys, string>> = {
  en: translationsEn,
  fr: {
    // Navigation & Settings Header
    settings: "Paramètres",
    appearanceLanguage: "Apparence et Langue",
    aiPromptImprovement: "IA et Amélioration de Prompt",
    apiConnections: "Connexions API",
    modelProfiles: "Profils de Modèles",

    // General & Theme
    theme: "Thème",
    darkMode: "Mode Sombre",
    lightMode: "Mode Clair",
    language: "Langue",
    english: "English 🇬🇧",
    french: "Français 🇫🇷",
    generalDesc: "Personnalisez l'apparence visuelle, le thème et la langue de Prompt Studio.",

    // AI & Prompt Improvement
    defaultKreaVariant: "Variante Krea 2 par défaut",
    turboDesc: "Turbo (Langage naturel rapide 2K)",
    mediumDesc: "Medium (Artistique & Illustration)",
    largeDesc: "Large (Haute fidélité & Optique)",
    defaultAIProvider: "Fournisseur LLM par défaut",
    autoCleanBuzzwords: "Nettoyage auto des mots-clés SD (8k, masterpiece, etc.)",
    autoQuoteTargets: "Guillemets automatiques pour les textes cibles",
    enableThinkingTokenBoost: "Activer le Boost de Tokens pour Modèles de Pensée",
    thinkingTokenHelp: "Permet aux modèles locaux (Gemma 4, DeepSeek R1) en mode pensée de générer le journal de pensée complet et le prompt final sans coupure.",
    maxOutputTokens: "Tokens de sortie max",
    promptRulesDesc: "Configurez les règles globales et modèles par défaut pour l'amélioration de prompts.",

    // API Connections
    comfyuiUrl: "URL ComfyUI",
    comfyuiHelp: "URL locale ou distante de votre instance ComfyUI.",
    ollamaUrl: "URL API Ollama",
    ollamaHelp: "URL du serveur Ollama local (ex: http://localhost:11434).",
    koboldUrl: "URL API KoboldCpp",
    koboldHelp: "URL du serveur KoboldCpp local (ex: http://localhost:5001).",
    geminiKey: "Clé API Google Gemini",
    geminiHelp: "Clé API pour le fournisseur Cloud Google Gemini.",
    testConnection: "Tester la connexion",
    testing: "Test en cours...",
    connected: "Connexion réussie !",
    connectionFailed: "Échec de la connexion",

    // Common
    save: "Enregistrer les paramètres",
    saved: "Paramètres enregistrés !",
  }
};

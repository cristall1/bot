const FALLBACK_THEME = {
    bg_color: '#ffffff',
    text_color: '#000000',
    hint_color: '#999999',
    link_color: '#2481cc',
    button_color: '#2481cc',
    button_text_color: '#ffffff',
    secondary_bg_color: '#f4f4f5',
    header_bg_color: '#ffffff',
    accent_text_color: '#2481cc',
    section_bg_color: '#ffffff',
    section_header_text_color: '#6d6d72',
    subtitle_text_color: '#999999',
    destructive_text_color: '#ff3b30'
};

const THEME_VAR_MAP = {
    bg_color: '--tg-theme-bg-color',
    text_color: '--tg-theme-text-color',
    hint_color: '--tg-theme-hint-color',
    link_color: '--tg-theme-link-color',
    button_color: '--tg-theme-button-color',
    button_text_color: '--tg-theme-button-text-color',
    secondary_bg_color: '--tg-theme-secondary-bg-color',
    header_bg_color: '--tg-theme-header-bg-color',
    accent_text_color: '--tg-theme-accent-text-color',
    section_bg_color: '--tg-theme-section-bg-color',
    section_header_text_color: '--tg-theme-section-header-text-color',
    subtitle_text_color: '--tg-theme-subtitle-text-color',
    destructive_text_color: '--tg-theme-destructive-text-color'
};

function setCSSVariables(params) {
    const root = document.documentElement;
    const theme = { ...FALLBACK_THEME, ...params };

    Object.entries(THEME_VAR_MAP).forEach(([telegramKey, cssVar]) => {
        const value = theme[telegramKey];
        if (!value) return;
        root.style.setProperty(cssVar, value);
    });
}

function setColorScheme(scheme) {
    if (!scheme) return;
    const normalized = scheme.toLowerCase();
    document.body.dataset.colorScheme = normalized;
    document.documentElement.style.setProperty('color-scheme', normalized);
}

export function initializeTheme() {
    const webApp = window.Telegram?.WebApp;
    const themeParams = webApp?.themeParams ?? {};
    setCSSVariables(themeParams);
    setColorScheme(webApp?.colorScheme ?? 'light');

    if (webApp?.onEvent) {
        webApp.onEvent('themeChanged', () => {
            setCSSVariables(webApp.themeParams ?? {});
            setColorScheme(webApp.colorScheme ?? 'light');
        });
    }
}

export function getThemeParams() {
    const webApp = window.Telegram?.WebApp;
    return {
        colorScheme: webApp?.colorScheme ?? 'light',
        themeParams: webApp?.themeParams ?? { ...FALLBACK_THEME }
    };
}

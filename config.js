// Configuration for deployment
// Change BACKEND_URL based on where your backend is deployed

window.CONFIG = {
    // OPTIONS:
    // 1. Render (RECOMMENDED): 'https://capm-gordon-valuation-model.onrender.com'
    // 2. PythonAnywhere: 'https://yourusername.pythonanywhere.com'
    // 3. Glitch: 'https://your-project.glitch.me'
    // 4. Replit: 'https://your-app.your-username.repl.co'
    // 5. Leave empty '' for same-origin deployment (Render serves both frontend+backend)

    // For Vercel frontend + Render backend deployment:
    // BACKEND_URL: 'https://capm-gordon-valuation-model.onrender.com'

    // For Render-only deployment (both frontend and backend on same URL):
    // BACKEND_URL: ''

    // Current setting: PythonAnywhere (same-origin)
    // NOTE: For local development, the hostname check in index.html overrides this
    BACKEND_URL: ''
};

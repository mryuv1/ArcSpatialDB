const express = require('express');
const cors = require('cors');
const path = require('path');
const projectsRouter = require('./api/projects');
const areasRouter = require('./api/areas');
const filesRouter = require('./api/files');

const app = express();

// Middleware
app.use(cors({ origin: '*' }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// API Routes
app.use('/api', projectsRouter);
app.use('/api', areasRouter);
app.use('/', filesRouter);

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        message: 'Backend API is running' 
    });
});

// Error handlers
app.use((req, res, next) => {
    res.status(404).json({ error: 'Endpoint not found' });
});

app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ error: 'Internal server error' });
});

// Start server
const PORT = process.env.PORT || 5000;
const HOST = process.env.HOST || '0.0.0.0';

app.listen(PORT, HOST, () => {
    console.log(`Server running on http://${HOST}:${PORT}`);
});

module.exports = app;

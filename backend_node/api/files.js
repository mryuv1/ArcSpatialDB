const express = require('express');
const path = require('path');
const fs = require('fs');

const router = express.Router();

const PROJECT_ROOT = path.join(__dirname, '..', '..');

router.get('/view_file/*', (req, res) => {
    try {
        // Get the relative path from the URL
        const relPath = req.params[0];
        const absPath = path.resolve(path.join(PROJECT_ROOT, relPath));
        
        // Security: Only allow files inside project directory
        if (!absPath.startsWith(PROJECT_ROOT)) {
            return res.status(403).json({ error: 'Access denied' });
        }
        
        if (!fs.existsSync(absPath)) {
            return res.status(404).json({ error: 'File not found' });
        }
        
        // Send the file
        res.sendFile(absPath);
        
    } catch (error) {
        console.error('Error serving file:', error);
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;

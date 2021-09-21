const express = require('express');
const path = require('path');
const fs = require('fs');
const router = express.Router();
const archive = path.resolve(__dirname, '../../archive');

/**
 * Get record by filename
 */
router.get('/:filename', async (req, res) => {
    // Make sure we don't have any relative path
    const filename = path.basename(req.params.filename + ".mp4");
    const recordPath = path.join(archive, filename);

    res.sendFile(recordPath);
});

/**
 * Get all records
 */
router.get('/', async (req, res) => {
    const records = fs.readdirSync(archive).filter(f => f.split('.').pop() == 'mp4').map(f => f.replace(/\.[^/.]+$/, ""));

    res.json(records);
});

module.exports = {
    router
};

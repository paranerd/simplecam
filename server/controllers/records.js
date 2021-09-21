const express = require('express');
const path = require('path');
const fs = require('fs');
const router = express.Router();
const ARCHIVE_PATH = '/home/pi/picam/archive';

/**
 * Get record by filename
 */
router.get('/:filename', async (req, res) => {
  // Make sure we don't have any relative path
  const filename = path.basename(req.params.filename + ".mp4");
  const recordPath = path.join(ARCHIVE_PATH, filename);

  res.sendFile(recordPath);
});

router.get('/', async (req, res) => {
  const records = fs.readdirSync(ARCHIVE_PATH).filter(f => f.split('.').pop() == 'mp4').map(f => f.replace(/\.[^/.]+$/, ""));

  res.json(records);
});

module.exports = {
  router
};

const path = require('path');
const cors = require('cors');
const express = require('express');
const router = express.Router();

if (!process.env.PRODUCTION) {
    router.use(cors());
}

// Serve static build
router.use('/', express.static('./dist'));

// Serve npm scripts
router.use('/hls', express.static(path.join(path.dirname(__dirname), 'node_modules', 'hls.js', 'dist', 'hls.min.js')));

// Serve stream data
router.use('/stream', express.static('./stream'));

// Include all controllers
router.use('/api/records', require('./records').router);

module.exports = router;

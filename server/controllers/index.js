const path = require('path');
const cors = require('cors');
const express = require('express');
const router = express.Router();

const dist_path = path.join(path.dirname(__dirname), 'dist');

if (!process.env.PRODUCTION) {
    router.use(cors());
}

// Serve static build
router.use('/', express.static(dist_path));

// Serve npm scripts
router.use('/hls', express.static(path.join(path.dirname(__dirname), 'node_modules', 'hls.js', 'dist', 'hls.min.js')));
router.use('/hls.min.js.map', express.static(path.join(path.dirname(__dirname), 'node_modules', 'hls.js', 'dist', 'hls.min.js.map')));

// Serve stream data
router.use('/stream', express.static('./stream'));

// Include all controllers
router.use('/api/records', require('./records').router);

router.get('*', function (req, res) {
    res.sendFile("index.html", { root: dist_path });
});

module.exports = router;

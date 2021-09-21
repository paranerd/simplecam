const express = require('express');
require('dotenv').config()

const app = express();
const port = process.env.PORT || 8081;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(require('./controllers'));

// Start server
app.listen(port, () => console.log(`Listening on port: ${port}`));

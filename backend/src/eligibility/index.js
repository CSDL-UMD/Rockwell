const express = require('express');
const app = express();
const cors = require('cors');
const port = 6000;

app.use('/', require('./routes/users'));
app.use(express.json());
app.use(cors());

app.listen(port, () => {
    console.log(`Server running on port: ${port}`)
});
const express = require('express');
const app = express();
const cors = require('cors');
const userRoutes = require('./routes/Users');
const port = 5000;

app.use(express.json());
app.use(cors());
app.use(userRoutes);

app.listen(port, () => {
    console.log(`Server running on port: ${port}`)
});

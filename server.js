const express = require('express');
const { MongoClient, ServerApiVersion } = require('mongodb');
const { exec } = require('child_process'); // To run the Python script
const cors = require('cors');
const fs = require('fs');

const app = express();
const port = 3000; // Using port 5001 to avoid conflicts

// Enable CORS
app.use(cors());
app.use(express.json()); // Middleware to parse JSON request body

// MongoDB connection URI
const uri = "mongodb+srv://vj4792:srm_omr@cluster0.xj4tc.mongodb.net/faculty?retryWrites=true&w=majority";

// Create a MongoClient with a MongoClientOptions object
const client = new MongoClient(uri, {
    serverApi: {
        version: ServerApiVersion.v1,
        strict: true,
        deprecationErrors: true,
    }
});

async function run() {
    try {
        // Connect the client to the server
        await client.connect();
        console.log("Connected to MongoDB!");

        // Ping the MongoDB server
        await client.db("admin").command({ ping: 1 });
        console.log("Pinged your deployment. You successfully connected to MongoDB!");

        // Login route to verify credentials
        app.post('/login', async (req, res) => {
            const { username, password } = req.body;
            try {
                const collection = client.db("faculty").collection("credentials");
                const user = await collection.findOne({ username: username, password: password });

                if (user) {
                    res.status(200).json({ message: 'Login successful!' });
                } else {
                    res.status(401).json({ message: 'Invalid username or password' });
                }
            } catch (err) {
                res.status(500).json({ message: 'Error occurred while logging in' });
                console.error(err);
            }
        });

        // Route for uploading data and triggering Python script
        app.post('/upload', (req, res) => {
            const { pdfFilePath, numQuestions, answerKey } = req.body;

            // Write to JSON file
            const inputData = {
                pdfFilePath: pdfFilePath,
                numQuestions: numQuestions,
                answerKey: answerKey.split(' '),
            };

            fs.writeFileSync('data.json', JSON.stringify({ input: inputData, output: {} }));

            // Execute the Python script
            exec('python backend.py', (error, stdout, stderr) => {
                if (error) {
                    console.error(`Error executing script: ${error}`);
                    return res.status(500).send('Error processing OMR.');
                }

                // Read the result file path from JSON
                const data = JSON.parse(fs.readFileSync('data.json'));
                const resultFilePath = data.output.resultFilePath;

                if (fs.existsSync(resultFilePath)) {
                    res.json({ filePath: resultFilePath });
                } else {
                    res.status(500).send('Result file not found.');
                }
            });
        });

    } catch (error) {
        console.error("MongoDB connection error:", error);
    }
}

run().catch(console.dir);

// Start the Express server
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});

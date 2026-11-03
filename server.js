const express = require('express');
const multer = require('multer');
const { xsltProcess, xmlParse } = require('xslt-processor');

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

app.post('/transform', upload.any(), (req, res) => {
  try {
    if (!req.files || req.files.length < 2) {
      return res.status(400).send('Servono 2 file: il file XML della fattura e il foglio XSLT.');
    }

    const xmlFile = req.files.find(f => f.fieldname.toLowerCase().includes('xml') || f.originalname.toLowerCase().endsWith('.xml'));
    const xslFile = req.files.find(f => f.fieldname.toLowerCase().includes('xsl') || f.originalname.toLowerCase().endsWith('.xsl'));

    if (!xmlFile || !xslFile) {
      return res.status(400).send('Impossibile identificare XML e XSL.');
    }

    const xmlString = xmlFile.buffer.toString('utf-8');
    const xslString = xslFile.buffer.toString('utf-8');

    // Chiamata corretta senza costruttori 'new'
    const xmlDoc = xmlParse(xmlString);
    const xsltDoc = xmlParse(xslString);
    const htmlResult = xsltProcess(xmlDoc, xsltDoc);

    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.status(200).send(htmlResult);
  } catch (err) {
    console.error('Errore durante la trasformazione:', err);
    return res.status(500).send('Errore trasformazione: ' + err.message);
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server avviato su porta ${PORT}`);
});

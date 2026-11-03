const express = require('express');
const multer = require('multer');
const xsltProcessor = require('xslt-processor');

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

// upload.any() accetta qualsiasi file caricato senza dare "Unexpected field"
app.post('/transform', upload.any(), (req, res) => {
  try {
    if (!req.files || req.files.length < 2) {
      return res.status(400).send('Servono 2 file: il file XML della fattura e il foglio XSLT.');
    }

    // Cerca i file per nome campo o per estensione/nome del file inviato
    const xmlFile = req.files.find(f => f.fieldname.toLowerCase().includes('xml') || f.originalname.toLowerCase().endsWith('.xml'));
    const xslFile = req.files.find(f => f.fieldname.toLowerCase().includes('xsl') || f.originalname.toLowerCase().endsWith('.xsl'));

    if (!xmlFile || !xslFile) {
      return res.status(400).send('Impossibile identificare XML e XSL. Verifica i campi inviati.');
    }

    const xmlString = xmlFile.buffer.toString('utf-8');
    const xslString = xslFile.buffer.toString('utf-8');

    const xslt = new xsltProcessor.Xslt();
    const xmlParser = new xsltProcessor.XmlParser();

    const xmlDoc = xmlParser.xmlParse(xmlString);
    const xsltDoc = xmlParser.xmlParse(xslString);

    const htmlResult = xslt.xsltProcess(xmlDoc, xsltDoc);

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

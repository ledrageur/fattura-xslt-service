const express = require('express');
const multer = require('multer');
const xsltProcessor = require('xslt-processor');

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

app.post('/transform', upload.fields([{ name: 'xml' }, { name: 'xslt' }]), (req, res) => {
  try {
    if (!req.files || !req.files['xml'] || !req.files['xslt']) {
      return res.status(400).send('File xml o xslt mancanti');
    }

    const xmlString = req.files['xml'][0].buffer.toString('utf-8');
    const xslString = req.files['xslt'][0].buffer.toString('utf-8');

    const xslt = new xsltProcessor.Xslt();
    const xmlParser = new xsltProcessor.XmlParser();

    const xmlDoc = xmlParser.xmlParse(xmlString);
    const xsltDoc = xmlParser.xmlParse(xslString);

    const htmlResult = xslt.xsltProcess(xmlDoc, xsltDoc);

    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    return res.status(200).send(htmlResult);
  } catch (err) {
    console.error(err);
    return res.status(500).send('Errore durante la trasformazione: ' + err.message);
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server avviato su porta ${PORT}`);
});

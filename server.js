const express = require('express');
const multer = require('multer');
const fs = require('fs');
const path = require('path');
const os = require('os');
const xsltproc = require('xsltproc');

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

app.post('/transform', upload.any(), (req, res) => {
  try {
    if (!req.files || req.files.length < 2) {
      return res.status(400).send('File xml o xslt mancanti');
    }

    const xmlFile = req.files.find(f => f.fieldname.toLowerCase().includes('xml') || f.originalname.toLowerCase().endsWith('.xml'));
    const xslFile = req.files.find(f => f.fieldname.toLowerCase().includes('xsl') || f.originalname.toLowerCase().endsWith('.xsl'));

    if (!xmlFile || !xslFile) {
      return res.status(400).send('Impossibile identificare XML e XSL.');
    }

    const tmpDir = os.tmpdir();
    const xmlPath = path.join(tmpDir, `doc_${Date.now()}.xml`);
    const xslPath = path.join(tmpDir, `style_${Date.now()}.xsl`);

    fs.writeFileSync(xmlPath, xmlFile.buffer);
    fs.writeFileSync(xslPath, xslFile.buffer);

    const xs = xsltproc();
    xs.transform(xslPath, xmlPath, (err, stdout, stderr) => {
      // Pulizia file temporanei
      try { fs.unlinkSync(xmlPath); } catch (e) {}
      try { fs.unlinkSync(xslPath); } catch (e) {}

      if (err) {
        console.error('Errore xsltproc:', stderr || err.message);
        return res.status(500).send('Errore trasformazione: ' + (stderr || err.message));
      }

      res.setHeader('Content-Type', 'text/html; charset=utf-8');
      return res.status(200).send(stdout);
    });
  } catch (err) {
    console.error('Errore server:', err);
    return res.status(500).send('Errore server: ' + err.message);
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server avviato su porta ${PORT}`);
});

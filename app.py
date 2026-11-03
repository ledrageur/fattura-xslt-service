import os
import re
import requests
from flask import Flask, request, Response
from lxml import etree

app = Flask(__name__)

# Carica il foglio di stile locale una sola volta all'avvio
XSLT_PATH = os.path.join(os.path.dirname(__file__), 'FoglioStileAssoSoftware.xsl')

@app.route('/transform', methods=['POST'])
def transform_to_pdf():
    try:
        # 1. Recupera il file XML inviato
        xml_file = None
        for key in request.files:
            f = request.files[key]
            if 'xml' in key.lower() or f.filename.lower().endswith('.xml'):
                xml_file = f
                break

        if not xml_file:
            return "File XML mancante", 400

        xml_bytes = xml_file.read()

        # 2. Parsing XML e rimozione namespace per estrazione dati rapida
        xml_root = etree.fromstring(xml_bytes)
        
        # Estrai Numero Fattura
        num_doc = xml_root.xpath("//DatiGeneraliDocumento/Numero/text()")
        num_doc_str = num_doc[0].strip() if num_doc else "SenzaNum"

        # Estrai Numero Ordine (se presente)
        num_ord = xml_root.xpath("//DatiOrdineAcquisto/IdDocumento/text()")
        num_ord_str = f"Ord_{num_ord[0].strip()}_" if num_ord else ""

        # Pulisci caratteri non validi per i nomi di file
        safe_num_doc = re.sub(r'[\\/*?:"<>|]', '-', num_doc_str)
        safe_num_ord = re.sub(r'[\\/*?:"<>|]', '-', num_ord_str)
        pdf_filename = f"{safe_num_ord}Fattura_{safe_num_doc}.pdf"

        # 3. Trasformazione XSLT -> HTML
        if os.path.exists(XSLT_PATH):
            with open(XSLT_PATH, 'rb') as f:
                xslt_root = etree.fromstring(f.read())
        else:
            return f"Foglio di stile non trovato sul server: {XSLT_PATH}", 500

        transform = etree.XSLT(xslt_root)
        html_tree = transform(xml_root)
        html_bytes = str(html_tree).encode('utf-8')

        # 4. Chiamata a Gotenberg per convertire HTML in PDF
        gotenberg_url = "https://demo.gotenberg.dev/forms/chromium/convert/html"
        files = {
            'files': ('index.html', html_bytes, 'text/html')
        }
        
        res = requests.post(gotenberg_url, files=files, timeout=60)
        
        if res.status_code != 200:
            return f"Errore generazione PDF da Gotenberg: {res.text}", 502

        # 5. Restituisce direttamente il binario PDF
        response = Response(res.content, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
        response.headers['X-Suggested-Filename'] = pdf_filename
        return response

    except Exception as e:
        print("Errore server:", str(e))
        return f"Errore interno: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

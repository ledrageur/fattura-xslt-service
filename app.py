import os
import re
import requests
from flask import Flask, request, Response
from lxml import etree

app = Flask(__name__)

# Percorso del foglio di stile presente nella stessa cartella dell'applicazione
XSLT_PATH = os.path.join(os.path.dirname(__file__), 'FoglioStileAssoSoftware.xsl')

def sanitize_value(value):
    """Pulisce i caratteri non consentiti nei nomi di file."""
    if not value:
        return ""
    # Sostituisce caratteri riservati con trattini
    cleaned = re.sub(r'[\\/*?:"<>|\n\r\t]', '-', str(value).strip())
    # Rimuove spazi doppi
    return re.sub(r'\s+', '_', cleaned)

@app.route('/transform', methods=['POST'])
def transform_to_pdf():
    try:
        # 1. Recupero del file XML
        xml_file = None
        for key in request.files:
            f = request.files[key]
            if 'xml' in key.lower() or f.filename.lower().endswith('.xml'):
                xml_file = f
                break

        if not xml_file:
            return "File XML mancante nella richiesta", 400

        xml_bytes = xml_file.read()

        # 2. Parsing dell'XML ed estrazione metadati per il nome parlante
        xml_root = etree.fromstring(xml_bytes)

        # CIG (se presente in DatiOrdineAcquisto o DatiContratto)
        cig_nodes = xml_root.xpath("//*[local-name()='CodiceCIG']/text()")
        cig_val = sanitize_value(cig_nodes[0]) if cig_nodes else "NoCIG"

        # Numero Ordine (IdDocumento in DatiOrdineAcquisto)
        ord_nodes = xml_root.xpath("//*[local-name()='DatiOrdineAcquisto']/*[local-name()='IdDocumento']/text()")
        ord_val = sanitize_value(ord_nodes[0]) if ord_nodes else "NoOrd"

        # Numero Fattura
        doc_num_nodes = xml_root.xpath("//*[local-name()='DatiGeneraliDocumento']/*[local-name()='Numero']/text()")
        doc_num_val = sanitize_value(doc_num_nodes[0]) if doc_num_nodes else "NoNum"

        # Periodo / Data Documento (formato AAAA-MM-GG)
        doc_date_nodes = xml_root.xpath("//*[local-name()='DatiGeneraliDocumento']/*[local-name()='Data']/text()")
        periodo_val = sanitize_value(doc_date_nodes[0]) if doc_date_nodes else "NoData"

        # Costruzione del nome parlante finale
        # Esempio: CIG-1234567890_Ord-5432_Fatt-99_2026-03-15.pdf
        pdf_filename = f"CIG-{cig_val}_Ord-{ord_val}_Fatt-{doc_num_val}_{periodo_val}.pdf"

        # 3. Trasformazione XSLT -> HTML
        if not os.path.exists(XSLT_PATH):
            return f"Foglio XSLT non trovato sul server: {XSLT_PATH}", 500

        with open(XSLT_PATH, 'rb') as f:
            xslt_root = etree.fromstring(f.read())

        transform = etree.XSLT(xslt_root)
        html_tree = transform(xml_root)
        html_bytes = str(html_tree).encode('utf-8')

        # 4. Generazione PDF tramite Gotenberg
        gotenberg_url = "https://demo.gotenberg.dev/forms/chromium/convert/html"
        files = {
            'files': ('index.html', html_bytes, 'text/html')
        }
        res = requests.post(gotenberg_url, files=files, timeout=60)

        if res.status_code != 200:
            return f"Errore Gotenberg: {res.text}", 502

        # 5. Restituzione del file binario con il nome valorizzato negli header
        response = Response(res.content, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
        response.headers['X-Suggested-Filename'] = pdf_filename
        return response

    except Exception as e:
        print("Errore:", str(e))
        return f"Errore server: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

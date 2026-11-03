import os
from flask import Flask, request, Response
from lxml import etree

app = Flask(__name__)

@app.route('/transform', methods=['POST'])
def transform():
    try:
        xml_file = None
        xsl_file = None

        # Ricerca automatica dei due file inviati
        for key in request.files:
            f = request.files[key]
            filename = f.filename.lower()
            if 'xml' in key.lower() or filename.endswith('.xml'):
                xml_file = f
            elif 'xsl' in key.lower() or filename.endswith('.xsl'):
                xsl_file = f

        if not xml_file or not xsl_file:
            return "File xml o xslt mancanti", 400

        # Parsing con lxml (gestisce al 100% qualsiasi costrutto XSLT 1.0/1.1)
        xml_doc = etree.fromstring(xml_file.read())
        xslt_doc = etree.fromstring(xsl_file.read())
        
        transform = etree.XSLT(xslt_doc)
        result_tree = transform(xml_doc)
        
        return Response(str(result_tree), mimetype='text/html')

    except Exception as e:
        print("Errore trasformazione:", str(e))
        return f"Errore trasformazione: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

from flask import Flask, render_template, request, jsonify, make_response
from datetime import datetime
from num2words import num2words
from xhtml2pdf import pisa
from io import BytesIO
import mysql.connector

app = Flask(__name__)

db = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="2308",
    database="srinivas_enterprises"
)

@app.route('/')
def form():

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT DISTINCT product_name
        FROM Catalog
        ORDER BY product_name
    """)

    products = cursor.fetchall()

    return render_template(
        'form.html',
        products=products
    )

@app.route('/get_models/<product_name>')
def get_models(product_name):

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            model,
            offer_price
        FROM Catalog
        WHERE product_name = %s
    """, (product_name,))

    models = cursor.fetchall()

    for m in models:
        if m['offer_price'] is None:
            m['offer_price'] = 0
        else:
            m['offer_price'] = float(m['offer_price'])

    #print(models) Debugger

    return jsonify(models)

@app.route('/generate', methods=['POST'])
def generate():
    #generate Date
    invoice_date = datetime.now()
    formatted_date = invoice_date.strftime("%d-%m-%Y")


    #Call for invoice no and date
    cursor = db.cursor(dictionary=True)    
    cursor.execute("""
        INSERT INTO invoices (invoice_date)
        VALUES (NOW())
    """)
    db.commit()
    invoice_no = cursor.lastrowid
    formatted_invoice_no = (str(invoice_no).zfill(5))
    

    #getting buyer,cosignee,product and quantites
    product_ids = request.form.getlist('product_id[]')
    quantities = request.form.getlist('qty[]')

    if len(product_ids) == 0:
        return "At least one product required"
    #buyer and Cosignee fields
    buyer_name = request.form['buyer_name']
    if not request.form['buyer_name'].strip():
        return "Buyer name required"
    buyer_address = request.form['buyer_address']
    if not request.form['buyer_address'].strip():
        return "Buyer address required"
    buyer_contact = request.form['buyer_contact']
    buyer_gstin = request.form['buyer_gstin']
    buyer_contract = request.form['buyer_contract']

    consignee_name = request.form['consignee_name']
    if not request.form['consignee_name'].strip():
        return "Consignee name required"
    consignee_address = request.form['consignee_address']
    if not request.form['consignee_address'].strip():
        return "Consignee address required"
    consignee_contact = request.form['consignee_contact']
    consignee_gstin = request.form['consignee_gstin']
    consignee_contract = request.form['consignee_contract']

    #HSN details
    hsn_codes = request.form.getlist('hsn[]')

    #Product Quantity list
    product_ids = request.form.getlist('product_id[]')
    quantities = request.form.getlist('qty[]')
    cursor = db.cursor(dictionary=True)
    taxable_total = 0
    cgst_total = 0
    sgst_total = 0
    igst_total = 0
    grand_total = 0
    items = []

    #taxing for correct GST
    seller_gstin =   "37AYFPS6096K1ZL"
    seller_state =   seller_gstin[:2]
    buyer_state =    buyer_gstin[:2]

    if seller_state == buyer_state:
        cgst_percent = 9
        sgst_percent = 9
        igst_percent = 0

    else:
        cgst_percent = 0
        sgst_percent = 0
        igst_percent = 18


    for pid, qty, hsn in zip(product_ids, quantities, hsn_codes):
        
        #fetching product details from Database
        cursor.execute("""
            SELECT
                product_name,
                model,
                offer_price,
                gst_percent
            FROM Catalog
            WHERE id = %s
        """, (pid,))
        item = cursor.fetchone()

        #calculation for gst_amount,Taxable_Amount and grand_Total
        qty = int(qty)
        price = float(item['offer_price'])
        gst_percent = float(item['gst_percent'])
        inclusive_total = round(qty * price,3)
        taxable_value = round(inclusive_total * 100 /(100 + gst_percent),3)

        total_gst = round(inclusive_total - taxable_value,3)

        #Selecting and intializing gst based on state
        if seller_state == buyer_state:
            cgst_percent = gst_percent / 2
            sgst_percent = gst_percent / 2
            igst_percent = 0

        else:
            cgst_percent = 0
            sgst_percent = 0
            igst_percent = gst_percent

        #calculate gst based on state
        if seller_state == buyer_state:
            cgst_amount = round(total_gst/ 2,3)
            sgst_amount = round(total_gst/ 2,3)
            igst_amount = 0
        else:
            igst_amount = round(total_gst,3)
            cgst_amount = 0
            sgst_amount = 0

        line_total = inclusive_total

        #adding invoice totals
        taxable_total += taxable_value
        cgst_total += cgst_amount
        sgst_total += sgst_amount
        igst_total += igst_amount
        grand_total += line_total

        #amount in words
        grand_total = round(grand_total, 2)
        amount_words = ( "Rupees " + num2words(grand_total, lang='en_IN').title() + " Only")

        #Store product rows
        items.append({
            "product":item['product_name'],
            "model":item['model'],
            "hsn": hsn,
            "price":price,
            "qty":qty,
            "taxable":taxable_value,
            "cgst":cgst_amount,
            "sgst":sgst_amount,
            "igst":igst_amount,
            "line_total": line_total
        })

    html = render_template(

        'invoice.html',

        invoice_no = formatted_invoice_no,
        invoice_date = formatted_date,

        buyer_name=buyer_name,
        buyer_address=buyer_address,
        buyer_contact=buyer_contact,
        buyer_gstin=buyer_gstin,
        buyer_contract=buyer_contract,

        consignee_name=consignee_name,
        consignee_address=consignee_address,
        consignee_contact=consignee_contact,
        consignee_gstin=consignee_gstin,
        consignee_contract=consignee_contract,


        items=items,
        taxable_total=taxable_total,

        cgst_total=cgst_total,
        sgst_total=sgst_total,
        igst_total=igst_total,
        
        grand_total=grand_total,
        
        seller_state=seller_state,
        buyer_state=buyer_state,
        
        amount_in_words=amount_words

    )
    #create pdf
    pdf_buffer = BytesIO()

    pisa.CreatePDF(html,dest=pdf_buffer)
    pdf = pdf_buffer.getvalue()
    pdf_buffer.close()

    response = make_response(pdf)

    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = (
        f'inline; filename='
        f'Invoice_{formatted_invoice_no}.pdf'
    )
    return response
    
app.run(debug=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
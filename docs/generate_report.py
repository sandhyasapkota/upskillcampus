"""Generate a project report using the company's Word package as a template."""
import copy
import io
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageFont

SOURCE = Path(__file__).parent / 'InventoryManagementSystem_SandhyaSapkota_USC_UCT.docx'
OUTPUT = Path(__file__).parent / 'Inventory_Management_Internship_Report.docx'
ASSETS = Path(__file__).parent / 'report_assets'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
def tag(name):
    return '{%s}%s' % (W, name)


def make_diagrams():
    """Create original inventory diagrams matching the reference report's visual style."""
    ASSETS.mkdir(exist_ok=True)
    green, fill, ink = '#167a63', '#edf4f0', '#1b2e2e'
    font_path = r'C:\Windows\Fonts\arial.ttf'
    face = lambda size: ImageFont.truetype(font_path, size)
    def canvas(): return Image.new('RGB', (1500, 900), 'white')
    def box(draw, rect, value, size=28):
        draw.rounded_rectangle(rect, radius=20, fill=fill, outline=green, width=3)
        lines = value.split('\n'); y = (rect[1]+rect[3]-len(lines)*(size+8))/2
        for line in lines:
            width = draw.textbbox((0,0), line, font=face(size))[2]
            draw.text(((rect[0]+rect[2]-width)/2,y), line, fill=ink, font=face(size)); y += size+8
    def arrow(draw, start, end, label=''):
        draw.line([start,end], fill=green, width=3); x,y=end
        draw.polygon([(x,y),(x-12,y-18),(x+12,y-18)], fill=green)
        if label: draw.text(((start[0]+end[0])/2+12,(start[1]+end[1])/2-28),label,fill='#64736d',font=face(22))
    img=canvas(); d=ImageDraw.Draw(img)
    box(d,(450,30,1050,150),'User browser\nDashboard, forms, reports'); arrow(d,(750,150),(750,230),'HTTP')
    box(d,(450,230,1050,350),'Flask application\nRoutes, validation, role checks')
    box(d,(80,470,670,600),'Authentication\nSessions and password hashing'); box(d,(830,470,1420,600),'Inventory workflows\nProducts, movements, exports')
    arrow(d,(590,350),(375,470)); arrow(d,(910,350),(1125,470))
    box(d,(450,700,1050,830),'SQLite database\nUsers, products, movements'); arrow(d,(375,600),(600,700)); arrow(d,(1125,600),(900,700))
    img.save(ASSETS/'architecture.png')
    img=canvas(); d=ImageDraw.Draw(img)
    box(d,(35,120,450,590),'USER\nid: primary key\nusername: unique\npassword_hash: required\nrole: admin or staff',25)
    box(d,(540,120,960,590),'PRODUCT\nid: primary key\nsku: unique\nname, category\nprice_cents\nquantity, threshold\nactive flag',24)
    box(d,(1050,70,1465,690),'MOVEMENT\nid: primary key\nproduct_id: foreign key\nuser_id: foreign key\nkind: in or out\namount: positive\nbalance after change\nnote\ncreated_at',23)
    arrow(d,(450,350),(1050,350),'1 : many'); arrow(d,(960,420),(1050,420),'1 : many'); img.save(ASSETS/'database-model.png')
    img=canvas(); d=ImageDraw.Draw(img)
    box(d,(450,25,1050,140),'Authenticated user records movement'); arrow(d,(750,140),(750,220))
    box(d,(450,220,1050,335),'CSRF, role, and form validation'); box(d,(40,450,650,580),'Invalid input\nShow feedback; do not save'); box(d,(850,450,1460,580),'Valid input\nBegin stock transaction')
    arrow(d,(590,335),(345,450)); arrow(d,(910,335),(1155,450)); arrow(d,(1155,580),(1155,665))
    box(d,(850,665,1460,800),'Update quantity and movement together\nCommit, then show activity log'); img.save(ASSETS/'stock-movement-flow.png')


make_diagrams()

with zipfile.ZipFile(SOURCE) as template:
    original = template.read('word/document.xml')
    for _, (prefix, uri) in ET.iterparse(io.BytesIO(original), events=['start-ns']):
        if prefix != 'xml':
            ET.register_namespace(prefix, uri)
    root = ET.fromstring(original)
    body = root.find(tag('body'))
    section = copy.deepcopy(body.find(tag('sectPr')))
    body.clear()

    def para(text='', style=None, size=24, bold=False, center=False, page=False):
        p = ET.SubElement(body, tag('p'))
        props = ET.SubElement(p, tag('pPr'))
        if style:
            ET.SubElement(props, tag('pStyle'), {tag('val'): style})
            ET.SubElement(props, tag('keepNext'))
            # Explicit section numbers avoid inheriting the sample's numbering.
            num = ET.SubElement(props, tag('numPr'))
            ET.SubElement(num, tag('numId'), {tag('val'): '0'})
        if page:
            ET.SubElement(props, tag('pageBreakBefore'))
        ET.SubElement(props, tag('spacing'), {tag('after'): '160', tag('line'): '276', tag('lineRule'): 'auto'})
        ET.SubElement(props, tag('jc'), {tag('val'): 'center' if center else 'left'})
        r = ET.SubElement(p, tag('r'))
        rp = ET.SubElement(r, tag('rPr'))
        ET.SubElement(rp, tag('rFonts'), {tag('ascii'): 'Calibri', tag('hAnsi'): 'Calibri'})
        ET.SubElement(rp, tag('sz'), {tag('val'): str(size)})
        if bold or style:
            ET.SubElement(rp, tag('b'))
        t = ET.SubElement(r, tag('t'))
        t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        t.text = text
        return p

    def h(text, level=1, page=False):
        para(text, 'Heading%d' % level, size=32 if level == 1 else 27, page=page)

    def table(headers, rows):
        tbl = ET.SubElement(body, tag('tbl'))
        pr = ET.SubElement(tbl, tag('tblPr'))
        ET.SubElement(pr, tag('tblW'), {tag('w'): '5000', tag('type'): 'pct'})
        borders = ET.SubElement(pr, tag('tblBorders'))
        for side in ['top','left','bottom','right','insideH','insideV']:
            ET.SubElement(borders, tag(side), {tag('val'): 'single', tag('sz'): '4', tag('color'): 'D4DFDA'})
        for i, row in enumerate([headers] + rows):
            tr = ET.SubElement(tbl, tag('tr'))
            trpr = ET.SubElement(tr, tag('trPr'))
            ET.SubElement(trpr, tag('cantSplit'))
            if i == 0:
                ET.SubElement(trpr, tag('tblHeader'))
            for value in row:
                cell = ET.SubElement(tr, tag('tc'))
                cp = ET.SubElement(cell, tag('tcPr'))
                if i == 0:
                    ET.SubElement(cp, tag('shd'), {tag('fill'): 'E5EFE9'})
                p = ET.SubElement(cell, tag('p'))
                r = ET.SubElement(p, tag('r'))
                rp = ET.SubElement(r, tag('rPr'))
                ET.SubElement(rp, tag('sz'), {tag('val'): '21'})
                if i == 0:
                    ET.SubElement(rp, tag('b'))
                ET.SubElement(r, tag('t')).text = str(value)
        para()

    def image(rel_id, filename, caption):
        """Insert a centered PNG using an existing image relationship from the template."""
        p = ET.SubElement(body, tag('p'))
        ppr = ET.SubElement(p, tag('pPr')); ET.SubElement(ppr, tag('jc'), {tag('val'): 'center'})
        r = ET.SubElement(p, tag('r'))
        drawing = ET.SubElement(r, tag('drawing'))
        inline = ET.SubElement(drawing, '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline', {'distT':'0','distB':'0','distL':'0','distR':'0'})
        ET.SubElement(inline, '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent', {'cx':'5486400','cy':'3291840'})
        ET.SubElement(inline, '{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}docPr', {'id':rel_id.replace('rId',''), 'name':filename})
        graphic = ET.SubElement(inline, '{http://schemas.openxmlformats.org/drawingml/2006/main}graphic')
        gd = ET.SubElement(graphic, '{http://schemas.openxmlformats.org/drawingml/2006/main}graphicData', {'uri':'http://schemas.openxmlformats.org/drawingml/2006/picture'})
        pic = ET.SubElement(gd, '{http://schemas.openxmlformats.org/drawingml/2006/picture}pic')
        nv = ET.SubElement(pic, '{http://schemas.openxmlformats.org/drawingml/2006/picture}nvPicPr')
        ET.SubElement(nv, '{http://schemas.openxmlformats.org/drawingml/2006/picture}cNvPr', {'id':'0','name':filename})
        ET.SubElement(nv, '{http://schemas.openxmlformats.org/drawingml/2006/picture}cNvPicPr')
        blipfill = ET.SubElement(pic, '{http://schemas.openxmlformats.org/drawingml/2006/picture}blipFill')
        ET.SubElement(blipfill, '{http://schemas.openxmlformats.org/drawingml/2006/main}blip', {'{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed':rel_id})
        stretch = ET.SubElement(blipfill, '{http://schemas.openxmlformats.org/drawingml/2006/main}stretch'); ET.SubElement(stretch, '{http://schemas.openxmlformats.org/drawingml/2006/main}fillRect')
        shape = ET.SubElement(pic, '{http://schemas.openxmlformats.org/drawingml/2006/picture}spPr')
        transform = ET.SubElement(shape, '{http://schemas.openxmlformats.org/drawingml/2006/main}xfrm')
        ET.SubElement(transform, '{http://schemas.openxmlformats.org/drawingml/2006/main}off', {'x':'0','y':'0'}); ET.SubElement(transform, '{http://schemas.openxmlformats.org/drawingml/2006/main}ext', {'cx':'5486400','cy':'3291840'})
        preset = ET.SubElement(shape, '{http://schemas.openxmlformats.org/drawingml/2006/main}prstGeom', {'prst':'rect'}); ET.SubElement(preset, '{http://schemas.openxmlformats.org/drawingml/2006/main}avLst')
        para(caption, size=21, center=True)

    para('Industrial Internship Report on', size=34, bold=True, center=True)
    para('Inventory Management System', size=44, bold=True, center=True)
    para('Stockroom — Python Development using Flask', size=28, center=True)
    para()
    para('Prepared by', center=True)
    para('[Student Name]', size=32, bold=True, center=True)
    para('Student / Enrollment ID: [Your ID]', center=True)
    para('College / Institution: [Your Institution]', center=True)
    para('Internship Domain: Python Development', center=True)
    para('Internship Duration: [Start Date] to [End Date]', center=True)
    para('Submission Date: [Submission Date]', center=True)
    para()
    para('upskill Campus and The IoT Academy', size=28, bold=True, center=True)
    para('Industrial Partner: UniConverge Technologies Pvt Ltd (UCT)', center=True)
    para('Mentor / Supervisor: [Mentor Name]', center=True)

    h('Executive Summary', page=True)
    para('This report presents Stockroom, a web-based Inventory Management System developed for a Python development internship. The report follows the structure of the sample supplied by upskill Campus and The IoT Academy in association with UniConverge Technologies Pvt Ltd (UCT).')
    para('The project addresses the difficulty of maintaining accurate stock records with paper registers or independently edited spreadsheets. It provides a central catalog, controlled stock receipts and issues, low-stock indicators, role-based access, and a permanent stock movement history.')
    para('The application uses Python and Flask for backend processing, SQLite for persistent storage, Jinja2 for server-rendered pages, and HTML, CSS, and JavaScript for the interface. Administrators manage products and team accounts; staff can view inventory, record movements, and export reports. Passwords are hashed and state-changing forms require CSRF tokens.')
    para('A stock transaction updates the product balance and writes the movement record in a single database transaction. Invalid quantities and requests that would create negative stock are rejected. Products may be archived only when their balance is zero, preserving the movement history.')
    para('Six automated test methods passed in the verified local test run. They exercise authentication, permissions, validation, stock consistency, archival history, CSV export, page rendering, and setup commands. These results demonstrate functional correctness for the tested scenarios; production load capacity has not been measured.')
    para('The current deliverable is a local small-team prototype. The remaining submission work includes adding personal information, reviewing the implementation, inserting screenshots, and recording a demonstration. Public deployment, email alerts, barcode scanning, and supplier workflows are future enhancements.')

    h('Table of Contents', page=True)
    contents = ['1  Preface','2  Introduction','2.1  About UniConverge Technologies Pvt Ltd','2.2  About upskill Campus and The IoT Academy','2.3  Objective','2.4  Reference','2.5  Glossary','3  Problem Statement','4  Existing and Proposed Solution','5  Proposed Design / Model','5.1  High-Level Diagram','5.2  Low-Level Design','5.3  Interfaces','6  Performance Test','6.1  Test Plan / Test Cases','6.2  Test Procedure','6.3  Performance Outcome','7  My Learnings','8  Future Work Scope']
    for line in contents:
        para(line, size=23)
    para('Section headings use Word heading styles. To add automatic page numbers to this contents list, replace it using References → Table of Contents after editing the final report.', size=20)

    h('1  Preface', page=True)
    para('An internship project connects programming concepts with a practical software workflow. Inventory management is a suitable problem because it requires persistent records, reliable validation, controlled access, and traceable changes rather than only a visual interface.')
    para('Stockroom was selected as the final project for the Python development domain. Its scope covers product records, stock movements, low-stock alerts, administrator and staff roles, and reporting. The implementation is designed to be understandable and practical for a one-week final-project preparation window.')
    para('The one-week preparation window refers to the remaining project and submission work, not the total internship duration. The official internship dates should be entered on the cover page.')
    table(['Day','Planned activity'], [
        ['1','Set up the app, review requirements, and understand the database relationships.'],
        ['2','Review authentication and access checks; create and test a staff account.'],
        ['3','Trace stock transactions and practice negative-stock rejection scenarios.'],
        ['4','Customize business categories, labels, colors, and currency presentation.'],
        ['5','Run automated tests and manually review desktop/mobile layouts.'],
        ['6','Complete report details, repository links, and application screenshots.'],
        ['7','Record the demo, review the deliverables, and submit.']])
    para('Acknowledgement: I thank [Mentor Name], [Faculty / Coordinator Name], and the internship team for their guidance and support. Replace these placeholders with the people who actually assisted with the internship.')
    para('Advice to peers: understand each feature before presenting it, use small reproducible test scenarios, and explain limitations honestly. Review and personalize this report so it reflects your own work and experience.')

    h('2  Introduction', page=True)
    h('2.1  About UniConverge Technologies Pvt Ltd', 2)
    para('The company-provided sample identifies UniConverge Technologies Pvt Ltd (UCT) as the industrial partner for the internship. It describes UCT as a digital transformation company established in 2013, working with technologies including IoT, cybersecurity, cloud computing, machine learning, communication systems, Java, and Python.')
    para('The sample also describes IoT and smart-factory applications, industrial monitoring, and predictive maintenance. This organizational background is summarized from the supplied sample; it is not a separate verification of current company offerings.')
    h('2.2  About upskill Campus and The IoT Academy', 2)
    para('According to the supplied sample, upskill Campus supports career development and facilitates the internship with The IoT Academy and UCT. The sample describes The IoT Academy as UCT’s education division. For this project, the relevant purpose is practical learning through requirements, implementation, testing, and technical reporting.')
    h('2.3  Objective', 2)
    para('The objective is to build and explain a functioning Python web application for managing inventory in a small organization.')
    for text in ['Maintain uniquely identified products with names, categories, unit prices, and reorder levels.', 'Record stock receipts and issues without allowing negative inventory.', 'Highlight products whose stock is at or below the reorder threshold.', 'Enforce administrator and staff access rules on the server.', 'Preserve the actor, reason, timestamp, and resulting balance for each movement.', 'Provide searchable inventory and a downloadable CSV report.', 'Validate important workflows through automated tests and a repeatable demonstration.']:
        para('• ' + text)
    h('2.4  Reference', 2)
    for text in ['[1] Company-supplied sample: Sample_InternshipReport_USC_UCT (1).docx.', '[2] Flask documentation: https://flask.palletsprojects.com/en/stable/', '[3] Python sqlite3 documentation: https://docs.python.org/3/library/sqlite3.html', '[4] Werkzeug security utilities: https://werkzeug.palletsprojects.com/en/stable/utils/#module-werkzeug.security', '[5] Project source: app.py, templates/, static/, tests/test_app.py, and README.md in the submitted repository.']:
        para(text, size=22)
    h('2.5  Glossary', 2)
    table(['Term','Meaning in this project'], [['SKU','Stock Keeping Unit; a unique product identifier.'],['CRUD','Create, read, update, and delete; products use archival instead of destructive deletion.'],['CSRF','Cross-Site Request Forgery; form tokens help reject unauthorized form submissions.'],['RBAC','Role-based access control; admin and staff have different permissions.'],['Transaction','A unit of database work committed or rolled back together.'],['UTC','Coordinated Universal Time; used for movement timestamps.'],['CSV','Comma-separated values; the downloadable inventory report format.'],['Reorder level','Quantity threshold at or below which an alert appears.']])

    h('3  Problem Statement', page=True)
    para('A small business needs a reliable way to identify products, see current stock, record incoming and outgoing items, and know when replenishment is required. When changes are tracked manually, users can overwrite records, miss low-stock conditions, or lose the reason for a quantity change.')
    para('The proposed system must provide a central source of inventory data and reject changes that violate business rules. Every accepted movement must identify the product, user, movement direction, quantity, resulting balance, optional reason, and time.')
    table(['Requirement','Acceptance criterion'], [['Product identification','SKU is unique; product name and SKU are mandatory.'],['Stock accuracy','Only positive whole movement amounts are accepted; stock remains nonnegative.'],['Traceability','Each accepted movement creates a permanent history record.'],['Access control','Staff cannot access product administration or user management routes.'],['Low-stock visibility','Products with quantity ≤ reorder level appear in the attention list.'],['Safe retirement','Only zero-stock products may be archived; previous movements remain visible.'],['Usable reporting','Users can search active products and export their catalog as CSV.']])
    para('Scope boundaries: one inventory workspace, whole-unit quantities, a single price convention, and in-app alerts. The app does not process payments, calculate accounting cost layers, send email, or manage multiple warehouse locations.')

    h('4  Existing and Proposed Solution', page=True)
    h('Existing Approaches', 2)
    table(['Approach','Advantages','Limitations for this project'], [['Paper register','Low setup cost and familiar workflow.','Difficult searching, calculations, role enforcement, and timely alerts.'],['Spreadsheet','Flexible tables, formulas, and exports.','Manual edits can change quantities without consistent movement history.'],['Full ERP / inventory platform','Broad purchasing, warehousing, and reporting workflows.','May introduce setup and training beyond a small internship prototype.']])
    para('These comparisons describe general workflow trade-offs, not a benchmark of any specific commercial product.')
    h('Proposed Solution and Value Addition', 2)
    para('Stockroom combines a simple web interface with server-side validation and a transactional SQLite database. Users authenticate before accessing inventory. The dashboard summarizes active products, units, current-price inventory value, and low-stock items.')
    para('Products are created with zero quantity. Opening stock is received through the same movement workflow used for later deliveries. This prevents an unexplained starting balance. A permanent movement log and zero-stock-only archival retain an auditable stock history.')
    para('Administrators manage catalog records and create accounts. Staff can record movements, view information, and export inventory without changing catalog definitions or creating additional users.')
    para('Code submission (GitHub link): [Insert your project repository URL]')
    para('Report submission (GitHub link): [Insert the report file URL after uploading it]')

    h('5  Proposed Design / Model', page=True)
    h('5.1  High-Level Diagram', 2)
    table(['Layer','Components','Responsibility'], [['Presentation','Browser → HTML / CSS / JavaScript','Forms, navigation, dashboard, tables, and confirmation prompts.'],['Application','Flask routes + Jinja templates','Authentication, permissions, validation, business rules, and rendered responses.'],['Persistence','SQLite: users, products, movements','Store accounts, balances, catalog attributes, and stock history.']])
    image('rId8', 'architecture.png', 'Figure 1. High-level architecture of Stockroom.')
    para('A user submits a form or requests a page. Flask loads the session user, checks access and form tokens where required, validates input, and queries or updates SQLite. The response is rendered as HTML or delivered as a CSV download.')
    h('5.2  Low-Level Design', 2)
    table(['Entity','Important attributes'], [['users','id (PK), username (unique), password_hash, role'],['products','id (PK), sku (unique), name, category, price_cents, quantity, threshold, active'],['movements','id (PK), product_id (FK), user_id (FK), kind, amount, balance, note, created_at']])
    image('rId9', 'database-model.png', 'Figure 2. User, product, and stock-movement database model.')
    h('Stock Movement Algorithm', 2)
    for text in ['1. Authenticate the user and verify the form’s CSRF token.', '2. Validate product ID, direction, positive integer quantity, and note length.', '3. Begin an immediate SQLite transaction to serialize balance updates.', '4. Calculate a positive delta for stock-in or a negative delta for stock-out.', '5. Update only an active product whose resulting quantity is between zero and the configured maximum.', '6. Reject the operation and roll back if no product matches those conditions.', '7. Read the resulting balance and insert a movement linked to the current user.', '8. Commit both changes together, then display the movement history.']:
        para(text)
    image('rId10', 'stock-movement-flow.png', 'Figure 3. Stock-movement validation and transaction flow.')
    para('Price values are converted to integer cents before storage. Database constraints additionally enforce nonnegative quantities/prices, positive movement amounts, permitted roles and directions, and foreign-key relationships.')
    h('5.3  Interfaces', 2)
    table(['Route / interface','Method','Purpose / access'], [['/login','GET / POST','Sign-in form and credential check.'],['/','GET','Dashboard; authenticated users.'],['/products','GET','Search/filter active inventory.'],['/products/new','GET / POST','Create a product; admin only.'],['/products/<id>/edit','GET / POST','Edit product details; admin only.'],['/products/<id>/archive','POST','Archive a zero-stock product; admin only.'],['/stock','GET / POST','Record stock receipt or issue.'],['/movements','GET','View permanent activity history.'],['/users','GET / POST','List/create team accounts; admin only.'],['/export/products.csv','GET','Download active product inventory.'],['/logout','POST','Clear the login session.']])
    para('Setup interfaces: the create-admin CLI command creates an administrator without default credentials; seed-demo adds six sample products only when the product database is empty.')
    h('Application Screenshots', 2)
    image('rId11', 'dashboard.png', 'Figure 4. Stockroom dashboard with metrics and low-stock alerts.')
    image('rId12', 'products.png', 'Figure 5. Product catalog with searchable stock status.')
    image('rId13', 'stock-movement.png', 'Figure 6. Stock receipt form with transaction reason.')
    image('rId14', 'activity-log.png', 'Figure 7. Permanent stock-movement activity log.')
    image('rId15', 'team-members.png', 'Figure 8. Team-member roles and account management.')

    h('6  Performance Test', page=True)
    para('Validation focuses on functional correctness and stock integrity. No throughput, latency, memory, or multi-user load benchmark has been completed. The outcomes below should not be interpreted as a production performance claim.')
    table(['Constraint','Design response','Validation / limitation'], [['Negative inventory','Conditional update plus nonnegative database constraint.','An overdraw is rejected and history/balance stay unchanged.'],['Partial stock updates','Balance and movement are in one transaction.','Tests verify accepted/rejected movement balances and history.'],['Unauthorized administration','Server-side admin role checks.','Staff requests to restricted routes return HTTP 403.'],['Malformed inputs','Server validation and database constraints.','Tests reject invalid prices and movement quantities.'],['History loss','Movement records are permanent; products are archived.','Tests confirm archived product history remains visible.'],['Concurrent writes','BEGIN IMMEDIATE and SQLite lock timeout.','Write serialization is implemented; concurrency/load benchmarking remains future work.'],['Large activity history','Current page loads the full history.','Pagination is recommended before large-scale use.']])
    h('6.1  Test Plan / Test Cases', 2)
    table(['ID','Test method / cases','Observed result'], [['T01','test_login_and_authentication: unauthenticated redirect, bad credentials, login, logout.','Pass'],['T02','test_staff_permissions: deny admin pages/archival; allow stock, catalog, reporting.','Pass'],['T03','test_movements_and_rejected_overdraw: receive 10, issue 7, reject issue 4; reject malformed/nonpositive quantities.','Pass; final balance 3, two movements.'],['T04','test_product_validation_edit_archive_and_history: create/edit, duplicate SKU, invalid prices, zero-stock archival, retained history.','Pass'],['T05','test_csrf_user_creation_csv_and_templates: token rejection, user validation, CSV formula escaping, page rendering, missing product.','Pass'],['T06','test_cli: create admin, reject demo seed on nonempty catalog, seed six products on empty catalog.','Pass']])
    h('6.2  Test Procedure', 2)
    for text in ['1. Install dependencies from requirements.txt and use the project directory as the working directory.', '2. Run: python -m unittest discover -s tests -v', '3. Each test creates a temporary SQLite database, prepares users/products, and uses Flask’s test client for requests.', '4. Assertions check HTTP responses, rendered content, persisted quantities, movement counts, and CLI results.', '5. Database connections are closed and temporary test data is cleaned up.', '6. Repeat manually in the browser: create a product, receive stock, issue stock, attempt an overdraw, export CSV, and check staff restrictions.']:
        para(text)
    h('6.3  Performance Outcome', 2)
    para('Verified development environment: Python 3.8.10 and Flask 3.0.0 on Windows. The reproducible dependency file specifies Flask 3.0.3 and Werkzeug 3.0.6; the recorded test run used the already-installed environment, not a newly installed dependency environment.')
    para('Recorded automated result: Ran 6 tests in 3.207 seconds — OK. This is test-suite duration, not application response latency. Re-run the suite in your submission environment and insert an updated screenshot if its versions or timing differ.')
    para('[Insert Figure 7: terminal screenshot of your final passing test run]')
    para('The tested scenarios demonstrate rejection of stock overdrafts, preserved balances after invalid requests, protected admin interfaces, and retained history after archival. Responsive layout, browser compatibility, and simultaneous-user behavior require additional manual or dedicated testing; no visual-browser verification is claimed here.')

    h('7  My Learnings', page=True)
    para('Personalize this section after reviewing and demonstrating the project. The following learning summary describes the concepts covered by the implementation; keep only statements you can explain from your own experience.', size=21)
    for title, text in [
        ('Python and Flask','The project illustrates how route functions process requests, validate forms, render Jinja templates, and redirect after successful writes. The application factory allows isolated test configurations.'),
        ('Relational data modeling','Separate account, product, and movement tables avoid mixing identity, current state, and historical events. Foreign keys connect movements to their product and actor.'),
        ('Transactions and business rules','A stock balance must not be changed without a corresponding history event. A transaction makes those changes succeed or fail together, and the conditional update prevents overdrawing stock.'),
        ('Authentication and security','Password hashes protect stored credentials. Session-based identity, role checks, CSRF validation, parameterized SQL, and template escaping address different parts of application security.'),
        ('Validation and testing','Unhappy paths such as negative quantities, duplicate identifiers, unauthorized actions, and insufficient stock are as important as successful form submissions.'),
        ('Documentation and presentation','A reproducible setup guide, small demo scenario, clear limitations, and meaningful screenshots make a project easier to review and maintain.')]:
        h(title, 2)
        para(text)
    para('My personal challenges and solutions: [Describe one or two problems you encountered and how you resolved them.]')
    para('My internship experience and career relevance: [Add your actual experience, mentor feedback, and the skills you plan to develop next.]')

    h('8  Future Work Scope', page=True)
    table(['Enhancement','Expected benefit'], [['Supplier and purchase-order modules','Connect low-stock decisions with ordering and receiving.'],['Barcode / QR scanning','Reduce manual product selection and entry errors.'],['Multiple stock locations','Track warehouses, transfers, and per-location availability.'],['Email alerts','Notify responsible staff outside the dashboard.'],['History pagination and filters','Keep activity pages usable as the movement table grows.'],['PostgreSQL and load testing','Evaluate stronger multi-user write workloads with measured evidence.'],['Account lifecycle controls','Add password reset, account deactivation, and restricted role changes.'],['Deployment hardening','Production WSGI server, HTTPS, secure cookies, login rate limits, and backups.'],['Stock valuation reports','Add explicit currency and a defined accounting valuation method.']])
    para('The delivered scope is complete for a local internship demonstration. Future improvements should be selected by business need and verified with new tests. Before submission, replace all personal placeholders, insert authentic screenshots, add repository links, and make sure the report reflects the final code.')

    body.append(section)
    document = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as result:
        for item in template.infolist():
            data = template.read(item.filename)
            if item.filename == 'word/document.xml':
                data = document
            elif item.filename == 'word/media/image1.png':
                data = (ASSETS / 'architecture.png').read_bytes()
            elif item.filename == 'word/media/image2.png':
                data = (ASSETS / 'database-model.png').read_bytes()
            elif item.filename == 'word/media/image3.png':
                data = (ASSETS / 'stock-movement-flow.png').read_bytes()
            elif item.filename == 'word/media/image4.png':
                data = (Path(__file__).parent / 'screenshots' / 'dashboard.png').read_bytes()
            elif item.filename == 'word/media/image5.png':
                data = (Path(__file__).parent / 'screenshots' / 'products.png').read_bytes()
            elif item.filename == 'word/media/image6.png':
                data = (Path(__file__).parent / 'screenshots' / 'stock-movement.png').read_bytes()
            elif item.filename == 'word/media/image7.png':
                data = (Path(__file__).parent / 'screenshots' / 'activity-log.png').read_bytes()
            elif item.filename == 'word/media/image8.png':
                data = (Path(__file__).parent / 'screenshots' / 'team-members.png').read_bytes()
            elif item.filename == 'docProps/core.xml':
                data = b'''<?xml version="1.0" encoding="UTF-8"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Inventory Management System - Internship Report</dc:title><dc:creator>Student</dc:creator><dc:description>Stockroom project report based on the company-provided sample structure.</dc:description></cp:coreProperties>'''
            result.writestr(item, data)

with zipfile.ZipFile(OUTPUT) as check:
    assert check.testzip() is None
    for item in check.namelist():
        if item.endswith('.xml') or item.endswith('.rels'):
            ET.fromstring(check.read(item))
    text = ''.join(ET.fromstring(check.read('word/document.xml')).itertext())
    assert '6.3  Performance Outcome' in text and '8  Future Work Scope' in text
print('Created:', OUTPUT)
print('Word package and XML validation passed.')

"""Generate a short Stockroom walkthrough animation for the internship submission."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / 'recordings' / 'stockroom-walkthrough.gif'
OUT.parent.mkdir(exist_ok=True)
W, H = 1280, 720
FONT = r'C:\Windows\Fonts\arial.ttf'
def f(size, bold=False):
    return ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf' if bold else FONT, size)
def text(d, xy, value, size=18, fill='#192b29', bold=False): d.text(xy, value, font=f(size,bold), fill=fill)
def rounded(d, box, fill='#ffffff', outline=None, radius=10, width=1): d.rounded_rectangle(box, radius, fill, outline, width)

def base(title, subtitle):
    im = Image.new('RGB', (W,H), '#f6f8f5'); d=ImageDraw.Draw(im)
    d.rectangle((0,0,220,H), fill='#ffffff'); rounded(d,(25,25,62,62),'#22745c'); text(d,(33,27),'▦',25,'white',True); text(d,(71,30),'Stockroom.',23,bold=True)
    text(d,(35,112),'WORKSPACE',10,'#95a19b',True)
    for i,label in enumerate(['◫  Overview','▦  Products','⇄  Stock movement','≡  Activity log','♙  Team members']):
        y=145+i*52
        if label.split('  ')[1].lower() in title.lower(): rounded(d,(22,y-9,198,y+30),'#eaf3ed')
        text(d,(37,y),label,15,'#22745c' if label.split('  ')[1].lower() in title.lower() else '#66756e')
    d.line((20,650,200,650),fill='#e5ebe6'); rounded(d,(28,665,60,697),'#e9eee9',radius=20); text(d,(39,670),'A',16,bold=True); text(d,(70,668),'admin',15,bold=True); text(d,(70,686),'Administrator',11,'#7a8581')
    d.rectangle((220,0,W,64),fill='white'); text(d,(255,24),'Workspace  /  Inventory management',13,'#708078'); text(d,(1080,24),'● Local workspace',12,'#22745c')
    text(d,(258,102),title,31,bold=True); text(d,(258,143),subtitle,15,'#7a8581')
    return im,d
def card(d,x,y,label,value,detail,warning=False):
    rounded(d,(x,y,x+210,y+122),'white','#e4ebe6'); text(d,(x+18,y+18),label,13,'#64736d'); text(d,(x+18,y+48),value,29,bold=True); text(d,(x+18,y+90),detail,11,'#7a8581');
    if warning: rounded(d,(x+170,y+16,x+194,y+40),'#fff0ce',radius=6); text(d,(x+178,y+18),'!',16,'#ae7c1d',True)
def table(d,x,y,headers,rows,width=950):
    rounded(d,(x,y,x+width,y+55+len(rows)*47),'white','#e4ebe6'); d.rectangle((x+1,y+1,x+width-1,y+40),fill='#fafbf9'); col=width//len(headers)
    for i,h in enumerate(headers): text(d,(x+18+i*col,y+14),h.upper(),10,'#89958e',True)
    for r,row in enumerate(rows):
        yy=y+48+r*47; d.line((x+1,yy-8,x+width-1,yy-8),fill='#eff2ee')
        for i,v in enumerate(row): text(d,(x+18+i*col,yy+4),v,12,'#263934',i==0)

frames=[]
im=Image.new('RGB',(W,H),'#edf5ef'); d=ImageDraw.Draw(im); rounded(d,(370,190,910,490),'white','#dce7df',18,1); rounded(d,(445,245,505,305),'#22745c',radius=14); text(d,(458,250),'▦',38,'white',True); text(d,(525,250),'Stockroom.',34,bold=True); text(d,(460,325),'Inventory Management System',21,'#52645b'); text(d,(457,367),'Python Development Virtual Internship',16,'#7a8581'); text(d,(453,430),'Walkthrough: products, stock, alerts, and roles',14,'#22745c'); frames.append(im)
im,d=base('Overview','A clear view of stock, value, and items that need attention.'); card(d,258,190,'TOTAL PRODUCTS','6','Active in your catalog'); card(d,488,190,'UNITS IN STOCK','134','Across all products'); card(d,718,190,'INVENTORY VALUE','18,722.00','At current unit prices'); card(d,948,190,'LOW-STOCK ITEMS','3','At or below reorder level',True); text(d,(258,355),'●  Needs attention',18,'#192b29',True); text(d,(258,382),'Products ready for a restock.',13,'#7a8581'); table(d,258,420,['Product','Category','In stock','Status'],[['USB-C Hub','Electronics','6','Low stock'],['Gel Pen Set','Stationery','4','Low stock'],['HDMI Cable','Electronics','0','Out of stock']],890); frames.append(im)
im,d=base('Products','Manage your catalog and keep stock levels in view.'); rounded(d,(940,95,1155,132),'#22745c'); text(d,(957,105),'+  Add product',14,'white',True); rounded(d,(258,185,650,225),'white','#dce4dd'); text(d,(276,198),'Search product, SKU, or category...',13,'#7a8581'); table(d,258,255,['Product / SKU','Category','Unit price','Stock','Status'],[['Wireless Mouse  /  EL-001','Electronics','18.99','34','In stock'],['USB-C Hub  /  EL-002','Electronics','34.99','6','Low stock'],['A5 Notebook  /  ST-001','Stationery','4.99','72','In stock'],['Gel Pen Set  /  ST-002','Stationery','7.99','4','Low stock']],950); frames.append(im)
im,d=base('Stock movement','Every change is recorded with the person and resulting balance.'); rounded(d,(258,190,1040,600),'white','#e4ebe6'); text(d,(285,220),'Record stock movement',21,bold=True); text(d,(285,270),'Product',12,bold=True); rounded(d,(285,290,1005,331),'white','#dce4dd'); text(d,(300,302),'USB-C Hub  ·  EL-002  ·  6 in stock',13); text(d,(285,360),'Movement type',12,bold=True); rounded(d,(285,380,625,421),'white','#dce4dd'); text(d,(300,392),'Stock in — receive inventory',13); text(d,(660,360),'Quantity',12,bold=True); rounded(d,(660,380,1005,421),'white','#dce4dd'); text(d,(675,392),'10',13); text(d,(285,453),'Reason / reference',12,bold=True); rounded(d,(285,473,1005,525),'white','#dce4dd'); text(d,(300,487),'Supplier delivery PO-1042',13,'#52645b'); rounded(d,(840,547,1005,584),'#22745c'); text(d,(870,557),'Record movement',13,'white',True); frames.append(im)
im,d=base('Activity log','A permanent record of every stock movement.'); table(d,258,200,['Product','Movement','Balance','Recorded by','Reason'],[['USB-C Hub','+10 · Stock in','16','admin','Supplier delivery PO-1042'],['Wireless Mouse','+34 · Stock in','34','admin','Opening stock'],['Gel Pen Set','+4 · Stock in','4','admin','Opening stock'],['HDMI Cable','+0 · Stock in','0','admin','Opening stock']],950); text(d,(258,510),'The latest receipt is now visible with the updated balance.',14,'#22745c'); frames.append(im)
im,d=base('Team members','Admins manage the catalog and accounts. Staff can record stock movements.'); table(d,258,205,['Username','Role'],[['admin','Admin'],['warehouse-staff','Staff']],610); rounded(d,(900,190,1170,530),'white','#e4ebe6'); text(d,(925,220),'Add team member',18,bold=True); text(d,(925,270),'Username',12,bold=True); rounded(d,(925,290,1145,330),'white','#dce4dd'); text(d,(940,302),'warehouse-staff',13); text(d,(925,360),'Role',12,bold=True); rounded(d,(925,380,1145,420),'white','#dce4dd'); text(d,(940,392),'Staff',13); rounded(d,(925,455,1070,492),'#22745c'); text(d,(950,465),'Create user',13,'white',True); frames.append(im)
im=Image.new('RGB',(W,H),'#edf5ef'); d=ImageDraw.Draw(im); rounded(d,(335,210,945,500),'white','#dce7df',18,1); text(d,(415,260),'Walkthrough complete',31,'#192b29',True); text(d,(415,315),'Products · Stock movements · Low-stock alerts · Roles',16,'#52645b'); text(d,(415,360),'Run: python app.py',16,'#22745c',True); text(d,(415,400),'Open: http://127.0.0.1:5000',16,'#22745c',True); text(d,(415,455),'Replace this animation with your own narrated browser recording if required.',13,'#7a8581'); frames.append(im)
frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=[2000,3500,3500,3500,3500,3500,2500], loop=0, optimize=True)
screenshots = Path(__file__).parent / 'screenshots'
screenshots.mkdir(exist_ok=True)
for frame, name in zip(frames[1:6], ['dashboard.png', 'products.png', 'stock-movement.png', 'activity-log.png', 'team-members.png']):
    frame.save(screenshots / name)
print('Created:', OUT)

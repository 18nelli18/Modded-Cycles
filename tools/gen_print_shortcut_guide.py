"""Guide imprime avec page Mod Setup, issu du guide HTML canonique."""
from pathlib import Path
import argparse
from html import escape
from html.parser import HTMLParser
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
class Node:
 def __init__(self,tag='',attrs=()):self.tag=tag;self.attrs=dict(attrs);self.children=[]
 def get_text(self,sep=' ',strip=False):
  v=sep.join(c.get_text(sep,strip) if isinstance(c,Node) else c for c in self.children)
  return v.strip() if strip else v
 def find_all(self,tag,recursive=True):
  found=[]
  for c in self.children:
   if isinstance(c,Node):
    if c.tag==tag:found.append(c)
    if recursive:found.extend(c.find_all(tag))
  return found
 def match(self,t):
  bits=t.split('.');return (not bits[0] or self.tag==bits[0]) and all(x in self.attrs.get('class','').split() for x in bits[1:])
 def descendants(self):
  for c in self.children:
   if isinstance(c,Node):yield c;yield from c.descendants()
 def select(self,selector):
  parts=selector.replace('>',' > ').split();current=[self];direct=False
  for part in parts:
   if part=='>':direct=True;continue
   found=[]
   for n in current:
    candidates=(c for c in n.children if isinstance(c,Node)) if direct else n.descendants()
    found.extend(c for c in candidates if c.match(part))
   current=found;direct=False
  return current
 def select_one(self,selector):return self.select(selector)[0]
class Parser(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.root=Node();self.stack=[self.root]
 def handle_starttag(self,tag,attrs):
  node=Node(tag,attrs);self.stack[-1].children.append(node)
  if tag not in ('meta','link','br','hr','img','input'):self.stack.append(node)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==tag:self.stack=self.stack[:i];break
 def handle_data(self,data):self.stack[-1].children.append(data)
def BeautifulSoup(raw,parser):
 p=Parser();p.feed(raw);return p.root
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',default='docs/flasher/shortcut-guide.html')
parser.add_argument('--output',default='output/pdf/Model-Cycles-Features-and-Shortcuts.pdf')
parser.add_argument('--test',action='store_true')
parser.add_argument('--test-version',default='v7')
parser.add_argument('--no-publish',action='store_true')
args=parser.parse_args()
soup=BeautifulSoup((ROOT/args.source).read_text(encoding='utf-8'),'html.parser')
# Le PDF anglais prend le meme article canonique que la page bilingue.
def english_only(node):
 children=[]
 for c in node.children:
  if isinstance(c,Node):
   if c.attrs.get('data-l')=='fr':continue
   english_only(c)
   if c.tag=='article' and c.attrs.get('data-l')=='en':children.extend(c.children);continue
  children.append(c)
 node.children=children
english_only(soup)
ink=colors.HexColor('#202820');accent=colors.HexColor('#36563e');line=colors.HexColor('#c7cfc5')
styles={
 'title':ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=22,leading=25,textColor=ink,spaceAfter=4),
 'sub':ParagraphStyle('sub',fontName='Helvetica',fontSize=8.2,leading=11,textColor=colors.HexColor('#566256'),spaceAfter=9),
 'section':ParagraphStyle('section',fontName='Helvetica-Bold',fontSize=10,leading=12,textColor=accent,spaceBefore=9,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='Helvetica',fontSize=7.3,leading=9.2,textColor=ink),
 'cell':ParagraphStyle('cell',fontName='Helvetica',fontSize=7.1,leading=8.8,textColor=ink),
 'label':ParagraphStyle('label',fontName='Helvetica-Bold',fontSize=7.2,leading=8.8,textColor=ink),
}
def text(node):
 t=node.get_text(' ',strip=True) if hasattr(node,'get_text') else str(node)
 t=t.translate({0x2013:45,0x2014:45,0x2011:45,0x2019:39,0x2018:39,0x2192:62})
 for old,new in [('â€“','-'),('â€”','-'),('â€™',"'"),('\u00a0',' ')]:t=t.replace(old,new)
 return escape(' '.join(t.split()))
def para(node,style='body'):
 value=text(node)
 if style=='label' and 'MIDI Out machine only' in value:value=value.replace('MIDI Out machine only','<br/><font size="6.6">MIDI Out machine only</font>')
 if hasattr(node,'attrs') and 'card' in node.attrs.get('class','').split():
  heading=node.find_all('b')[0].get_text();value='<b>'+escape(heading)+'</b><br/>'+value[len(escape(heading)):].strip()
 return Paragraph(value,styles[style])
def section(title):return Paragraph(title,styles['section'])
def table(node):
 rows=[]
 for tr in node.select('tbody tr'):
  cells=tr.find_all('td',recursive=False)
  rows.append([para(c,'label' if i==0 else 'cell') for i,c in enumerate(cells)])
 head=[Paragraph('<b>'+text(v)+'</b>',styles['cell']) for v in node.find_all('th')]
 t=Table([head]+rows,colWidths=[87,166,299],repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7ede4')),('LINEBELOW',(0,0),(-1,0),.6,accent),('LINEBELOW',(0,1),(-1,-1),.35,line),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
 return t
flow=[Paragraph('Supermodel Edition',styles['title']),Paragraph('Model:Cycles | '+('MIDI-input test '+args.test_version+' - no-filter / P-O-N' if args.test else 'Supermodel 2.17 - Features and shortcut guide'),styles['sub']),para(soup.select_one('main > p')),Spacer(1,7)]
cards=soup.select('.grid .card');grid=[]
for i in range(0,len(cards),2):grid.append([para(n) for n in cards[i:i+2]])
ct=Table(grid,colWidths=[276,276]);ct.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f0f3ed')),('BOX',(0,0),(-1,-1),.4,line),('INNERGRID',(0,0),(-1,-1),.3,line),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));flow.append(ct)
headings=soup.select('main > h2');tables=soup.select('main > table')
pages=4
for h,t in zip(headings[1:],tables):
 title=text(h)
 if title in ('Effects and Elder','LFO and MACRO controls','Mod Setup'):
  flow.extend([PageBreak(),Paragraph(title,styles['title']),Paragraph('Supermodel 2.17 - Feature and shortcut reference',styles['sub'])])
 else:flow.append(section(title))
 if title=='Mod Setup':flow.extend([para(soup.select_one('p.mod-setup-intro')),Spacer(1,8)])
 flow.append(table(t))
 if title=='Mod Setup':flow.extend([Spacer(1,8),para(soup.select_one('p.mod-setup-save'))])
flow.extend([Spacer(1,9),para(soup.select_one('main > p.note'))])
out=ROOT/args.output;out.parent.mkdir(exist_ok=True,parents=True)
def chrome(c,doc):
 c.setFillColor(accent);c.setFont('Helvetica-Bold',7);c.drawString(30,773,'SUPERMODEL EDITION | MODEL:CYCLES');c.setFont('Helvetica',7);c.drawRightString(582,773,f'Page {doc.page} / {pages}')
 c.setStrokeColor(line);c.line(30,25,582,25);c.setFont('Helvetica',6.5);c.drawString(30,15,'Features and shortcuts | 22 October 2026');c.drawRightString(582,15,'Stk = Stock | Startup: USB 2ch, numbers Off')
doc=SimpleDocTemplate(str(out),pagesize=letter,rightMargin=30,leftMargin=30,topMargin=36,bottomMargin=34,title='Supermodel Edition - Features and Shortcuts',author='A.V.')
doc.build(flow,onFirstPage=chrome,onLaterPages=chrome)
r=PdfReader(out);assert len(r.pages)==pages,len(r.pages)
alltext=' '.join(' '.join(p.extract_text().split()) for p in r.pages)
for term in ('PLAY advances','STOP moves back','Mute: LTC','Num Off','harmony locks','sample browser must be open'):assert term in alltext,term
for term in ('Elder', 'Chorus I', 'Chorus II', 'Crush', 'Both', 'Rate 0', 'Bits 2', 'nine knobs', 'Glycinate', 'Fors'):assert term in alltext,term
for term in ('Channel','Output','KbT','Pad Note','Two MIDI LFOs','MIDI Out machine'):assert term in alltext,term
if pages>=3:
 for term in ('DX', 'LTC', 'SIL', 'Mod Setup','Stk / SIL','2ch / 6ch','Off / On','Stk / LTC','Stk / Div','global preferences','save waits until it stops'):assert term in alltext,term
for term in ('Model-TG','Model TG','B-side'):assert term not in alltext,term
if args.test:
 for term in ('MIDI keyboard recording','P / O / N','note-off removes'):assert term in alltext,term
elif not args.no_publish:
 (ROOT/'docs/flasher/shortcut-guide.pdf').write_bytes(out.read_bytes())
print('PASS:',pages,'page PDF, MIDI Out controls and guide tables verified:',out)

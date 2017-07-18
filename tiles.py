import requests
import ui
import math
import shortest
from PIL import Image, ImageDraw, ImageFont
from StringIO import StringIO
from fpdf import FPDF

class pdfmap():
	def __init__(self,dpi=160,a4x=11.69,a4y=8.27,zoom=16,centre=(52.4815,-1.9132),BASEURL="http://c.tile.openstreetmap.org/"):
		dpi=160
		a4x,a4y=11.69,8.27
		self.tilex,self.tiley=int((a4x*dpi)/256.0),int((a4y*dpi)/256)
		self.WIDTH,self.HEIGHT=self.tilex*256,self.tiley*256 #but based on centre point
		self.BASEURL=BASEURL
		self.zoom=zoom
		self.centre=centre
		self.createpdf()
		
	def createpdf(self):	
		img=self.tilesa4()
		img.show()
		img.save('testimg.png')
		pdf = FPDF('L', 'mm', 'A4')
		pdf.add_page()
		pdf.set_font('Arial', 'B', 16)
		pdf.cell(40, 10, 'Hello World!')
		pdf.image('testimg.png', 23.5,20,250)
		pdf.output('tuto1.pdf', 'F')

	def tilesa4(self):
		tilecentre=deg2num(self.centre[0],self.centre[1],self.zoom)
		master=Image.new('RGB',(((self.tilex+2)*256),((self.tiley+2)*256)),'White')
		degrees=[]
		for x in range(self.tilex+2):
			for y in range(self.tiley+2):
				#print x-((tilex/2)+1)
				tx=tilecentre[0]+x-int(((self.tilex)/2)+1)
				ty=tilecentre[1]+y-int(((self.tiley)/2)+1)
				part=getmeimagetiles(self.BASEURL,tx,ty,self.zoom)
				degrees.append(num2deg(tx,ty,self.zoom))
				master.paste(part,(x*256,y*256))
		adjx=256+(tilecentre[2]-128)
		adjy=256+(tilecentre[3]-128)
		nx=adjx+((tilecentre[0]-int(((self.tilex)/2)+1))*256)
		ny=adjy+((tilecentre[1]-int(((self.tiley)/2)+1))*256)
	
		#crop
		crp=master.crop((0+adjx,0+adjy,self.WIDTH+adjx,self.HEIGHT+adjy))
		draw=ImageDraw.Draw(crp)
		
		#isochrones
		ike=master.load()
		i=self.isochrones(num2deg(nx/256.0,(ny+self.HEIGHT)/256.0,self.zoom),num2deg((nx+self.WIDTH)/256.0,ny/256.0,self.zoom))
					
		#draw centre
		draw.ellipse(((self.WIDTH/2)-20, (self.HEIGHT/2)-20,(self.WIDTH/2)+20,(self.HEIGHT/2)+20), fill = 'yellow', outline ='blue')
		
		#draw grid
		font = ImageFont.truetype('Arial', 20)
		for x in range(self.tilex+2):
			draw.line(((x*256,0),(x*256,self.HEIGHT-1)),fill='black',width=1)
			draw.text(((x*256)+128,30),unichr(65+x),fill='black', font=font)
		for y in range(self.tiley+2):
			draw.line(((0,y*256),(self.WIDTH-1,y*256)),fill='black',width=1)		
			draw.text((30,(y*256)+128),str(y+1),fill='black', font=font)
		tps=[[3,6],[10,4],[15,2]]
		for n in tps:
			wdth=n[0]
			fat=n[1]
			draw.line(((wdth,wdth),(self.WIDTH-wdth,wdth)),fill='black',width=fat)
			draw.line(((wdth,wdth),(wdth,self.HEIGHT-wdth)),fill='black',width=fat)
			draw.line(((self.WIDTH-wdth,wdth),(self.WIDTH-wdth,self.HEIGHT-wdth)),fill='black',width=fat)
			draw.line(((wdth,self.HEIGHT-wdth),(self.WIDTH-wdth,self.HEIGHT-wdth)),fill='black',width=fat)
			
		return crp
		
	def isochrones(self,x,y):
		print x,y
		print 'downloading ways'
		osmdata=shortest.osmcreate(x,y)
		start=deg2num(x[0],x[1],self.zoom)
		finish=deg2num(y[0],y[1],self.zoom)
		print start,finish
		stc=(((start[0]*256)+start[2]),((start[1]*256)+start[3]))
		ftc=(((finish[0]*256)+finish[2]),((finish[1]*256)+finish[3]))
		cenx=((ftc[0])-stc[0])/2
		ceny=((stc[1])-ftc[1])/2
		print 'download complete'
		edges,nodes=shortest.OsmRouteImport(osmdata)
		startnode=shortest.findclosest(nodes,self.centre[0],self.centre[1])
		pixels=[]
		for n in shortest.Dijkstra(edges,startnode[1],0):
			xx,yy=nodes[n[0]]
			result=deg2num(xx,yy,self.zoom)
			pixels.append([(result[0]*256)+result[2],(result[1]*256)+result[3],n[0],n[1],n[2]])
		
		minx=map(min,zip(*pixels))
		maxx=map(max,zip(*pixels))
		miny=min(pixels, key=lambda x:x[1])
		maxy=max(pixels, key=lambda x:x[1])
		coffx=(cenx+stc[0])-minx[0]
		coffy=(ceny+ftc[1])-miny[1]
		
		pic=Image.new('RGB',(maxx[0]-minx[0],maxy[1]-miny[1]),'White')
		draw=ImageDraw.Draw(pic)
		selected=[]
		for n in pixels:
			if n[3]>.7>n[4]:
				a=n[0]-minx[0]
				b=n[1]-miny[1]
				c=math.sqrt(((a-coffx)**2)+((b-coffy)**2))
				v1 = math.atan2(coffx-a,coffy-b)
				r = (v1) * (180.0 / math.pi)
				selected.append([a,b,c,r])
		print selected
		selected.sort(key=lambda x: float(x[3]))
		lenj=len(selected)
		ctr=0
		elm=0
		for n in selected:
			elm+=n[2]
		final=[]
		for n in iter(selected):
			if n[2]>((elm/lenj)/1.5):
				final.append((n[0],n[1]))
				draw.ellipse(((n[0])-20, (n[1])-20,(n[0])+20,(n[1])+20), fill =(int((ctr/lenj)*256),int((ctr/lenj)*256),int((ctr/lenj)*256)), outline ='blue')
			ctr+=1.0
		draw.polygon(final,fill='cyan',outline='red')
		draw.ellipse((coffx-20, coffy-20,coffx+20,coffy+20), fill = 'blue', outline ='yellow')
		pic.show()
		return pic
	
	
def deg2num(lat_deg,lon_deg,zoom):
	#from osm wiki
	lat_rad = math.radians(lat_deg)
	n = 2.0 ** zoom
	xtile = ((lon_deg +180.0)/360.0 *n)
	ytile = ((1.0 - math.log(math.tan(lat_rad)+(1/math.cos(lat_rad)))/math.pi)/2.0 *n)
	xrem=int((xtile%1)*256)
	yrem=int((ytile%1)*256)
	xtile=int(xtile)
	ytile=int(ytile)
	return (xtile,ytile,xrem,yrem)
	
def num2deg(xtile, ytile, zoom):
	n = 2.0 ** zoom
	lon_deg = xtile / n * 360.0 - 180.0
	lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
	lat_deg = math.degrees(lat_rad)
	return (lat_deg, lon_deg)
	

def getmeimagetiles(BASEURL,a,b,zoom):
	url=BASEURL+str(zoom)+"/"+str(a)+"/"+str(b)+".png"
	#print url
	response=requests.get(url)
	img=Image.open(StringIO(response.content)).convert("RGB")
	return img

pdfmap(zoom=14)

#16 256,256
#15 256+128,128
#14 512-64,64
#13 256,32

#from pycoingecko import CoinGeckoAPI
from IPython.display import display, clear_output
from IPython.display import Image
import datetime, time, glob
import pandas as pd
import random, pickle
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import ipywidgets as ipw
import plotly.figure_factory as ff
from ipywidgets import interact, widgets

# %%
from datetime import timedelta
from datetime import datetime
class dateprice:
    def __init__(self,strdate):
        self.strdate = strdate
        self.date_time_obj = None
        
    def convertformat(self):
        self.date_time_obj = datetime.strptime(self.strdate, "%m/%d/%Y")
    
    def addDay(self):
        self.date_time_obj = self.date_time_obj + timedelta(days=1)
        #datex = self.date_time_obj.strftime("%m/%d/%Y  %H:%M:%S")
        dayx = str(self.date_time_obj.date().strftime("%m/%d/%Y"))
        return dayx

# %%
class priceHistorical:
    def __init__(self,symbol,simiters,startsToday=True):
        self.startsToday = startsToday
        self.callno = 0
        self.gotindex = -1
        self.valid = 0
        self.fprefix = "tickerdata/"
        #self.pricedata = pd.read_pickle("pricevectors.pkl")
        symupper = symbol.upper()
        #fname = "tickerdata/"+ symupper +".csv"
        fname = self.fprefix + symupper +".csv"
        stockdata = pd.DataFrame(pd.read_csv(fname))  
        
        if self.is_integer(simiters)==True:
            if self.startsToday==True:
                self.callno = simiters
            else:
                self.callno = 0
        else:
            indx = stockdata.index[stockdata['Date']==simiters]
            if len(indx)==1:
                self.valid=1
                if self.startsToday==True:
                    self.gotindex = indx[0]
                    self.callno = indx[0]
        self.newdata = stockdata[['Date',' Close/Last',' Volume']]
            
    def getCallno(self):
        return self.gotindex
            
    def is_integer(self,n):
        try:
            float(n)
        except ValueError:
            return False
        else:
            return float(n).is_integer()
        
    def defineColumnNames(self):
        close = None
        date = None
        volume = None

    def getPrice(self):
        price = float(self.newdata.loc[self.callno][' Close/Last'][2:])
        datex = self.newdata.loc[self.callno]['Date']
        volume = self.newdata.loc[self.callno][' Volume']
        if self.startsToday==True:
            self.callno-=1
        else:
            self.callno+=1
        return [datex,price,volume]

class tickerPriceLayer:
    def __init__(self, tikr,simno):
        self.ticker = tikr
        self.eblogo = Image(filename='assets/images/dovizdark.png')
        self.priceVectors, self.volumeVectors, self.movingVectors = None, None, None
        self.priceTrackers = ['date','price']
        self.volumeTrackers = ['volume']
        self.movingaverageTrackers = ['date']
        self.priceIndices, self.volumeIndices, self.movingIndices = None, None, None
        #self.pricemodule = priceLocal(tikr)
        self.pricemodule = priceHistorical(tikr,simno)
        self.globalTimeID = 0
        self.indexhere = 0
        self.lprice = 0
        self.datex = None
        self.hmap = []
        self.prices50day = []
        self.movingAvgDaily = []
        self.priceavailable = 0
        #self.tickerStatus = 0
        
    def gettickerStatus(self):
        return self.pricemodule.valid
        
    def printPriceVectors(self):
        print("\nPriceLayer",self.ticker)
        print(self.priceVectors)
        
    def assignTimeContext(self,tclist):
        #tclist = [-1,-3,-5,-10,-20]
        self.priceIndices = tclist
        for tc in tclist:
            self.priceTrackers.append('change_'+str(-tc))
        self.priceVectors = pd.DataFrame(columns=self.priceTrackers)
        #print("Assigning priceVectors!")
        
    def addMovingAverage(self,mvlist):
        self.movingIndices = mvlist
        for mv in mvlist:
            self.movingaverageTrackers.append('moving_'+str(mv))
        self.movingVectors = pd.DataFrame(columns=self.movingaverageTrackers)
        #print("Assigning Moving average trackers!")
        
    def assignVolumeContext(self,vback=None):
        if vback is not None:
            self.volumeIndices = vback
            for vc in vback:
                self.volumeTrackers.append('volume_'+str(-vc))
        self.volumeVectors = pd.DataFrame(columns=self.volumeTrackers)
        #print("Assign volume Vectors!")
    
    def updateWithLatestPrice(self):
        self.datex, self.lprice, self.volume = self.pricemodule.getPrice()
        #print("inedxhere/lprice", self.indexhere, self.lprice)
        #compute price vector
        pvec = [self.datex,self.lprice]
        vvec = [self.volume]
        mvec = [self.datex]
        
        for mindx in self.movingIndices:
            data50day = self.priceVectors[-50:]['price']
            #print("data50day",data50day)
            try:
                avg50d = np.nanmean(data50day)
            except:
                avg50d = None
            mvec.append(avg50d)
        self.movingVectors.loc[self.indexhere]=mvec
        
        for indx in self.priceIndices:
            if self.indexhere+indx>0:
                pvec.append((self.lprice/float(self.priceVectors.loc[self.indexhere+indx]['price'])-1)*100)
            else:
                pvec.append(None)        
        self.priceVectors.loc[self.indexhere]=pvec
        
        if len(self.hmap)>49:
            self.hmap.pop()
        if pvec[2] is not None:    
            self.hmap.insert(0,1-pvec[2])
        
        if self.volumeIndices is not None:
            for vindx in self.volumeIndices:
                if self.indexhere+vindx>=0:
                    vvec.append(self.volume/float(self.volumeTrackers.loc[self.indexhere+indx]['volume']))
                else:
                    vvec.append(None)
        self.volumeVectors.loc[self.indexhere]=vvec
        self.indexhere+=1
        
    def displayPriceVectorData(self,themex,last=250,priceonly=False):
        changeheatmap = []
        displayData = self.priceVectors[-last:]
        movingAverageData = self.movingVectors[-last:]
        volumeData = self.volumeVectors[-25:]        
        color1slot = [self.getcolor(d) for d in displayData['change_1']]
        size1slot = [self.getsize(d) for d in displayData['change_1']]
        if priceonly==False:
            figure_pricechange = make_subplots(rows=2, cols=2, subplot_titles=('Price','Price Velocity($/day)','Volume','49day Change Heatmap'))
            figure_pricechange.add_scatter(x=displayData['date'],y=displayData['price'], mode="lines", name=self.ticker, row=1, col=1)
            figure_pricechange.add_scatter(x=movingAverageData['date'],y=movingAverageData['moving_50'], mode="lines", name="mavg_" + self.ticker, line_color='#7f7f7f',row=1, col=1)
            figure_pricechange.add_scatter(x=displayData['date'],y=displayData['price'], mode="markers", marker=dict(size=size1slot, color=color1slot),  name = "direction", row=1, col=1)        
            figure_pricechange.add_scatter(x=displayData['date'],y=displayData['change_1']-1, mode="lines", marker=dict(size=size1slot, color=color1slot), name = "change_"+ self.ticker, row=1, col=2)
            figure_pricechange.add_bar(y=volumeData['volume'], text="Volume", name = "volume", row=2, col=1)         
            if len(self.hmap)>49:
                for j in range(7):
                    chunkch = []
                    for k in range(7):
                        try:
                            pindx = j*7+k
                            chunkch.insert(0,self.hmap[pindx])
                        except:
                            chunkch.insert(0,None)
                    changeheatmap.append(chunkch)
                fig = ff.create_annotated_heatmap(changeheatmap, colorscale='RdYlGn')
                figure_pricechange.add_trace(fig.data[0],2,2)     
            ttext = "<🦤Simulator> TIKR : " + self.ticker.upper() + " -- Date:" + str(self.datex) + " -- $" + str(self.lprice) 
            figure_pricechange.update_layout(height=750, width=750,title_text=ttext,template="plotly_dark")  
        else:
            figure_pricechange = make_subplots(rows=1, cols=1, subplot_titles=('Price'))
            figure_pricechange.add_scatter(x=displayData['date'],y=displayData['price'], mode="lines", row=1, col=1)
            #figure_pricechange = go.scatter(x=displayData['date'],y=displayData['price'], mode="lines")
            figure_pricechange.add_scatter(x=movingAverageData['date'],y=movingAverageData['moving_50'], mode="lines", line_color='#7f7f7f',row=1, col=1)
            ttext = "<🦤Simulator> tikr : " + self.ticker.upper() + " -- Date:" + str(self.datex) + " -- $" + str(self.lprice) 
            figure_pricechange.update_layout(height=500, width=750,title_text=ttext,template=themex)  
        return figure_pricechange
    
    def getPriceData(self,last,colx):
        displayData = self.priceVectors[-last:]
        return [displayData['date'], displayData[colx]]
    
    def getMovingAverageData(self,last):
        movingAverageData = self.movingVectors[-last:]
        return movingAverageData
    
    def getPriceVectorData(self,last):
        displayData = self.priceVectors[-last:]
        return displayData[['price','change_1']]
    
    def getcolor(self,dx):
        if dx is None:
            return 'blue'
        if dx==0:
            return 'yellow'
        elif dx>0:
            return 'green'
        else:
            return 'red'
        
    def getsize(self,dx):
        if dx is None:
            return 3
        if dx==0:
            return 3
        elif dx>0:
            return 4
        else:
            return 4

class priceDataLayer:
    def __init__(self,simdays,sleeptime):
        #print("Starting a price data layer")
        self.tickers = []
        self.temporaryPriceLayers = []
        self.tickerPriceLayers = []
        self.plotstoshow = ['price','change_1']
        self.steps = 250
        self.sleeptime=sleeptime
        self.dovislogo_dark = Image(filename='assets/images/dovizdark.png')
        self.dovislogo_light = Image(filename='assets/images/doviz.png')
        self.simdays = simdays
        self.plotlytheme = False
        self.selectedTickers = None
        self.menuglobal = None
        self.butt, self.outt, self.textbox = None, None, None
                    
    def is_integer(self,n):
        try:
            float(n)
        except ValueError:
            return False
        else:
            return float(n).is_integer()
        
    def setDarkMode(self,dm):
        if dm:
            self.plotlytheme = "plotly_dark"
        else:
            self.plotlytheme = "plotly"
        
    def addTickers(self,tikrlist,tclist):
        self.tickers = tikrlist
        if self.is_integer(self.simdays)==True:
            simstat = 1
        else:
            simstat = 0
        for tikr in self.tickers:
            self.temporaryPriceLayers.append(tickerPriceLayer(tikr.lower(),self.simdays))
        indexa=0
        for tmpl in self.temporaryPriceLayers:
            if tmpl.gettickerStatus()==1:
                if simstat==0:
                    indexa = max(indexa,tmpl.pricemodule.gotindex)
                    #print(indexa)
                    simstat=1
                self.tickerPriceLayers.append(tmpl)
            else:
                print("Price data for",tmpl.ticker,"not available! Removing Ticker!")
        if indexa!=0:
            self.simdays = indexa
        #print("self.simdays",self.simdays)
        for tpl in self.tickerPriceLayers:
            tpl.assignTimeContext(tclist)
            tpl.assignVolumeContext(None) 
            tpl.addMovingAverage([50])         
            
    def getalltickers(self):
        alltickers = []
        for el in glob.glob("tickerdata/*.csv"):
            tmp = el.split("\\")[1]
            finx= tmp.split(".")[0]
            alltickers.append(finx)
        return alltickers
    
    # creating menu with them   
    def createMenuItem(self):
        self.menuglobal = widgets.SelectMultiple(
            options=self.getalltickers())
        # button, output, function and linkage
        self.butt = widgets.Button(description='Select Tickers!')
        self.outt = widgets.Output()
        self.textbox = widgets.Text(
            value='last',
            placeholder='Enter Simulation start date!',
            description='Enter Date to start Simulation!:',
            disabled=False
        )
            
    def assignselected(self,stickers):
        print("stickers",stickers)
        global selectedTickers
        selectedTickers = stickers

    def on_butt_clicked(self,b):
        with self.outt:
            clear_output()
            self.selectedTickers = list(self.menuglobal.value)
            #assignselected(selectedTickers)
            
    def callback(self,wdgt):
        datex = wdgt.value
        if self.simdays is None:
            for tikr in self.selectedTickers:
                self.temporaryPriceLayers.append(tickerPriceLayer(tikr.lower(),self.simdays))
        indexa=0
        for tmpl in self.temporaryPriceLayers:
            if tmpl.gettickerStatus()==1:
                if simstat==0:
                    indexa = max(indexa,tmpl.pricemodule.gotindex)
                    #print(indexa)
                    simstat=1
                self.tickerPriceLayers.append(tmpl)
            else:
                print("Price data for",tmpl.ticker,"not available! Removing Ticker!")
        if indexa!=0:
            self.simdays = indexa
        #print("self.simdays",self.simdays)
        for tpl in self.tickerPriceLayers:
            tpl.assignTimeContext([-1])
            tpl.assignVolumeContext(None) 
            tpl.addMovingAverage([50])       
        #pdl = self.priceDataLayer(datex,1)
        #pdl.setDarkMode(True)
        #pdl.addTickers(selectedTickers,[-1]) #tickerpricelayerdays
        print("self.simdays", self.simdays)
        self.visualize("priceonly")
        
    def visualizeEasy(self):
        self.createMenuItem()
        #dovislogo = Image(filename='assets/images/doviz.png')
        display(self.eblogo)
        self.textbox.on_submit(self.callback)
        self.butt.on_click(self.on_butt_clicked)
        display(widgets.VBox([self.menuglobal,self.butt,self.outt,self.textbox]))

    def updateAllTickers(self):
        for tpl in self.tickerPriceLayers:
            tpl.updateWithLatestPrice()
            
    def printAllTickerPriceLayers(self):
        for tpl in self.tickerPriceLayers:
            tpl.printPriceVectors()     
            
    def visualize(self,typex="priceonly",plotsx=None):
        #print("simulate called with self.simdays", self.simdays)
        if typex=="priceonly":
            if plotsx is not None:
                self.plotstoshow = plotsx
            if self.is_integer(self.simdays)==True:
                for j in range(self.simdays):
                    if self.plotlytheme=="plotly":
                        display(self.dovislogo_light)
                    else:
                        display(self.dovislogo_dark)
                    self.updateAllTickers()
                    if 'price' in self.plotstoshow:
                        self.getpricevectorsalltickers(j,self.steps,True,'price')
                    if 'change_1' in self.plotstoshow:
                        self.getpricevectorsalltickers(j,self.steps,True,'change_1')
                    time.sleep(self.sleeptime)
                    clear_output(wait = True)
            else:
                print("This day is UNTRADED! Add or suntract a day!")
        else:
            if self.is_integer(self.simdays)==True:
                for j in range(self.simdays):
                    if self.plotlytheme=="plotly":
                        display(self.dovislogo_light)
                    else:
                        display(self.dovislogo_dark)
                    self.updateAllTickers()
                    self.getpricevectorsalltickers(j,self.steps,False,None)
                    time.sleep(self.sleeptime)
                    clear_output(wait = True)
            else:
                print("This day is UNTRADED! Add or suntract a day!")
            
    def getpricevectorsalltickers(self,simno,last,priceonly,colx):
        pvd = []
        if priceonly is False:
            for tpl in self.tickerPriceLayers:
                tpl.displayPriceVectorData(self.plotlytheme,last,False).show()
        else:
            dateList = None
            if colx=='price':
                cname = [str(colx)+" ($)"] 
            else:
                cname = [str(colx)+" ($/Step)"] 
            combinedPrice = make_subplots(rows=1, cols=1, subplot_titles=(cname))
            priceshere = []
            for tpl in self.tickerPriceLayers:
                dateprice = tpl.getPriceData(500,colx)  
                mavg = tpl.getMovingAverageData(500)            
                dateList = dateprice[0]
                priceList = dateprice[1]
                tkrs = ",".join(self.tickers)
                priceshere.append(str(tpl.lprice))
                pricesShow = "/ ".join(priceshere)
                combinedPrice.add_scatter(x=dateList, y=priceList, mode="lines", name = tpl.ticker.upper(), row=1, col=1)
                if colx=='price':
                    combinedPrice.add_scatter(x=mavg['date'], y=mavg['moving_50'], mode="lines", name="mavg_"+tpl.ticker.upper(), line_color='#7f7f7f',row=1, col=1)
                ttext = "<🦤vizualizer> : " + tkrs.upper() + " -- Date:" + str(tpl.datex) + " -- $:" + pricesShow 
                combinedPrice.update_layout(height=500, width=780,title_text=ttext,template=self.plotlytheme)
            combinedPrice.show()
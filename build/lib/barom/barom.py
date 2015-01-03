# -*- coding: utf-8 -*-

# Barom -- A utility for tracking altitude/predicting weather
#
# Copyright (C) 2011 Benjamin Deering <ben_deering@swissmail.org>
# http://jeepingben.homelinux.net/barom/
#
# This file is part of Barom.
#
# Barom-chooser is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Barom-chooser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 
import sys, os, signal, math
from time import time
import elementary, evas, ecore
import ConfigParser
from collections import deque
from threading import Lock
from const import *

class pressureGraphUpdater( ):
	def __init__ (self, getPressure, graphFrame, usingMetric):
		
		self.getPressure = getPressure
		self.graphFrame = graphFrame
		self.maxLabel = self.graphFrame.evas.Text(color=(25,25,25,255),font=("sans serif", 12))
		self.minLabel = self.graphFrame.evas.Text(color=(25,25,25,255),font=("sans serif", 12))
		
		self.enabled = 1
		self.daemon = False
		self.die = False
		try:
			self.lastPres = self.getPressure(self)
		except:
			self.lastPres = 1010.0
		self.maxPres = 1013.0
		self.minPres = 1000.0
		self.usingMetric = usingMetric
	
		#sizeY = self.graphFrame.data["bg"].size[1]
		
		self.bottomY = 550
		self.topY = 230
		self.sizeY = self.bottomY - self.topY
		self.numPts = 88 * 2
		self.numScreenPts = 88
		self.rightX = 460
		self.leftX = 15
		self.updatePeriod = 200
		self.Xdim = float((self.rightX - self.leftX)/self.numScreenPts)
		
		self.pressureVals	= deque(maxlen = self.numPts)	
		self.lines = [self.graphFrame.evas.Line(color=(255,0,0,255)) for i in range(self.numScreenPts)]
		
		self.setLabels()		
		self.maxLabel.move(self.leftX,self.topY)
		self.maxLabel.show()
		self.maxLabel.clip_set(self.graphFrame.data["bg"])		
		
		self.minLabel.move(self.leftX,self.bottomY)
		self.minLabel.show()
		self.minLabel.clip_set(self.graphFrame.data["bg"])
		self.durLabel = self.graphFrame.evas.Text(color=(25,25,25,255),font=("sans serif", 12))
		self.durLabel.text = "Past " + "{0:.2f}".format( self.updatePeriod * self.numScreenPts / 3600.0) + "hrs"
		self.durLabel.layer_set(3)
		self.durLabel.move((self.rightX - self.leftX)/2.0,self.topY)
		self.durLabel.show()
		self.durLabel.clip_set(self.graphFrame.data["bg"])
		for i in range(self.numScreenPts):
			self.lines[i].layer_set(2)	
			self.lines[i].clip_set(self.graphFrame.data["bg"])
		self.pressureVals.appendleft( self.lastPres )
		self.lastSampleTime = time()
	def pressureGraphUpdate(self):
		if time() - self.lastSampleTime < self.updatePeriod:
			return True
		lastline = self.lines[self.numScreenPts - 1]
		try:
			curPres = self.getPressure(self)
		
			self.pressureVals.appendleft( curPres )
			
			if curPres > self.maxPres or curPres <self.minPres:
				self.rerange()
				
						
			curTime = time() 
			x2 = self.rightX - (self.Xdim * round((curTime - self.lastSampleTime)/float(self.updatePeriod)))
			lastXdim = self.rightX - x2
			self.lastSampleTime = curTime	
			
			for i in range( self.numScreenPts - 1  ):
				try:
						j = self. numScreenPts - i
						#print str(i) + " " + str(j)+ " : " + str( self.pressureVals[j] )
						y2 = self.topY + (self.maxPres - self.pressureVals[j-1])/(self.maxPres - self.minPres)*self.sizeY 	
						y1 = self.topY + (self.maxPres - self.pressureVals[j])/(self.maxPres - self.minPres)*self.sizeY
						#print "y1: " + str(y1)
						#print "y2: " + str(y2)
						if self.lines[i+1 ].visible_get() == True:
							next_xys = self.lines[i+1].xy_get()
							#print "nextxys: " + str( next_xys )
						
							self.lines[i].xy_set( next_xys[0] - lastXdim  , y2, next_xys[2] - lastXdim, y1 )
							#print "new line[" + str(i) +"]: " + str(self.lines[i].xy_get())
							self.lines[i].show()
				
						else:
							self.lines[i].hide()				
				except:
						self.lines[i].hide()
		except:
				print "Failed to get pressure\n"
		y1 = self.topY + (self.maxPres - self.lastPres)/(self.maxPres - self.minPres)*self.sizeY 	
		y2 = self.topY + (self.maxPres - curPres)/(self.maxPres - self.minPres)*self.sizeY
		
		lastline.xy_set( self.rightX,y2, x2,y1)
		lastline.show()
		self.lastPres = curPres
		return True
	def rerange( self ):
		max = 0.0
		min = 3000.0
		for pres in self.pressureVals:
			if pres > max:
				max = pres
			if pres < min:
				min = pres
		self.maxPres = max + (max - min + 1)/3.0
		self.minPres = min - (max - min + 1)/3.0
		self.setLabels()
	def setUnits( self, usingMetric ):
		self.usingMetric = usingMetric
		self.setLabels()
	def setLabels(self):
		if( self.usingMetric ):
			self.maxLabel.text = "{0:.2f}".format(self.maxPres)
			self.minLabel.text = "{0:.2f}".format(self.minPres)
		else:
			self.maxLabel.text = "{0:.2f}".format(self.hpaToinHG(self.maxPres))
			self.minLabel.text = "{0:.2f}".format(self.hpaToinHG(self.minPres))
	def hpaToinHG(self, pressure):
		return (pressure / 33.86)
	def inHGtoHpa(self, pressure):
		return (pressure * 33.86)
	def enable( self ):
		self.enabled = 1
	def disable( self ):
		self.enabled = 0
	def terminate( self, *args, **kargs ):
		self.die = True	


class baromGUI(object ):
	def __init__ (self):
		self.usingMetric = False
		self.seaLevelPressure = 0
		self.altitudeLock = Lock()
		self.pressureLock = Lock()
		self.configfile = os.path.expanduser ('~/.barom.cfg')
		#print "Attempting to load config"
		self.config = ConfigParser.SafeConfigParser ()
		self.LoadConfig (self.configfile)
		#print "loaded config"
		self.widgets = self.build_gui()
		#print "built gui succesfully"
		self.widgets['mainwin'].show ()
		elementary.init()     
		elementary.run()                                            
		elementary.shutdown()   
	
	def interrupted (self, signal, frame):
		self.pressureLabelTimer.delete()
		self.altitudeLabelTimer.delete()
		self.pressureGraphTimer.delete()
		self.SaveConfig (self.configfile)
		elementary.exit ()
	def build_gui (self):

		def destroy (obj, *args, **kargs):
			try:
				self.pressureLabelTimer.delete()
				self.altitudeLabelTimer.delete()
				self.pressureGraphTimer.delete()
				self.SaveConfig (self.configfile)	
			except:
				print "Exception occured on exit"
			elementary.exit ()

		gui_items = dict ()

		

		# Create main window
		gui_items['mainwin'] = elementary.Window ("Barom", elementary.ELM_WIN_BASIC)
		gui_items['mainwin'].title_set ("Barom")
		gui_items['mainwin'].callback_destroy_add (destroy)

		# Create background
		bg = elementary.Background (gui_items['mainwin'])
		bg.size_hint_weight_set (1.0, 1.0)
		#bg.size_hint_min_set (200,300)
		gui_items['mainwin'].resize_object_add (bg)
		bg.show ()

		# Create main box (vertical by default)
		gui_items['mainbox'] = elementary.Box (gui_items['mainwin'])
		gui_items['mainbox'].size_hint_weight_set (1.0, 1.0)
		gui_items['mainbox'].size_hint_align_set (-1.0, -1.0)
		gui_items['mainwin'].resize_object_add (gui_items['mainbox'])
		gui_items['mainbox'].show ()
				
		#Create top toolbar
		toptoolbar = elementary.Toolbar(gui_items['mainwin'])
		toptoolbar.menu_parent_set(gui_items['mainwin'])
		toptoolbar.homogenous_set(False)			
		#toptoolbar.icon_size_set( 64 )                                          
		#toptoolbar.size_hint_align_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		#toptoolbar.size_hint_weight_set (1.0, 1.0)                                                            
		toptoolbar.size_hint_align_set (-1.0, 0.0)
		toptoolbar.item_append(os.path.join(IMAGE_DIR, 'altitude.png'), "Altitude", self.altitudeDialog)
		toptoolbar.item_append(os.path.join(IMAGE_DIR, "weather.png"), "Weather", self.weatherDialog)		
		toptoolbar.item_append(os.path.join(IMAGE_DIR, 'calibrate.png'), "Calibrate", self.calibrateDialog)
		toptoolbar.item_append(os.path.join(IMAGE_DIR, "about.png"), "About", self.aboutDialog)
		gui_items['mainbox'].pack_end( toptoolbar )
		toptoolbar.show()

		gui_items['pager'] = elementary.Naviframe (gui_items['mainwin'])
		gui_items['pager'].size_hint_weight_set (1.0, 1.0)
		gui_items['pager'].size_hint_align_set (-1.0, -1.0)
		
		
		
		# Create weather box (vertical by default)
		gui_items['weatherbox'] = elementary.Box (gui_items['mainwin'])
		gui_items['weatherbox'].size_hint_weight_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		gui_items['weatherbox'].size_hint_align_set (-1.0, -1.0)
		gui_items['pressureLabel'] = elementary.Label(gui_items['mainwin'])
		gui_items['pressureLabel'].text_set('weather')
		
		gui_items['pressureLabel'].scale_set(3.5)
		gui_items['pressureLabel'].size_hint_weight_set (1.0, 0.0)
		gui_items['pressureLabel'].size_hint_align_set (0.5, -1.0)
		gui_items['weatherbox'].pack_end( gui_items['pressureLabel'])
		gui_items['pressureLabel'].show()	
		
			
		# Include the graph of past pressures
		gui_items['graphframe'] = elementary.Frame(gui_items['mainwin'])
		
		sc = elementary.Scroller(gui_items['mainwin'])
		sc.bounce_set(0, 0)
		sc.size_hint_weight_set(evas.EVAS_HINT_EXPAND, 1.0)
		sc.size_hint_align_set(-1.0,-1.0)
		#gui_items['weatherbox'].pack_end(sc)
		gui_items['mainwin'].resize_object_add (sc)
		sc.show()

		gui_items['graphframe'].size_hint_weight_set (1.0, 1.0 )
		gui_items['graphframe'].size_hint_align_set (-1.0,-1.0)
		gui_items['graphframe'].show()
		
		graphcanvas = gui_items['graphframe'].evas
	
		bg = graphcanvas.Rectangle(color=(255,255,255,255))
		bg.size = (460, 380)
		bg.layer_set(1)
		gui_items['graphframe'].data["bg"] = bg
		#print "FrameSize: " + str(gui_items['graphframe'].size)
		bg.show()
		
		gui_items['graphframe'].content_set(bg)
		sc.content_set(gui_items['graphframe'] )
		#gb.pack_end(gui_items['graphframe'])
		gui_items['weatherbox'].pack_end(sc)
		
		self.pressureGraphThread = pressureGraphUpdater(self.getPressureFromSensor,gui_items['graphframe'],self.usingMetric )
		
		self.pressureLabelTimer = ecore.timer_add(2, self.PressureLabelUpdate)
		self.pressureGraphTimer = ecore.timer_add(2, self.pressureGraphThread.pressureGraphUpdate)
		
		gui_items['mainwin'].resize_object_add (gui_items['weatherbox'])
		gui_items['pager'].item_simple_push (gui_items['weatherbox'])
		#####
		# Create calibrate box (vertical by default)
		gui_items['calibratebox'] = elementary.Box (gui_items['mainwin'])
		
		gui_items['calibratebox'].size_hint_weight_set (1.0, 1.0)
		gui_items['calibratebox'].size_hint_align_set (-1.0,-1.0)
		
				
		# Create scroller to hold calibrate toggles items
		sc2 = elementary.Scroller(gui_items['mainwin'])
		sc2.bounce_set(0, 0)
		sc2.size_hint_weight_set(1.0, 1.0)
		sc2.size_hint_align_set(-1.0,-1.0)
		gui_items['calibratebox'].pack_end(sc2)
		gui_items['mainwin'].resize_object_add (sc2)
		sc2.show()
		
		tb = 	elementary.Box(gui_items['calibratebox'])
		tb.size_hint_weight_set(1.0, 1.0)
		tb.size_hint_align_set(-1.0,-1.0)
		
		ut = elementary.Check (gui_items['mainwin'])
		ut.style_set("toggle")
		ut.text_set('Units')
		ut.text_part_set( 'on', 'Metric' )
		ut.text_part_set( 'off', 'Imperial' )
		ut.size_hint_weight_set (1.0, 1.0)
		ut.size_hint_align_set (-1.0, 0.0)
		tb.pack_end( ut )
		ut.state_set(self.usingMetric)
		ut._callback_add('changed',self.setUnits)
		ut.show()

		al = elementary.Label(gui_items['mainwin'])
		al.text_set("Known current altitude")
		al.show()
		tb.pack_end(al)
		
		tbAlt = 	elementary.Box(gui_items['mainwin'])
		tbAlt.horizontal_set(1)
		gui_items['calibrateAltnumber'] = elementary.Entry(gui_items['mainwin'])            
		gui_items['calibrateAltnumber'].single_line_set(True)                     
		gui_items['calibrateAltnumber'].entry_set('XX')   
		gui_items['calibrateAltnumber'].scale_set(2.0)            
		gui_items['calibrateAltnumber'].size_hint_weight_set(1, 1)          
		gui_items['calibrateAltnumber'].callback_activated_add(self.calibrate) 
		                     
		tbAlt.pack_end(gui_items['calibrateAltnumber'])               
		gui_items['calibrateAltnumber'].show()
		
		gui_items['unitaltlabel'] = elementary.Label(gui_items['mainwin'])
					
		gui_items['unitaltlabel'].show()		
		tbAlt.pack_end(gui_items['unitaltlabel'])
		tbAlt.show()		
		tb.pack_end(tbAlt)
		
		pl = elementary.Label(gui_items['mainwin'])
		pl.text_set("Known current pressure at sea level")
		pl.show()
		tb.pack_end(pl)
		
		tbPres = 	elementary.Box(gui_items['mainwin'])
		tbPres.horizontal_set(1)
		
		gui_items['calibratePresnumber'] = elementary.Entry(gui_items['mainwin'])            
		gui_items['calibratePresnumber'].single_line_set(True)                     
		gui_items['calibratePresnumber'].entry_set('XX')   
		gui_items['calibratePresnumber'].scale_set(2.0)            
		gui_items['calibratePresnumber'].size_hint_weight_set(1, 1)          
		gui_items['calibratePresnumber'].callback_activated_add(self.calibrate)                      
		tbPres.pack_end(gui_items['calibratePresnumber'])               
		gui_items['calibratePresnumber'].show()
		
		gui_items['unitpreslabel'] = elementary.Label(gui_items['mainwin'])
					
		gui_items['unitpreslabel'].show()		
		tbPres.pack_end(gui_items['unitpreslabel'])
		tbPres.show()
		tb.pack_end(tbPres)
		
		if self.usingMetric:
		 	 gui_items['unitaltlabel'].text_set('m')
		 	 gui_items['unitpreslabel'].text_set('hpa')
		else:
		 	 gui_items['unitaltlabel'].text_set('ft')
		 	 gui_items['unitpreslabel'].text_set('in hg')	 	 
		 	 
		# Create the calibrate button
		bt = elementary.Button (gui_items['mainwin'])
		bt.text_set ('Calibrate')
		bt._callback_add ('clicked', self.calibrate)
		bt.size_hint_weight_set (1.0, 1.0)
		bt.size_hint_align_set (-1.0, 0.0)
		tb.pack_end (bt)
		bt.show ()		
		
		tbFile = 	elementary.Box(gui_items['mainwin'])
		tbFile.horizontal_set(1)
		#create the sensor name label
		fl = elementary.Label(gui_items['mainwin'])
		fl.text_set("location of the sensor sysfs file")
		fl.show()
		tb.pack_end(fl)
		# Create the sensor name Entry
		gui_items['pressureSensorFile'] = elementary.Entry(gui_items['mainwin'])            
		gui_items['pressureSensorFile'].single_line_set(True)                     
		gui_items['pressureSensorFile'].entry_set(self.pressureSensorFile)   
		gui_items['pressureSensorFile'].scale_set(1.0)            
		gui_items['pressureSensorFile'].size_hint_weight_set(1, 1)          
		gui_items['pressureSensorFile'].callback_activated_add(self.changeSensorFile)                      
		tbFile.pack_end(gui_items['pressureSensorFile'])               
		gui_items['pressureSensorFile'].show()
		tbFile.show()
		tb.pack_end(tbFile)
		sc2.content_set( tb )
		gui_items['mainwin'].resize_object_add (gui_items['calibratebox'])
		gui_items['pager'].item_simple_push(gui_items['calibratebox'])
		#####
		# Create about box (vertical by default)
		gui_items['aboutbox'] = elementary.Box (gui_items['mainwin'])
		gui_items['aboutbox'].size_hint_weight_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		gui_items['aboutbox'].size_hint_align_set (-1.0,-1.0)
		al = elementary.Label(gui_items['mainwin'])
		al.size_hint_weight_set (evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)
		al.size_hint_align_set (0.5, -1.0)
		al.text_set("About Barom")
		gui_items['aboutbox'].pack_end(al)
		al.show()
		
		# Create scroller to hold the author's picture
		sc2 = elementary.Scroller(gui_items['mainwin'])
		sc2.bounce_set(0, 0)
		sc2.size_hint_weight_set(1.0, 1.0)
		sc2.size_hint_align_set(evas.EVAS_HINT_FILL,-1.0)
		gui_items['aboutbox'].pack_end(sc2)
		gui_items['mainwin'].resize_object_add (sc2)
		sc2.show()
		
		ib = 	elementary.Box(gui_items['aboutbox'])
		ic = elementary.Icon(gui_items['aboutbox'])
		gui_items['mainwin'].resize_object_add (ic)
		ic.size_hint_weight_set(0.5, 0.5)
		ic.scale_set(0.5, 0.5) 
		ic.size_hint_align_set(0.5, 0.0)
		ic.file_set(os.path.join(IMAGE_DIR, "author.png"))
		ib.size_hint_weight_set(0.5, 0.5)
		ib.size_hint_align_set(evas.EVAS_HINT_FILL, evas.EVAS_HINT_FILL)		
		ib.pack_end(ic)
		
		sc2.content_set(ib)
		ic.show()
		
		# Create text box with 'about' info
		at = elementary.Entry( gui_items['aboutbox'] )
		at.size_hint_weight_set(1.0, 0.0)
		at.size_hint_align_set(evas.EVAS_HINT_FILL, 0.0)
		at.scale_set(1)
		info = self.infoadd("Barom " + APP_VERSION)
		info += self.infoadd("Copyright (c) 2011 Benjamin Deering")
		info += self.infoadd("<ben_deering@swissmail.org>" )
		at.text_set( info )	
		gui_items['aboutbox'].pack_end(at)
		at.show()
		gui_items['mainwin'].resize_object_add (gui_items['aboutbox'])
		gui_items['pager'].item_simple_push(gui_items['aboutbox'])
		
		#####
		# Create altitude box (vertical by default)
		gui_items['altitudebox'] = elementary.Box (gui_items['mainwin'])
		gui_items['altitudebox'].size_hint_weight_set (1.0, 1.0)
		gui_items['altitudebox'].size_hint_align_set (-1.0, -1.0)
		gui_items['altitudeLabel'] = elementary.Label(gui_items['mainwin'])
		gui_items['altitudeLabel'].text_set('altitude')
		
		gui_items['altitudeLabel'].scale_set(3.5)
		gui_items['altitudeLabel'].size_hint_weight_set (1.0, 1.0)
		gui_items['altitudeLabel'].size_hint_align_set (0.5, -1.0)
		gui_items['altitudebox'].pack_end( gui_items['altitudeLabel'])
		gui_items['altitudeLabel'].show()
		self.altitudeLabelTimer = ecore.timer_add(2, self.AltitudeLabelUpdate)
		gui_items['mainwin'].resize_object_add (gui_items['altitudebox'])
		gui_items['pager'].item_simple_push (gui_items['altitudebox'])
		gui_items['pager'].show()
		gui_items['mainbox'].pack_end( gui_items['pager'] )
		
		gui_items['pager'].item_simple_promote(gui_items['altitudebox'])
			
		return gui_items
	def getPressureFromSensor(self, obj, *args, **kargs):
		 #print( "attempting to read pressure from file" )
		 presfile = open( self.pressureSensorFile,'r' )
		 presx100 = int(presfile.read())
		 pres = presx100 / 100.0
		 #print "read pressure from file: " + str(pres)
		 return pres
		 
	# This is not being called currently.  Rarely the BMP085
	# gets in a state where the pressure changes with temperature
	# reading the temperature once gets it out of the bad state
	# but it is so rare, I haven't added this to the program.
	def getTemperatureFromSensor(self, obj, *args, **kargs):
		 #print( "attempting to read temperature from file" )
		 tempfile = open( '/sys/bus/i2c/devices/2-0077/temp0_input','r' )
		 tempx10 = int(tempfile.read())
		 tempfile.close()
		 #print "read temperature from file: " + tempx10 / 10.0
		 return tempx10 / 10.0
	def getAltitudeString(self, obj, *args, **kargs):
		unit = "m"
		if not self.usingMetric:
			unit = "ft"
		try:
			altStr = "{0:.2f}".format(self.getAltitudeFromSensor(self)) + " " + unit
		except:
			altStr = "No Sensor"
		return altStr
	def getPressureString(self, obj, *args, **kargs):
		unit = "hpa"
		pressureStr = "No Sensor"
		try:
			pressure = self.getPressureFromSensor(self)
			if not self.usingMetric:
				unit = "in hg"
				pressure = self.hpaToinHG(pressure)
			pressureStr = "{0:.2f}".format(pressure) + " " + unit
		except:
				pass
		return pressureStr
	def getAltitudeFromSensor(self, obj, *args, **kargs):
		 p0 = self.seaLevelPressure
		 p = self.getPressureFromSensor(self)
		 
		 rlgm = (R*L)/(g*M)
		 		 
		 alt = (1.0/L) * (-1 * (pow( p / p0 ,rlgm) - 1 ) * pow(p0 / p, rlgm) * Tb )	 		 
		 if self.usingMetric:
		 	return alt
		 else:
		 	return self.MtoF( alt ) 
	def altitudeDialog (self, *args, **kargs):
		self.widgets['pager'].item_simple_promote(self.widgets['altitudebox'])
	def weatherDialog (self, *args, **kargs):
		self.widgets['pager'].item_simple_promote(self.widgets['weatherbox'])	
	def aboutDialog(self, *args, **kargs):
		self.widgets['pager'].item_simple_promote(self.widgets['aboutbox'])
	def calibrateDialog(self, *args, **kargs):
		self.widgets['pager'].item_simple_promote(self.widgets['calibratebox'])
	

	def AltitudeLabelUpdate(self):
		self.widgets['altitudeLabel'].text_set( self.getAltitudeString(self))
		return True
		
	def PressureLabelUpdate(self):
		self.widgets['pressureLabel'].text_set( self.getPressureString(self))
		return True
	def MtoF (self, distance):
		return (distance / 0.3048)
	def hpaToinHG(self, pressure):
		return (pressure / 33.86)
	def inHGtoHpa(self, pressure):
		return (pressure * 33.86)
	def FtoM (self, distance):
		return (distance * 0.3048)
	def infoadd(self, text):                               
		 return elementary.Entry.utf8_to_markup(text)+'<br>'
	def setUnits(self, obj, *args, **kargs):
		 self.usingMetric = obj.state_get()
		 self.pressureGraphThread.setUnits( self.usingMetric )
		 if self.usingMetric:
		 	 self.widgets['unitaltlabel'].text_set('m')
		 	 self.widgets['unitpreslabel'].text_set('hpa')
		 else:
		 	 self.widgets['unitaltlabel'].text_set('ft')
		 	 self.widgets['unitpreslabel'].text_set('in hg')	 
	def calibrateWithKnownPres(self, pres ):
		if self.usingMetric:
			self.seaLevelPressure = pres
		else:
			 self.seaLevelPressure = self.inHGtoHpa(pres)
	def calibrateWithKnownAlt(self, alt):
		absPres = self.getPressureFromSensor(self) 
		if not self.usingMetric:
			alt = self.FtoM( alt )
				
		slPres = self.normalizePressure(absPres, alt) 
		self.seaLevelPressure = slPres 
	def normalizePressure( self, absPressure, alt ):
		if alt == -9999:
			alt = self.getAltitudeFromSensor(self)
		return( absPressure * pow( Tb /(Tb + L * alt ), (-1 * g * M) / ( L * R)) )
	def changeSensorFile( self, args ):
		self.pressureSensorFile = self.widgets['pressureSensorFile'].entry_get()
		self.SaveConfig()
	def calibrate (self, args):
		#Not sure which calibration is in use, try both		
		try:
			alt = float(self.widgets['calibrateAltnumber'].entry_get())
			self.calibrateWithKnownAlt(alt)
		except:
			try:
				pres = float(self.widgets['calibratePresnumber'].entry_get())
				self.calibrateWithKnownPres(pres)
			except:
				print "Incorrect calibration"
		self.SaveConfig()
	def LoadConfig (self, cfpath):
		"""
		Load configuration file, create a default if it doesn't exist.
		"""
		self.config.read (cfpath)
		if not self.config.has_section ('Main'):
			self.config.add_section ('Main')
		if not self.config.has_option( 'Main', 'units' ):
			self.config.set ('Main', 'units', 'metric')
		self.usingMetric = self.config.get ('Main', 'units', 0) == 'metric'
		if not self.config.has_option( 'Main', 'base pressure' ):
			self.config.set ('Main', 'base pressure', '1013.25')
		self.seaLevelPressure = float( self.config.get('Main', 'base pressure', 0))
		if not self.config.has_option( 'Main', 'pressure sensor file' ):
			self.config.set('Main', 'pressure sensor file', '/sys/bus/i2c/devices/0-0077/pressure0_input')
		self.pressureSensorFile = self.config.get('Main', 'pressure sensor file')
		
		self.SaveConfig (cfpath)
	def SaveConfig (self, cfpath):
		'''
		Save config file.
		'''
		if self.usingMetric:
			self.config.set ('Main', 'units', 'metric')
		else:
			self.config.set ('Main', 'units', 'imperial')
		self.config.set( 'Main', 'base pressure', str( self.seaLevelPressure ) )
		self.config.set('Main', 'pressure sensor file', self.pressureSensorFile)
		with open(cfpath, 'wb') as configfile:
			self.config.write (configfile)
			configfile.close ()
if __name__ == '__main__':
    app = baromGUI()


	

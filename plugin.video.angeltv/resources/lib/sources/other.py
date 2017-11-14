import urllib, urllib2, sys, re, os, unicodedata
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

xml_regex = '<title>(.*?)</title>\s*<link>(.*?)</link>\s*<thumbnail>(.*?)</thumbnail>'

class info():
    def __init__(self):
		self.mode = 'shadownet'
		self.xml = 'xtra.xml'
		self.xml_regex = '<title>(.*?)</title>\s*<link>(.*?)</link>\s*<thumbnail>(.*?)</thumbnail>'
		self.url = url

class main():
	def __init__(self,url = 'http://i4pro.co.uk/'):
		self.base = 'http://i4pro.co.uk/'
		self.base1 = 'kodi/'
		self.base2 = 'shadownet/'

	def make_request(self,url)
		try:
			req = urllib2.Request(url)
			req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0')
			response = urllib2.urlopen(req)	  
			content = response.read()
			response.close()  
			return content
		except:
			pass
			
	def channels(self,url):
		self.url = url
		content = make_request(online_xml)
		match = re.compile(xml_regex).findall(content)
		for name, url, thumb in match:
			try:
				xml_playlist(name, url, thumb)
			except:
				pass
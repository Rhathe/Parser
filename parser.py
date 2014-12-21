from pyquery import PyQuery as pq
from lxml import etree
import urllib, urllib2
import sys
import re,os
import urlparse
from urlparse import urljoin
import socket
from socket import AF_INET, SOCK_DGRAM
from cookielib import CookieJar
import string

class Parser:

	valid_chars = "-_() %s%s" % (string.ascii_letters, string.digits)
	prependName = None

	def __init__(self,folder='Parser Downloads'):
		self.socket = socket
		self.socket.setdefaulttimeout(100)
		self.folder = folder
		self.fileIndex = 0
		self.undowloaded = []
		self.cj = CookieJar()
		self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))

	def login(self,login_url,form_params,form_specifier):
		
		page = self.opener.open(login_url)
		d = pq(page.read())

		values = {}
		selector = ''
		try:
			selector = form_specifier['selector'] + ' '
		except Exception:
			pass

		forms = d(selector + 'form')
		form = None

		try:
			for f in forms:
				if f.attrib['action'] == form_specifier['action']:
					form = f;
		except Exception:
			pass
		
		try:
			for input in pq(form).find('input'):
				try:
					values[input.name] = input.value
				except Exception:
					pass
		except Exception:
			pass

		page.close()
		
		for key in form_params:
			values[key] = form_params[key]
		
		login_form = urllib.urlencode(values)	

		page = self.opener.open(login_url,login_form)
		page.close()
		return page

	def pq_url_open(self,src,type='',headers={}):
		u = self.url_open(src,type,headers)
		if (u):
			return pq(u)
		else: 
			return None


	def url_open(self,src,type='',headers={}):
		
		try:
			for key in headers:	
				self.opener.addheaders.append((key,headers[key]))
			f = self.opener.open(src)
			u_src_txt = f.read()
			f.close()
		except (urllib2.URLError,urllib2.HTTPError):
			print "-----"	
			print "-----"	
			print type + ": couldn't get " + src
			print "-----"	
			print "-----"
			return None	
		except socket.error:
			print "-----"	
			print "-----"	
			print type + ": timed out " + src
			print "-----"	
			print "-----"
			return None	

		return u_src_txt

	def grab_links(self,d,src,quals):
		links = []
		
		try:
			alinks = d(quals)
		except Exception as e:
			return None

		if alinks is None: 
			alinks = []

		for alink in alinks:
			link = 0
			if 'href' in alink.attrib and alink.attrib['href']: 
				link = alink.attrib['href']
			elif 'src' in alink.attrib and alink.attrib['src']: 
				link = alink.attrib['src']

			if link:
				if not ("http://" in link or "https://" in link):
					link = urljoin(src,link)
				links.append(link)

		return links


	def sanitize_filename(self,name):
		return ''.join( c for c in name if c in valid_chars)

	def get_filename(self,name,ext=None,sanitize=1,alt=''):
		index = len(name)
		found = 0
		if ("." in name):
			index = name.rfind(".")
			found = 1
		else:
			if ext is not None and ext != 'dir':
				name = name + "." + ext
				index = name.index(".")
				found = 1
	
		name_parts = [name[:index],alt,name[index:]]
		s = lambda x: self.sanitize_filename(x)
		if sanitize: name_parts = map(s,name_parts)
		
		tmpname = ''
		if self.prependName is not None:
			tmpname = ("%03d" % self.prependName) + " - "
			self.prependName += 1
			
		tmpname += name_parts[0] + name_parts[1]
		if not found and ext != 'dir':
			tmpname += "."
		
		tmpname += name_parts[2]
		if len(tmpname) == 0:
			return 'tmp'
		return tmpname

	def download(self,url,type,alt,default_write=None):
		data = None
		data2 = self.url_open(url,type)

		if (data2):
			data = data2

		name = url.rsplit('/',1)[1]	
		name = self.get_filename(name,'jpg',alt)	

		print url
		print name

		localFile = open(self.folder + '/' + name, 'w')

		if data is None: 
			if default_write is not None:
				localFile.write(default_write)
			self.undownloaded.append({
				url: url,
				type: type,
				name: name
			})
		else:
			localFile.write(data)
		
		localFile.close()
		
		if (data is None):
			return 0
		return 1 

	def get_imgs(self,d,url,quals = '',default_write=None):
		links = self.grab_links(d,url,quals + ' img')
		try:
			for link in links:
				self.download(link,"IMAGE",'',default_write)
		except Exception as e:
			pass
			

	def get_next(d,url,quals,index=None):
		next = d(quals)
		nextlinks = next.find('a')
		if index is not None:
			nextlinks = pq(next[index]).find('a')
		
		if nextlinks is not None:
			for nextlink in nextlinks:
				nextlinksrc = urlparse.urljoin(src,nextlink.attrib['href'])
				return nextlinksrc
		return 0

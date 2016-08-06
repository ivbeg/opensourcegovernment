#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import csv
import yaml
import time
from StringIO import StringIO
from pygithub3 import Github

# Write valid login and password
GIT_NAME = 'ivbeg'
GIT_PASSWORD = file('../git_pass.txt', 'r').read()

FILEPATH = 'data/'
REPPATH = 'data/repos/'

def calc_list(l):
	n = 0
	try:
		for k in l:
			print k.login, k.name, k.email, k.id
			n += 1
	except KeyboardInterrupt:
		sys.exit(0)
	except:
		return 0
	return n

def get_list(l):
	alist = []
	print len(l)
	try:
		for k in l:
			print k.login
#			print k.login, k.name, k.email, k.id
			alist.append({'login': k.login, 'id' : k.id})
	except KeyboardInterrupt:
		sys.exit(0)
	return alist


def get_all():
	g= yaml.load(open('governments.yml', 'r').read())
	return g

def process_org(g, orgname):
	if os.path.exists(FILEPATH + orgname+'.csv'): return
	f = StringIO()
	s = ('\t'.join(['orgname','name'])).encode('utf8')
	f.write(s)
	f.write(u'\n')
#	try:
#		org = g.orgs.get(orgname)
#	except KeyboardInterrupt:
#		sys.exit(0)
#	except:
#		print orgname, 'not found'
#		pass
#		return
#	print orgname
	repos = g.repos.list_by_org(orgname).all()
#	print repos
	for r in repos:
		if r.fork: continue
		repfilename = '_'.join([orgname, r.name]) + '.yml'
		if os.path.exists(REPPATH + repfilename):
			print ' - repository %s already processed' % (r.name)
			arr = [orgname, r.name]
			s = ('\t'.join(map(str, arr))).encode('utf8')
			f.write(s)
			f.write(u'\n')#		print arr
			continue
		print ' - repository %s is being processed' % (r.name)
		repfile = file(REPPATH + repfilename, 'w')
		forks = g.repos.forks.list(orgname, r.name).all()
		issues = g.issues.list_by_repo(orgname, r.name).all()
		for n in range(0, 5):
			try:
				contributors = g.repos.list_contributors(orgname, r.name).all()
				break
			except:
				time.sleep(2)
				continue
		data = {'orgname' : orgname, 'name': r.name, 'stargazers_count': r.stargazers_count, 'size' : r.size,
				'forks': len(forks),
				'issues' : len(issues),
				'watchers_count': r.watchers_count,
				'contributors': len(contributors)}
#		print data
		yaml.dump(data, repfile)
		arr = [orgname, r.name]
		s = ('\t'.join(map(str, arr))).encode('utf8')
		f.write(s)
		f.write(u'\n')#		print arr
	fo = open(FILEPATH + orgname+'.csv', 'w')
	f.seek(0)
	fo.write(f.read())
	fo.close()
	
def process_all():
	thelist = get_all()
	g = Github(login=GIT_NAME, password=GIT_PASSWORD)
	for country, orglist in thelist.items():
		for r in orglist:
			print 'Processing  %s from %s' % (r, country)
			process_org(g, r)
			try:
				pass
#				process_org(g, r)
			except:
				print "Error occured, but we don't give up. Skip and follow to next one"
			
			
def calc_stats():
	thelist = get_all()

	frep = open('repositories.csv', 'w')
	wrrep = csv.DictWriter(frep, ['country', 'orgname', 'repname', 'watchers_count',  'forks', 'issues', 'contributors', 'size'], delimiter=',')
	wrrep.writeheader()

	forgs = open('organizations.csv', 'w')
	wrorgs = csv.DictWriter(forgs, ['country', 'orgname', 'repos', 'watchers_count',  'forks', 'issues', 'contributors', 'size'], delimiter=',')
	wrorgs.writeheader()

	f = open('countries.csv', 'w')
	wr = csv.DictWriter(f, ['country', 'orgs', 'repos', 'watchers_count',  'forks', 'issues', 'contributors', 'size'], delimiter=',')
	wr.writeheader()
	for country, orglist in thelist.items():
		c = {'country' : country, 'orgs' : 0, 'repos' : 0, 'contributors' : 0, 'issues' : 0, 'forks' : 0, "size" : 0,  'watchers_count' : 0}
		for orgname in orglist:
			c['orgs'] += 1
			org = {'country' : country, 'orgname' : orgname, 'repos' : 0, 'contributors' : 0, 'issues' : 0, 'forks' : 0, "size" : 0,  'watchers_count' : 0}
			try:
				f = open(FILEPATH+orgname+'.csv', 'r')
			except:
				continue
			r = csv.DictReader(f, delimiter="\t")
			for row in r:
				c['repos'] += 1
				org['repos'] += 1
				rep = {'country' : country, 'orgname' : orgname, 'repname' : row['name'], 'contributors' : 0, 'issues' : 0, 'forks' : 0, "size" : 0,  'watchers_count' : 0}
#				for k in ['name', 'orgname']:
#					c[k] = row[k]
				repfilename = '_'.join([orgname, row['name']]) + '.yml'
				repf = open(REPPATH + repfilename, 'r')
				repdata = yaml.load(repf)
				if not repdata:
					print orgname, row['name'], 'no data'
					continue
				for k in ['contributors', 'forks', 'issues', 'size', 'watchers_count']:
					c[k] += repdata[k]
				for k in ['contributors', 'forks', 'issues', 'size', 'watchers_count']:
					org[k] += repdata[k]
				for k in ['contributors', 'forks', 'issues', 'size', 'watchers_count']:
					rep[k] += repdata[k]
				wrrep.writerow(rep)
			wrorgs.writerow(org)
		print c
		wr.writerow(c)
#			process_org(r)
	
#		print dir(r.get_forks()
if __name__ == "__main__":
#	process_all()
	calc_stats()
#	process_org(orgname='gcba')
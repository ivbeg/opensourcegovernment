#!/usr/bin/env python
import os
import csv
import yaml
from StringIO import StringIO
from github import Github

# Write valid login and password
GIT_NAME = ''
GIT_PASSWORD = ''

FILEPATH = 'data/'

def calc_list(l):
	n = 0
	try:
		for k in l:
#			print k.login, k.name, k.email, k.id
			n += 1
	except:
		return 0
	return n
	


def get_all():
	g= yaml.load(open('governments.yml', 'r').read())
	return g

def process_org(orgname):
	if os.path.exists(FILEPATH + orgname+'.csv'): return
	f = StringIO()
	s = ('\t'.join(['orgname','name', 'star_count', 'forks', 'issues', 'contributors', 'size'])).encode('utf8')
	f.write(s)
	f.write(u'\n')
	g = Github(GIT_NAME, GIT_PASSWORD)
	try:
		org = g.get_organization(orgname)
	except:
		print orgname, 'not found'
		pass
		return
	for r in org.get_repos():
		if r.source is not None:
			continue
		arr = [orgname, r.name, r.stargazers_count, calc_list(r.get_forks()), calc_list(r.get_issues()), calc_list(r.get_contributors()), r.size]
		s = ('\t'.join(map(str, arr))).encode('utf8')
		f.write(s)
		f.write(u'\n')
		print arr
	fo = open(FILEPATH + orgname+'.csv', 'w')
	f.seek(0)
	fo.write(f.read())
	fo.close()
	
def process_all():
	thelist = get_all()
	for country, orglist in thelist.items():
		for r in orglist:
			print country, r
			process_org(r)
			
			
def calc_stats():
	thelist = get_all()
	f = open('rating.csv', 'w')
	wr = csv.DictWriter(f, ['country', 'orgs', 'repos', 'star_count', 'forks', 'issues', 'contributors', 'size'], delimiter='\t')
	wr.writeheader()
	for country, orglist in thelist.items():
		c = {'country' : country, 'orgs' : 0, 'repos' : 0, 'contributors' : 0, 'issues' : 0, 'forks' : 0, "size" : 0, 'star_count' : 0}
		for orgname in orglist:
			c['orgs'] += 1
			try:
				f = open(FILEPATH+orgname+'.csv', 'r')
			except:
				continue
#			data = f.read()
#			f.close()
			r = csv.DictReader(f, delimiter="\t")
			for row in r:
				c['repos'] += 1
				for k in row.keys():
					if k not in ['name', 'orgname']:
						c[k] += int(row[k]) 
		print c
		wr.writerow(c)
#			process_org(r)
	
#		print dir(r.get_forks()
if __name__ == "__main__":
	process_all()
#	calc_stats()
#	process_org(orgname='gcba')
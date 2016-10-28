#!/usr/bin/env python
# -*- coding: utf-8 -*-
import click
import os
import urllib
import urllib2, base64
import sys
import csv
import yaml
import json
import time
from StringIO import StringIO
from pygithub3 import Github

# Write valid login and password
GIT_NAME = 'ivbeg'
GIT_TOKEN = file('../../git_pass.txt', 'r').read()

FILEPATH = 'data'
MEMBERSFILE = os.path.join(FILEPATH, 'members.json')
ORGPATH = os.path.join(FILEPATH, 'orgs')
REPPATH = os.path.join(FILEPATH, 'repos')
MEMBERSPATH = os.path.join(FILEPATH, 'members')
MEMBERSORGSPATH = os.path.join(FILEPATH, 'membersorgs')
PARTPATH = os.path.join(FILEPATH, 'participation')



def get_all(filename):
    g = yaml.load(open(filename, 'r').read())
    return g

def get_data(username, token, url, filename=None, limit=30, iterate=False, page=None, force=False):
    if not page and filename and not force:
        if os.path.exists(filename):
            return json.load(file(filename, 'r'))
    if page is not None:
        finurl = url + '?page=%d' % (page)
    else:
        finurl = url
    request = urllib2.Request(finurl)
    base64string = base64.encodestring('%s:%s' % (username, token)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    result = urllib2.urlopen(request)
    data = result.read()
    js = json.loads(data)
    if iterate:
        num = len(js)
        if num == limit:
            pg = 1 if not page else page
            while num == limit:
                pg += 1
                jdn = get_data(username, token, url, limit, iterate=True, page=pg)
                num = len(jdn)
                js.extend(jdn)
    if not page and filename:
        f = file(filename, 'w')
        f.write(json.dumps(js, indent=4))
        f.close()
    print url, len(js)
    print 'Sleeping for 0.5 second'
    time.sleep(0.5)
    return js



def process_org(orgname, force=False):
    get_data(GIT_NAME, GIT_TOKEN, 'https://api.github.com/users/%s' % (orgname), os.path.join(ORGPATH, orgname) + '.json', force=force)
    get_data(GIT_NAME, GIT_TOKEN, 'https://api.github.com/orgs/%s/members' % (orgname), os.path.join(MEMBERSPATH, orgname) + '.json', iterate=True, force=force)
    repdata = get_data(GIT_NAME, GIT_TOKEN, 'https://api.github.com/users/%s/repos' % (orgname), os.path.join(REPPATH, orgname) + '_repos.json', iterate=True, force=force)
    for rep in repdata:
        get_data(GIT_NAME, GIT_TOKEN, 'https://api.github.com/repositories/%s/stats/participation' % (str(rep['id'])), os.path.join(PARTPATH, str(rep['id'])) + '_participation.json', force=force)
        print rep['id']

def process_all(filename='governments.yml', force=False):
    thelist = get_all(filename)
    for country, orglist in thelist.items():
        for r in orglist:
            print 'Processing  %s from %s' % (r, country)
            process_org(r, force=False)


def calc_stats(filename='governments_full.yml'):
    thelist = get_all(filename)

    frep = open('repositories.csv', 'w')
    wrrep = csv.DictWriter(frep, ['country', 'orgname', 'repname', 'watchers_count',  'forks', 'open_issues', 'size', '52weeksactivity'], delimiter=',')
    wrrep.writeheader()

    forgs = open('organizations.csv', 'w')
    wrorgs = csv.DictWriter(forgs, ['country', 'orgname', 'repos', 'watchers_count', 'forks', 'open_issues', 'size', 'followers', 'public_gists', 'members', '52weeksactivity'], delimiter=',')
    wrorgs.writeheader()

    f = open('countries.csv', 'w')
    wr = csv.DictWriter(f, ['country', 'orgs', 'repos', 'watchers_count',  'forks', 'open_issues',  'size', 'members', 'uniqmembers', 'followers', 'public_gists', '52weeksactivity'], delimiter=',')
    wr.writeheader()
    for country, orglist in thelist.items():
        uniqmembers = []
        c = {'country' : country, 'orgs' : 0, 'repos' : 0, 'open_issues' : 0, 'forks' : 0, "size" : 0,  'watchers_count' : 0, 'uniqmembers' : 0, 'followers' : 0, 'public_gists' : 0, 'members' : 0, '52weeksactivity' : 0}
        for orgname in orglist:
            c['orgs'] += 1
            org = {'country' : country, 'orgname' : orgname,
            'open_issues' : 0, 'forks' : 0, "size" : 0,  'watchers_count' : 0, 'repos' : 0, 'members' : 0, '52weeksactivity' : 0}
            f = open(os.path.join(ORGPATH, orgname + '.json'))
            frep = open(os.path.join(REPPATH, orgname + '_repos.json'))
            fmem = open(os.path.join(MEMBERSPATH, orgname + '.json'))
            orgdata = json.load(f)

            for k in ['followers', 'public_gists']:
                org[k] = orgdata[k]
            memdata = json.load(fmem)
            org['members'] = len(memdata)
            for member in memdata:
                try:
                    if member['login'] not in uniqmembers: uniqmembers.append(member['login'])
                except:
                    print 'Error reading members of', orgname
                    continue

            orgrepdata = json.load(frep)
            for row in orgrepdata:
                if row['fork']: continue
                org['repos'] += 1
                rep = {'country' : country, 'orgname' : orgname, 'repname' : row['name'],
                'open_issues' : 0, 'forks' : 0, "size" : 0,
                'watchers_count' : 0}


                for k in ['forks', 'open_issues', 'size', 'watchers_count']:
                    c[k] += row[k]
                for k in ['forks', 'open_issues', 'size', 'watchers_count']:
                    org[k] += row[k]
                for k in ['forks', 'open_issues', 'size', 'watchers_count']:
                    rep[k] += row[k]

                # Load repository participation stats
                repstatdatafile = file(os.path.join(PARTPATH, str(row['id'])) + '_participation.json', 'r')
                rd = json.load(repstatdatafile)
                rep['52weeksactivity'] = sum(rd['all']) if rd.has_key('all') else 0
                org['52weeksactivity'] += rep['52weeksactivity']
                c['52weeksactivity'] += rep['52weeksactivity']
                wrrep.writerow(rep)
            org['52weeksactivity'] = org['52weeksactivity'] / org['repos'] if org['repos'] > 0 else 0
            for k in ['members', 'followers', 'repos', 'public_gists']:
                c[k] += org[k]
            wrorgs.writerow(org)
        c['uniqmembers'] = len(uniqmembers)
        c['52weeksactivity'] = c['52weeksactivity'] / c['repos'] if c['repos'] > 0 else 0
        print c
        wr.writerow(c)
#            process_org(r)


def calc_countrygroups():
    f = open('countries.csv', 'r')
    headers = ['country', 'orgs', 'repos', 'watchers_count',  'forks', 'open_issues',  'size', 'members', 'uniqmembers', 'followers', 'public_gists', '52weeksactivity']
    dict = {}
    dr = csv.DictReader(f, headers, delimiter=',')
    for r in dr:
        dict[r['country']] = r

    f = open('countrygroups.csv', 'w')
    wr = csv.DictWriter(f, ['group', 'orgs', 'repos', 'watchers_count',  'forks', 'open_issues',  'size', 'members', 'uniqmembers', 'followers', 'public_gists', '52weeksactivity'], delimiter=',')
    wr.writeheader()

    g = get_all('countrygroups.yml')
    for r in g:
        group = {'group' : r, 'orgs' : 0, 'repos' : 0, 'open_issues' : 0, 'forks' : 0, "size" : 0,  'watchers_count' : 0, 'uniqmembers' : 0, 'followers' : 0, 'public_gists' : 0, 'members' : 0, '52weeksactivity' : 0}
        for country in g[r]:
            for k in ['orgs', 'repos', 'open_issues', 'forks', 'size', 'watchers_count', 'uniqmembers', 'followers', 'public_gists', 'members']:
                group[k] += int(dict[country][k])
            group['52weeksactivity'] += int(dict[country]['52weeksactivity']) * int(dict[country]['repos'])
        group['52weeksactivity'] = group['52weeksactivity'] / group['repos']
        wr.writerow(group)


@click.group()
def cli1():
    pass

@cli1.command()
@click.argument('filename')
def processall(filename):
    """Process all repositories"""
    process_all(filename)


@click.group()
def cli2():
    pass

@cli2.command()
@click.argument('orgname')
@click.option('--force', default=False, type=bool)
def process(orgname, force):
    """Process repository by org"""
    force = True if force else False
    process_org(orgname=orgname, force=force)



@click.group()
def cli3():
    pass

@cli3.command()
@click.argument('filename')
def stats(filename):
    """Calculate statistics"""
    calc_stats(filename)
    calc_countrygroups()

@click.group()
def cli4():
    pass

@cli4.command()
def updatelist():
    """Update list of organizations"""
    CIVHACKERS_LIST = 'https://raw.githubusercontent.com/github/government.github.com/gh-pages/_data/civic_hackers.yml'
    GOVERNMENT_LIST = 'https://raw.githubusercontent.com/github/government.github.com/gh-pages/_data/governments.yml'
    RESEARCH_LIST = 'https://raw.githubusercontent.com/github/government.github.com/gh-pages/_data/research.yml'
    print 'Downloading lists from government.github.com'
    urllib.urlretrieve(CIVHACKERS_LIST, 'civic_hackers.yml')
    urllib.urlretrieve(GOVERNMENT_LIST, 'governments.yml')
    urllib.urlretrieve(RESEARCH_LIST, 'research.yml')
    output = file('merged.yml', 'w')
    for f in ['civic_hackers.yml', 'governments.yml', 'research.yml']:
        data = file(f).read()
        output.write(data)

@click.group()
def cli5():
    pass

@cli5.command()
@click.argument('filename')
def findorgs(filename):
    """Creates list of members and seeks for shared orgs"""
    print 'Collect cached orgs'
    thelist = get_all(filename)
    cached_orgs = []
    for country, orglist in thelist.items():
        for orgname in orglist:
            cached_orgs.append(orgname.lower())
    if not os.path.exists(MEMBERSFILE):
        uniqusers = []
        members = []
        files = os.listdir(MEMBERSPATH)
        for name in files:
            f = file(os.path.join(MEMBERSPATH, name), 'r')
            js = json.load(f)
            f.close()
            for rec in js:
                if rec['id'] not in uniqusers:
                    uniqusers.append(rec['id'])
                    members.append(rec)
        f = file(MEMBERSFILE, 'w')
        f.write(json.dumps(members))
        f.close()
    else:
        members = json.load(file(MEMBERSFILE, 'r'))
    print 'Download and load members list of organizations'
    for r in members:
        get_data(GIT_NAME, GIT_TOKEN, 'https://api.github.com/users/%s/orgs' % (r['login']), os.path.join(MEMBERSORGSPATH, r['login']) + '.json', force=False)
        print '-', r['login']

    print 'Analyze orgs members'
    orgs = {}
    for r in members:
        try:
            f = file(os.path.join(MEMBERSORGSPATH, r['login']) + '.json', 'r')
        except:
            continue
        js = json.load(f)
        f.close()
        for org in js:
            v = orgs.get(org['login'].lower(), 0)
            orgs[org['login'].lower()] = v + 1

    print 'Remove cached orgs'
    for org in cached_orgs:
        org = unicode(org)
        if org in orgs.keys():
            print '- remove', org
            del orgs[org]

    import tabulate
    table = sorted(orgs.items(), lambda x, y: cmp(x[1], y[1]), reverse=True)
    keys = ['organization', 'members']
    print tabulate.tabulate(table, headers=keys)
    writer = csv.writer(file('missingsorgs.csv', 'w'))
    writer.writerow(['organization', 'members'])
    writer.writerows(table)


cli = click.CommandCollection(sources=[cli1, cli2, cli3, cli4, cli5])


if __name__ == "__main__":
    cli()
#    process_all()
#    calc_stats()
#    process_org(orgname='gcba')

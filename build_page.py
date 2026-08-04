#!/usr/bin/env python3
"""Összefűzi a sablont a geometriával és a folyóadatokkal."""
import json

tpl = open('holaviz_template.html').read()
geo = json.dumps(json.load(open('geometry.json')), ensure_ascii=False, separators=(',', ':'))
riv = json.dumps(json.load(open('rivers_data.json')), ensure_ascii=False, separators=(',', ':'))
liv = json.dumps(json.load(open('live_data.json')), ensure_ascii=False, separators=(',', ':'))
out = tpl.replace('/*__GEO__*/', geo).replace('/*__RIVERS__*/', riv).replace('/*__LIVE__*/', liv)
open('holaviz.html', 'w').write(out)
print('holaviz.html:', len(out), 'bytes')

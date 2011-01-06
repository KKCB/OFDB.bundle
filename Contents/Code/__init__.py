# -*- coding: utf-8 -*-
#
# OFDB metadata agent for Plex
# Adds German summaries from www.ofdb.de to movies

import re

OFDB_SEARCH_URL = 'http://www.ofdb.de/view.php?page=suchergebnis&Kat=IMDb&SText=%s'
OFDB_MOVIE_URL = 'http://www.ofdb.de/film/%s'
OFDB_PLOT_URL = 'http://www.ofdb.de/plot/%s'

def Start():
  HTTP.CacheTime = CACHE_1DAY
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13'


def do_page(url, pattern):
  f = urllib.urlopen(url)
  html = f.read()
  hits = re.findall(pattern, html, re.S)
  return hits

class OFDBAgent(Agent.Movies):
  name = 'OFDB'
  languages = ['de']
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb']

  def search(self, results, media, lang):
    # Use the IMDB id found by the primary metadata agent (IMDB/Freebase)
    results.Append(MetadataSearchResult(id=media.primary_metadata.id, score=100))

  def update(self, metadata, media, lang):
    # Only use data from OFDB if the user has set the language for this section to German (Deutsch)
    if lang == 'de':
      search_result = HTTP.Request(OFDB_SEARCH_URL % metadata.id).content
      ofdb_id = re.findall('href="film/([^"/]+)', search_result)

      if len(ofdb_id) > 0:
        movie_page = HTTP.Request(OFDB_MOVIE_URL % ofdb_id[0]).content
        plot_url = re.findall('href="plot/([^"/]+)', movie_page)

        if len(plot_url) > 0:
          plot_page = HTTP.Request(OFDB_PLOT_URL % plot_url[0]).content
          plot_text = re.findall('gelesen</b></b><br><br>(.*?)</font></p>', plot_page, re.DOTALL)

          if len(plot_text) > 0:
            summary = plot_text[0].replace('<br />', '\n')
            summary = re.sub('(\r)?\n((\r)?\n)+', '\n', summary) # Replace 2 or more newlines with just 1
            summary = String.StripTags(summary).strip() # Strip HTML tags
            Log("summary")
            Log(summary)

            if summary != '':
              metadata.summary = summary

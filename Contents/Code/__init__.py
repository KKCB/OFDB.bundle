# -*- coding: utf-8 -*-
#
# OFDB metadata agent for Plex
# Adds German title, summaries, ratings and genres from www.ofdb.de to movies

import re

OFDB_SEARCH_URL = 'http://www.ofdb.de/view.php?page=suchergebnis&Kat=IMDb&SText=%s'
OFDB_MOVIE_URL = 'http://www.ofdb.de/film/%s'
OFDB_PLOT_URL = 'http://www.ofdb.de/plot/%s'

def Start():
  HTTP.CacheTime = CACHE_1DAY
  HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:15.0) Gecko/20100101 Firefox/15.0.1'

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
      search_result = HTTP.Request(OFDB_SEARCH_URL % (metadata.id), sleep=1.0).content
      ofdb_id = re.findall('href="film/([^"/]+)', search_result)

      if len(ofdb_id) > 0:
        movie_page = HTTP.Request(OFDB_MOVIE_URL % (ofdb_id[0]), sleep=1.0).content

        # Title
        metadata.title = '';
        if Prefs['title']:
          title = re.findall('<font face="Arial,Helvetica,sans-serif" size="3"><b>([^<]+)</b></font>', movie_page)

        if len(title) > 0:
          metadata.title = metadata.title = re.sub(r"(.*), (Die|Der|Das|The)", r"\2 \1", title[0])


        # Genre(s)
        metadata.genres.clear()
        if Prefs['genres']:
          genres = re.findall('page=genre&Genre=.+?>([^<]+)', movie_page)

          if len(genres) > 0:
            metadata.genres.clear()
            for genre in genres:
              metadata.genres.add(genre)

        # Rating
        metadata.rating = None
        if Prefs['rating']:
          rating = re.findall('<br>Note: ([0-9]+\.[0-9]+) &nbsp', movie_page)
          votes = re.findall('&nbsp;Stimmen: ([0-9]+) &nbsp', movie_page)

          if len(rating) > 0 and len(votes) > 0:
            if votes > 3:
              metadata.rating = float(rating[0])

        # Summary
        metadata.summary = ''
        if Prefs['summary']:
          plot_url = re.findall('href="plot/([^"/]+)', movie_page)

          if len(plot_url) > 0:
            plot_page = HTTP.Request(OFDB_PLOT_URL % (plot_url[0]), sleep=1.0).content
            plot_text = re.findall('gelesen</b></b><br><br>(.*?)</font></p>', plot_page, re.DOTALL)

            if len(plot_text) > 0:
              summary = plot_text[0].replace('<br />', '\n')
              summary = re.sub('(\r)?\n((\r)?\n)+', '\n', summary) # Replace 2 or more newlines with just 1
              summary = String.StripTags(summary).strip() # Strip HTML tags

              if summary != '':
                metadata.summary = summary

        # Content rating
        metadata.content_rating = ''
        if Prefs['content_rating']:
          content_rating = re.findall('Freigabe: FSK ([0-9]+)', movie_page)

          if len(content_rating) > 0:
            metadata.content_rating = 'de/%s' % content_rating[0]

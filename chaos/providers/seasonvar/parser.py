# coding: utf-8

#
# Copyright © 2017 weirdgiraffe <giraffe@cyberzoo.xyz>
#
# Distributed under terms of the MIT license.
#
import re

def main_page_items(main_page_html, datestr):
    '''Collect all dayblock items(i.e episode changes) for a given date
    and yields dict {'url': ..., 'name': ..., 'changes': ...} for each
    episode for that date.
    datestr should be in format 'dd.mm.yyyy'
    '''
    for (date, dayblock) in _main_page_dayblocks(main_page_html):
        if datestr == date:
            for item in _main_page_dayblock_items(dayblock):
                yield item


def search_items(search_response):
    '''yield dict {'name':..., 'url': ...} for items in search_response
    search_response is dict representation of search response
    '''
    try:
        r = re.compile(r'serial-\d+-[^.]+?\.html')
        suggestions = search_response['suggestions']
        data = search_response['data']
        for name, url in zip(suggestions['valu'], data):
            if url and r.match(url) is not None:
                yield {'name': name, 'url': '/' + url}
    except (KeyError, TypeError):
        return


def seasons(season_page_html):
    '''takes content of season page and yields
    all seasons for the same show.
    season_page_html should be utf-8 encoded html content
    '''
    r = re.compile(r'<h2>\s*<a\s+href="(/serial-\d+-[^.]+?\.html)"')
    for url in r.findall(season_page_html):
        yield url


def player_params(season_page_html):
    '''extract parameters for player.php to retrieve playlists
    if parameters not found return None
    '''
    sands = _season_and_serial(season_page_html)
    sandt = _secure_and_time(season_page_html)
    if sands and sandt:
        return {
            'id': sands[0],
            'serial': sands[1],
            'secure': sandt[0],
            'time': sandt[1],
            'type': 'html5',
        }


def playlists(player_response_html):
    '''takes response from player.php and yield dict {'tr':..., 'url':...}
    where 'tr' is a translation name and 'url' is a playlist url.
    If no translations found on page, then search for playlist urls only
    will be done. In this case translation names will be None.
    season_page_html should be utf-8 encoded html content
    '''
    r = re.compile(r'var pl = {\'0\': "(.+)"};')
    for url in r.findall(player_response_html):
        yield {'tr': None,
               'url': url.strip()}
    translations = _translate_list(player_response_html)
    if translations is not None:
        r = re.compile(r'<li data-click="translate[^>]*?>([^<]+)</li>[\s\n]*?'
                       '<script>pl\[\d+\] = "(.*?)";',
                       re.DOTALL)
        for name, url in r.findall(translations):
            yield {'tr': name.strip() if name != 'Стандартный' else None,
                   'url': url.strip()}


def episodes(playlist):
    '''yield dict {'name':..., 'url': ...} for items in playlist_dict
    playlist_html is response from requester.playlist()
    '''
    for entry in playlist:
        if 'playlist' in entry:
            for episode in entry['playlist']:
                yield {'url': episode['file'],
                       'name': episode['title'].replace('<br>', ' ')}
        else:
            yield {'url': entry['file'],
                   'name': entry['title'].replace('<br>', ' ')}


def _translate_list(season_page_html):
    r = re.compile(r'<ul class="pgs-trans"(.*?)</ul>', re.DOTALL)
    for b in r.findall(season_page_html):
        return b


def _season_and_serial(season_page_html):
    r = re.compile(r'data-id-season="(\d+)"\s+data-id-serial="(\d+)"')
    match = r.search(season_page_html)
    if match:
        return match.groups()


def _secure_and_time(season_page_html):
    r = re.compile(r"var\s+data4play\s*=\s*{\s*"
                   r"'secureMark'\s*:\s*'([a-f0-9]+)',\s*"
                   r"'time'\s*:\s*([0-9]+)\s*"
                   r"}")
    match = r.search(season_page_html)
    if match:
        return match.groups()


def _main_page_dayblocks(full_page_html):
    '''Collect all dayblocks from full_page_html
    and yield (date, content) for every dayblock'''
    r = re.compile(
        r'<div class="news-head">\s*?(\d{2}\.\d{2}\.\d{4})(.*?)'
        r'(?=<div class="doptxt"|<div class="news")',
        re.DOTALL)
    for group in r.findall(full_page_html):
        d, c = group
        yield group


def _main_page_dayblock_items(dayblock_content):
    '''Collect all series items from dayblock_content
    and for every item yield dict with description'''
    r = re.compile(
        r'<a href="(\/serial-.+?\.html)"[^>]*?>'
        '.*?div.*?<div[^>]*?>(.+?)<\/div>'
        '(.*?)<span[^>]*?>(.+?)<\/span>.*?<\/a>',
        re.DOTALL)
    for (url, name, season, changes) in r.findall(dayblock_content):
        changes = season.strip() + ' ' + changes.strip()
        name = name.replace("<span>", "")
        name = name.replace("</span>", "")
        yield {'url': url,
               'name': name.strip(),
               'changes': changes.strip()}
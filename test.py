import seasonvar

a = seasonvar.search('doctor who');
for it in a:
  print it['name'], '>', it['url']

e = seasonvar.season_info(it[0]['url']);
for et in e:
  print et['name'], '>', et['url']

import requests

def query(request):
    request['action'] = 'query'
    request['format'] = 'json'
    # Call API
    result = requests.get('https://en.wiktionary.org/w/api.php', params=request).json()
    if 'error' in result:
        raise Exception(result['error'])
    if 'warnings' in result:
        print(result['warnings'])
    if 'query' in result:
        return result['query']


def query_generator(request):
    request['action'] = 'query'
    request['format'] = 'json'
    lastContinue = {}
    while True:
        # Clone original request
        req = request.copy()
        # Modify it with the values returned in the 'continue' section of the last result.
        req.update(lastContinue)
        # Call API
        result = requests.get('https://en.wiktionary.org/w/api.php', params=req).json()
        if 'error' in result:
            raise Exception(result['error'])
        if 'warnings' in result:
            print(result['warnings'])
        if 'query' in result:
            yield result['query']
        if 'continue' not in result:
            break
        lastContinue = result['continue']

def parse(request):
    request['action'] = 'parse'
    request['format'] = 'json'
    # Call API
    result = requests.get('https://en.wiktionary.org/w/api.php', params=request)
    print(result.status_code)
    if result.ok:
        result = result.json()
        if 'error' in result:
            raise Exception(result['error'])
        if 'warnings' in result:
            print(result['warnings'])
        if 'parse' in result:
            return result['parse']
    
def get_html(word):
    categories = parse({'page':word, 'prop':'sections'})['sections']

    lang_found = False
    pron_passed = False
    for cat in categories:
        if cat['line'] == 'Chinese':
            lang_found = True
        elif lang_found and not pron_passed:
            if 'Pronunciation' in cat['line']:
                pron_passed = True
                continue
        elif pron_passed:
            section = cat['index']
            title = cat['fromtitle']
            break

    request = {'page':word, 'section':section, 'prop':'wikitext'}

    wikitext = parse(request)['wikitext']['*']

    # try to cut the wikitext a bit
    wikitext = wikitext[:wikitext.find('====Derived terms====')]
    print(wikitext)

    # {{lb|zh|neologism|slang}} [[romantic]] [[couple]] {{zh-mw|對}}
    # {{lb|zh|ACG}} [[cosplay]] [[partner]]; [[character]] [[pairing]]

    request = {'text':wikitext, 'prop':'text', 'title':title} 
    html = parse(request)['text']['*']
    return html

get_html('主義')
f = open('result.html', 'w', encoding='utf-8')
print('<base href="https://en.wiktionary.org">', file=f)
for result in query_generator({'list': 'categorymembers', 'cmtitle': 'Category:Chinese_orthographic_borrowings_from_Japanese', 'cmprop': 'title|ids'}):
    # process result data
    pages = '|'.join([str(w['pageid']) for w in result['categorymembers']])
    print(pages)
    res = query({'prop': 'categories', 'pageids': pages, 'cllimit':'max'})
    for page in res['pages'].values():
        if 'Category:Chinese proper nouns' not in [category['title'] for category in page['categories']]:
            word = page['title']
            print(word)
            html = get_html(word)
            link = f'https://en.wiktionary.org/wiki/{word}#Chinese'
            print(f'<a href="{link}">{word}</a>', file=f)
            print(html, file=f)
    # print(res, file=f)

f.close()
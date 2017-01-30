#!/usr/bin/env python

def get(results):

    # initialize lists
    titles = []
    dates = []
    links = []
    full_texts = []
    authors = []
    sections = []

    # scrape results into lists
    for x in results:
        # get link
        link = x.find('a')['href']
        # set regex to eliminate interactive features
        match = re.search('^http://www.nytimes.com/20', link)
        if match:
            links.append(link)

    # resoup it
    for link in links:
        all_p = ''
        cj = cookielib.CookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        new_soup = BeautifulSoup(opener.open(link).read().decode('utf-8', 'ignore'), 'html.parser')
        # get the article content
        body = new_soup.find_all('p', attrs = {'class': 'story-body-text story-content'})
        for p in body:
            new_p = p.text.strip()
            all_p = all_p + new_p
        full_texts.append(all_p)

        # get titles
        title = new_soup.find('meta', attrs = {'property': 'og:title'})['content']
        titles.append(title)

        # get authors
        author = new_soup.find('meta', attrs = {'name': 'author'})['content']
        authors.append(author)

        # get sections
        section = new_soup.find('meta', attrs = {'name': 'CG'})['content']
        sections.append(section)

        # get dates
        date = new_soup.find('meta', attrs = {'name': 'pdate'})['content']
        dates.append(date)

    data_dict = {
        'title': titles, 'link': links, 'author': authors, 'full_text': full_texts,
        'section': sections, 'date': dates
    }
    return data_dict

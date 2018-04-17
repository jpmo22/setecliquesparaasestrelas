from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import quote, unquote
from sqlite3 import connect
from datetime import datetime


# Creates a database
db = connect(':memory:')

# Constants
DB_COL_LINK = 0
DB_COL_PARENT_LINK = 1
DB_COL_LEVEL = 2
DB_COL_IS_READ = 3
DEFAULT_URL = 'https://pt.wikipedia.org'


class Link(object):
    def __init__(self, link, parent_link, level, is_read):
        self.link = link
        self.parent_link = parent_link
        self.level = level
        self.is_read = is_read


def init_db(cur):
    """ Database initializer """
    cur.execute('''CREATE TABLE link_table (
                        link VARCHAR PRIMARY KEY, 
                        parent_link VARCHAR, 
                        level INTEGER, 
                        is_read INTEGER)''')


def is_internal_link(tag):
    """ Removes all external links and anchors """
    return tag.name == 'a' and tag.has_attr('href') and tag.get('href').startswith('/wiki/') and tag.get('href').\
        find(':') == -1 and tag.get('href').find('#') == -1


def list_all_links(url, target_link):
    """ Lists all internal links from url informed """
    req = Request(url)
    html_page = urlopen(req)
    soup = BeautifulSoup(html_page, "lxml")
    links = []
    for link in soup.findAll(is_internal_link):
        links.append(link.get('href'))
        if link.get('href') == target_link:
            break
    return set(links)


def is_url_valid(url):
    """ Verify if url is valid """
    request = Request(url)
    request.get_method = lambda: 'HEAD'
    try:
        urlopen(request)
        return True
    except HTTPError:
        return False


def db_insert_all(links, parent_link, level, is_read):
    for link in links:
        db_insert(link, parent_link, level, is_read)


def db_insert(link, parent_link, level, is_read):
    """ Inserts the given link on Database """
    db.cursor().execute('INSERT OR IGNORE INTO link_table (link, parent_link, level, is_read) VALUES (?, ?, ?, ?)',
                        (link, parent_link, level, is_read))


def db_set_read(link):
    """ Updates the given link to is_read = True """
    if not isinstance(link, str) and not isinstance(link, Link):
        raise TypeError('The db_set_read function must receive str or Link')

    db.cursor().execute('UPDATE link_table SET is_read = 1 WHERE link = ?', (link,) if isinstance(link, str) else (link.link,))


def db_get_parent(link):
    """ Returns the parent (object) of the given link """
    if not isinstance(link, str) and not isinstance(link, Link):
        raise TypeError('The db_get_parent function must receive str or Link')

    cur = db.cursor()
    cur.execute('SELECT * FROM link_table WHERE link = ?', (link,) if isinstance(link, str) else (link.parent_link,))
    data = cur.fetchone()
    cur.close()
    return Link(data[DB_COL_LINK], data[DB_COL_PARENT_LINK], data[DB_COL_LEVEL], data[DB_COL_IS_READ]) \
        if data is not None else None


def db_next_not_read():
    """ Retrives the nex unread link from Database """
    cur = db.cursor()
    cur.execute('SELECT * FROM link_table WHERE is_read = 0 ORDER BY level ASC LIMIT 1')
    data = cur.fetchone()
    cur.close()
    return Link(data[DB_COL_LINK], data[DB_COL_PARENT_LINK], data[DB_COL_LEVEL], data[DB_COL_IS_READ]) \
        if data is not None else None


def log_track(source_link, links, target_link):
    print('TRACK:')
    print('"{}"'.format(unquote(source_link)))
    i = 0
    for link in links:
        i += 1
        print('\t' * i, '"{}"'.format(unquote(link)))

    i += 1
    print('\t' * i, '"{}"'.format(unquote(target_link)))


def db_list_parents(child_link):
    parents = []
    parents.insert(0, child_link.link)
    parent = db_get_parent(child_link)
    if child_link.level > 0:
        while parent is not None:
            parents.insert(0, parent.link)
            if parent.level == 0:
                break
            parent = db_get_parent(parent)
    return parents


def run(source_link, target_link):
    started_at = datetime.now()
    print('Starting at {}'.format(started_at))
    print('Searching for links between "{}" and "{}" in {}...'
          .format(unquote(source_link), unquote(target_link), DEFAULT_URL))
    try:
        if not is_url_valid(DEFAULT_URL + source_link):
            raise ValueError('RESULT: The source link "{}" is invalid page'.format(unquote(source_link)))
        if not is_url_valid(DEFAULT_URL + target_link):
            raise ValueError('RESULT: The target link "{}" is invalid page'.format(unquote(target_link)))

        cur = db.cursor()
        init_db(cur)
        current_link = source_link
        found_links = list_all_links(DEFAULT_URL + current_link, target_link)

        # If found target_link in the source_link
        if target_link in found_links:
            print('Found at level 0')
            log_track(source_link, [], target_link)
            return

        db_insert_all(found_links, None, 1, 0)
        db.commit()

        next_link = db_next_not_read()
        while next_link is not None:
            db_set_read(next_link.link)
            print('[level {}] Crawling "{}"... '.format(next_link.level, unquote(next_link.link)), end="", flush=True)
            links = list_all_links(DEFAULT_URL + next_link.link, target_link)
            print('{} links found'.format(len(links)))
            if target_link in links:
                print('RESULT: Found at level', next_link.level + 1)
                parents = db_list_parents(next_link)
                log_track(source_link, parents, target_link)
                return
            else:
                if (next_link.level + 1) > 7:
                    print('RESULT: Not found in 7 levels')
                    return

                db_insert_all(links, next_link.link, (next_link.level + 1), 0)

            db.commit()
            next_link = db_next_not_read()

    finally:
        print('Finished in {}'.format(datetime.now() - started_at))


if __name__ == '__main__':
    _source_link = quote('/wiki/Osvald_Moberg')
    _target_link = quote('/wiki/Ilha')
    run(_source_link, _target_link)

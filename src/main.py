import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, EXPECTED_STATUS, MAIN_DOC_URL, MAIN_PEP_URL
from outputs import control_output
from utils import find_tag, get_response, log_unexpected_status


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')

    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')

    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = (
        div_with_ul.find_all('li', attrs={'class': 'toctree-l1'})
    )

    results = [('URL', 'Header', 'Editor, Author')]

    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')
        version_link = urljoin(whats_new_url, version_a_tag['href'])
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, 'lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1.text, dl_text)
        )

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')

    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Nothing was found')

    results = [('URL', 'Version', 'Status')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, str(a_tag))
        if text_match is not None:
            version = text_match.group(1)
            status = text_match.group(2)
        else:
            version = a_tag.text
            status = ''
        results.append((link, version, status))

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')

    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')

    main_tag = find_tag(soup, 'div', {'role': 'main'})
    table_tag = find_tag(main_tag, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)

    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)

    filename = archive_url.split('/')[-1]
    archive_path = downloads_dir / filename

    response = session.get(archive_url)

    with open(archive_path, 'wb') as file:
        file.write(response.content)

    logging.info(f'Archive downloaded and saved: {archive_path}')


def pep(session):
    response = get_response(session, MAIN_PEP_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')

    numerical_index = find_tag(soup, 'section', {'id': 'numerical-index'})
    lines = numerical_index.find_all('tr')

    results = [('Status', 'Quantity')]
    statuses = {}

    for line in tqdm(lines[1:]):
        td_tag = find_tag(line, 'td')
        a_tag = find_tag(line, 'a')

        preview_status = td_tag.text[1:]
        link = urljoin(MAIN_PEP_URL, a_tag['href'])
        response = get_response(session, link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features='lxml')

        dl_tag = find_tag(soup, 'dl')
        dt_tags = dl_tag.find_all('dt')

        for dt in dt_tags:
            if dt.text == 'Status:':
                view_status = dt.find_next_sibling('dd').string
                break

        statuses[view_status] = (
                (statuses.get(view_status) or 0) + 1
        )

        if view_status not in EXPECTED_STATUS[preview_status]:
            log_unexpected_status(
                link, view_status, EXPECTED_STATUS[preview_status]
            )

    results.extend(statuses.items())
    results.append(('Total:', len(lines[1:])))

    return results


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('PyParser launched')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Command line arguments: {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)

    if results is not None:
        control_output(results, args)
    logging.info('Parsing completed')


if __name__ == '__main__':
    main()

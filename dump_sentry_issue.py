# coding: utf-8
"""
Given a Sentry issue id, a bearer token, and a list of fields, output a CSV to
stdout of the collected data.
"""
import argparse
import datetime  # needed to `eval` some datetimes
import json
import logging
import sys

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def _get_parser():
    parser = argparse.ArgumentParser(
        description='Dump some data to CSV from a Sentry issue')

    parser.add_argument(
        '-b',
        '--bearer-token',
        nargs=1,
        required=True,
        metavar='token_hash',
        help='Your Sentry bearer token (a hexadecimal string, see https://sentry.io/api/)')

    parser.add_argument(
        '-i',
        '--issue',
        nargs=1,
        required=True,
        metavar='id',
        help='The Sentry issue id')

    parser.add_argument(
        '-m',
        '--max-events',
        nargs=1,
        required=False,
        metavar='n',
        type=int,
        help='Maximum number of events to retrieve')

    parser.add_argument(
        'fields',
        nargs='+',
        metavar='field_name',
        help='The field names you wish to capture')

    return parser


def scrape(bearer_token, issue, max_events, fields):

    initial_url = 'https://sentry.io/api/0/issues/{}/events/'.format(issue)
    authorization = 'Bearer {}'.format(bearer_token)

    urls_processed = []
    urls_to_process = [initial_url]

    contexts = []

    while urls_to_process:
        count = len(contexts)
        if max_events > 0 and count > max_events:
            logger.info(
                'Got %d events, requested max %d events. Ending event-fetching early.',
                count,
                max_events)
            break

        url = urls_to_process.pop(0)

        logger.info('processing %s', url)

        r = requests.get(url=url, headers={
            'Content-Type': 'application/json',
            'Authorization': authorization,
        })

        urls_processed.append(url)

        if r.status_code > 200:
            logger.error('Got non-200 response: %d', r.status_code)
            break

        # Pull "next" links out of response headers and throw them on the pile of
        # urls to process. An example of the Link header is:
        #   '<https://sentry.io/api/...>; rel="previous"; results="false"; cursor="1478885085000:0:1", '
        #   '<https://sentry.io/api/...>; rel="next"; results="true"; cursor="1478807933000:0:0"'
        # What this block does is (roughly) break up into individul links, break up
        # each link into (url, rel, results, cursor), discard non-next and
        # non-results links, keep only the url, drop the angle brackets enclosing
        # the url
        link_header = r.headers.get('Link', '')
        if link_header:
            next_links = [
                link[0][1:-1] for link in [
                    l.split('; ') for l in link_header.split(', ')
                ] if 'rel="next"' in link and 'results="true"' in link
            ]
            urls_to_process.extend(next_links)

        content = json.loads(r.content)
        contexts.extend([event['context'] for event in content])

    logger.info('%d urls processed...', len(urls_processed))
    logger.info('generating csv...')

    # column names
    print('') # blank leading row
    print(','.join(
        [''] +  # blank leading column
        fields))

    # create a new context, once keys we don't care about have been removed.
    cleaned_contexts = []
    for ctx in contexts:
        ctx = {k: v for k, v in ctx.items() if k in fields}
        cleaned_contexts.append(ctx)

    for ctx in cleaned_contexts:
        # Sentry presents most values as their Python repr strings -- here we'll
        # get back our ints and datetimes into native Python types and strings will
        # be "unwrapped" (e.g. u'u"foo"' becomes u"foo")
        for k, v in ctx.items():
            if isinstance(v, str):
                try:
                    ctx[k] = eval(v)
                except SyntaxError:
                    pass
            if isinstance(ctx[k], datetime.date):
                ctx[k] = ctx[k].isoformat()

        # Output something csv-like
        print(','.join(
            [''] +  # blank leading column
            [str(ctx[f]) for f in fields]
        ))


if __name__ == '__main__':
    parser = _get_parser()
    settings = parser.parse_args()
    scrape(
        settings.bearer_token[0],
        settings.issue[0],
        settings.max_events[0] if settings.max_events else -1,
        settings.fields)

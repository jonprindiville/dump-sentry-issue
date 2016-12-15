# dump-sentry-issue
CLI tool to dump some data from a Sentry issue to CSV


## Requirements

- You should have a [Sentry](https://sentry.io) account and some issue from which you'd like to extract some data.

- This tool depends on the `requests` library. You can install it pretty easily with `pip install requests`. You might want to do that in [a virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) -- your call!

## Usage

```
usage: dump_sentry_issue.py [-h] -b token_hash -i id
                            field_name [field_name ...]

Dump some data to CSV from a Sentry issue

positional arguments:
  field_name            The field names you wish to capture

optional arguments:
  -h, --help            show this help message and exit
  -b token_hash, --bearer-token token_hash
                        Your Sentry bearer token (a hexadecimal string, see
                        https://sentry.io/api/)
  -i id, --issue id     The Sentry issue id
```

## Output format

By default you're going to get something CSV-like on stdout (you could redirect it to a file if you like) and some logger output on stderr.

For example:

```
$ python dump_sentry_issue.py -b YOUR_BEARER_TOKEN -i YOUR_EVENT_ID id_param gapi_departure_id
2016-12-15 09:56:14,213 - __main__ - INFO - processing https://sentry.io/api/0/issues/YOUR_EVENT_ID/events/
2016-12-15 09:56:16,361 - __main__ - INFO - 1 urls processed...
2016-12-15 09:56:16,361 - __main__ - INFO - generating csv...

,id_param,gapi_departure_id
,1484285,605831
,1700248,639472
,1497602,542842
,1380424,600239
,1571296,646942
,1452581,532488
...
```

## Thing this tool does not do

- non-CSV output (or CSV output without empty leading row/column)
- limit the number of returned rows (we just page through everything that Sentry gives us)
- any fancy handling of the data the Sentry gives back (Sentry returns most values as `repr`-strings, for instance if you sent Sentry the string `u'foo'` it would come back through their API as `u"u'foo'"`. We `eval` the values to get back a Python value -- if your value is a list, probably the things inside your list will still be `repr`-strings, and also the commas in the list's representation will mess up your CSV... we could be nicer and more extensible about post-processing the received data, but we're not... maybe later)

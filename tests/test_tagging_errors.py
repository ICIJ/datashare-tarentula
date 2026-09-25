import re

import click
import pytest
import responses
from click.testing import CliRunner
from requests.exceptions import ReadTimeout

from tarentula.cli import cli
from tarentula.tag_cleaning_by_query import TagsCleanerByQuery
from tarentula.tagging import Tagger
from tarentula.tagging_by_query import TaggerByQuery

DATASHARE_URL = 'http://localhost:8080'
DATASHARE_PROJECT = 'local-datashare'
TAGGING_ENDPOINT_RE = re.compile(r'^%s/api/%s/documents/tags/' % (DATASHARE_URL, DATASHARE_PROJECT))

THREE_DOCUMENTS_CSV = ('tag,documentId\n'
                       'spider,aaaaaaaaaaaaaaaaaaaa\n'
                       'spider,bbbbbbbbbbbbbbbbbbbb\n'
                       'spider,cccccccccccccccccccc\n')


def csv_file(tmp_path, content=THREE_DOCUMENTS_CSV):
    path = tmp_path / 'tags.csv'
    path.write_text(content)
    return str(path)


def invoke_tagging(path):
    return CliRunner().invoke(cli, ['tagging', '--datashare-url', DATASHARE_URL,
                                    '--datashare-project', DATASHARE_PROJECT, path])


@responses.activate
def test_a_read_timeout_does_not_abort_the_remaining_documents(tmp_path):
    responses.add(responses.PUT, TAGGING_ENDPOINT_RE, body='', status=201)
    responses.add(responses.PUT, TAGGING_ENDPOINT_RE, body=ReadTimeout('timed out'))
    responses.add(responses.PUT, TAGGING_ENDPOINT_RE, body='', status=201)
    invoke_tagging(csv_file(tmp_path))
    assert len(responses.calls) == 3


@responses.activate
def test_exit_code_is_not_zero_when_every_tagging_request_fails(tmp_path):
    responses.add(responses.PUT, TAGGING_ENDPOINT_RE, body='{"error":"boom"}', status=500)
    result = invoke_tagging(csv_file(tmp_path))
    assert result.exit_code != 0


def test_a_blank_tag_cell_is_a_readable_error(tmp_path):
    tagger = Tagger(csv_path=csv_file(tmp_path, 'tag,documentId\n,atypidae\n'))
    with pytest.raises(click.BadParameter):
        tagger.tree


def test_a_csv_without_a_tag_column_is_a_readable_error(tmp_path):
    tagger = Tagger(csv_path=csv_file(tmp_path, 'documentId,routing\natypidae,atypidae\n'))
    with pytest.raises(click.BadParameter):
        tagger.tree


@pytest.mark.parametrize('cookies', ['Cookie: _ds_session_id=abc', '_ds_session_id=abc; display name=bob'])
def test_a_malformed_cookie_string_is_a_readable_error(cookies):
    for tagger in (Tagger(cookies=cookies),
                   TaggerByQuery(cookies=cookies),
                   TagsCleanerByQuery(cookies=cookies)):
        with pytest.raises(click.BadParameter):
            tagger.cookies

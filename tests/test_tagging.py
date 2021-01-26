import csv
import re
import responses

from click.testing import CliRunner
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

from .test_abstract import TestAbstract
from tarentula.cli import cli
from tarentula.tagging import Tagger


class TestTagging(TestAbstract):

    @contextmanager
    def mock_tagging_endpoint(self):
        with responses.RequestsMock() as resp:
            tagging_endpoint_re = r"^%s\/api/%s/documents/tags/" % (self.datashare_url, self.datashare_project)
            resp.add(responses.PUT, re.compile(tagging_endpoint_re), body='', status=201)
            yield resp

    def test_summary(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\n'
                       b'Actinopodidae,l7VnZZEzg2fr960NWWEG,l7VnZZEzg2fr960NWWEG\n'
                       b'Antrodiaetidae,DWLOskax28jPQ2CjFrCo')
            file.flush()
            file.seek(0)
            with self.mock_tagging_endpoint():
                runner = CliRunner()
                result = runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project',
                                             self.datashare_project, file.name])
                self.assertIn('Adding 2 tags to 2 documents', result.output)

    def test_progression(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\n'
                       b'Actinopodidae,l7VnZZEzg2fr960NWWEG,l7VnZZEzg2fr960NWWEG\n'
                       b'Antrodiaetidae,DWLOskax28jPQ2CjFrCo')
            file.flush()
            file.seek(0)
            with self.mock_tagging_endpoint():
                runner = CliRunner()
                result = runner.invoke(cli, ['--stdout-loglevel', 'INFO', 'tagging', '--datashare-url',
                                             self.datashare_url, '--datashare-project', self.datashare_project,
                                             file.name])
                self.assertIn('Added "Actinopodidae" to document "l7VnZZEzg2fr960NWWEG"', result.output)
                self.assertIn('Added "Antrodiaetidae" to document "DWLOskax28jPQ2CjFrCo"', result.output)
                self.assertTrue(result.exit_code == 0)

    def test_http_tagging_requests(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\n'
                       b'Actinopodidae,l7VnZZEzg2fr960NWWEG,l7VnZZEzg2fr960NWWEG\n'
                       b'Antrodiaetidae,DWLOskax28jPQ2CjFrCo')
            file.flush()
            file.seek(0)
            with self.mock_tagging_endpoint() as resp:
                runner = CliRunner()
                runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project',
                                    self.datashare_project, file.name])
                self.assertTrue(len(resp.calls) == 2)

    def test_routing_is_correct(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\n'
                       b'Actinopodidae,l7VnZZEzg2fr960NWWEG,l7VnZZEzg2fr960NWWEG\n'
                       b'Atracidae,6VE7cVlWszkUd94XeuSd,vZJQpKQYhcI577gJR0aN')
            file.flush()
            file.seek(0)
            tagger = Tagger(self.datashare_url, self.datashare_project, 0, file.name, progressbar=False)
            self.assertEqual(tagger.tree['l7VnZZEzg2fr960NWWEG']['routing'], 'l7VnZZEzg2fr960NWWEG')
            self.assertEqual(tagger.tree['6VE7cVlWszkUd94XeuSd']['routing'], 'vZJQpKQYhcI577gJR0aN')

    def test_routing_uses_fallback(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\n'
                       b'Antrodiaetidae,DWLOskax28jPQ2CjFrCo')
            file.flush()
            file.seek(0)
            tagger = Tagger(self.datashare_url, self.datashare_project, 0, file.name, progressbar=False)
            self.assertEqual(tagger.tree['DWLOskax28jPQ2CjFrCo']['routing'], 'DWLOskax28jPQ2CjFrCo')

    def test_document_is_in_tree(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\n'
                       b'Actinopodidae,l7VnZZEzg2fr960NWWEG,l7VnZZEzg2fr960NWWEG')
            file.flush()
            file.seek(0)
            tagger = Tagger(self.datashare_url, self.datashare_project, 0, file.name, progressbar=False)
            self.assertIn('l7VnZZEzg2fr960NWWEG', tagger.tree)

    def test_tags_are_in_tree(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\n'
                       b'Antrodiaetidae,DWLOskax28jPQ2CjFrCo\n'
                       b'Idiopidae,DWLOskax28jPQ2CjFrCo,DWLOskax28jPQ2CjFrCo')
            file.flush()
            file.seek(0)
            tagger = Tagger(self.datashare_url, self.datashare_project, 0, file.name, progressbar=False)
            self.assertIn('Antrodiaetidae', tagger.tree['DWLOskax28jPQ2CjFrCo']['tags'])
            self.assertIn('Idiopidae', tagger.tree['DWLOskax28jPQ2CjFrCo']['tags'])

    def test_document_has_two_tags(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\n'
                       b'Antrodiaetidae,DWLOskax28jPQ2CjFrCo\n'
                       b'Idiopidae,DWLOskax28jPQ2CjFrCo,DWLOskax28jPQ2CjFrCo')
            file.flush()
            file.seek(0)
            tagger = Tagger(self.datashare_url, self.datashare_project, 0, file.name)
            self.assertEqual(len(tagger.tree['DWLOskax28jPQ2CjFrCo']['tags']), 2)

    def test_tags_are_in_tree_with_url(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentUrl\n'
                       b'Antrodiaetidae,http://localhost:8080/#/d/local-datashare/DWLOskax28jPQ2CjFrCo\n'
                       b'Idiopidae,http://localhost:8080/#/d/local-datashare/DWLOskax28jPQ2CjFrCo/DWLOskax28jPQ2CjFrCo')
            file.flush()
            file.seek(0)
            tagger = Tagger(self.datashare_url, self.datashare_project, 0, file.name)
            self.assertIn('Antrodiaetidae', tagger.tree['DWLOskax28jPQ2CjFrCo']['tags'])
            self.assertIn('Idiopidae', tagger.tree['DWLOskax28jPQ2CjFrCo']['tags'])

    def test_routing_is_correct_with_url(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentUrl\n'
                       b'Actinopodidae,http://localhost:8080/#/d/local-datashare/l7VnZZEzg2fr960NWWEG/'
                       b'l7VnZZEzg2fr960NWWEG\n'
                       b'Atracidae,http://localhost:8080/#/d/local-datashare/6VE7cVlWszkUd94XeuSd/vZJQpKQYhcI577gJR0aN')
            file.flush()
            file.seek(0)
            tagger = Tagger(self.datashare_url, self.datashare_project, 0, file.name)
            self.assertEqual(tagger.tree['l7VnZZEzg2fr960NWWEG']['routing'], 'l7VnZZEzg2fr960NWWEG')
            self.assertEqual(tagger.tree['6VE7cVlWszkUd94XeuSd']['routing'], 'vZJQpKQYhcI577gJR0aN')

    def test_tags_are_all_created(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\n'
                       b'Actinopodidae,l7VnZZEzg2fr960NWWEG,l7VnZZEzg2fr960NWWEG\n'
                       b'Antrodiaetidae,DWLOskax28jPQ2CjFrCo')
            file.flush()
            file.seek(0)
            with self.datashare_client.temporary_project(self.datashare_project) as project:
                tagger = Tagger(self.datashare_url, project, 0, file.name, progressbar=False)
                # Ensure there is no documents yet
                self.assertEqual(self.datashare_client.query(index=project, size=0).get('hits', {}).get('total', {}).get('value', None), 0)
                # Create all the docs
                for document_id, leaf in tagger.tree.items():
                    self.datashare_client.index(project, {'tags': []}, document_id, leaf['routing'])
                # Ensure the docs exists
                self.assertEqual(self.datashare_client.query(index=project, size=0).get('hits', {}).get('total', {}).get('value', None), 2)
                # Ensure the docs are not tagged yet
                self.assertEqual(self.datashare_client.query(index=project, size=0, q='tags:*')
                                 .get('hits', {}).get('total', {}).get('value', None), 0)
                # Tag them all!
                tagger.start()
                # Refresh the index
                self.datashare_client.refresh(project)
                # Ensure the docs have been tagged
                self.assertEqual(self.datashare_client.query(index=project, size=0, q='tags:*')
                                 .get('hits', {}).get('total', {}).get('value', None), 2)

    def test_tag_is_correct(self):
        with self.datashare_client.temporary_project(self.datashare_project) as project:
            # Create the document
            self.datashare_client.index(index=project,  document={'name': 'Atypidae', 'tags': []}, id='atypidae')
            runner = CliRunner()
            with runner.isolated_filesystem():
                # Create a small CSV with just one tag
                with open('tags.csv', 'w') as file:
                    writer = csv.writer(file)
                    writer.writerows([['tag', 'documentId'], ['mygalomorph', 'atypidae']])
                runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project', project,
                                    'tags.csv'])
            # Get the document from Elasticsearch
            document = self.datashare_client.document(index=project, id='atypidae')
            self.assertIn('mygalomorph', document.get('_source', {}).get('tags', []))

    def test_tags_are_correct(self):
        with self.datashare_client.temporary_project(self.datashare_project) as project:
            # Create the document
            self.datashare_client.index(index=project, document={'name': 'Atypidae', 'tags': []}, id='atypidae')
            runner = CliRunner()
            with runner.isolated_filesystem():
                # Create a small CSV with just one tag
                with open('tags.csv', 'w') as file:
                    writer = csv.writer(file)
                    writer.writerows([['tag', 'documentId'], ['mygalomorph', 'atypidae'], ['spider', 'atypidae']])
                runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project',
                                    project, 'tags.csv'])
            # Get the document from Elasticsearch
            document = self.datashare_client.document(index=project, id='atypidae')
            self.assertIn('mygalomorph', document.get('_source').get('tags', []))
            self.assertIn('spider', document.get('_source').get('tags', []))

    def test_cookies_are_parsed_by_tagger(self):
        with NamedTemporaryFile() as file:
            cookies = 'session=mygalomorph;age=14'
            tagger = Tagger(self.datashare_url, self.datashare_project, 0, file.name, cookies, progressbar=False)
            self.assertEqual(tagger.cookies['session'], 'mygalomorph')
            self.assertEqual(tagger.cookies['age'], '14')
            self.assertEqual(len(tagger.cookies.keys()), 2)

    def test_multiple_cookies_are_parsed_by_tagger(self):
        with NamedTemporaryFile() as file:
            cookies = 'session=mygalomorph'
            tagger = Tagger(self.datashare_url, self.datashare_project, 0, file.name, cookies, progressbar=False)
            self.assertEqual(tagger.cookies['session'], 'mygalomorph')
            self.assertEqual(len(tagger.cookies.keys()), 1)

    def test_session_cookies_are_parsed_by_tagger(self):
        with NamedTemporaryFile() as file:
            cookies = r'_ds_session_id="{\"login\":\"\",\"roles\":[],\"sessionId\":\"dq18s0kj08dq10skLYGSu8SFVsg\",' \
                      r'\"redirectAfterLogin\":\"/\"}"'
            tagger = Tagger(self.datashare_url, self.datashare_project, 0, file.name, cookies, progressbar=False)
            self.assertEqual(tagger.cookies['_ds_session_id'], r'{"login":"","roles":[],"sessionId":'
                                                               r'"dq18s0kj08dq10skLYGSu8SFVsg",'
                                                               r'"redirectAfterLogin":"/"}')
            self.assertEqual(len(tagger.cookies.keys()), 1)

    def test_cookies_are_sent_while_tagging(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\n'
                       b'Actinopodidae,l7VnZZEzg2fr960NWWEG,l7VnZZEzg2fr960NWWEG\n'
                       b'Antrodiaetidae,DWLOskax28jPQ2CjFrCo')
            file.flush()
            file.seek(0)
            with self.mock_tagging_endpoint() as resp:
                cookies = 'session=mygalomorph'
                Tagger(self.datashare_url, self.datashare_project, 0, file.name, cookies, progressbar=False).start()
                self.assertEqual(resp.calls[0].request.headers['Cookie'], cookies)
                self.assertEqual(resp.calls[1].request.headers['Cookie'], cookies)

    def test_cookies_are_NOT_sent_while_tagging(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\n'
                       b'Actinopodidae,l7VnZZEzg2fr960NWWEG,l7VnZZEzg2fr960NWWEG\n'
                       b'Antrodiaetidae,DWLOskax28jPQ2CjFrCo')
            file.flush()
            file.seek(0)
            with self.mock_tagging_endpoint() as resp:
                Tagger(self.datashare_url, self.datashare_project, 0, file.name, progressbar=False).start()
                self.assertNotIn('Cookie', resp.calls[0].request.headers)
                self.assertNotIn('Cookie', resp.calls[1].request.headers)

    def test_cookies_are_sent_while_tagging_with_the_cli(self):
        with NamedTemporaryFile() as file:
            file.write(b'tag,documentId,routing\n'
                       b'Actinopodidae,l7VnZZEzg2fr960NWWEG,l7VnZZEzg2fr960NWWEG\n'
                       b'Antrodiaetidae,DWLOskax28jPQ2CjFrCo')
            file.flush()
            file.seek(0)
            with self.mock_tagging_endpoint() as resp:
                cookies = r'_ds_session_id="{\"login\":\"\",\"roles\":[],\"sessionId\":' \
                          r'\"dq18s0kj08dq10skLYGSu8SFVsg\",\"redirectAfterLogin\":\"/\"}"'
                cookies_not_escaped = '_ds_session_id={"login":"","roles":[],"sessionId":' \
                                      '"dq18s0kj08dq10skLYGSu8SFVsg","redirectAfterLogin":"/"}'
                runner = CliRunner()
                runner.invoke(cli, ['tagging', '--datashare-url', self.datashare_url, '--datashare-project',
                                    self.datashare_project, '--cookies', cookies, file.name])
                self.assertEqual(resp.calls[0].request.headers['Cookie'], cookies_not_escaped)
                self.assertEqual(resp.calls[1].request.headers['Cookie'], cookies_not_escaped)

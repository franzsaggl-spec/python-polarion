"""Tests for Config and XmlParser in polarion.xml."""

import os
import pytest

from polarion.xml import Config, XmlParser
from polarion.exceptions import PolarionConfigError


# ---------------------------------------------------------------------------
# Config creation
# ---------------------------------------------------------------------------

class TestConfigCreation:
    def _valid_data(self, **overrides):
        """Return minimal valid config data dict."""
        data = {
            'xml_file': 'test.xml',
            'url': 'http://polarion.example.com/polarion',
            'project_id': 'test_project',
            'token': 'my-token',
        }
        data.update(overrides)
        return data

    def test_creation_with_valid_data(self):
        config = Config(self._valid_data())
        assert config.xml_file == 'test.xml'
        assert config.url == 'http://polarion.example.com/polarion'
        assert config.project_id == 'test_project'
        assert config.token == 'my-token'

    def test_creation_with_user_password(self):
        config = Config(self._valid_data(
            token=None, username='user', password='pass'))
        assert config.username == 'user'
        assert config.password == 'pass'

    def test_from_dict(self):
        config = Config.from_dict(self._valid_data())
        assert config.xml_file == 'test.xml'


# ---------------------------------------------------------------------------
# Mandatory field validation
# ---------------------------------------------------------------------------

class TestConfigMandatory:
    def test_missing_xml_file_raises(self):
        with pytest.raises(PolarionConfigError, match='xml_file'):
            Config({
                'url': 'http://example.com',
                'project_id': 'proj',
                'token': 'tok',
            })

    def test_missing_url_raises(self):
        with pytest.raises(PolarionConfigError, match='url'):
            Config({
                'xml_file': 'test.xml',
                'project_id': 'proj',
                'token': 'tok',
            })

    def test_missing_project_id_raises(self):
        with pytest.raises(PolarionConfigError, match='project_id'):
            Config({
                'xml_file': 'test.xml',
                'url': 'http://example.com',
                'token': 'tok',
            })

    def test_no_auth_raises(self):
        with pytest.raises(PolarionConfigError):
            Config({
                'xml_file': 'test.xml',
                'url': 'http://example.com',
                'project_id': 'proj',
            })

    def test_only_username_no_password_raises(self):
        with pytest.raises(PolarionConfigError):
            Config({
                'xml_file': 'test.xml',
                'url': 'http://example.com',
                'project_id': 'proj',
                'username': 'user',
            })


# ---------------------------------------------------------------------------
# generate_test_run_id
# ---------------------------------------------------------------------------

class TestGenerateTestRunId:
    def test_default_format(self):
        config = Config({
            'xml_file': 'test.xml',
            'url': 'http://example.com',
            'project_id': 'proj',
            'token': 'tok',
        })
        run_id = config.generate_test_run_id()
        assert run_id.startswith('unit-')
        # Should be in format unit-YYYY-MM-DD-HH-MM-SS-ffffff
        parts = run_id.split('-')
        assert len(parts) >= 8  # unit + year + month + day + hour + min + sec + microsec

    def test_custom_generator(self):
        config = Config({
            'xml_file': 'test.xml',
            'url': 'http://example.com',
            'project_id': 'proj',
            'token': 'tok',
            'testrun_id_generator': lambda c: 'custom-id-123',
        })
        run_id = config.generate_test_run_id()
        assert run_id == 'custom-id-123'

    def test_existing_id_returned(self):
        config = Config({
            'xml_file': 'test.xml',
            'url': 'http://example.com',
            'project_id': 'proj',
            'token': 'tok',
            'testrun_id': 'existing-id',
        })
        run_id = config.generate_test_run_id()
        assert run_id == 'existing-id'


# ---------------------------------------------------------------------------
# _default_value
# ---------------------------------------------------------------------------

class TestDefaultValue:
    def test_testrun_title_default(self):
        assert Config._default_value('testrun_title') == 'New unit test run'

    def test_testrun_type_default(self):
        assert Config._default_value('testrun_type') == 'xUnit Test Manual Upload'

    def test_skip_missing_testcase_default(self):
        assert Config._default_value('skip_missing_testcase') is False

    def test_verify_cert_default(self):
        assert Config._default_value('verify_cert') is True

    def test_use_cache_default(self):
        assert Config._default_value('use_cache') is False

    def test_unknown_attribute_default_none(self):
        assert Config._default_value('nonexistent') is None


# ---------------------------------------------------------------------------
# XmlParser.tranform_string_properties
# ---------------------------------------------------------------------------

class TestXmlParserTransformStringProperties:
    def test_single_property(self):
        result = XmlParser.tranform_string_properties('[[PROPERTY|verifies=REQ-001]]')
        assert len(result) == 1
        assert result[0]['name'] == 'verifies'
        assert result[0]['value'] == 'REQ-001'

    def test_multiple_properties_on_separate_lines(self):
        # Each property must be on its own line due to greedy regex matching
        text = '[[PROPERTY|verifies=REQ-001]]\n[[PROPERTY|validates=REQ-002]]'
        result = XmlParser.tranform_string_properties(text)
        assert len(result) == 2

    def test_no_properties(self):
        result = XmlParser.tranform_string_properties('plain text no properties')
        assert result == []

    def test_empty_string(self):
        result = XmlParser.tranform_string_properties('')
        assert result == []


# ---------------------------------------------------------------------------
# XmlParser.parse_root
# ---------------------------------------------------------------------------

class TestXmlParserParseRoot:
    def test_parse_minimal_testsuites(self, tmp_path):
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
  <testsuite name="suite1">
    <testcase name="test1" classname="com.example.Test"/>
  </testsuite>
</testsuites>'''
        xml_file = tmp_path / 'test_results.xml'
        xml_file.write_text(xml_content)

        cases = XmlParser.parse_root(str(xml_file))
        assert len(cases) == 1
        assert cases[0]['id'] == 'com.example.Test.test1'

    def test_parse_single_testsuite(self, tmp_path):
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="suite1">
  <testcase name="test1" classname="com.example.Test"/>
  <testcase name="test2" classname="com.example.Test"/>
</testsuite>'''
        xml_file = tmp_path / 'test_results.xml'
        xml_file.write_text(xml_content)

        cases = XmlParser.parse_root(str(xml_file))
        assert len(cases) == 2

    def test_parse_with_failure(self, tmp_path):
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="suite1">
  <testcase name="failing_test" classname="com.example.Test">
    <failure message="assertion failed">Expected true but got false</failure>
  </testcase>
</testsuite>'''
        xml_file = tmp_path / 'test_results.xml'
        xml_file.write_text(xml_content)

        cases = XmlParser.parse_root(str(xml_file))
        assert len(cases) == 1
        assert 'failure' in cases[0]
        assert 'assertion failed' in cases[0]['failure']

    def test_parse_with_properties(self, tmp_path):
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="suite1">
  <testcase name="test1" classname="com.example.Test">
    <properties>
      <property name="verifies" value="REQ-001"/>
    </properties>
  </testcase>
</testsuite>'''
        xml_file = tmp_path / 'test_results.xml'
        xml_file.write_text(xml_content)

        cases = XmlParser.parse_root(str(xml_file))
        assert len(cases) == 1
        assert 'properties' in cases[0]
        assert {'verifies': 'REQ-001'} in cases[0]['properties']

    def test_parse_unmanaged_root_raises(self, tmp_path):
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<unknown_root/>'''
        xml_file = tmp_path / 'test_results.xml'
        xml_file.write_text(xml_content)

        with pytest.raises(PolarionConfigError, match='Unmanaged root'):
            XmlParser.parse_root(str(xml_file))

    def test_parse_with_time_attribute(self, tmp_path):
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="suite1">
  <testcase name="test1" classname="com.example.Test" time="0.123"/>
</testsuite>'''
        xml_file = tmp_path / 'test_results.xml'
        xml_file.write_text(xml_content)

        cases = XmlParser.parse_root(str(xml_file))
        assert cases[0]['time'] == '0.123'

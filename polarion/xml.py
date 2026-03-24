from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from .client import Polarion
from .exceptions import PolarionConfigError
from .record import Record

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Config structure for the XML importer.

    Required fields: xml_file, url, project_id, and either token or
    username+password.
    """

    xml_file: str
    url: str
    project_id: str
    username: str | None = None
    password: str | None = None
    token: str | None = None
    testrun_id: str | None = None
    testrun_id_generator: Callable[[Config], str] | None = None
    testrun_title: str = "New unit test run"
    testrun_type: str = "xUnit Test Manual Upload"
    testrun_comment: str | None = None
    skip_missing_testcase: bool = False
    verify_cert: bool | str = True
    use_cache: bool = False

    def __post_init__(self) -> None:
        self._check_mandatory()

    def _check_mandatory(self) -> None:
        if not self.xml_file:
            raise PolarionConfigError("xml_file shall be set")
        if not self.url:
            raise PolarionConfigError("url shall be set")
        if not self.project_id:
            raise PolarionConfigError("project_id shall be set")
        if self.token is None and (self.username is None or self.password is None):
            raise PolarionConfigError("Shall set either username / password or token")

    @classmethod
    def from_json(cls, json_file: str) -> Config:
        """Create config from a JSON file."""
        with open(json_file, "r") as f:
            return cls(**json.loads(f.read()))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create config from a dict."""
        return cls(**data)

    def generate_test_run_id(self) -> str:
        """Generate or return the test run ID."""
        if self.testrun_id is None:
            if self.testrun_id_generator is not None:
                self.testrun_id = self.testrun_id_generator(self)
            else:
                self.testrun_id = f"unit-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S-%f')}"
        return self.testrun_id


class XmlParser:
    """XML parser for xml_junit.xsd format."""

    TEST_SUITES = "testsuites"
    TEST_SUITE = "testsuite"
    TEST_CASE = "testcase"
    PROPERTIES = "properties"
    PROPERTY = "property"
    SYSOUT = "system-out"

    @classmethod
    def parse_root(cls, xml_file: str) -> list[dict[str, Any]]:
        """Parse an XML file.

        :return: List of cases for the file
        """
        root = ET.parse(xml_file).getroot()
        returned_cases: list[dict[str, Any]] = []
        if root.tag == XmlParser.TEST_SUITES:
            for test_suite in root:
                XmlParser._parse_suite(test_suite, {"path": f"{xml_file}/{XmlParser.TEST_SUITES}"}, returned_cases)
        elif root.tag == XmlParser.TEST_SUITE:
            XmlParser._parse_suite(root, {"path": f"{xml_file}/{XmlParser.TEST_SUITE}"}, returned_cases)
        else:
            raise PolarionConfigError(f"Unmanaged root {root.tag} in {xml_file}")
        return returned_cases

    @classmethod
    def _parse_suite(cls, test_suite: Any, parent: dict[str, Any], returned_cases: list[dict[str, Any]]) -> None:
        """Parse test_suite node child of parent and append returned_cases.

        :param test_suite: test_suite node to parse
        :param parent: parent node (used for log)
        :param returned_cases: as result, append test case of the suite to this list
        """
        if test_suite.tag == XmlParser.TEST_SUITE:
            suite = parent.copy()
            suite.update({"path": f"{parent['path']}/{XmlParser.TEST_SUITE}{XmlParser._xmlnode_name(test_suite)}"})
            if "timestamp" in test_suite.attrib:
                suite.update({"timestamp": test_suite.attrib["timestamp"]})
            for child in test_suite:
                if child.tag == XmlParser.TEST_SUITE:
                    XmlParser._parse_suite(child, suite, returned_cases)
                if child.tag == XmlParser.TEST_CASE:
                    XmlParser._parse_case(child, suite, returned_cases)
        else:
            raise PolarionConfigError(f"Unmanaged {XmlParser.TEST_SUITE} {test_suite.tag} in {parent['path']}")

    # matches expressions like [[PROPERTY|verifies=REQ-001]]
    RE_PATTTERN = re.compile("\\[\\[PROPERTY\\|(.*)\\=(.*)\\]\\]")

    @classmethod
    def tranform_string_properties(cls, value: str) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []
        tmp = XmlParser.RE_PATTTERN.findall(value)
        for res in tmp:
            if len(res) == 2:
                result.append({"name": res[0], "value": res[1]})
        return result

    @classmethod
    def _parse_case(cls, test_case: Any, parent: dict[str, Any], returned_cases: list[dict[str, Any]]) -> None:
        if test_case.tag == XmlParser.TEST_CASE:
            case = parent.copy()
            case.update({"path": f"{parent['path']}/{XmlParser.TEST_CASE}{XmlParser._xmlnode_name(test_case)}"})
            # id
            if "name" not in test_case.attrib.keys() or "classname" not in test_case.attrib.keys():
                logger.warning(f"{case['path']}: no name or classname. Case skipped")
                return
            case.update({"id": test_case.attrib["classname"] + "." + test_case.attrib["name"]})

            # time
            if "time" in test_case.attrib.keys():
                case.update({"time": test_case.attrib["time"]})

            # error & failure & properties
            for elem in test_case:
                if elem.tag in ["error", "failure", "skipped"]:
                    text = []
                    for attrib in ["type", "message"]:
                        if attrib in elem.attrib.keys():
                            text.append(elem.attrib[attrib])
                    if elem.text is not None:
                        text.append(elem.text)
                    case.update({elem.tag: "\n".join(text)})
                elif elem.tag == XmlParser.PROPERTIES:
                    if "properties" not in case:
                        case.update({"properties": []})
                    for prop in elem:
                        if (
                            XmlParser.PROPERTY == prop.tag
                            and "name" in prop.attrib.keys()
                            and "value" in prop.attrib.keys()
                        ):
                            case["properties"].append({prop.get("name"): prop.get("value")})
                elif elem.tag == XmlParser.SYSOUT:
                    if "properties" not in case:
                        case.update({"properties": []})
                    for prop in XmlParser.tranform_string_properties(elem.text):
                        case["properties"].append({prop["name"]: prop["value"]})
            returned_cases.append(case)
        else:
            raise PolarionConfigError(f"Unmanaged {XmlParser.TEST_CASE} {test_case.tag} in {parent['path']}")

    @classmethod
    def _xmlnode_name(cls, node: Any) -> str:
        """Build name of the xmlnode."""
        if "name" in node.attrib.keys():
            return f"{node.tag}[name={node.attrib['name']}]"
        return node.tag


class Importer:
    """Import an XML file to Polarion using a config."""

    TEST_CASE_ID_CUSTOM_FIELD = "testCaseID"
    TEST_CASE_TYPE = "type:testcase"
    TEST_CASE_WI_TYPE = "testcase"
    TEST_CASE_WI_TITLE = "title"
    TEST_RUN_COMMENT_CUSTOM_FIELD = "environmentDescription"

    @classmethod
    def from_xml(cls, config: Config) -> Any:
        """Import an XML file having junit.xsd structure (see documentation)."""
        logger.info(f"Parsing test file {config.xml_file}")
        cases = XmlParser.parse_root(config.xml_file)

        logger.info(f"Connection to polarion {config.url} on project {config.project_id}")

        polarion = Polarion(
            polarion_url=config.url,
            user=config.username or "",
            password=config.password,
            token=config.token,
            verify_certificate=config.verify_cert,
        )
        project = polarion.get_project(config.project_id)

        # Index existing test cases by the testCaseID custom field
        test_cases = project.search_workitems(
            Importer.TEST_CASE_TYPE, field_list=["id", f"customFields.{Importer.TEST_CASE_ID_CUSTOM_FIELD}"]
        )
        test_cases_from_id: dict[str, str] = {}
        for test_case in test_cases:
            if isinstance(test_case, dict):
                custom_fields = test_case.get("customFields")
                if custom_fields is not None:
                    cf_list = custom_fields if isinstance(custom_fields, list) else [custom_fields]
                    for custom in cf_list:
                        if isinstance(custom, dict):
                            if custom.get("key") == Importer.TEST_CASE_ID_CUSTOM_FIELD:
                                value = custom.get("value")
                                if value is not None:
                                    wi_id = test_case.get("id")
                                    if wi_id is not None:
                                        test_cases_from_id[value] = wi_id

        # Getting or creating test run
        if config.testrun_id is None:
            config.generate_test_run_id()
            logger.info(f"Creating testrun {config.testrun_id}")
            test_run = project.create_test_run(config.testrun_id, config.testrun_title, config.testrun_type)
        else:
            logger.info(f"Loading testrun {config.testrun_id}")
            test_run = project.get_test_run(config.testrun_id)

        # Updating test run comment
        if config.testrun_comment is not None:
            comment = "<html><body>" + config.testrun_comment + "</body></html>"
            custom_field = test_run.get_custom_field(Importer.TEST_RUN_COMMENT_CUSTOM_FIELD)
            if custom_field is not None:
                content = custom_field if isinstance(custom_field, str) else custom_field.get("content", "")
                if content is not None:
                    split = content.split("</body>")
                    if len(split) == 2:
                        comment = split[0] + "<br>" + config.testrun_comment + "</body></html>"
                    else:
                        logger.warning(
                            f"unable to parse properly {Importer.TEST_RUN_COMMENT_CUSTOM_FIELD} of testrun: {content}. So it is not updated"
                        )
            test_run.set_custom_field(
                Importer.TEST_RUN_COMMENT_CUSTOM_FIELD,
                {"content": comment, "type": "text/html", "contentLossy": False},
            )

        # Cache for work items used for traceability links
        cache_for_workitems: dict[str, Any] = {}

        # Filling results
        logger.info("Saving results")
        for case in cases:
            if case["id"] not in test_cases_from_id.keys():
                if config.skip_missing_testcase:
                    logger.warning(f"Skipping case with {Importer.TEST_CASE_ID_CUSTOM_FIELD} {case['id']}")
                    continue
                logger.info(f"Creating case with {Importer.TEST_CASE_ID_CUSTOM_FIELD} {case['id']}")
                wi_case = project.create_workitem(
                    workitem_type=Importer.TEST_CASE_WI_TYPE,
                    fields={Importer.TEST_CASE_WI_TITLE: case["id"]},
                )
                wi_case.set_custom_field(key=Importer.TEST_CASE_ID_CUSTOM_FIELD, value=case["id"])
            else:
                wi_case = project.get_workitem(test_cases_from_id[case["id"]])
            test_run.add_test_case(wi_case)

            if "time" in case.keys():
                test_run.records[-1].duration = case["time"]

            if "timestamp" in case.keys():
                test_run.records[-1].executed = case["timestamp"]

            if "failure" in case.keys():
                test_run.records[-1].set_result(Record.ResultType.FAILED, case["failure"])
            elif "error" in case.keys():
                test_run.records[-1].set_result(Record.ResultType.BLOCKED, case["error"])
            elif "skipped" in case.keys():
                test_run.records[-1].set_result(Record.ResultType.NOTTESTED, case["skipped"])
            else:
                test_run.records[-1].set_result(Record.ResultType.PASSED)

            # Handle traceability -- links are made using IDs or titles.
            # Because of the API, traceability must use the default role,
            # not the opposite one.  This implementation does not allow
            # traceability between test cases.
            if "properties" in case.keys():
                for prop in case["properties"]:
                    for key in prop.keys():
                        linked_item = None
                        title = prop.get(key)
                        if title in cache_for_workitems:
                            linked_item = cache_for_workitems[title]
                        else:
                            try:
                                linked_item = project.get_workitem(prop.get(key))
                            except Exception:
                                linked_items = project.search_workitems(
                                    query=f"title:{title}", field_list=["id", "title"]
                                )
                                if len(linked_items) > 0:
                                    first = linked_items[0]
                                    first_title = first.get("title") if isinstance(first, dict) else None
                                    if first_title == title:
                                        first_id = first.get("id") if isinstance(first, dict) else None
                                        if first_id is not None:
                                            linked_item = project.get_workitem(first_id)
                                    else:
                                        logger.error(f"impossible to link {wi_case.id} to {title}")
                                else:
                                    logger.error(f"impossible to link {wi_case.id} to {title}")
                                cache_for_workitems[title] = linked_item
                        if linked_item is not None:
                            wi_case.add_linked_item(linked_item, key)

        logger.info(f"Results saved in {config.url}/#/project/{config.project_id}/testrun?id={config.testrun_id}")

        return test_run


class ResultExporter:
    """Export an object as JSON (tested with a testrun).

    In v2 the API returns plain Python dicts/lists rather than zeep
    objects, so the handler table is simplified accordingly.
    """

    _HANDLERS: dict[str, Callable] = {
        "Testrun": lambda cls, obj: cls._make_serialisable(
            {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        ),
        "Record": lambda cls, obj: cls._make_serialisable(
            {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        ),
    }

    @classmethod
    def _make_serialisable(cls, obj: Any) -> Any:
        if obj is None:
            return None
        if isinstance(obj, (str, bool)):
            return obj
        if isinstance(obj, (int, float)):
            return str(obj)
        if isinstance(obj, list):
            return [cls._make_serialisable(item) for item in obj]
        if isinstance(obj, dict):
            return {k: cls._make_serialisable(v) for k, v in obj.items()}
        if isinstance(obj, datetime):
            return obj.strftime("%d-%m-%Y-%H-%M-%S-%f")
        handler = cls._HANDLERS.get(type(obj).__name__)
        if handler:
            return handler(cls, obj)
        logger.warning("Not processed type: %s having value: %s", type(obj), obj)
        return str(obj)

    @classmethod
    def save_json(cls, results_file: str, test_run: Any) -> None:
        logger.info(f"Saving results in {results_file}")
        result = ResultExporter._make_serialisable(test_run)
        with open(results_file, "w") as outfile:
            outfile.write(json.dumps(result, indent=4))

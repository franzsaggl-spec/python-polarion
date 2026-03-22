from __future__ import annotations

import copy
import os
from typing import Any, Optional, TYPE_CHECKING

from .base.comments import Comments
from .base.custom_fields import CustomFields
from .exceptions import PolarionNotFoundError, PolarionFieldError
from .record import Record
from .factory import Creator

if TYPE_CHECKING:
    from .polarion import Polarion
    from .workitem import Workitem


class Testrun(CustomFields, Comments):
    """
    Create a Polarion testrun object from uri or directly with Polarion content

    :param polarion: Polarion client object
    :param uri: Polarion uri
    :param polarion_test_run: The data from Polarion of this testrun

    :ivar records: An array of :class:`.Record`
    """

    def __init__(self, polarion: Polarion, uri: Optional[str] = None, polarion_test_run: Optional[Any] = None) -> None:
        super().__init__(polarion, None, None, uri)

        if uri is not None:
            service = self._polarion.getService('TestManagement')
            try:
                self._polarion_test_run = service.getTestRunByUri(uri)
            except Exception as e:
                raise PolarionNotFoundError(f'Cannot find test run {uri}') from e

        elif polarion_test_run is not None:
            self._polarion_test_run = polarion_test_run
        else:
            raise PolarionFieldError('Provide either an uri or polarion_test_run')

        self._original_polarion_test_run = copy.deepcopy(self._polarion_test_run)
        self._buildWorkitemFromPolarion()

    def isCustomFieldAllowed(self, key: str) -> bool:
        return True
        
    def _buildWorkitemFromPolarion(self) -> None:
        if self._polarion_test_run is not None and not self._polarion_test_run.unresolvable:
            self._populate_attrs(self, self._polarion_test_run, remap={'records': '_records'})

            self.records = []
            self._record_dict = {}
            if self._records is not None:
                for index, r in enumerate(self._records.TestRecord):
                    new_record = Record(self._polarion, self, r, index)
                    self.records.append(new_record)
                    if new_record.testcase_id not in self._record_dict:
                        self._record_dict[new_record.testcase_id] = new_record

        else:
            raise PolarionNotFoundError('Testrun not retrieved from Polarion')

    def _reloadFromPolarion(self) -> None:
        service = self._polarion.getService('TestManagement')
        self._polarion_test_run = service.getTestRunByUri(self.uri)
        self._buildWorkitemFromPolarion()
        self._original_polarion_test_run = copy.deepcopy(self._polarion_test_run)

    def hasTestCase(self, id: str) -> bool:
        """
        Checks if the the specified test case id is in the records.

        :return: True/False
        :rtype: boolean
        """
        return id in self._record_dict

    def getTestCase(self, id: str) -> Optional[Record]:
        """
        Get the specified test case record from the test run records

        :return: Specified record fi ti exists
        :rtype: Record
        """
        if self.hasTestCase(id):
            return self._record_dict[id]
        return None

    def hasAttachment(self) -> bool:
        """
        Checks if the test run has attachments

        :return: True/False
        :rtype: boolean
        """
        return self.attachments is not None

    def getAttachment(self, file_name: str) -> bytes:
        """
        Get the attachment data

        :param file_name: The attachment file name
        :return: list of bytes
        :rtype: bytes[]
        """
        service = self._polarion.getService('TestManagement')
        at = service.getTestRunAttachment(self.uri, file_name)

        if at is not None:
            return self._polarion.downloadFromSvn(at.url)
        raise PolarionNotFoundError(f'Could not find attachment {file_name}')

    def saveAttachmentAsFile(self, file_name: str, file_path: str) -> None:
        """
        Save an attachment to file.

        :param file_name: The attachment file name
        :param file_path: File where to save the attachment
        """
        binary = self.getAttachment(file_name)
        with open(file_path, "wb") as file:
            file.write(binary)

    def deleteAttachment(self, file_name: str) -> None:
        """
        Delete an attachment.

        :param file_name: The attachment file name
        """
        service = self._polarion.getService('TestManagement')
        service.deleteTestRunAttachment(self.uri, file_name)
        self._reloadFromPolarion()

    def addAttachment(self, file_path: str, title: str) -> None:
        """
        Upload an attachment

        :param file_path: Source file to upload
        :param title: The title of the attachment
        """
        service = self._polarion.getService('TestManagement')
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as file_content:
            service.addAttachmentToTestRun(self.uri, file_name, title, file_content.read())
        self._reloadFromPolarion()

    def addTestcase(self, workitem: Workitem) -> None:
        """
        Add a workitem to the test run. A test case cannot be added to a template.
        :param workitem: Workitem object
        """
        service = self._polarion.getService('TestManagement')
        new_record = self._polarion.TestRecordType(testCaseURI=workitem.uri)
        service.addTestRecordToTestRun(self.uri, new_record)
        self._reloadFromPolarion()

    def updateAttachment(self, file_path: str, title: str) -> None:
        """
        Upload an attachment

        :param file_path: Source file to upload
        :param title: The title of the attachment
        """
        service = self._polarion.getService('TestManagement')
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as file_content:
            service.updateTestRunAttachment(self.uri, file_name, title, file_content.read())
        self._reloadFromPolarion()

    def save(self) -> None:
        """
        Update the testrun in polarion
        """
        updated_item = self._build_update_dict(self, self._polarion_test_run, self._original_polarion_test_run, skip={'records'})
        if updated_item:
            updated_item['uri'] = self.uri
            service = self._polarion.getService('TestManagement')
            service.updateTestRun(updated_item)
            self._reloadFromPolarion()

    def __repr__(self) -> str:
        return f'Testrun {self.id} ({self.title}) created {self.created}'

    __str__ = __repr__


class TestrunCreator(Creator):
    def createFromUri(self, polarion: Polarion, project: Any, uri: str) -> Testrun:
        return Testrun(polarion, uri)

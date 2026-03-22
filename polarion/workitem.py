from __future__ import annotations

import copy
import logging
import os
from datetime import datetime, date
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING, Union

from zeep import xsd

from .base.comments import Comments
from .base.custom_fields import CustomFields
from .exceptions import PolarionNotFoundError, PolarionFieldError, PolarionApiError
from .factory import Creator
from .user import User

if TYPE_CHECKING:
    from .polarion import Polarion
    from .project import Project
    from .document import Document

logger = logging.getLogger(__name__)


class Workitem(CustomFields, Comments):
    """
    Create a Polarion workitem object either from and id or from an Polarion uri.

    :param polarion: Polarion client object
    :param project: Polarion Project object
    :param id: Workitem ID
    :param uri: Polarion uri
    :param polarion_workitem: Polarion workitem content

    """

    class HyperlinkRoles(Enum):
        """
        Hyperlink reference type enum
        """
        INTERNAL_REF = 'internal reference'
        EXTERNAL_REF = 'external reference'

    def __init__(self, polarion: Polarion, project: Project, id: Optional[str] = None, uri: Optional[str] = None, new_workitem_type: Optional[str] = None, new_workitem_fields: Optional[dict[str, Any]] = None, polarion_workitem: Optional[Any] = None) -> None:
        super().__init__(polarion, project, id, uri)
        self._polarion = polarion
        self._project = project
        self._id = id
        self._uri = uri
        self._postpone_save = False

        service = self._polarion.getService('Tracker')

        if self._uri:
            try:
                self._polarion_item = service.getWorkItemByUri(self._uri)
                self._id = self._polarion_item.id
            except Exception as e:
                raise PolarionNotFoundError(
                    f'Cannot find workitem {self._id} in project {self._project.id}') from e
        elif id is not None:
            try:
                self._polarion_item = service.getWorkItemById(
                    self._project.id, self._id)
            except Exception as e:
                raise PolarionNotFoundError(
                    f'Cannot find workitem {self._id} in project {self._project.id}') from e
        elif new_workitem_type is not None:
            # construct empty workitem
            self._polarion_item = self._polarion.WorkItemType(
                type=self._polarion.EnumOptionIdType(id=new_workitem_type))
            self._polarion_item.project = self._project.polarion_data

            # get the required field for a new item
            required_features = service.getInitialWorkflowActionForProjectAndType(self._project.id, self._polarion.EnumOptionIdType(id=new_workitem_type))
            if required_features.requiredFeatures is not None:
                # if there are any, go and check if they are all supplied
                if new_workitem_fields is None or not set(required_features.requiredFeatures.item) <= new_workitem_fields.keys():
                    # let the user know with a better error
                    raise PolarionFieldError(f'New workitem required field: {required_features.requiredFeatures.item} to be filled in using new_workitem_fields')

            if new_workitem_fields is not None:
                for new_field in new_workitem_fields:
                    if new_field in self._polarion_item:
                        self._polarion_item[new_field] = new_workitem_fields[new_field]
                    else:
                        raise PolarionFieldError(f'{new_field} in new_workitem_fields is not recognised as a workitem field')

            # and create it
            new_uri = service.createWorkItem(self._polarion_item)
            # reload from polarion
            self._polarion_item = service.getWorkItemByUri(new_uri)
            self._id = self._polarion_item.id

        elif polarion_workitem is not None:
            self._polarion_item = polarion_workitem
            self._id = self._polarion_item.id
        else:
            raise PolarionFieldError('No id, uri, polarion workitem or new workitem type specified!')

        self._buildWorkitemFromPolarion()

    def __enter__(self) -> Workitem:
        self._postpone_save = True
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._postpone_save = False
        self.save()

    def _buildWorkitemFromPolarion(self) -> None:
        if self._polarion_item is not None and not self._polarion_item.unresolvable:
            self._original_polarion = copy.deepcopy(self._polarion_item)
            for attr, value in self._polarion_item.__dict__.items():
                for key in value:
                    setattr(self, key, value[key])
            self._polarion_test_steps = None
            try:
                # check if any of the field has the test steps
                if self._hasTestStepField() is True:
                    service_test = self._polarion.getService('TestManagement')
                    self._polarion_test_steps = service_test.getTestSteps(self.uri)
            except Exception as e:
                logger.debug('Could not fetch test steps for workitem %s: %s', self._id, e)
            self._parsed_test_steps = None
            if self._polarion_test_steps is not None:
                if self._polarion_test_steps.keys is not None and self._polarion_test_steps.steps:
                    # oh god, parse the test steps...
                    columns = []
                    self._parsed_test_steps = []
                    for col in self._polarion_test_steps.keys.EnumOptionId:
                        columns.append(col.id)
                    # now parse the rows
                    for row in self._polarion_test_steps.steps.TestStep:
                        current_row = {}
                        if row.values is not None:
                            for col_id in range(len(row.values.Text)):
                                current_row[columns[col_id]] = row.values.Text[col_id].content
                            self._parsed_test_steps.append(current_row)
        else:
            raise PolarionNotFoundError('Workitem not retrieved from Polarion')

    def getAuthor(self) -> Optional[User]:
        """
        Get the author of the workitem

        :return: Author
        :rtype: User
        """
        if self.author is not None:
            return User(self._polarion, self.author)
        return None

    def removeApprovee(self, user: User) -> None:
        """
        Remove a user from the approvers

        :param user: The user object to remove
        """
        service = self._polarion.getService('Tracker')
        service.removeApprovee(self.uri, user.id)
        self._reloadFromPolarion()

    def addApprovee(self, user: User, remove_others: bool = False) -> None:
        """
        Adds a user as approvee

        :param user: The user object to add
        :param remove_others: Set to True to make the new user the only approver user.
        """
        service = self._polarion.getService('Tracker')

        if remove_others:
            current_users = self.getApproverUsers()
            for current_user in current_users:
                service.removeApprovee(self.uri, current_user.id)

        service.addApprovee(self.uri, user.id)
        self._reloadFromPolarion()

    def getApproverUsers(self) -> list[User]:
        """
        Get an array of approval users

        :return: An array of User objects
        :rtype: User[]
        """
        assigned_users = []
        if self.approvals is not None:
            for approval in self.approvals.Approval:
                assigned_users.append(User(self._polarion, approval.user))
        return assigned_users

    def getAssignedUsers(self) -> list[User]:
        """
        Get an array of assigned users

        :return: An array of User objects
        :rtype: User[]
        """
        assigned_users = []
        if self.assignee is not None:
            for user in self.assignee.User:
                assigned_users.append(User(self._polarion, user))
        return assigned_users

    def removeAssignee(self, user: User) -> None:
        """
        Remove a user from the assignees

        :param user: The user object to remove
        """
        service = self._polarion.getService('Tracker')
        service.removeAssignee(self.uri, user.id)
        self._reloadFromPolarion()

    def addAssignee(self, user: User, remove_others: bool = False) -> None:
        """
        Adds a user as assignee

        :param user: The user object to add
        :param remove_others: Set to True to make the new user the only assigned user.
        """
        service = self._polarion.getService('Tracker')

        if remove_others:
            current_users = self.getAssignedUsers()
            for current_user in current_users:
                service.removeAssignee(self.uri, current_user.id)

        service.addAssignee(self.uri, user.id)
        self._reloadFromPolarion()

    def getStatusEnum(self) -> list[str]:
        """
        tries to get the status enum of this workitem type
        When it fails to get it, the list will be empty

        :return: An array of strings of the statusses
        :rtype: string[]
        """
        try:
            enum = self._project.getEnum(f'{self.type.id}-status')
            return enum
        except Exception as e:
            logger.debug('Could not get status enum: %s', e)
            return []

    def getResolutionEnum(self) -> list[str]:
        """
        tries to get the resolution enum of this workitem type
        When it fails to get it, the list will be empty

        :return: An array of strings of the resolutions
        :rtype: string[]
        """
        try:
            enum = self._project.getEnum(f'{self.type.id}-resolution')
            return enum
        except Exception as e:
            logger.debug('Could not get resolution enum: %s', e)
            return []

    def getSeverityEnum(self) -> list[str]:
        """
        tries to get the severity enum of this workitem type
        When it fails to get it, the list will be empty

        :return: An array of strings of the severities
        :rtype: string[]
        """
        try:
            enum = self._project.getEnum(f'{self.type.id}-severity')
            return enum
        except Exception as e:
            logger.debug('Could not get severity enum: %s', e)
            return []

    def getAllowedCustomKeys(self) -> list[str]:
        """
        Gets the list of keys that the workitem is allowed to have.

        :return: An array of strings of the keys
        :rtype: string[]
        """
        try:
            service = self._polarion.getService('Tracker')
            return service.getCustomFieldKeys(self.uri)
        except Exception as e:
            logger.debug('Could not get custom field keys: %s', e)
            return []

    def isCustomFieldAllowed(self, key: str) -> bool:
        """
        Checks if the custom field of a given key is allowed.

        :return: If the field is allowed
        :rtype: bool
        """
        return key in self.getAllowedCustomKeys()

    def getAvailableStatus(self) -> list[str]:
        """
        Get all available status option for this workitem

        :return: An array of string of the statusses
        :rtype: string[]
        """
        available_status = []
        service = self._polarion.getService('Tracker')
        av_status = service.getAvailableEnumOptionIdsForId(self.uri, 'status')
        for status in av_status:
            available_status.append(status.id)
        return available_status

    def getAvailableActionsDetails(self) -> list[Any]:
        """
        Get all actions option for this workitem with details

        :return: An array of dictionaries of the actions
        :rtype: dict[]
        """
        available_actions = []
        service = self._polarion.getService('Tracker')
        av_actions = service.getAvailableActions(self.uri)
        for action in av_actions:
            available_actions.append(action)
        return available_actions

    def getAvailableActions(self) -> list[str]:
        """
        Get all actions option for this workitem without details

        :return: An array of strings of the actions
        :rtype: string[]
        """
        available_actions = []
        service = self._polarion.getService('Tracker')
        av_actions = service.getAvailableActions(self.uri)
        for action in av_actions:
            available_actions.append(action.nativeActionId)
        return available_actions

    def performAction(self, action_name: str) -> None:
        """
        Perform selected action. An exception will be thrown if some prerequisite is not set.

        :param action_name: string containing the action name
        """
        # get id from action name
        service = self._polarion.getService('Tracker')
        av_actions = service.getAvailableActions(self.uri)
        for action in av_actions:
            if action.nativeActionId == action_name or action.actionName == action_name:
                service.performWorkflowAction(self.uri, action.actionId)

    def performActionId(self, actionId: int) -> None:
        """
        Perform selected action. An exception will be thrown if some prerequisite is not set.

        :param actionId: number for the action to perform
        """
        service = self._polarion.getService('Tracker')
        service.performWorkflowAction(self.uri, actionId)

    def setStatus(self, status: str) -> None:
        """
        Sets the status opf the workitem and saves the workitem, not respecting any project configured limits or requirements.

        :param status: name of the status
        """
        if status in self.getAvailableStatus():
            self.status.id = status
            self.save()

    def getDescription(self) -> Optional[str]:
        """
        Get a comment if available. The comment may contain HTML if edited in Polarion!

        :return: The content of the description, may contain HTML
        :rtype: string
        """
        if self.description is not None:
            return self.description.content
        return None

    def setDescription(self, description: str) -> None:
        """
        Sets the description and saves the workitem

        :param description: the description
        """
        self.description = self._polarion.TextType(
            content=description, type='text/html', contentLossy=False)
        self.save()

    def setResolution(self, resolution: str) -> None:
        """
        Sets the resolution and saves the workitem

        :param resolution: the resolution
        """

        if self.resolution is not None:
            self.resolution.id = resolution
        else:
            self.resolution = self._polarion.EnumOptionIdType(
                id=resolution)
        self.save()

    def hasTestSteps(self) -> bool:
        """
        Checks if the workitem has test steps

        :return: True/False
        :rtype: boolean
        """
        if self._parsed_test_steps is not None:
            return len(self._parsed_test_steps) > 0
        return False

    def addHyperlink(self, url: str, hyperlink_type: Union[str, HyperlinkRoles]) -> None:
        """
        Adds a hyperlink to the workitem.

        :param url: The URL to add
        :param hyperlink_type: Select internal or external hyperlink. Can be a string for custom link types.
        """
        service = self._polarion.getService('Tracker')
        if isinstance(hyperlink_type, Enum):  # convert Enum to str
            hyperlink_type = hyperlink_type.value
        service.addHyperlink(self.uri, url, {'id': hyperlink_type})
        self._reloadFromPolarion()

    def removeHyperlink(self, url: str) -> None:
        """
        Removes the url from the workitem
        @param url: url to remove
        @return:
        """
        service = self._polarion.getService('Tracker')
        service.removeHyperlink(self.uri, url)
        self._reloadFromPolarion()

    def addLinkedItem(self, workitem: Workitem, link_type: str) -> None:
        """
            Add a link to a workitem

            :param workitem: A workitem
            :param link_type: The link type
        """

        service = self._polarion.getService('Tracker')
        service.addLinkedItem(self.uri, workitem.uri, role={'id': link_type})
        self._reloadFromPolarion()
        workitem._reloadFromPolarion()

    def removeLinkedItem(self, workitem: Workitem, role: Optional[str] = None) -> None:
        """
        Remove the workitem from the linked items list. If the role is specified, the specified link will be removed.
        If not specified, all links with the workitem will be removed

        :param workitem: Workitem to be removed
        :param role: the role to remove
        :return: None
        """
        service = self._polarion.getService('Tracker')
        if role is not None:
            service.removeLinkedItem(self.uri, workitem.uri, role={'id': role})
        else:
            if self.linkedWorkItems is not None:
                for linked_item in self.linkedWorkItems.LinkedWorkItem:
                    if linked_item.workItemURI == workitem.uri:
                        service.removeLinkedItem(self.uri, linked_item.workItemURI, role=linked_item.role)
            if self.linkedWorkItemsDerived is not None:
                for linked_item in self.linkedWorkItemsDerived.LinkedWorkItem:
                    if linked_item.workItemURI == workitem.uri:
                        service.removeLinkedItem(linked_item.workItemURI, self.uri, role=linked_item.role)
        self._reloadFromPolarion()
        workitem._reloadFromPolarion()

    def getLinkedItemWithRoles(self) -> list[tuple[str, Workitem]]:
        """
        Get linked workitems both linked and back linked item will show up. Will include link roles.

        @return: Array of tuple ('link type', Workitem)
        """
        linked_items = []
        service = self._polarion.getService('Tracker')
        if self.linkedWorkItems is not None:
            for linked_item in self.linkedWorkItems.LinkedWorkItem:
                if linked_item.role is not None:
                    linked_items.append((linked_item.role.id, Workitem(self._polarion, self._project, uri=linked_item.workItemURI)))
        if self.linkedWorkItemsDerived is not None:
            for linked_item in self.linkedWorkItemsDerived.LinkedWorkItem:
                if linked_item.role is not None:
                    linked_items.append((linked_item.role.id, Workitem(self._polarion, self._project, uri=linked_item.workItemURI)))
        return linked_items

    def getLinkedItem(self) -> list[Workitem]:
        """
        Get linked workitems both linked and back linked item will show up.

        @return: Array of  Workitem
        @return:
        """
        return [item[1] for item in self.getLinkedItemWithRoles()]

    def hasAttachment(self) -> bool:
        """
        Checks if the workitem has attachments

        :return: True/False
        :rtype: boolean
        """
        if self.attachments is not None:
            return True
        return False

    def getAttachment(self, id: str) -> Any:
        """
        Get the attachment data

        :param id: The attachment id
        :return: list of bytes
        :rtype: bytes[]
        """
        service = self._polarion.getService('Tracker')
        return service.getAttachment(self.uri, id)

    def saveAttachmentAsFile(self, id: str, file_path: str) -> None:
        """
        Save an attachment to file.

        :param id: The attachment id
        :param file_path: File where to save the attachment
        """
        bin = self.getAttachment(id)
        with open(file_path, "wb") as file:
            file.write(bin)

    def deleteAttachment(self, id: str) -> None:
        """
        Delete an attachment.

        :param id: The attachment id
        """
        service = self._polarion.getService('Tracker')
        service.deleteAttachment(self.uri, id)
        self._reloadFromPolarion()

    def addAttachment(self, file_path: str, title: str) -> None:
        """
        Upload an attachment

        :param file_path: Source file to upload
        :param title: The title of the attachment
        """
        service = self._polarion.getService('Tracker')
        file_name = os.path.split(file_path)[1]
        with open(file_path, "rb") as file_content:
            service.createAttachment(self.uri, file_name, title, file_content.read())
        self._reloadFromPolarion()

    def updateAttachment(self, id: str, file_path: str, title: str) -> None:
        """
        Upload an attachment

        :param id: The attachment id
        :param file_path: Source file to upload
        :param title: The title of the attachment
        """
        service = self._polarion.getService('Tracker')
        file_name = os.path.split(file_path)[1]
        with open(file_path, "rb") as file_content:
            service.updateAttachment(self.uri, id, file_name, title, file_content.read())
        self._reloadFromPolarion()

    def delete(self) -> None:
        """
        Delete the work item in polarion
        This does not remove workitem references from documents
        """
        service = self._polarion.getService('Tracker')
        service.deleteWorkItem(self.uri)

    def moveToDocument(self, document: Document, parent: Optional[Workitem]) -> None:
        """
        Move the work item into a document as a child of another workitem

        :param document: Target document
        :param parent: Parent workitem, None if it shall be placed as top item
        """
        service = self._polarion.getService('Tracker')
        service.moveWorkItemToDocument(self.uri, document.uri, parent.uri if parent is not None else xsd.const.Nil, -1,
                                       False)

    def addTestStep(self, *args: str) -> None:
        """
        Add a new test step to a test case work item
        @param args: list of strings, one for each column
        @return: None
        """
        # check test step custom field
        if self._hasTestStepField() is False:
            raise PolarionFieldError('Cannot add test steps to work item that does not have the custom field')

        # if the keys do not exist, add them now
        if self._polarion_test_steps.keys is None:
            keys = self._getConfiguredTestStepColumnIDs()
            self._polarion_test_steps.keys = self._polarion.ArrayOfEnumOptionIdType()
            for key in keys:
                self._polarion_test_steps.keys.EnumOptionId.append(self._polarion.EnumOptionIdType(id=key))

        # check correct argument length
        if len(args) != len(self._polarion_test_steps.keys.EnumOptionId):
            raise PolarionFieldError(f'Incorrect number of argument. Test step requires {len(self._polarion_test_steps.keys.EnumOptionId)} arguments.')

        # check for any steps, if not present create array here
        if self._polarion_test_steps.steps is None:
            self._polarion_test_steps.steps = self._polarion.ArrayOfTestStepType()

        # prepare structure for Polarion
        step_text = []
        for arg in args:
            step_text.append(self._polarion.TextType(content=arg, type='text/html', contentLossy=False))
        step_array_text = self._polarion.ArrayOfTextType(step_text)
        new_test_step = self._polarion.TestStepType(step_array_text)

        # append the new step
        self._polarion_test_steps.steps.TestStep.append(new_test_step)

        # execute check for content being None after reload
        self._testStepNoneCheck()

        # save it to the service
        service = self._polarion.getService('TestManagement')
        service.setTestSteps(self.uri, self._polarion_test_steps.steps.TestStep)

        self._reloadFromPolarion()

    def removeTestStep(self, index: int) -> None:
        """
        Remove a test step at the specified index.
        @param index: zero based index
        @return: None
        """
        # check test step custom field
        if self._hasTestStepField() is False:
            raise PolarionFieldError('Cannot remove test steps from work item that does not have the custom field')

        if index >= len(self._polarion_test_steps.steps.TestStep):
            raise ValueError(f'Index should be in range of test step length of {len(self._polarion_test_steps.steps.TestStep)}')

        # remove from array
        self._polarion_test_steps.steps.TestStep.pop(index)

        # execute check for content being None after reload
        self._testStepNoneCheck()

        # save it to the service
        service = self._polarion.getService('TestManagement')
        service.setTestSteps(self.uri, self._polarion_test_steps.steps.TestStep)

        self._reloadFromPolarion()

    def updateTestStep(self, index: int, *args: str) -> None:
        """
        Update a test step at the specified index.
        @param index: zero based index
        @param args: list of strings, one for each column
        @return: None
        """
        # check test step custom field
        if self._hasTestStepField() is False:
            raise PolarionFieldError('Cannot update test steps on work item that does not have the custom field')

        # Verify validity of index
        if type(index) != int:
            raise PolarionFieldError('First argument of updateTestStep must be an integer.')
        if index >= len(self._polarion_test_steps.steps.TestStep):
            raise ValueError(f'Index should be in range of test step length of {len(self._polarion_test_steps.steps.TestStep)}')

            # check correct argument length
        if len(args) != len(self._polarion_test_steps.keys.EnumOptionId):
            raise PolarionFieldError(
                f'Incorrect number of argument. Test step requires {len(self._polarion_test_steps.keys.EnumOptionId)} arguments.')

        # prepare structure for Polarion
        step_text = []
        for arg in args:
            step_text.append(self._polarion.TextType(content=arg, type='text/html', contentLossy=False))
        step_array_text = self._polarion.ArrayOfTextType(step_text)
        new_test_step = self._polarion.TestStepType(step_array_text)

        # do update
        self._polarion_test_steps.steps.TestStep[index] = new_test_step

        # execute check for content being None after reload
        self._testStepNoneCheck()

        # save it to the service
        service = self._polarion.getService('TestManagement')
        service.setTestSteps(self.uri, self._polarion_test_steps.steps.TestStep)

        self._reloadFromPolarion()

    def getTestStepHeader(self) -> list[str]:
        """
        Get the Header names for the test step header.
        @return: List of strings containing the header names.
        """
        # check test step custom field
        if self._hasTestStepField() is False:
            raise PolarionFieldError('Work item does not have test step custom field')

        return self._getConfiguredTestStepColumns()

    def getTestStepHeaderID(self) -> list[str]:
        """
        Get the Header ID for the test step header.
        @return: List of strings containing the header IDs.
        """
        if self._hasTestStepField() is False:
            raise PolarionFieldError('Work item does not have test step custom field')

        return self._getConfiguredTestStepColumnIDs()

    def getTestSteps(self) -> list[dict[str, str]]:
        """
        Return a list of test steps.
        @return: Array of test steps
        """
        if self._parsed_test_steps is None:
            return []
        else:
            return self._parsed_test_steps

    def getRevision(self) -> int:
        """
        Return the revision number of the work item.
        @return: Integer with revision number
        """
        service = self._polarion.getService('Tracker')
        try:
            history: list = service.getRevisions(self.uri)
            return int(history[-1])
        except Exception as e:
            raise PolarionApiError("Could not get Revision!") from e


    def _getConfiguredTestStepColumns(self):
        """
        Return a list of coulmn headers
        @return: [str]
        """
        columns = []
        service = self._polarion.getService('TestManagement')
        config = service.getTestStepsConfiguration(self._project.id)
        for col in config:
            columns.append(col.name)
        return columns

    def _getConfiguredTestStepColumnIDs(self):
        """
        Return a list of column header IDs.
        @return: [str]
        """
        columns = []
        service = self._polarion.getService('TestManagement')
        config = service.getTestStepsConfiguration(self._project.id)
        for col in config:
            columns.append(col.id)
        return columns

    def _testStepNoneCheck(self):
        """
        Sanity check on content of test steps when empty strings are use.
        Sometimes they show up as None, which is not accepted by the API.
        @return: None
        """
        for step_id, step in enumerate(self._polarion_test_steps.steps.TestStep):
            for col_id, col in enumerate(self._polarion_test_steps.steps.TestStep[step_id].values.Text):
                if self._polarion_test_steps.steps.TestStep[step_id].values.Text[col_id].content is None:
                    self._polarion_test_steps.steps.TestStep[step_id].values.Text[col_id].content = ""

    def _hasTestStepField(self):
        """
        Checks if the testSteps custom field is available for this workitem. If so it allows test steps to be added.
        @return: True when test steps are available
        """
        service = self._polarion.getService('Tracker')
        custom_fields = service.getCustomFieldKeys(self.uri)
        if 'testSteps' in custom_fields:
            return True
        return False


    def save(self) -> None:
        """
        Update the workitem in polarion
        """
        if self._postpone_save:
            return
        updated_item = {}

        for attr, value in self._polarion_item.__dict__.items():
            for key in value:
                current_value = getattr(self, key)
                prev_value = getattr(self._original_polarion, key)
                if current_value != prev_value:
                    updated_item[key] = current_value
        if len(updated_item) > 0:
            updated_item['uri'] = self.uri
            service = self._polarion.getService('Tracker')
            service.updateWorkItem(updated_item)
            self._reloadFromPolarion()

    def _reloadFromPolarion(self) -> None:
        service = self._polarion.getService('Tracker')
        self._polarion_item = service.getWorkItemByUri(self._polarion_item.uri)
        self._buildWorkitemFromPolarion()
        self._original_polarion = copy.deepcopy(self._polarion_item)

    def __eq__(self, other: object) -> bool:
        try:
            a = vars(self)
            b = vars(other)
        except TypeError:
            return False
        return self._compareType(a, b)

    def _compareType(self, a, b):
        basic_types = [int, float,
                       bool, type(None), str, datetime, date]

        for key in a:
            if key.startswith('_'):
                # skip private types
                continue
            # first to a quick type compare to catch any easy differences
            if type(a[key]) == type(b[key]):
                if type(a[key]) in basic_types:
                    # direct compare capable
                    if a[key] != b[key]:
                        return False
                elif isinstance(a[key], list):
                    # special case for list items
                    if len(a[key]) != len(b[key]):
                        return False
                    for idx, sub_a in enumerate(a[key]):
                        self._compareType(sub_a, b[key][idx])
                else:
                    if not self._compareType(a[key], b[key]):
                        return False
            else:
                # exit, type mismatch
                return False
        # survived all exits, must be good then
        return True

    def __repr__(self) -> str:
        return f'{self._id}: {self.title}'

    def __str__(self) -> str:
        return f'{self._id}: {self.title}'


class WorkitemCreator(Creator):
    def createFromUri(self, polarion: Polarion, project: Project, uri: str) -> Workitem:
        return Workitem(polarion, project, None, uri)

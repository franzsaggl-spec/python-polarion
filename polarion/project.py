from __future__ import annotations

import logging
from typing import Any, Optional, TYPE_CHECKING

from .exceptions import PolarionNotFoundError
from .factory import createFromUri
from .workitem import Workitem
from .testrun import Testrun
from .user import User
from .plan import Plan
from .document import Document

if TYPE_CHECKING:
    from .polarion import Polarion

logger = logging.getLogger(__name__)


class Project(object):
    """
    A Polarion project instance usable to access workitem, testruns and more. usually create by using the Polarion client.

    :param polarion: The polarion client instance
    :param project_id: The project id, as can be found in the URL of the project

    """

    def __init__(self, polarion: Polarion, project_id: str) -> None:
        self.polarion = polarion
        self.id = project_id

        # get details from polarion on this project
        service = self.polarion.getService('Project')
        try:
            self.polarion_data = service.getProject(self.id)
        except Exception as e:
            raise PolarionNotFoundError(f'Could not find project {project_id}') from e

        if 'name' in self.polarion_data and not self.polarion_data.unresolvable:
            # succeeded
            self.name = self.polarion_data.name
            self.tracker_prefix = self.polarion_data.trackerPrefix
        else:
            raise PolarionNotFoundError(f'Could not find project {project_id}')

    def getUsers(self) -> list[User]:
        """
        Gets all users in this project
        """
        users = []
        service = self.polarion.getService('Project')
        project_users = service.getProjectUsers(self.id)
        for user in project_users:
            try:
                users.append(User(self.polarion, user))
            except Exception as e:
                logger.warning("Could not retrieve %s from server: %s", user['name'], e)
        return users

    def findUser(self, name: str) -> Optional[User]:
        """
        Find a specific user by id or name in this project
        """
        project_users = self.getUsers()
        for user in project_users:
            if user.id.lower() == name.lower() or user.name.lower() == name.lower():
                return user
        return None

    def getWorkitem(self, id: str) -> Workitem:
        """Get a workitem by string

        :param id: The ID of the project workitem (PREF-123).
        :return: The request workitem
        :rtype: Workitem
        """
        return Workitem(self.polarion, self, id)

    def getPlan(self, id: str) -> Plan:
        """Get a plan by string

        :param id: The ID of the project plan.
        :return: The request plan
        :rtype: Plan
        """
        return Plan(self.polarion, self, id=id)

    def createPlan(self, new_plan_name: str, new_plan_id: str, new_plan_template: str, new_plan_parent: Optional[Plan] = None) -> Plan:
        """
        Create a plan based on a template, plan name and plan ID.
        :param new_plan_name: The new plan name
        :param new_plan_id: The new plan ID
        :param new_plan_template: The plan template to use. Defaults are 'release' and 'iteration'. But this depends on
         the project configuration.
        :param new_plan_parent: Optionally the parent plan
        :return: A new plan
        :rtype: Plan
        """
        return Plan(self.polarion, self, new_plan_name=new_plan_name, new_plan_id=new_plan_id, new_plan_template=new_plan_template,
                    new_plan_parent=new_plan_parent)

    def searchPlan(self, query: str = '', order: str = 'Created', limit: int = -1) -> list[Any]:
        """Query for available plans. This will return the polarion data structures.

        :param query: The query to use while searching
        :param order: Order by
        :param limit: The limit of plans, -1 for no limit
        :return: The search results
        :rtype: dict[]
        """
        query += f' AND project.id:{self.id}'
        service = self.polarion.getService('Planning')
        return service.searchPlans(query, order, limit)

    def searchPlanFullItem(self, query: str = '', order: str = 'Created', limit: int = -1) -> list[Plan]:
        """Query for available plans. This will query for the plans and then fetch all result. May take a while for a big search with many results.

        :param query: The query to use while searching
        :param order: Order by
        :param limit: The limit of plans, -1 for no limit
        :return: The search results
        :rtype: Plan[]
        """
        return_list = []
        plans = self.searchPlan(query, order, limit)
        for plan in plans:
            return_list.append(Plan(self.polarion, self, polarion_record=plan))
        return return_list


    def createWorkitem(self, workitem_type: str, new_workitem_fields: Optional[dict[str, Any]] = None) -> Workitem:
        """
        Create a workitem based on the workitem type.
        :param workitem_type: The new workitem type
        :return: A new workitem
        :rtype: Workitem
        """
        return Workitem(self.polarion, self, new_workitem_type=workitem_type, new_workitem_fields=new_workitem_fields)

    def searchWorkitem(self, query: str = '', order: str = 'Created', field_list: Optional[list[str]] = None, limit: int = -1) -> list[Any]:
        """Query for available workitems. This will only query for the items.
        If you also want the Workitems to be retrieved, used searchWorkitemFullItem.

        For retrieving custom field using field_list, use the following syntax:
        field_list=['customFields.<key of custom field here>']
        
        :param query: The query to use while searching
        :param order: Order by
        :param field_list: list of fields to retrieve for each search result
        :param limit: The limit of workitems, -1 for no limit
        :return: The search results
        :rtype: Workitem[] but only with the given fields set
        """
        if field_list is None:
            field_list = ['id']

        query += f' AND project.id:{self.id}'
        service = self.polarion.getService('Tracker')
        return service.queryWorkItemsLimited(
            query, order, field_list, limit)
    
    def searchWorkitemInBaseline(self, baselineRevision: str, query: str = '', sort: str = 'uri', field_list: Optional[list[str]] = None, limit: int = -1) -> list[Any]:
        """Query for available workitems in a baseline. This will only query for the items.
        If you also want the Workitems to be retrieved, used searchWorkitemFullItemInBaseline.

        For retrieving custom field using field_list, use the following syntax:
        field_list=['customFields.<key of custom field here>']

        :param baselineRevision: The revision number of the baseline to search in
        :param query: The query to use while searching
        :param sort: Sort by
        :param fieldList: list of fields to retrieve for each search result
        :param limit: The limit of workitems, -1 for no limit
        :return: The search results
        :rtype: Workitem[] but only with the given fields set
        """
        if field_list is None:
            field_list = ['id']
        
        query += f' AND project.id:{self.id}'
        service = self.polarion.getService('Tracker')
        return service.queryWorkItemsInBaselineLimited(
            query, sort, baselineRevision, field_list, limit)

    def searchWorkitemFullItem(self, query: str = '', order: str = 'Created', limit: int = -1) -> list[Workitem]:
        """Query for available workitems. This will query for the items and then fetch all result. May take a while for a big search with many results.

        :param query: The query to use while searching
        :param order: Order by
        :param limit: The limit of workitems, -1 for no limit
        :return: The search results
        :rtype: Workitem[]
        """
        return_list = []
        workitems = self.searchWorkitem(query, order, ['id'], limit)
        for workitem in workitems:
            return_list.append(
                Workitem(self.polarion, self, workitem.id))
        return return_list
    
    def searchWorkitemFullItemInBaseline(self, baselineRevision: str, query: str = '', sort: str = 'uri', limit: int = -1) -> list[Workitem]:
        """Query for available workitems in baseline. This will query for the items and then fetch all result. May take a while for a big search with many results.

        :param baselineRevision: The revision number of the baseline to search in
        :param query: The query to use while searching
        :param sort: Sort by
        :param limit: The limit of workitems, -1 for no limit
        :return: The search results
        :rtype: Workitem[]
        """
        return_list = []
        workitems = self.searchWorkitemInBaseline(baselineRevision, query, sort, ['id'], limit)
        for workitem in workitems:
            return_list.append(
                Workitem(self.polarion, self, uri=workitem.uri))
        return return_list

    def getTestRun(self, id: str) -> Testrun:
        """Get a testrun by string

        :param id: The ID of the project testrun.
        :return: The request testrun
        :rtype: Testrun
        """
        return Testrun(self.polarion, f'subterra:data-service:objects:/default/{self.id}${{TestRun}}{id}')

    def searchTestRuns(self, query: str = '', order: str = 'Created', limit: int = -1) -> list[Testrun]:
        """Query for available test runs

        :param query: The query to use while searching
        :param order: Order by
        :param limit: The limit of test runs, -1 for no limit
        :return: The request testrun
        :rtype: Testrun[]
        """
        if len(query) > 0:
            query += ' AND '
        query += f'project.id:{self.id}'
        return_list = []
        service = self.polarion.getService('TestManagement')
        test_runs = service.searchTestRunsLimited(query, order, limit)
        for test_run in test_runs:
            return_list.append(
                Testrun(self.polarion, polarion_test_run=test_run))
        return return_list

    def createTestRun(self, id: str, title: str, template_id: str) -> Testrun:
        """
        Create a new test run with specified title from an existing test run template
        :param id: 
        :param title: 
        :param template_id: 
        """
        service = self.polarion.getService('TestManagement')
        new_testrun_uri = service.createTestRunWithTitle(self.id, id, title, template_id)
        return createFromUri(self.polarion, self, new_testrun_uri)

    def getEnum(self, enum_name: str) -> list[str]:
        """Get the options for a selected enumeration

        :param enum_name: The first part of the enum name. Will be postpended by -enum.xml by Polarion API
        :return: A list of options for the enum
        :rtype: string[]
        """
        available = []
        service = self.polarion.getService('Tracker')
        av = service.getAllEnumOptionsForId(self.id, enum_name)
        for a in av:
            if a.id not in available:
                available.append(a.id)
        return available

    def createDocument(self, location: str, name: str, title: str, allowed_workitem_types: list[str], structure_link_role: str, home_page_content: str = '') -> Document:
        """
        Creates a new document

        :param location: Document location, the default location is _default
        :param name: Name of the document
        :param title: Document title
        :param allowed_workitem_types: List of workitem types to be allowed inside the document
        :param structure_link_role: Link role to be used when defining the document hierarchy between parents and children
        :param home_page_content: Initial content of the document as HTML
        :return: New document
        """
        allowed_workitem_ids = []
        for allowed_workitem_type in allowed_workitem_types:
            allowed_workitem_ids.append(self.polarion.EnumOptionIdType(id=allowed_workitem_type))

        structure_link_role_id = self.polarion.EnumOptionIdType(id=structure_link_role)

        service = self.polarion.getService('Tracker')
        uri = service.createDocument(self.id, location, name, title, allowed_workitem_ids, structure_link_role_id, home_page_content)
        return Document(self.polarion, self, uri)

    def getDocumentSpaces(self) -> list[str]:
        """
        Get a list al all document spaces.
        :return:string[]
        """
        service = self.polarion.getService('Tracker')
        spaces = service.getDocumentSpaces(self.id)
        return sorted(spaces)

    def getDocumentLocations(self) -> list[str]:
        """
        Get a list of all document locations.
        :return:string[]
        """
        service = self.polarion.getService('Tracker')
        locations = service.getDocumentLocations(self.id)
        return sorted(locations)

    def getDocumentsInSpace(self, space: str) -> list[Document]:
        """
        Get all documents in a space.
        :param space: Name of the space.
        :return: Document[]
        """
        documents = []
        service = self.polarion.getService('Tracker')
        uris = service.getModuleUris(self.id, space)
        for uri in uris:
            documents.append(Document(self.polarion, self, uri=uri))
        return documents

    def getDocument(self, location: str) -> Document:
        """
        Get a document by location.

        :param location: Location of the document.
        :return: Document
        """
        return Document(self.polarion, self, location=location)

    def __repr__(self) -> str:
        return f'Polarion project {self.name} prefix {self.tracker_prefix}'

    __str__ = __repr__
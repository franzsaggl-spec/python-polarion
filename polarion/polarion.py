from __future__ import annotations

import atexit
import logging
import re
import time
from typing import Any, Optional, Union
from urllib.parse import urljoin, urlparse

import requests
from zeep import Client, CachingClient
from zeep.plugins import HistoryPlugin
from zeep.transports import Transport

from .exceptions import (
    PolarionAuthError,
    PolarionConnectionError,
    PolarionApiError,
)
from .project import Project
from .workitem import Workitem

logger = logging.getLogger(__name__)

_baseServiceUrl = 'ws/services'


_SESSION_CHECK_INTERVAL = 300  # seconds


class Polarion(object):
    """
    Create a Polarion client which communicates to the Polarion server.

    :param polarion_url: The base URL for the polarion instance. For example http://example/com/polarion
    :param user: The user name to login
    :param password: The password for that user
    :param token: The token to log with token. In this case, no need to set password
    :param static_service_list: Set to True when this class may not use a request to get the services list
    :param verify_certificate: Set to True/False to activate certification validation for TLS connection or provide string with link to certification chain (PEM & x264 encoded)
    :param svn_repo_url: Set to the correct url when the SVN repo is not accessible via <host>/repo. For example http://example/repo_extern
    :param proxy: Set to a proxy address to use a proxy, use the format: proxy='ip:port'
    """

    def __init__(self, polarion_url: str, user: str, password: Optional[str] = None, token: Optional[str] = None,
                 static_service_list: bool = False, verify_certificate: Union[bool, str] = True,
                 svn_repo_url: Optional[str] = None, proxy: Optional[str] = None,
                 request_session: Optional[requests.Session] = None, cache: bool = False) -> None:
        self.user = user
        self.password = password
        self.token = token
        self.url = polarion_url
        self.verify_certificate = verify_certificate
        self.svn_repo_url = svn_repo_url
        self.proxy = None
        self.request_session = request_session
        self.cache = cache
        self.transport = None
        if proxy is not None:
            self.proxy = {
                'http': proxy,
                'https': proxy}

        self.services = {}

        if not self.url.endswith('/'):
            self.url += '/'
        self.url = urljoin(self.url, _baseServiceUrl)

        if static_service_list:
            self._getStaticServices()
        else:
            self._getServices()
        self._createSession()
        self._getTypes()
        self._last_session_check = time.time()

        atexit.register(self._atexit_cleanup)

    def _atexit_cleanup(self) -> None:
        """
        Cleanup function to logout when Python is shutting down.
        :return: None
        """
        self.services['Session']['client'].service.endSession()

    def _getStaticServices(self) -> None:
        default_services = ['Session', 'Project', 'Tracker',
                            'Builder', 'Planning', 'TestManagement', 'Security']
        service_base_url = self.url + '/'
        for service in default_services:
            self.services[service] = {'url': urljoin(
                service_base_url, service + 'WebService')}

    def _getServices(self) -> None:
        """
        Parse the list of services available in the overview
        """
        service_overview = requests.get(self.url, verify=self.verify_certificate)
        service_base_url = self.url + '/'
        if service_overview.ok:
            services = re.findall(r"(\w+)WebService", service_overview.text)
            for service in services:
                if service not in self.services:
                    self.services[service] = {'url': urljoin(
                        service_base_url, service + 'WebService')}

    def _createSession(self) -> None:
        """
        Starts a session with the specified user/password
        """
        if 'Session' in self.services:
            self.history = HistoryPlugin()
            self.services['Session']['client'] = self.get_client('Session',[self.history])
            if self.proxy is not None:
                self.services['Session']['client'].transport.session.proxies = self.proxy
            try:
                self.sessionHeaderElement = None
                self.sessionCookieJar = None
                if self.token is not None:
                    self.services['Session']['client'].service.logInWithToken(
                        "AccessToken", "", self.token)
                else:
                    self.services['Session']['client'].service.logIn(
                        self.user, self.password)
                tree = self.history.last_received['envelope'].getroottree()
                self.sessionHeaderElement = tree.find(
                    './/{http://ws.polarion.com/session}sessionID')
                self.sessionCookieJar = self.services['Session']['client'].transport.session.cookies
            except Exception as err:
                logger.error(err)
                raise PolarionAuthError(
                    f'Could not log in to Polarion for user {self.user}') from err
            if self.sessionHeaderElement is not None:
                self._updateServices()
        else:
            raise PolarionConnectionError(
                'Cannot login because WSDL has no SessionWebService')

    def get_client(self, service: str, plugins: Optional[list] = None) -> Union[Client, CachingClient]:
        if plugins is None:
            plugins = []
        client = None

        session = requests.Session()
        session.verify = self.verify_certificate
        transport = Transport(session=session)

        if self.cache:
            client = CachingClient(self.services[service]['url'] + '?wsdl', plugins=plugins, transport=transport)
        else:
            client = Client(self.services[service]['url'] + '?wsdl', plugins=plugins, transport=transport)
        return client

    def _updateServices(self) -> None:
        """
        Updates all services with the correct session ID
        """
        if self.sessionHeaderElement is None:
            raise PolarionAuthError('Cannot update services when not logged in')
        for service in self.services:
            if service != 'Session':
                if 'client' not in service:
                    self.services[service]['client'] = self.get_client(service)
                self.services[service]['client'].set_default_soapheaders(
                    [self.sessionHeaderElement])
                if self.proxy is not None:
                    self.services[service]['client'].transport.session.proxies = self.proxy
                self.services[service]['client'].transport.session.cookies = self.sessionCookieJar
            if service == 'Tracker':
                if hasattr(self.services[service]['client'].service, 'addComment'):
                    # allow addComment to be send without title, needed for reply comments
                    self.services[service]['client'].service.addComment._proxy._binding.get(
                        'addComment').input.body.type._element[1].nillable = True
                    self.services[service]['client'].service.getModuleWorkItemUris._proxy._binding.get(
                        'getModuleWorkItemUris').input.body.type._element[1].nillable = True
                    self.services[service]['client'].service.moveWorkItemToDocument._proxy._binding.get(
                        'moveWorkItemToDocument').input.body.type._element[2].nillable = True
                    self.services[service]['client'].service.reuseDocument._proxy._binding.get(
                        'reuseDocument').input.body.type._element[6].nillable = True
                    self.services[service]['client'].service.reuseDocument._proxy._binding.get(
                        'reuseDocument').input.body.type._element[7].nillable = True
            if service == 'Planning':
                self.services[service]['client'].service.createPlan._proxy._binding.get(
                    'createPlan').input.body.type._element[3].nillable = True

            if service == 'TestManagement':
                self.services[service]['client'].service.setTestSteps._proxy._binding.get(
                    'setTestSteps').input.body.type._element[1].min_occurs = 0

    def _getTypes(self) -> None:
        # TODO: check if the namespace is always the same
        self.EnumOptionIdType = self.getTypeFromService('TestManagement', 'ns3:EnumOptionId')
        self.TextType = self.getTypeFromService('TestManagement', 'ns1:Text')
        self.ArrayOfTestStepResultType = self.getTypeFromService('TestManagement', 'ns4:ArrayOfTestStepResult')
        self.ArrayOfTestStepType = self.getTypeFromService('TestManagement', 'ns4:ArrayOfTestStep')
        self.TestStepType = self.getTypeFromService('TestManagement', 'ns4:TestStep')
        self.ArrayOfTextType = self.getTypeFromService('TestManagement', 'ns1:ArrayOfText')
        self.TestStepResultType = self.getTypeFromService('TestManagement', 'ns4:TestStepResult')
        self.TestRecordType = self.getTypeFromService('TestManagement', 'ns4:TestRecord')
        self.WorkItemType = self.getTypeFromService('Tracker', 'ns2:WorkItem')
        self.LinkedWorkItemType = self.getTypeFromService('Tracker', 'ns2:LinkedWorkItem')
        self.LinkedWorkItemArrayType = self.getTypeFromService('Tracker', 'ns2:ArrayOfLinkedWorkItem')
        self.ArrayOfCustomType = self.getTypeFromService('Tracker', 'ns2:ArrayOfCustom')
        self.CustomType = self.getTypeFromService('Tracker', 'ns2:Custom')
        self.ArrayOfEnumOptionIdType = self.getTypeFromService('Tracker', 'ns2:ArrayOfEnumOptionId')
        self.ArrayOfSubterraURIType = self.getTypeFromService('Tracker', 'ns1:ArrayOfSubterraURI')
        self._PdfProperties = None
        try:
            self._PdfProperties = self.getTypeFromService('Tracker', 'ns2:PdfProperties')
        except Exception:
            logger.debug('PDF properties not available in this Polarion version')

    @property
    def PdfProperties(self):
        """
        Get PDF properties object but only if it exist.
        If is was not able to get it from Polarion, fail with a exception only when using this feature
        @return: PdfProperties
        """
        if self._PdfProperties is None:
            raise PolarionApiError('PDF not supported in this Polarion version')
        return self._PdfProperties

    def hasService(self, name: str) -> bool:
        """
        Checks if a WSDL service is available
        """
        return name in self.services

    def getService(self, name: str) -> Any:
        """
        Get a WSDL service client. The name can be 'Tracker' or 'Session'
        """
        # periodically check if the session is still valid
        if time.time() - self._last_session_check > _SESSION_CHECK_INTERVAL:
            try:
                self.services['Project']['client'].service.getUser(self.user)
                self._last_session_check = time.time()
            except Exception:
                self._createSession()
                self._last_session_check = time.time()

        if name in self.services:
            return self.services[name]['client'].service
        else:
            raise PolarionConnectionError(f'Service {name} does not exist')

    def getTypeFromService(self, name: str, type_name: str) -> Any:
        """
        Get a SOAP type from a named service.
        """
        if name in self.services:
            return self.services[name]['client'].get_type(type_name)
        else:
            raise PolarionConnectionError(f'Service {name} does not exist')

    def getProject(self, project_id: str) -> Project:
        """Get a Polarion project

        :param project_id: The ID of the project.
        :return: The request project
        :rtype: Project
        """
        return Project(self, project_id)

    def queryWorkitems(self, query: str, sort: str) -> list[Workitem]:
        """Get List of workitems based on a query.
        Query is global and not project specific, so it will return workitems from all projects. Use with caution.
        Uses the Polarion query language. Documented as 'Advanced Work Item querying' in the Polarion documentation.

        :param query: The query.
        :param sort: The field to be used for sorting.
        :return: The workitems matching the query
        :rtype: Workitem[]
        """
        service = self.getService("Tracker")
        results = service.queryWorkItems(query, sort, fields=["project.id"])
        workitems = []
        for result in results:
            project = self.getProject(result.project.id)
            workitems.append(Workitem(self, project, uri=result.uri))
        return workitems


    def downloadFromSvn(self, url: str) -> bytes:

        if self.svn_repo_url is not None:
            # user specified new url to try, use that instead of the default value
            orig_url = urlparse(url)
            orig_url_path_without_repo = '/'.join(orig_url.path.split('/')[2:])
            new_root_url = urlparse(self.svn_repo_url)
            new_repo_url = f'{new_root_url.scheme}://{new_root_url.netloc}/{new_root_url.path.strip("/")}/{orig_url_path_without_repo}'
            resp = requests.get(new_repo_url, auth=(self.user, self.password))
            if resp.ok:
                return resp.content
            raise PolarionApiError(f'Could not download attachment from {url}. Got error {resp.status_code}: {resp.reason}')
        else:
            # try the url that was given
            resp = requests.get(url, auth=(self.user, self.password))
            if resp.ok:
                return resp.content

            raise PolarionApiError(f'Could not download attachment from {url}. Got error {resp.status_code}: {resp.reason}')

    def __repr__(self) -> str:
        return f'Polarion client for {self.url} with user {self.user}'

    __str__ = __repr__

import os
import re
import time
import json
import urllib
import logging
import requests
from typing import List

from pathlib import Path
from dataclasses import dataclass
from collections import namedtuple
from cachetools.func import ttl_cache, lru_cache

from jira import JIRA

from qa_tool.static.templates import JIRA_ISSUE_TEMPLATE
from qa_tool.settings import ALLURE_PROJECT_ID, JENKINS_JOB_BUILD_URL, JIRA_URL, MAIN_APP_URL

JIRA_NEW_ISSUE_URL = JIRA_URL + "secure/CreateIssueDetails!init.jspa?"

# This hack need for create any files in container
CURR_DIR = Path('/app').resolve() if Path('/app').is_dir() else Path(__file__).parent
AUTOTEST_ISSUES = CURR_DIR / "autotest_issues.json"
CACHE_JIRA_TICKETS = 60 * 5
MAX_JIRA_ISSUES_IN_SEARCH = 5000

GitInfo = namedtuple("RepoInfo", ["repo", "branch", "pr_status"])
FieldInfo = namedtuple("FieldInfo", ["name", "custom_name", "parse"])

TEST_TOKEN_PREFIX = 'autotests'
JIRA_USER = os.getenv('JIRA_USER')
JIRA_PASSWORD = os.getenv('JIRA_PASSWORD')
JIRA_BASE_AUTH = (JIRA_USER, JIRA_PASSWORD)


SKIPPING_STATUSES = ['backlog', 'to do', 'in progress', 'review']  # 'review'


class IssueTypes(object):
    STORY = "Story"
    BUG = "Bug"
    EPIC = "Epic"
    TASK = "Task"


class PRStatuses:
    MERGED = "MERGED"
    OPEN = "OPEN"


JIRA_PROJECT_ID_BY_ALLURE_PROJECT = {
    7: 10047,  # CMENABACK
    2: 10044,  # JTICKER
    3: 10046,  # CMENAWEB
    4: 10029,  # QA - testing
    5: 10055,  # NIL JSearch
}


JiraProject = namedtuple('JiraProject', ['id', 'key', 'name'])


def issue_obj_to_issue_info(issue):
    converted = {"id": issue.key, "jira_id": issue.id}
    for field in FIELDS:
        name = jira.fields_map[field.custom_name] if field.custom_name else field.name
        value = issue.fields.__dict__.get(name)
        converted[field.name] = field.parse(value)
    return IssueInfo(**converted)


FIELDS = [
    FieldInfo("assignee", None, lambda v: getattr(v, 'key', None)),
    # FieldInfo("branch_name", "Branch name", property(l)),
    FieldInfo("components", None, lambda v: tuple([e.name for e in v]) if v else tuple()),
    FieldInfo("description", None, lambda v: v or ''),
    FieldInfo("labels", None, lambda v: v or tuple()),
    FieldInfo("project", None, lambda v: JiraProject(v.id, v.key, v.name) if v else ''),
    FieldInfo("status", None, lambda v: v.name),
    FieldInfo("versions", None, lambda v: tuple([e.name for e in v]) if v else tuple()),
    FieldInfo("fixVersions", None, lambda v: [e.name for e in v] if v else []),
    FieldInfo("summary", None, lambda v: v),
    FieldInfo("issuetype", None, lambda v: v.name),
]


@dataclass
class IssueInfo:
    id: str
    jira_id: int
    assignee: str
    components: tuple
    description: str
    labels: tuple
    project: str
    status: str
    versions: tuple
    fixVersions: list
    summary: str
    issuetype: str

    @property
    def branches(self):
        return jira.get_repos_by_issue(self.jira_id)


class JiraIntegrate(object):
    def __init__(self):
        self._jira = None
        self._fields_map = None
        self.project_id = ''

    @property
    def jira(self):
        if self._jira is None:
            self._jira = JIRA(JIRA_URL, basic_auth=JIRA_BASE_AUTH)
        return self._jira

    @property
    @lru_cache()
    def fields(self):
        return [field.name for field in FIELDS]

    def search_issues(self, query, fields=None):
        fields = fields or self.fields
        logging.info("JIRA: Searching issues by query '%s'" % query)
        issues = self.jira.search_issues(query, 0, MAX_JIRA_ISSUES_IN_SEARCH, fields=fields)
        return [issue_obj_to_issue_info(issue) for issue in issues]

    def get_autotest_issues(self):
        logging.info("JIRA: Searching issues with autotests tokens")
        issues = self.search_issues(f"text ~ '{TEST_TOKEN_PREFIX}_*'")
        return issues

    @property
    def fields_map(self):
        if self._fields_map is None:
            self._fields_map = {field['name']: field['id'] for field in self.jira.fields()}
        return self._fields_map

    @lru_cache()
    def issue(self, issue_key):
        logging.info("JIRA: Getting issue '%s'" % issue_key)
        issue = self.jira.issue(issue_key)
        return issue_obj_to_issue_info(issue)

    def __format_branches(self, jira_branch_data, issue_id):
        branches_info = jira_branch_data.get('detail', [])
        if not branches_info:
            logging.warning(f"Can't find any branches for {issue_id}!")
        if len(branches_info) > 1:
            raise Exception(f"Have more than one item in DEVELOPMENT issue property: {issue_id}!!!! FIX THIS!!!")
        branches_info = branches_info[0]
        branches_info, branches_prs = branches_info['branches'], branches_info['pullRequests']
        pr_status_by_branch = {pr_branch['source']['url']:pr_branch['status'] for pr_branch in branches_prs}
        result = []
        for branch in branches_info:
            _tmp = GitInfo(branch['repository']['name'], branch['name'], pr_status_by_branch.get(branch['url']))
            result.append(_tmp)
        return result

    @ttl_cache(ttl=60)
    def get_repos_by_issue(self, issue_id:str):
        #  https://community.atlassian.com/t5/Answers-Developer-Questions/How-can-I-get-at-development-information-associated-with-an/qaq-p/568400
        #  https://jibrelnetwork.atlassian.net/rest/dev-status/1.0/issue/detail?issueId=13770&applicationType=github&dataType=pullrequest&_=1559045801209
        if not issue_id.isdigit():
            issue_id = self.issue(issue_id).jira_id
        hack_url = JIRA_URL + "rest/dev-status/1.0"
        _issue = 'issue/detail?issueId=%s' % issue_id
        _args = 'applicationType=github&dataType=branch&_=%s' % int(time.time())
        req_url = '%s/%s&%s' % (hack_url, _issue, _args)
        response = self.jira._session.get(req_url)
        return self.__format_branches(json.loads(response.content), issue_id)

    def get_jira_created_issue_url(self, test_name, error_text):
        report_link = JENKINS_JOB_BUILD_URL + "allure/#suites"
        test_file_name = test_name.split("/")[-1].split("::")[0]
        data = {
            'pid': JIRA_PROJECT_ID_BY_ALLURE_PROJECT.get(ALLURE_PROJECT_ID),
            'issuetype': 10004,  # Bug
            'priority': 3,  # Medium
            'labels': urllib.parse.quote("autotest"),
            'summary': urllib.parse.quote(f"Test '{test_file_name}' is failed, {error_text[:60] + '...'}".replace('\n', ' ')),
            'description': urllib.parse.quote(JIRA_ISSUE_TEMPLATE.format(**locals())),
        }
        return JIRA_NEW_ISSUE_URL + "&".join(["%s=%s" % (k, v) for k, v in data.items()])


jira = JiraIntegrate()


def dump_jira_issues():
    issues = [i.__dict__ for i in jira.get_autotest_issues()]
    AUTOTEST_ISSUES.write_text(json.dumps(issues))


@lru_cache()
def get_autotest_issues():
    try:
        issues = json.loads(AUTOTEST_ISSUES.read_text())
        return [IssueInfo(**issue) for issue in issues]
    except Exception:
        return []


@lru_cache()
def get_interesting_issues(label, project):
    issues = jira.search_issues(f"labels = '{label}' AND project = '{project}'")
    return issues


def get_version_from_text(text):
    default = tuple([0, 0, 0, 0])
    try:
        pattern = "((\d+\.)+(\*|\d+))"
        version = re.findall(pattern, text)
        if not version:
            return default
        version = version[0]
        if isinstance(version, (list, tuple)):
            version = version[0]
        version = tuple(int(i) for i in version.split('.'))
        return version
    except Exception as e:
        print(str(e))
        return default


@ttl_cache(ttl=10)
def get_health_check():
    try:
        url = urllib.parse.urljoin(MAIN_APP_URL, '/healthcheck')
        data = requests.get(url)
        return data.json()
    except Exception as e:
        print(str(e))
        return {}


def in_progress_issue(issue, check_version=False):
    is_affected_current_version = True
    if check_version:
        current_version = get_version_from_text(get_health_check().get('version', ''))
        is_affected_current_version = current_version >= get_version_from_text(str(issue.fixVersions))
    return issue.status.lower() in SKIPPING_STATUSES or not is_affected_current_version


@lru_cache()
def issue_is_open(issue, check_version=False):
    jira_ticket = issue.split('/')[-1]
    issue = jira.issue(jira_ticket)
    return in_progress_issue(issue, check_version)


def attach_known_issues_and_check_pending(known_issues: List[IssueInfo]):
    from qa_tool.libs.reporter import reporter
    is_pending = False
    for known_issue in known_issues:
        if in_progress_issue(known_issue, True):
            reporter.dynamic_issue(known_issue.id)
            is_pending = True
    return is_pending


def test_fixversion_assinging():
    issue = jira.issue('JTICKER-105')
    # issue1 = jira.issue('JASSETS-5')
    print('test')
    print(issue.branches)
    # ololo = jira.get_repos_by_issue('JSEARCH-29')


if __name__ == '__main__':
    print(get_health_check())
    print(attach_known_issues_and_check_pending([jira.issue("CMENABACK-353")]))
    test_fixversion_assinging()
    dump_jira_issues()
    keks = get_autotest_issues()[0]
    print(issue_is_open('https://jibrelnetwork.atlassian.net/browse/JTICKER-11'))
    logging.basicConfig(level=logging.INFO)


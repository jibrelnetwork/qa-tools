import os
import json
import time
import logging
from cachetools.func import ttl_cache

from dataclasses import dataclass

from jira import JIRA
from collections import namedtuple
from functools import lru_cache

JIRA_URL = "https://jibrelnetwork.atlassian.net/"
CURR_DIR = os.path.dirname(__file__)
AUTOTEST_ISSUES = os.path.join(CURR_DIR, "autotest_issues.json")
JIRA_FILTER = ""
CACHE_JIRA_TICKETS = 60 * 5
MAX_JIRA_ISSUES_IN_SEARCH = 5000

FieldInfo = namedtuple("FieldInfo", ["name", "custom_name", "parse"])
RepoInfo = namedtuple("RepoInfo", ["repo", "branch", "pr_status"])

JIRA_BASE_AUTH = ('alex.vasilev@jibrel.network', '')


class IssueTypes(object):
    STORY = "Story"
    BUG = "Bug"
    EPIC = "Epic"
    TASK = "Task"


class PRStatuses:
    MERGED = "MERGED"
    OPEN = "OPEN"


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
    FieldInfo("project", None, lambda v: v.key if v else ''),
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
        issues = self.search_issues("text ~ 'autotests_*'")
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
            _tmp = RepoInfo(branch['name'], branch['repository']['name'], pr_status_by_branch.get(branch['url']))
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


jira = JiraIntegrate()


def dump_jira_issues():
    issues = jira.get_autotest_issues()
    with open(AUTOTEST_ISSUES, "w") as fp:
        json.dump(issues, fp)


@lru_cache()
def get_autotest_issues():
    try:
        with open(AUTOTEST_ISSUES) as fp:
            issues = json.load(fp)
            return [IssueInfo(*issue) for issue in issues]
    except Exception:
        return []


@lru_cache()
def get_issues_by_fixversion(fix_version):
    issues = jira.search_issues("fixVersion = '%s'" % fix_version)
    return issues


def test_fixversion_assinging():
    issue = jira.issue('JSEARCH-234')
    print('test')
    print(issue.branches)
    ololo = jira.get_repos_by_issue('JSEARCH-330')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_fixversion_assinging()


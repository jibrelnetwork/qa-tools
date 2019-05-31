import os


from collections import defaultdict
from qa_tool.libs.reporter import reporter
from libs.jira_integrate import get_interesting_issues, PRStatuses



# TODO: now we can get images from docker registry need small research

# jenkins params: env - required, service_scope - required, branch - optional
# service_scope - jticker, jsearch, jassets, etc
# Behavior:
#   1) only env: Get all not merged tasks not in ('in progress', 'TO DO'). Set images for each service
#
#   2) env + branch: set on some env, services with branch. Branch must exist on each repo
#
#
#

DOCKER_REGISTRY_ORG = "jibrelnetwork"

ENVIRONMENTS = ['ENV_01', 'ENV_02']
SERVICE_SCOPE = {
    'jticker': {
        'jticker-api': 'API_IMAGE',
        'jticker-grabber': 'GRABBER_IMAGE',
        'jticker-aggregator': 'AGGREGATOR_IMAGE',
    },
    'jassets': {
        'jassets': 'JASSETS_IMAGE'
    }
}

WARNING_BRANCHES = ['master', 'develop']


READY_TO_MERGE_STATUSES = (
)

STATUSES_SKIPPING = (
)



def join_image_info(name, tag, organization=DOCKER_REGISTRY_ORG):
    return f"{organization}/{name}:{tag}"


def get_and_check_env_variable(, name, one_of_item):
    data = os.environ.get(name)
    assert data in one_of_item
    return data


@reporter.scenario
class TestMerge:

    def get_and_check_env_variable(self, name, one_of_item):
        data = os.environ.get(name)
        assert data in one_of_item
        return data

    def setup_class(self):
        self.env = get_and_check_env_variable('ENV', ENVIRONMENTS)
        self.service_scope = get_and_check_env_variable('SVC_SCOPE', SERVICE_SCOPE)
        self.services = SERVICE_SCOPE[self.service_scope]
        self.branch = os.environ.get('TESTING_BRANCH', None)

    def get_all_not_merged_branches_for_env_by_service(self, issues):
        result = defaultdict(set)
        for issue in issues:
            for branch in issue.branches:
                assert branch.repo in self.services
                if branch.pr_status == PRStatuses.MERGED:
                    continue
                if issue.status in STATUSES_SKIPPING:
                    continue


    def test_collect_all_finished_tasks_for_each_service(self):
        if self.branch:
            return
        issues = get_interesting_issues(self.env, self.service_scope)
        branch_by_service = self.get_all_not_merged_branches_for_env_by_service(issues)

    def test_prepare_image_env_data(self):
        pass

    def test_set_tag_for_service_images_in_env_file(self):

        with open("./.env", "w") as env_file:

            pass




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

WARNING_BRANCHES = ['master', ]


READY_TO_MERGE_STATUSES = ()
STATUSES_SKIPPING = ('To Do', 'Backlog')



def join_image_info(name, tag, organization=DOCKER_REGISTRY_ORG):
    return f"{organization}/{name}:{tag}"


def get_and_check_env_variable(name, one_of_item):
    data = os.environ.get(name)
    assert data in one_of_item
    return data


@reporter.scenario
class TestMerge:

    def get_and_check_env_variable(self, name, one_of_item):
        data = os.environ.get(name)
        supported_items = [i for i in one_of_item]
        assert data in one_of_item, f"Variable {name} not supported. Now supported this values {supported_items}"
        return data

    def setup_class(self):
        self.env = get_and_check_env_variable('ENVIRONMENT', ENVIRONMENTS)
        self.service_scope = get_and_check_env_variable('SERVICE_SCOPE', SERVICE_SCOPE)
        self.branch = os.environ.get('TESTING_BRANCH') or None
        self.errors = []

    def get_all_not_merged_branches_for_env_by_service(self, issues):
        result = defaultdict(set)
        for issue in issues:
            for branch in issue.branches:
                assert branch.repo in self.services
                if branch.pr_status == PRStatuses.MERGED:
                    continue
                if issue.status in STATUSES_SKIPPING:
                    continue
                result[branch.repo].add(branch.branch)
        return result

    def test_collect_all_finished_tasks_for_each_service(self):
        if self.branch:
            return {i:{self.branch,} for i in SERVICE_SCOPE[self.service_scope]}
        issues = get_interesting_issues(self.env, self.service_scope)
        self.branches_by_service = self.get_all_not_merged_branches_for_env_by_service(issues)

    def test_prepare_image_env_data(self):
        self.prepared_image_variables = {}
        image_env_variable_by_service = SERVICE_SCOPE[self.service_scope]
        for service, branches in self.branches_by_service.items():
            branches = branches or ['develop']
            if len(branches) != 1:
                self.errors.append(f'Service {service} have more than one branch(image) to merge: {branches}')
            variable_name = image_env_variable_by_service[service]
            self.prepared_image_variables[variable_name] = branches[0]
        if all([i=='develop' for i in self.prepared_image_variables.values()]) and self.branch != 'develop':
            self.errors.append(f"Haven't issues with images for testing on '{self.env}' environment. All branches are 'develop'")
        if any([i in WARNING_BRANCHES for i in self.prepared_image_variables.values()]):
            raise Exception(f"Use 'master' branch for deploy on env {self.env}")

    def test_set_tag_for_service_images_in_env_file(self):
        file_data = '\n'.join([f"{k}={v}" for k, v in self.prepared_image_variables.items()])
        reporter.attach('Data for .env file. Use for prepare/pull images', file_data)
        with open("./.env", "w") as env_file:
            env_file.write(file_data)

    def test_result_errors(self):
        if self.errors:
            errors = sorted(set(self.errors))
            reporter.attach("errors.log", '\n'.join(errors))
            print(f'{"ERRORS:":=^50}')
            for error in errors:
                print(error)
            raise AssertionError("Has errors, see in attached file")


if __name__ == "__main__":
    from qa_tool import run_test
    run_test(__file__)



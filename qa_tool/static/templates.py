
JIRA_ISSUE_TEMPLATE = """
*Autotests*:
Run autotest {test_name}
report link: {report_link}

*Steps*:
{{noformat}}
{{noformat}}

*Actual result*:
test is failed
{{noformat}}
{error_text}
{{noformat}}

*Expected data*:
{{noformat}}
{{noformat}}

"""
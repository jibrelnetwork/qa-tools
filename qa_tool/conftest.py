import pytest


pytest.register_assert_rewrite('qa_tool.utils.common')
pytest.register_assert_rewrite('qa_tool.utils.api_helper')
pytest.register_assert_rewrite('qa_tool.libs.reporter')
pytest.register_assert_rewrite('qa_tool.libs.postgres_connector')

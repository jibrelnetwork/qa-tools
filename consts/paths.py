from pathlib import Path

CONST_DIR = (Path(__file__) / '..').resolve()
ROOT_DIR = CONST_DIR / '..'
LIBS_DIR = ROOT_DIR / 'libs'
QA_TOOL_DIR = ROOT_DIR / 'qa_tool'

QA_TEST_DATA_DIR = ROOT_DIR / "tests" / 'test_data'

import os

import chartpress

def test_git_repo_fixture(git_repo):
    assert git_repo.working_dir == os.getcwd()
    assert os.path.isfile("chartpress.yaml")
    assert os.path.isfile("testchart/Chart.yaml")
    assert os.path.isfile("testchart/values.yaml")


def test_chartpress_run(git_repo):
    chartpress.main([])

import pytest

from chartpress import GITHUB_TOKEN_KEY

from chartpress import git_remote
from chartpress import image_needs_pushing
from chartpress import latest_tag_or_mod_commit
from chartpress import render_build_args
from chartpress import _strip_identifiers_build_suffix
from chartpress import _get_identifier
from chartpress import _get_published_chart_information

from ruamel.yaml import YAML
# use safe roundtrip yaml loader
yaml = YAML(typ='rt')
yaml.preserve_quotes = True ## avoid mangling of quotes
yaml.indent(mapping=2, offset=2, sequence=4)

def test__strip_identifiers_build_suffix():
    assert _strip_identifiers_build_suffix(identifier="0.1.2-005.asdf1234") == "0.1.2"
    assert _strip_identifiers_build_suffix(identifier="0.1.2-alpha.1.005.asdf1234") == "0.1.2-alpha.1"

def test__get_identifier():
    assert _get_identifier(tag="0.1.2",         n_commits="0", commit="asdf123",  long=True)  == "0.1.2-000.asdf123"
    assert _get_identifier(tag="0.1.2",         n_commits="0", commit="asdf123",  long=False) == "0.1.2"
    assert _get_identifier(tag="0.1.2",         n_commits="5", commit="asdf123",  long=False) == "0.1.2-005.asdf123"
    assert _get_identifier(tag="0.1.2-alpha.1", n_commits="0", commit="asdf1234", long=True)  == "0.1.2-alpha.1.000.asdf1234"
    assert _get_identifier(tag="0.1.2-alpha.1", n_commits="0", commit="asdf1234", long=False) == "0.1.2-alpha.1"
    assert _get_identifier(tag="0.1.2-alpha.1", n_commits="5", commit="asdf1234", long=False) == "0.1.2-alpha.1.005.asdf1234"

def test_git_remote(monkeypatch):
    monkeypatch.setenv(GITHUB_TOKEN_KEY, "test-github-token")
    assert git_remote("jupyterhub/helm-chart") == "https://test-github-token@github.com/jupyterhub/helm-chart"

    monkeypatch.delenv(GITHUB_TOKEN_KEY)
    assert git_remote("jupyterhub/helm-chart") == "git@github.com:jupyterhub/helm-chart"

def test_image_needs_pushing():
    assert image_needs_pushing("jupyterhub/image-not-to-be-found:latest")
    assert not image_needs_pushing("jupyterhub/k8s-hub:0.8.2")

def test_latest_tag_or_mod_commit(git_repo):
    open('tag-mod.txt', "w").close()
    git_repo.index.add("tag-mod.txt")
    tag_commit = git_repo.index.commit("tag commit")
    git_repo.create_tag("1.0.0", message="1.0.0")

    open('post-tag-mod.txt', "w").close()
    git_repo.index.add("post-tag-mod.txt")
    post_tag_commit = git_repo.index.commit("post tag commit")

    assert latest_tag_or_mod_commit("chartpress.yaml")  == tag_commit.hexsha[:7]
    assert latest_tag_or_mod_commit("tag-mod.txt")      == tag_commit.hexsha[:7]
    assert latest_tag_or_mod_commit("post-tag-mod.txt") == post_tag_commit.hexsha[:7]

def test_render_build_args(git_repo):
    with open('chartpress.yaml') as f:
        config = yaml.load(f)
    for chart in config["charts"]:
        for name, options in chart["images"].items():
            build_args = render_build_args(
                options,
                {
                    'LAST_COMMIT': "sha",
                    'TAG': "tag",
                },
            )
            assert build_args == {
                'TEST_STATIC_BUILD_ARG': 'test',
                'TEST_DYNAMIC_BUILD_ARG': 'tag-sha',
            }

@pytest.mark.parametrize(
    "chart_repo_url,chart_name,chart_version",
    [
        ("https://jupyterhub.github.io/helm-chart", "jupyterhub", "0.8.2"),
        ("https://jupyterhub.github.io/helm-chart/", "jupyterhub", "0.8.0-beta.1"),
        pytest.param("https://jupyterhub.github.io/invalid-url", "jupyterhub", "0.8.2", marks=pytest.mark.xfail),
    ],
)
def test__get_published_chart_information(chart_repo_url, chart_name, chart_version):
    assert _get_published_chart_information(chart_repo_url, chart_name, chart_version)

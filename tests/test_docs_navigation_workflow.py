from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / '.github' / 'workflows' / 'docs-navigation.yml'


def test_privileged_dispatcher_never_executes_pull_request_code() -> None:
    workflow = WORKFLOW.read_text(encoding='utf-8')

    assert 'pull_request_target:' in workflow
    assert "github.event.label.name == 'trigger:docs'" in workflow
    assert 'docs-navigation-${{ github.event.pull_request.number }}-${{ github.event.label.name }}' in workflow
    assert 'timeout-minutes: 5' in workflow
    assert 'actions/checkout@' not in workflow
    assert '/collaborators/${ACTOR}/permission' in workflow
    assert 'admin|maintain|write)' in workflow
    assert 'permission-contents: write' in workflow
    assert workflow.index('Verify a maintainer triggered the check') < workflow.index('Generate app token')
    assert '-f "client_payload[library]=validation"' in workflow
    assert '-f "client_payload[source_repo]=${REPO}"' in workflow
    assert '-f "client_payload[source_sha]=${HEAD_SHA}"' in workflow


def test_public_comments_describe_data_only_navigation_validation() -> None:
    workflow = WORKFLOW.read_text(encoding='utf-8')

    assert 'github.com/pydantic/unified-docs' not in workflow
    assert 'Docs Navigation Check — queued' in workflow
    assert 'Navigation validation for commit' in workflow
    assert 'preview URL' not in workflow
    assert '--paginate --slurp' in workflow
    assert 'startswith("## Docs Preview")' in workflow
    assert '| last).url // empty' in workflow
    assert "steps.verify.outcome == 'failure'" in workflow
    assert "steps.app-token.outcome == 'failure' || steps.dispatch.outcome == 'failure'" in workflow
    assert "steps.acknowledge.outcome == 'failure'" in workflow

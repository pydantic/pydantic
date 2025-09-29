"""Use the github API to get lists of people who have contributed in various ways to Pydantic.

This logic is inspired by that of @tiangolo's
[FastAPI people script](https://github.com/tiangolo/fastapi/blob/master/.github/actions/people/app/main.py).
"""

# ruff: noqa: D101
# ruff: noqa: D103

import logging
import subprocess
import sys
from collections import Counter
from collections.abc import Container
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
import yaml
from github import Github
from pydantic_settings import BaseSettings

from pydantic import BaseModel, SecretStr

github_graphql_url = 'https://api.github.com/graphql'

discussions_query = """
query Q($after: String) {
  repository(name: "pydantic", owner: "pydantic") {
    discussions(first: 100, after: $after) {
      edges {
        cursor
        node {
          number
          author {
            login
            avatarUrl
            url
          }
          title
          createdAt
          comments(first: 100) {
            nodes {
              createdAt
              author {
                login
                avatarUrl
                url
              }
              isAnswer
              replies(first: 10) {
                nodes {
                  createdAt
                  author {
                    login
                    avatarUrl
                    url
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

issues_query = """
query Q($after: String) {
  repository(name: "pydantic", owner: "samuelcolvin") {
    issues(first: 100, after: $after) {
      edges {
        cursor
        node {
          number
          author {
            login
            avatarUrl
            url
          }
          title
          createdAt
          state
          comments(first: 100) {
            nodes {
              createdAt
              author {
                login
                avatarUrl
                url
              }
            }
          }
        }
      }
    }
  }
}
"""

prs_query = """
query Q($after: String) {
  repository(name: "pydantic", owner: "samuelcolvin") {
    pullRequests(first: 100, after: $after) {
      edges {
        cursor
        node {
          number
          labels(first: 100) {
            nodes {
              name
            }
          }
          author {
            login
            avatarUrl
            url
          }
          title
          createdAt
          state
          comments(first: 100) {
            nodes {
              createdAt
              author {
                login
                avatarUrl
                url
              }
            }
          }
          reviews(first:100) {
            nodes {
              author {
                login
                avatarUrl
                url
              }
              state
            }
          }
        }
      }
    }
  }
}
"""


class Author(BaseModel):
    """Represents a GitHub user with their basic information."""

    login: str
    avatarUrl: str
    url: str


# Issues and Discussions


class CommentsNode(BaseModel):
    """Represents a comment node with creation time and author information."""

    createdAt: datetime
    author: Author | None = None


class Replies(BaseModel):
    """Container for reply nodes in a discussion."""

    nodes: list[CommentsNode]


class DiscussionsCommentsNode(CommentsNode):
    """Extends CommentsNode to include replies in discussions."""

    replies: Replies


class Comments(BaseModel):
    """Container for comment nodes."""

    nodes: list[CommentsNode]


class DiscussionsComments(BaseModel):
    """Container for discussion comment nodes."""

    nodes: list[DiscussionsCommentsNode]


class IssuesNode(BaseModel):
    """Represents a GitHub issue with its metadata and comments."""

    number: int
    author: Author | None = None
    title: str
    createdAt: datetime
    state: str
    comments: Comments


class DiscussionsNode(BaseModel):
    """Represents a GitHub discussion with its metadata and comments."""

    number: int
    author: Author | None = None
    title: str
    createdAt: datetime
    comments: DiscussionsComments


class IssuesEdge(BaseModel):
    """Represents an edge in the GitHub GraphQL issues query."""

    cursor: str
    node: IssuesNode


class DiscussionsEdge(BaseModel):
    """Represents an edge in the GitHub GraphQL discussions query."""

    cursor: str
    node: DiscussionsNode


class Issues(BaseModel):
    """Container for issue edges."""

    edges: list[IssuesEdge]


class Discussions(BaseModel):
    """Container for discussion edges."""

    edges: list[DiscussionsEdge]


class IssuesRepository(BaseModel):
    """Represents a repository's issues in the GitHub GraphQL response."""

    issues: Issues


class DiscussionsRepository(BaseModel):
    """Represents a repository's discussions in the GitHub GraphQL response."""

    discussions: Discussions


class IssuesResponseData(BaseModel):
    """Top-level container for issues response data."""

    repository: IssuesRepository


class DiscussionsResponseData(BaseModel):
    """Top-level container for discussions response data."""

    repository: DiscussionsRepository


class IssuesResponse(BaseModel):
    """Complete response structure for issues query."""

    data: IssuesResponseData


class DiscussionsResponse(BaseModel):
    """Complete response structure for discussions query."""

    data: DiscussionsResponseData


# PRs


class LabelNode(BaseModel):
    """Represents a GitHub label."""

    name: str


class Labels(BaseModel):
    """Container for label nodes."""

    nodes: list[LabelNode]


class ReviewNode(BaseModel):
    """Represents a pull request review with author and state."""

    author: Author | None = None
    state: str


class Reviews(BaseModel):
    """Container for review nodes."""

    nodes: list[ReviewNode]


class PullRequestNode(BaseModel):
    """Represents a GitHub pull request with its metadata and interactions."""

    number: int
    labels: Labels
    author: Author | None = None
    title: str
    createdAt: datetime
    state: str
    comments: Comments
    reviews: Reviews


class PullRequestEdge(BaseModel):
    """Represents an edge in the GitHub GraphQL pull requests query."""

    cursor: str
    node: PullRequestNode


class PullRequests(BaseModel):
    """Container for pull request edges."""

    edges: list[PullRequestEdge]


class PRsRepository(BaseModel):
    """Represents a repository's pull requests in the GitHub GraphQL response."""

    pullRequests: PullRequests


class PRsResponseData(BaseModel):
    """Top-level container for pull requests response data."""

    repository: PRsRepository


class PRsResponse(BaseModel):
    """Complete response structure for pull requests query."""

    data: PRsResponseData


class Settings(BaseSettings):
    """Configuration settings for the GitHub API interaction."""

    input_token: SecretStr
    github_repository: str = 'pydantic/pydantic'
    request_timeout: int = 30


def get_graphql_response(
    *,
    settings: Settings,
    query: str,
    after: str | None = None,
) -> dict[str, Any]:
    """Make a GraphQL request to GitHub API.

    Args:
        settings: Configuration settings including API token
        query: GraphQL query string
        after: Cursor for pagination, if any

    Returns:
        Response data from GitHub API in JSON format

    Raises:
        RuntimeError: If the API request fails or returns errors
    """
    headers = {'Authorization': f'token {settings.input_token.get_secret_value()}'}
    variables = {'after': after}
    response = requests.post(
        github_graphql_url,
        headers=headers,
        timeout=settings.request_timeout,
        json={'query': query, 'variables': variables, 'operationName': 'Q'},
    )
    if response.status_code != 200:
        logging.error(f'Response was not 200, after: {after}')
        logging.error(response.text)
        raise RuntimeError(response.text)
    data = response.json()
    if 'errors' in data:
        logging.error(f'Errors in response, after: {after}')
        logging.error(data['errors'])
        logging.error(response.text)
        raise RuntimeError(response.text)
    return data


def get_graphql_issue_edges(*, settings: Settings, after: str | None = None) -> list[IssuesEdge]:
    """Fetch issue edges from GitHub GraphQL API.

    Args:
        settings: Configuration settings
        after: Cursor for pagination, if any

    Returns:
        List of issue edges from the GraphQL response
    """
    data = get_graphql_response(settings=settings, query=issues_query, after=after)
    graphql_response = IssuesResponse.model_validate(data)
    return graphql_response.data.repository.issues.edges


def get_graphql_question_discussion_edges(
    *,
    settings: Settings,
    after: str | None = None,
) -> list[DiscussionsEdge]:
    """Fetch discussion edges from GitHub GraphQL API.

    Args:
        settings: Configuration settings
        after: Cursor for pagination, if any

    Returns:
        List of discussion edges from the GraphQL response
    """
    data = get_graphql_response(
        settings=settings,
        query=discussions_query,
        after=after,
    )
    graphql_response = DiscussionsResponse.model_validate(data)
    return graphql_response.data.repository.discussions.edges


def get_graphql_pr_edges(*, settings: Settings, after: str | None = None) -> list[PullRequestEdge]:
    """Fetch pull request edges from GitHub GraphQL API.

    Args:
        settings: Configuration settings
        after: Cursor for pagination, if any

    Returns:
        List of pull request edges from the GraphQL response
    """
    data = get_graphql_response(settings=settings, query=prs_query, after=after)
    graphql_response = PRsResponse.model_validate(data)
    return graphql_response.data.repository.pullRequests.edges


def get_issues_experts(settings: Settings) -> tuple[Counter, Counter, dict[str, Author]]:
    """Analyze issues to identify expert contributors.

    Args:
        settings: Configuration settings

    Returns:
        A tuple containing:
            - Counter of all commentors
            - Counter of commentors from the last month
            - Dictionary mapping usernames to Author objects
    """
    issue_nodes: list[IssuesNode] = []
    issue_edges = get_graphql_issue_edges(settings=settings)

    while issue_edges:
        issue_nodes.extend(edge.node for edge in issue_edges)
        last_edge = issue_edges[-1]
        issue_edges = get_graphql_issue_edges(settings=settings, after=last_edge.cursor)

    commentors = Counter()
    last_month_commentors = Counter()
    authors: dict[str, Author] = {}

    now = datetime.now(tz=timezone.utc)
    one_month_ago = now - timedelta(days=30)

    for issue in issue_nodes:
        issue_author_name = None
        if issue.author:
            authors[issue.author.login] = issue.author
            issue_author_name = issue.author.login
        issue_commentors = set()
        for comment in issue.comments.nodes:
            if comment.author:
                authors[comment.author.login] = comment.author
                if comment.author.login != issue_author_name:
                    issue_commentors.add(comment.author.login)
        for author_name in issue_commentors:
            commentors[author_name] += 1
            if issue.createdAt > one_month_ago:
                last_month_commentors[author_name] += 1

    return commentors, last_month_commentors, authors


def get_discussions_experts(settings: Settings) -> tuple[Counter, Counter, dict[str, Author]]:
    """Analyze discussions to identify expert contributors.

    Args:
        settings: Configuration settings

    Returns:
        A tuple containing:
            - Counter of all commentors
            - Counter of commentors from the last month
            - Dictionary mapping usernames to Author objects
    """
    discussion_nodes: list[DiscussionsNode] = []
    discussion_edges = get_graphql_question_discussion_edges(settings=settings)

    while discussion_edges:
        discussion_nodes.extend(discussion_edge.node for discussion_edge in discussion_edges)
        last_edge = discussion_edges[-1]
        discussion_edges = get_graphql_question_discussion_edges(settings=settings, after=last_edge.cursor)

    commentors = Counter()
    last_month_commentors = Counter()
    authors: dict[str, Author] = {}

    now = datetime.now(tz=timezone.utc)
    one_month_ago = now - timedelta(days=30)

    for discussion in discussion_nodes:
        discussion_author_name = None
        if discussion.author:
            authors[discussion.author.login] = discussion.author
            discussion_author_name = discussion.author.login
        discussion_commentors = set()
        for comment in discussion.comments.nodes:
            if comment.author:
                authors[comment.author.login] = comment.author
                if comment.author.login != discussion_author_name:
                    discussion_commentors.add(comment.author.login)
            for reply in comment.replies.nodes:
                if reply.author:
                    authors[reply.author.login] = reply.author
                    if reply.author.login != discussion_author_name:
                        discussion_commentors.add(reply.author.login)
        for author_name in discussion_commentors:
            commentors[author_name] += 1
            if discussion.createdAt > one_month_ago:
                last_month_commentors[author_name] += 1
    return commentors, last_month_commentors, authors


def get_experts(settings: Settings) -> tuple[Counter, Counter, dict[str, Author]]:
    """Get combined expert contributors from discussions.

    Args:
        settings: Configuration settings

    Returns:
        A tuple containing:
            - Counter of all commentors
            - Counter of commentors from the last month
            - Dictionary mapping usernames to Author objects
    """
    # Migrated to only use GitHub Discussions
    # (
    #     issues_commentors,
    #     issues_last_month_commentors,
    #     issues_authors,
    # ) = get_issues_experts(settings=settings)
    (
        discussions_commentors,
        discussions_last_month_commentors,
        discussions_authors,
    ) = get_discussions_experts(settings=settings)
    # commentors = issues_commentors + discussions_commentors
    commentors = discussions_commentors
    # last_month_commentors = (
    #     issues_last_month_commentors + discussions_last_month_commentors
    # )
    last_month_commentors = discussions_last_month_commentors
    # authors = {**issues_authors, **discussions_authors}
    authors = {**discussions_authors}
    return commentors, last_month_commentors, authors


def get_contributors(settings: Settings) -> tuple[Counter, Counter, Counter, dict[str, Author]]:
    """Analyze pull requests to identify contributors, commentors, and reviewers.

    Args:
        settings: Configuration settings

    Returns:
        A tuple containing:
            - Counter of contributors (merged PRs)
            - Counter of commentors
            - Counter of reviewers
            - Dictionary mapping usernames to Author objects
    """
    pr_nodes: list[PullRequestNode] = []
    pr_edges = get_graphql_pr_edges(settings=settings)

    while pr_edges:
        pr_nodes.extend(edge.node for edge in pr_edges)
        last_edge = pr_edges[-1]
        pr_edges = get_graphql_pr_edges(settings=settings, after=last_edge.cursor)

    contributors = Counter()
    commentors = Counter()
    reviewers = Counter()
    authors: dict[str, Author] = {}

    for pr in pr_nodes:
        author_name = None
        if pr.author:
            authors[pr.author.login] = pr.author
            author_name = pr.author.login
        pr_commentors: set[str] = set()
        pr_reviewers: set[str] = set()
        for comment in pr.comments.nodes:
            if comment.author:
                authors[comment.author.login] = comment.author
                if comment.author.login == author_name:
                    continue
                pr_commentors.add(comment.author.login)
        for author_name in pr_commentors:
            commentors[author_name] += 1
        for review in pr.reviews.nodes:
            if review.author:
                authors[review.author.login] = review.author
                pr_reviewers.add(review.author.login)
        for reviewer in pr_reviewers:
            reviewers[reviewer] += 1
        if pr.state == 'MERGED' and pr.author:
            contributors[pr.author.login] += 1
    return contributors, commentors, reviewers, authors


def get_top_users(
    *,
    counter: Counter,
    min_count: int,
    authors: dict[str, Author],
    skip_users: Container[str],
) -> list[dict[str, Any]]:
    """Get top users based on their contribution counts.

    Args:
        counter: Counter with user contribution counts
        min_count: Minimum count to be included in results
        authors: Dictionary mapping usernames to Author objects
        skip_users: Container of usernames to exclude from results

    Returns:
        List of dictionaries containing:
            - login: Username
            - count: Number of contributions
            - avatarUrl: URL to user's avatar
            - url: URL to user's GitHub profile
    """
    users: list[dict[str, Any]] = []
    for commentor, count in counter.most_common(50):
        if commentor in skip_users:
            continue
        if count >= min_count:
            author = authors[commentor]
            users.append(
                {
                    'login': commentor,
                    'count': count,
                    'avatarUrl': author.avatarUrl,
                    'url': author.url,
                }
            )
    return users


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    logging.info(f'Using config: {settings.model_dump_json()}')
    g = Github(settings.input_token.get_secret_value())
    repo = g.get_repo(settings.github_repository)
    question_commentors, question_last_month_commentors, question_authors = get_experts(settings=settings)
    contributors, pr_commentors, reviewers, pr_authors = get_contributors(settings=settings)
    authors = {**question_authors, **pr_authors}
    maintainers_logins = {
        'samuelcolvin',
        'adriangb',
        'dmontagu',
        'hramezani',
        'Kludex',
        'davidhewitt',
        'alexmojaki',
        'Viicos',
    }
    bot_names = {'codecov', 'github-actions', 'pre-commit-ci', 'dependabot'}
    maintainers = []
    for login in maintainers_logins:
        user = authors[login]
        maintainers.append(
            {
                'login': login,
                'answers': question_commentors[login],
                'prs': contributors[login],
                'avatarUrl': user.avatarUrl,
                'url': user.url,
            }
        )

    min_count_expert = 10
    min_count_last_month = 3
    min_count_contributor = 4
    min_count_reviewer = 4
    skip_users = maintainers_logins | bot_names
    experts = get_top_users(
        counter=question_commentors,
        min_count=min_count_expert,
        authors=authors,
        skip_users=skip_users,
    )
    last_month_active = get_top_users(
        counter=question_last_month_commentors,
        min_count=min_count_last_month,
        authors=authors,
        skip_users=skip_users,
    )
    top_contributors = get_top_users(
        counter=contributors,
        min_count=min_count_contributor,
        authors=authors,
        skip_users=skip_users,
    )
    top_reviewers = get_top_users(
        counter=reviewers,
        min_count=min_count_reviewer,
        authors=authors,
        skip_users=skip_users,
    )

    extra_experts = [
        {
            'login': 'ybressler',
            'count': None,
            'avatarUrl': 'https://avatars.githubusercontent.com/u/40807730?v=4',
            'url': 'https://github.com/ybressler',
        },
    ]
    expert_logins = {e['login'] for e in experts}
    experts.extend([expert for expert in extra_experts if expert['login'] not in expert_logins])

    people = {
        'maintainers': maintainers,
        'experts': experts,
        'last_month_active': last_month_active,
        'top_contributors': top_contributors,
        'top_reviewers': top_reviewers,
    }
    people_path = Path('./docs/plugins/people.yml')
    people_old_content = people_path.read_text(encoding='utf-8')
    new_people_content = yaml.dump(people, sort_keys=False, width=200, allow_unicode=True)
    if people_old_content == new_people_content:
        logging.info("The Pydantic People data hasn't changed, finishing.")
        sys.exit(0)
    people_path.write_text(new_people_content, encoding='utf-8')

    logging.info('Setting up GitHub Actions git user')
    subprocess.run(['git', 'config', 'user.name', 'github-actions'], check=True)
    subprocess.run(['git', 'config', 'user.email', 'github-actions@github.com'], check=True)

    branch_name = 'pydantic-people-update'
    logging.info(f'Creating a new branch {branch_name}')
    subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
    logging.info('Adding updated file')
    subprocess.run(['git', 'add', str(people_path)], check=True)
    logging.info('Committing updated file')
    message = '👥 Update Pydantic People'
    result = subprocess.run(['git', 'commit', '-m', message], check=True)
    logging.info('Pushing branch')
    subprocess.run(['git', 'push', 'origin', branch_name], check=True)
    logging.info('Creating PR')
    pr = repo.create_pull(title=message, body=message, base='main', head=branch_name)
    logging.info(f'Created PR: {pr.number}')
    logging.info('Finished')

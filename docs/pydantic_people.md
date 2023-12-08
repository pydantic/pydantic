# Pydantic People

Pydantic has an amazing community of contributors, reviewers, and experts that help propel the project forward.
Here, we celebrate those people and their contributions.

## Experts

These are the users that have helped others the most with questions in GitHub through *all time*.

{: if people :}
<div class="user-list user-list-center">
{: for user in people.experts :}

<div class="user"><a href="{= user.url =}" target="_blank"><div class="avatar-wrapper"><img src="{= user.avatarUrl =}"/></div><div class="title">@{= user.login =}</div></a> <div class="count">Questions replied: {= user.count =}</div></div>
{: endfor :}

</div>
{: endif :}

### Most active users last month

These are the users that have helped others the most with questions in GitHub during the last month.

{: if people :}
<div class="user-list user-list-center">
{: for user in people.last_month_active :}

<div class="user"><a href="{= user.url =}" target="_blank"><div class="avatar-wrapper"><img src="{= user.avatarUrl =}"/></div><div class="title">@{= user.login =}</div></a> <div class="count">Questions replied: {= user.count =}</div></div>
{: endfor :}

</div>
{: endif :}

## Top contributors

These are the users that have created the most pull requests that have been *merged*.

{: if people :}
<div class="user-list user-list-center">
{: for user in people.top_contributors :}

<div class="user"><a href="{= user.url =}" target="_blank"><div class="avatar-wrapper"><img src="{= user.avatarUrl =}"/></div><div class="title">@{= user.login =}</div></a> <div class="count">Pull Requests: {= user.count =}</div></div>
{: endfor :}

</div>
{: endif :}

## Top Reviewers

These are the users that have reviewed the most Pull Requests from others, assisting with code quality, documentation, bug fixes, feature requests, etc.

{: if people :}
<div class="user-list user-list-center">
{: for user in people.top_reviewers :}

<div class="user"><a href="{= user.url =}" target="_blank"><div class="avatar-wrapper"><img src="{= user.avatarUrl =}"/></div><div class="title">@{= user.login =}</div></a> <div class="count">Reviews: {= user.count =}</div></div>
{: endfor :}

</div>
{: endif :}

## About the data

The data displayed above is calculated monthly via the Github GraphQL API.

The source code for this script is located [here](https://github.com/pydantic/pydantic/tree/main/.github/actions/people/people.py).
Many thanks to [Sebastián Ramírez](https://github.com/tiangolo) for the script from which we based this logic.

Depending on changing conditions, the thresholds for the different categories of contributors may change in the future.

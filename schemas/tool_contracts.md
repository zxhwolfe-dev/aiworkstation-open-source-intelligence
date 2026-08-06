# MCP Tool Contracts v0.1

All tools are read-only.

## search_ai_projects

Input:

- query
- constraints
- locale
- source_mode

Output:

- projects
- matching_constraints
- evidence
- confidence
- unknowns

## get_project_facts

Input:

- project_id

Output:

- repository
- license
- deployment
- languages
- last_verified
- evidence

## get_license_evidence

Input:

- project_id

Output:

- license_name
- source
- timestamp
- uncertainty

## compare_ai_projects

Input:

- project_ids
- evaluation_criteria

Output:

- comparison_matrix
- verified_facts
- recommendations

## find_alternatives

Input:

- project_id
- constraints

Output:

- alternatives
- reasons
- evidence

## compose_ai_stack

Input:

- business_goal
- constraints

Output:

- architecture
- components
- implementation_steps
- risks

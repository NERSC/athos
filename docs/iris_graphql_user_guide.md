# Iris GraphQL API User Guide: SystemInfo, Projects, and Users

## Overview

This guide provides comprehensive documentation for the Iris GraphQL API, specifically focusing on the `systemInfo` root field and its `projects` and `users` sub-fields. The information in this guide was generated using GraphQL introspection queries.

## Table of Contents

1. [Root Query Structure](#root-query-structure)
2. [SystemInfo Root Field](#systeminfo-root-field)
3. [Users Sub-field](#users-sub-field)
4. [Projects Sub-field](#projects-sub-field)
5. [Example Queries](#example-queries)
6. [Common Arguments](#common-arguments)
7. [Best Practices](#best-practices)

## Root Query Structure

The Iris GraphQL API uses a `QueryPrivate` root type with the following available fields:

- `node` - Generic node interface
- **`systemInfo`** - Main system information object (focus of this guide)
- `sfapiSchema` - SFAPI schema information
- `storageArchive` - Storage archive data
- `pendingProjdirs` - Pending project directories
- `ops` - Operations data
- `newt` - NEWT system integration
- `report` - Reporting functionality
- `piToolboxWorkflow` - PI Toolbox workflow queries

## SystemInfo Root Field

The `systemInfo` field provides access to comprehensive system information including users, projects, and various other system entities.

### Basic Usage

```graphql
query {
  systemInfo {
    id
    # Add specific sub-fields here
  }
}
```

### Available Sub-fields

The SystemInfo type includes the following major sub-fields:

| Field Name | Type | Description |
|------------|------|-------------|
| `id` | ID! | The unique identifier of the SystemInfo object |
| `users` | [User] | List of system users |
| `projects` | [Project] | List of system projects |
| `ldapHosts` | [LdapHost] | LDAP host configurations |
| `offices` | [Office] | Office information |
| `programs` | [Program] | Program data |
| `scicats` | [SciCat] | Science catalog entries |
| `computeAllocations` | [ComputeAllocation] | Compute resource allocations |
| `groups` | [Group] | System groups |
| `computes` | [Compute] | Compute resource information |
| `fileSystems` | [FileSystem] | File system details |
| `qos` | [Qos] | Quality of Service configurations |
| `organizations` | [Organization] | Organization data |
| `userQuotas` | [UserQuota] | User storage quotas |
| `projectQuotas` | [ProjectQuota] | Project storage quotas |
| `publications` | [Publication] | Publications associated with projects |

## Users Sub-field

The `users` sub-field provides access to user account information in the system.

### Common Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `uid` | Int | null | Filter by user ID |
| `name` | String | null | Filter by username |
| `email` | String | null | Filter by email address |
| `since` | String | null | Filter users created since this date |
| `year` | Int | null | Filter by specific year |
| `first` | Int | 100 | Limit results (pagination) |
| `last` | Int | null | Last N results (pagination) |
| `before` | String | null | Pagination cursor |
| `after` | String | null | Pagination cursor |

### Key User Fields

The User type contains extensive information about user accounts:

#### Basic Information
- `id` (ID!) - Unique identifier
- `name` (String!) - Username
- `email` (String!) - Primary email address
- `uid` (Int) - Unix user ID
- `firstname` (String) - First name
- `lastname` (String) - Last name
- `middlename` (String) - Middle name

#### Authentication & Security
- `accessToken` (String) - Access token for API
- `tokenExpiresAt` (DateTime!) - Token expiration time
- `mfaEnabled` (Boolean) - Multi-factor authentication status
- `hasRandomPassword` (Boolean) - Random password flag
- `passwordExpireDays` (Int) - Password expiration period

#### Account Status
- `userType` (String!) - Type of user account
- `accountState` (String) - Current account state
- `suspended` (String) - Suspension status
- `createdAt` (DateTime) - Account creation date
- `updatedAt` (DateTime) - Last update date

#### Personal Information
- `citizenof` (String) - Citizenship
- `pronouns` (String) - Preferred pronouns
- `gender` (String) - Gender identity
- `race` (String) - Race information
- `ethnicity` (String) - Ethnicity information
- `disability` (String) - Disability status

#### Associated Data
- `projects` ([Project]) - Projects the user is associated with
- `groups` ([Group]) - Groups the user belongs to
- `organizations` ([Organization]) - User's organizations
- `userQuotas` ([UserQuota]) - Storage quotas
- `sshkeys` ([Sshkey]) - SSH public keys
- `allocations` ([AdminAllocation]) - Compute allocations

### Example User Query

```graphql
query GetUsers {
  systemInfo {
    users(first: 10, name: "john") {
      id
      name
      email
      uid
      firstname
      lastname
      userType
      accountState
      mfaEnabled
      projects {
        code
        label
      }
      groups {
        name
      }
    }
  }
}
```

## Projects Sub-field

The `projects` sub-field provides access to project information and associated resources.

### Common Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `id` | Int | null | Filter by project ID |
| `repoName` | String | null | Filter by repository name |
| `slurmCategoryName` | String | null | Filter by SLURM category |
| `since` | String | null | Filter projects created since this date |
| `year` | Int | null | Filter by specific year |
| `first` | Int | 100 | Limit results (pagination) |
| `last` | Int | null | Last N results (pagination) |
| `before` | String | null | Pagination cursor |
| `after` | String | null | Pagination cursor |

### Key Project Fields

The Project type contains comprehensive project information:

#### Basic Information
- `id` (ID!) - Unique identifier
- `code` (String) - Project code
- `label` (String) - Project label/name
- `description` (String) - Project description
- `repoName` (String) - Repository name

#### Resource Requirements
- `mppReq` (Float) - MPP (compute) hours requested
- `hpssReq` (Float) - HPSS storage requested
- `gpfsReq` (Float) - GPFS storage requested
- `gpuReq` (Float) - GPU hours requested
- `cfsDirMax` (Int) - Maximum CFS directories

#### Project Management
- `programId` (Int) - Associated program ID
- `organizationId` (Int) - Organization ID
- `slurmCategoryName` (String) - SLURM category
- `fundingSource` (String) - Funding source
- `tags` (String) - Project tags

#### Dates and Status
- `createdAt` (DateTime) - Project creation date
- `updatedAt` (DateTime) - Last update date
- `willContinueDone` (Boolean!) - Continuation status

#### Associated Data
- `users` ([User]) - Users associated with the project
- `owners` ([ProjectUser]) - Project owners
- `groups` ([Group]) - Project groups
- `computeAllocations` ([ComputeAllocation]) - Compute allocations
- `projectQuotas` ([ProjectQuota]) - Storage quotas
- `publications` ([Publication]) - Associated publications
- `program` (Program) - Associated program
- `organization` (Organization) - Associated organization

### Example Project Query

```graphql
query GetProjects {
  systemInfo {
    projects(first: 5, slurmCategoryName: "premium") {
      id
      code
      label
      description
      repoName
      mppReq
      gpuReq
      fundingSource
      users {
        name
        email
      }
      owners {
        user {
          name
        }
        role
      }
      computeAllocations {
        repoName
        allocationHours
        usedHours
      }
    }
  }
}
```

## Example Queries

### 1. Basic System Information

```graphql
query BasicSystemInfo {
  systemInfo {
    id
    users(first: 5) {
      name
      email
      uid
    }
    projects(first: 5) {
      code
      label
      description
    }
  }
}
```

### 2. User Details with Projects

```graphql
query UserWithProjects($userName: String) {
  systemInfo {
    users(name: $userName, first: 1) {
      id
      name
      email
      firstname
      lastname
      userType
      accountState
      projects {
        code
        label
        description
        repoName
      }
      allocations {
        repoName
        allocationHours
      }
    }
  }
}
```

### 3. Project with Resource Usage

```graphql
query ProjectResourceUsage($projectCode: String) {
  systemInfo {
    projects(repoName: $projectCode, first: 1) {
      id
      code
      label
      description
      mppReq
      gpuReq
      hpssReq
      users {
        name
        email
      }
      computeAllocations {
        repoName
        allocationHours
        usedHours
        compute {
          name
        }
      }
      recentMppUsage {
        date
        totalCoreHours
      }
    }
  }
}
```

### 4. Pagination Example

```graphql
query PaginatedUsers($after: String) {
  systemInfo {
    users(first: 10, after: $after) {
      id
      name
      email
      createdAt
    }
  }
}
```

## Common Arguments

Most list fields in the SystemInfo type support the following common arguments:

### Filtering Arguments
- `since` (String) - Filter entities created since a specific date
- `year` (Int) - Filter by a specific year
- Entity-specific filters (e.g., `name`, `email`, `uid` for users)

### Pagination Arguments
- `first` (Int) - Number of items to return (default: 100)
- `last` (Int) - Return last N items
- `before` (String) - Return items before this cursor
- `after` (String) - Return items after this cursor

## Best Practices

### 1. Use Pagination
Always use pagination for large datasets to avoid performance issues:

```graphql
query {
  systemInfo {
    users(first: 50) {
      # fields
    }
  }
}
```

### 2. Request Only Needed Fields
Be specific about which fields you need to minimize data transfer:

```graphql
query {
  systemInfo {
    users(first: 10) {
      name
      email
      # Only request fields you actually need
    }
  }
}
```

### 3. Use Variables for Dynamic Queries
Use GraphQL variables for dynamic filtering:

```graphql
query GetUserByName($userName: String) {
  systemInfo {
    users(name: $userName, first: 1) {
      id
      name
      email
    }
  }
}
```

### 4. Handle Nested Relationships Carefully
Be mindful of deeply nested queries that could impact performance:

```graphql
query {
  systemInfo {
    projects(first: 5) {
      code
      users(first: 10) {  # Nested pagination
        name
        projects(first: 5) {  # Avoid deep nesting when possible
          code
        }
      }
    }
  }
}
```

### 5. Use Appropriate Filters
Apply filters to reduce the dataset at the query level:

```graphql
query {
  systemInfo {
    users(year: 2024, first: 100) {  # Filter by year
      name
      email
    }
  }
}
```

## Error Handling

The API may return errors for various reasons. Always check for errors in your response:

```json
{
  "data": { ... },
  "errors": [
    {
      "message": "Error description",
      "locations": [{"line": 2, "column": 3}],
      "path": ["systemInfo", "users"]
    }
  ]
}
```

## Additional Resources

- Use GraphQL introspection to explore the schema further
- Refer to the official GraphQL specification for query syntax
- Consider using GraphQL client libraries for better error handling and caching

---

*This guide was generated using GraphQL introspection queries on the Iris API. For the most up-to-date schema information, perform introspection queries directly against the API.*

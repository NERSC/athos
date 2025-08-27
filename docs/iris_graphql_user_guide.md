# Iris GraphQL API User Guide: SystemInfo, Projects, and Users

## Overview

This guide provides comprehensive documentation for the Iris GraphQL API, specifically focusing on the `systemInfo` root field and its `projects`, `users`, and `computeAllocations` sub-fields. The information in this guide was generated using GraphQL introspection queries.

## Table of Contents

1. [Root Query Structure](#root-query-structure)
2. [SystemInfo Root Field](#systeminfo-root-field)
3. [Users Sub-field](#users-sub-field)
4. [Projects Sub-field](#projects-sub-field)
5. [ComputeAllocations Sub-field](#computeallocations-sub-field)
6. [UserQuotas Sub-field](#userquotas-sub-field)
7. [ProjectQuotas Sub-field](#projectquotas-sub-field)
8. [Example Queries](#example-queries)
9. [Common Arguments](#common-arguments)
10. [Best Practices](#best-practices)
11. [Quota Management Best Practices](#quota-management-best-practices)

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
        id
        repoName
        currentAlloc
        usedAlloc
        repoStatus
      }
    }
  }
}
```

## ComputeAllocations Sub-field

The `computeAllocations` sub-field provides access to compute resource allocation information for projects and users.

### Common Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `id` | Int | null | Filter by allocation ID |
| `repoName` | String | null | Filter by repository name |
| `since` | String | null | Filter allocations created since this date |
| `year` | Int | null | Filter by specific year |
| `before` | String | null | Pagination cursor |
| `after` | String | null | Pagination cursor |
| `first` | Int | 100 | Limit results (pagination) |
| `last` | Int | null | Last N results (pagination) |

### Key ComputeAllocation Fields

The ComputeAllocation type contains comprehensive allocation information:

#### Basic Information
- `id` (ID!) - Unique identifier
- `repoName` (String) - Repository/project name
- `repoStatus` (String) - Repository status
- `year` (Int) - Allocation year
- `quarter` (String) - Allocation quarter

#### Allocation Amounts
- `currentAlloc` (Float) - Current allocation amount
- `usedAlloc` (Float) - Used allocation amount
- `initialAlloc` (Float) - Initial allocation amount
- `finalAward` (Int) - Final awarded amount
- `remainingAlloc` (Float) - Remaining allocation

#### Usage Information
- `usedRaw` (Float) - Raw usage hours
- `usedMachine` (Float) - Machine usage hours
- `usedGpu` (Float) - GPU usage hours
- `percentUsed` (Float) - Percentage of allocation used

#### Dates and Status
- `startDate` (DateTime) - Allocation start date
- `endDate` (DateTime) - Allocation end date
- `createdAt` (DateTime) - Creation timestamp
- `updatedAt` (DateTime) - Last update timestamp

#### Associated Data
- `project` (Project) - Associated project
- `user` (User) - Associated user (for user allocations)
- `compute` (Compute) - Compute resource information

### Example ComputeAllocations Query

```graphql
query GetComputeAllocations {
  systemInfo {
    computeAllocations(first: 10, year: 2024) {
      id
      repoName
      repoStatus
      currentAlloc
      usedAlloc
      initialAlloc
      percentUsed
      year
      quarter
      startDate
      endDate
      project {
        code
        label
      }
      compute {
        name
        description
      }
    }
  }
}
```

### ComputeAllocations by Project

```graphql
query GetProjectAllocations($projectRepo: String) {
  systemInfo {
    computeAllocations(repoName: $projectRepo, first: 5) {
      id
      currentAlloc
      usedAlloc
      remainingAlloc
      percentUsed
      year
      quarter
      usedRaw
      usedMachine
      usedGpu
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
        currentAlloc
        usedAlloc
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
        id
        repoName
        currentAlloc
        usedAlloc
        percentUsed
        year
        compute {
          name
          description
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



## UserQuotas Sub-field

The `userQuotas` sub-field provides access to user storage quota information, including both home directory and scratch space quotas.

### Common Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `year` | Int | null | Filter by specific year |
| `first` | Int | 100 | Limit results (pagination) |
| `last` | Int | null | Last N results (pagination) |
| `before` | String | null | Pagination cursor |
| `after` | String | null | Pagination cursor |

### Key UserQuota Fields

The UserQuota type contains information about storage quotas assigned to users:

#### Basic Information
- `id` (ID!) - Unique identifier for the user quota
- `userId` (Int) - The ID of the user this quota belongs to
- `homeQuotaId` (Int) - Reference ID for the home directory quota
- `scratchQuotaId` (Int) - Reference ID for the scratch space quota

#### Timestamps
- `createdAt` (DateTime) - When the quota was created
- `updatedAt` (DateTime) - When the quota was last updated

#### Associated Data
- `user` (User) - The user this quota belongs to
- `homeQuota` (Quota) - Detailed home directory quota information
- `scratchQuota` (Quota) - Detailed scratch space quota information

### Quota Type Fields

The associated `Quota` objects contain the actual quota details:

#### Basic Quota Information
- `id` (ID!) - Unique identifier for the quota
- `type` (String!) - Type of quota (e.g., "home", "scratch", "project")
- `store` (Float) - Storage quota limit in appropriate units
- `inode` (Float) - Inode (file count) quota limit
- `prevStore` (Float) - Previous storage quota limit
- `prevInode` (Float) - Previous inode quota limit
- `end` (String) - Quota expiration date/time

#### Timestamps
- `createdAt` (DateTime) - When the quota was created
- `updatedAt` (DateTime) - When the quota was last updated

#### Relationships
- `userHomeQuotas` ([UserQuota]) - User quotas using this as home quota
- `userScratchQuotas` ([UserQuota]) - User quotas using this as scratch quota
- `projectQuotas` ([ProjectQuota]) - Project quotas using this quota
- `projectPaidQuotas` ([ProjectQuota]) - Project paid quotas using this quota
- `projectTmpQuotas` ([ProjectQuota]) - Project temporary quotas using this quota

### Example UserQuotas Queries

#### 1. Basic User Quotas Query

```graphql
query GetUserQuotas {
  systemInfo {
    userQuotas(first: 10) {
      id
      userId
      user {
        name
        email
      }
      homeQuota {
        id
        type
        store
        inode
        end
      }
      scratchQuota {
        id
        type
        store
        inode
        end
      }
      createdAt
      updatedAt
    }
  }
}
```

#### 2. User Quotas for Specific Year

```graphql
query GetUserQuotasForYear($year: Int) {
  systemInfo {
    userQuotas(year: $year, first: 50) {
      id
      user {
        name
        uid
        email
      }
      homeQuota {
        store
        inode
        prevStore
        prevInode
        end
      }
      scratchQuota {
        store
        inode
        prevStore
        prevInode
        end
      }
    }
  }
}
```

#### 3. Detailed User Quota Information

```graphql
query GetDetailedUserQuotas {
  systemInfo {
    userQuotas(first: 5) {
      id
      user {
        name
        email
        uid
        firstname
        lastname
      }
      homeQuota {
        id
        type
        store
        inode
        prevStore
        prevInode
        end
        createdAt
        updatedAt
      }
      scratchQuota {
        id
        type
        store
        inode
        prevStore
        prevInode
        end
        createdAt
        updatedAt
      }
    }
  }
}
```

## ProjectQuotas Sub-field

The `projectQuotas` sub-field provides access to project storage quota information, including regular, paid, and temporary quota allocations.

### Common Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `year` | Int | null | Filter by specific year |
| `first` | Int | 100 | Limit results (pagination) |
| `last` | Int | null | Last N results (pagination) |
| `before` | String | null | Pagination cursor |
| `after` | String | null | Pagination cursor |

### Key ProjectQuota Fields

The ProjectQuota type contains information about storage quotas assigned to projects:

#### Basic Information
- `id` (ID!) - Unique identifier for the project quota
- `userId` (Int) - ID of the user associated with this quota
- `groupId` (Int) - ID of the group associated with this quota
- `projectId` (Int) - ID of the project this quota belongs to
- `pname` (String) - Project name
- `status` (String) - Current status of the project quota
- `oldPname` (String) - Previous project name (if renamed)

#### Quota References
- `quotaId` (Int) - Reference ID for the main project quota
- `paidQuotaId` (Int) - Reference ID for paid storage quota
- `tmpQuotaId` (Int) - Reference ID for temporary storage quota
- `projectQuotaId` (Int) - Additional project quota reference

#### Status and Timestamps
- `createStatus` (String) - Status of quota creation process
- `createStatusAt` (DateTime) - When the creation status was last updated
- `createdAt` (DateTime) - When the project quota was created
- `updatedAt` (DateTime) - When the project quota was last updated

#### Associated Data
- `user` (User) - The user associated with this project quota
- `group` (Group) - The group associated with this project quota
- `project` (Project) - The project this quota belongs to
- `quota` (Quota) - Main project quota details
- `paidQuota` (Quota) - Paid storage quota details
- `tmpQuota` (Quota) - Temporary storage quota details

### Example ProjectQuotas Queries

#### 1. Basic Project Quotas Query

```graphql
query GetProjectQuotas {
  systemInfo {
    projectQuotas(first: 10) {
      id
      pname
      status
      createStatus
      project {
        code
        label
      }
      user {
        name
        email
      }
      quota {
        type
        store
        inode
        end
      }
      createdAt
      updatedAt
    }
  }
}
```

#### 2. Project Quotas with All Quota Types

```graphql
query GetProjectQuotasDetailed {
  systemInfo {
    projectQuotas(first: 5) {
      id
      pname
      status
      createStatus
      project {
        code
        label
        description
      }
      user {
        name
        email
      }
      group {
        name
      }
      quota {
        id
        type
        store
        inode
        prevStore
        prevInode
        end
      }
      paidQuota {
        id
        type
        store
        inode
        prevStore
        prevInode
        end
      }
      tmpQuota {
        id
        type
        store
        inode
        prevStore
        prevInode
        end
      }
    }
  }
}
```

#### 3. Project Quotas for Specific Year

```graphql
query GetProjectQuotasForYear($year: Int) {
  systemInfo {
    projectQuotas(year: $year, first: 25) {
      id
      pname
      status
      createStatus
      createStatusAt
      project {
        code
        label
        repoName
      }
      quota {
        store
        inode
        end
      }
      paidQuota {
        store
        inode
        end
      }
      tmpQuota {
        store
        inode
        end
      }
    }
  }
}
```

#### 4. Project Quota Status Overview

```graphql
query GetProjectQuotaStatus {
  systemInfo {
    projectQuotas(first: 20) {
      id
      pname
      status
      createStatus
      createStatusAt
      oldPname
      project {
        code
        label
        repoName
        description
      }
      createdAt
      updatedAt
    }
  }
}
```

### Combined Quota Queries

#### 1. User and Project Quotas Overview

```graphql
query GetAllQuotasOverview {
  systemInfo {
    userQuotas(first: 5) {
      id
      user {
        name
        email
      }
      homeQuota {
        store
        inode
      }
      scratchQuota {
        store
        inode
      }
    }
    projectQuotas(first: 5) {
      id
      pname
      status
      project {
        code
        label
      }
      quota {
        store
        inode
      }
    }
  }
}
```

#### 2. Quota Usage Analysis

```graphql
query GetQuotaUsageAnalysis {
  systemInfo {
    userQuotas(first: 10) {
      user {
        name
        uid
      }
      homeQuota {
        type
        store
        prevStore
        inode
        prevInode
        updatedAt
      }
      scratchQuota {
        type
        store
        prevStore
        inode
        prevInode
        updatedAt
      }
    }
    projectQuotas(first: 10) {
      pname
      status
      project {
        code
      }
      quota {
        type
        store
        prevStore
        inode
        prevInode
        updatedAt
      }
      paidQuota {
        store
        inode
        updatedAt
      }
    }
  }
}
```

## Quota Management Best Practices

### 1. Monitor Quota Usage
Regularly check quota usage by comparing current and previous values:

```graphql
query MonitorQuotaUsage {
  systemInfo {
    userQuotas(first: 100) {
      user {
        name
      }
      homeQuota {
        store
        prevStore
        inode
        prevInode
      }
    }
  }
}
```

### 2. Track Quota Changes
Use the `updatedAt` field to track recent quota modifications:

```graphql
query RecentQuotaChanges {
  systemInfo {
    projectQuotas(first: 50) {
      pname
      status
      quota {
        store
        prevStore
        updatedAt
      }
      updatedAt
    }
  }
}
```

### 3. Filter by Year for Historical Data
Use the `year` parameter to analyze quota trends:

```graphql
query HistoricalQuotas($year: Int) {
  systemInfo {
    userQuotas(year: $year) {
      user {
        name
      }
      homeQuota {
        store
        inode
      }
    }
    projectQuotas(year: $year) {
      pname
      quota {
        store
        inode
      }
    }
  }
}
```

### 4. Paginate Large Quota Datasets
Always use pagination when querying large numbers of quotas:

```graphql
query PaginatedQuotas($after: String) {
  systemInfo {
    userQuotas(first: 50, after: $after) {
      # quota fields
    }
    projectQuotas(first: 50, after: $after) {
      # quota fields
    }
  }
}
```

## Additional Resources

- Use GraphQL introspection to explore the schema further
- Refer to the official GraphQL specification for query syntax
- Consider using GraphQL client libraries for better error handling and caching

---

*This guide was generated using GraphQL introspection queries on the Iris API. For the most up-to-date schema information, perform introspection queries directly against the API.*

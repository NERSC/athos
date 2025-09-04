
# NERSC Documentation Summary and Chroma Ingestion Plan

## Documentation Summary

### Overview
The NERSC documentation repository contains comprehensive technical documentation for the National Energy Research Scientific Computing Center (NERSC), a Department of Energy facility providing high-performance computing resources for scientific research.

### Main Documentation Sections

1. **Getting Started and Accounts** (accounts/, getting-started.md, beginner-guide/)
   - New user orientation and account management
   - Password policies and security procedures
   - Collaboration accounts and access management

2. **Computing Systems** (systems/)
   - Perlmutter supercomputer (HPE Cray EX with AMD EPYC CPUs and NVIDIA A100 GPUs)
   - System architecture and specifications
   - Timeline and deployment information

3. **Job Management** (jobs/)
   - Slurm job scheduler usage and best practices
   - Queue policies, charges, and resource allocation
   - Interactive and batch job examples
   - Workflow tools and job monitoring

4. **Development Environment** (development/)
   - Compilers: Base compilers and wrapper compilers
   - Build Tools: Autoconf, Make, CMake, Spack
   - Programming Models: MPI, OpenMP, OpenACC, CUDA, UPC, Kokkos, etc.
   - Languages: Python, Julia, R, Rust, IDL
   - Libraries: FFTW, LAPACK, MKL, HDF5, NetCDF, etc.
   - Containers: Podman-hpc and Shifter containerization

5. **Applications and Software** (applications/)
   - Scientific applications: AMBER, CP2K, GROMACS, LAMMPS, NAMD, VASP, etc.
   - Quantum chemistry: NWChem, ORCA, Q-Chem, Quantum ESPRESSO
   - Visualization: ParaView, VisIt
   - Weather modeling: WRF
   - E4S software stack

6. **Performance and Debugging Tools** (tools/)
   - Performance analysis: CrayPat, Darshan, MAP, NVIDIA profiling tools
   - Debugging: DDT, GDB, TotalView, Valgrind, CUDA-GDB
   - Profiling and optimization guidance

7. **Data Management and Storage** (filesystems/)
   - File systems: Perlmutter scratch, Community, Archive (HPSS)
   - Data transfer: Globus, GridFTP, SCP
   - Storage policies and quotas
   - Unix file permissions

8. **Services and Infrastructure** (services/)
   - Jupyter notebooks for interactive computing
   - Spin platform for hosting services
   - Superfacility API
   - Databases and specialized services

9. **Machine Learning and Analytics** (machinelearning/, analytics/)
   - PyTorch, TensorFlow, and distributed training
   - Hyperparameter optimization
   - Dask for parallel analytics

10. **Project Management** (allocations/, iris/)
    - ERCAP allocation requests and management
    - Project administration through Iris
    - Resource allocation policies

### Technical Characteristics
- **Format**: Markdown files organized in a hierarchical directory structure
- **Site Generator**: MkDocs with Material theme and NERSC customizations
- **Content Volume**: Extensive documentation covering all aspects of HPC usage
- **Target Audience**: Scientific researchers, application developers, system administrators
- **Update Frequency**: Actively maintained with regular updates

## Chroma Database Ingestion Plan

### Objective
Create a searchable knowledge base of NERSC documentation to enable efficient retrieval of technical information for user support, consulting, and knowledge management.

### Collection Design

#### Collection Name: `nersc_documentation`

#### Embedding Strategy
- **Embedding Function**: Use `openai` or `jina` embedding function for high-quality semantic representations
- **Chunk Strategy**: Process documents at the page level initially, with potential sub-chunking for very large documents

#### Metadata Schema
Each document will include the following metadata:
```json
{
  "file_path": "relative/path/to/file.md",
  "section": "main_section_category",
  "subsection": "subsection_if_applicable", 
  "title": "document_title",
  "last_modified": "timestamp",
  "doc_type": "documentation_type",
  "topics": ["topic1", "topic2", "topic3"],
  "system_relevance": ["perlmutter", "general"],
  "audience": ["beginner", "intermediate", "advanced"]
}
```

### Implementation Steps

#### Phase 1: Collection Setup and Basic Ingestion
1. **Create Collection**: Initialize Chroma collection with appropriate embedding function
2. **Document Discovery**: Recursively traverse docs directory to identify all .md files
3. **Content Processing**: 
   - Read and clean markdown content
   - Extract frontmatter metadata if present
   - Parse document titles and headings
4. **Basic Ingestion**: Add documents with file path, section, and title metadata

#### Phase 2: Enhanced Metadata Extraction
1. **Section Classification**: Automatically categorize documents by directory structure
2. **Topic Extraction**: Identify key topics from content and headings
3. **Audience Classification**: Determine complexity level (beginner/intermediate/advanced)
4. **System Relevance**: Tag documents as Perlmutter-specific or general

#### Phase 3: Content Optimization
1. **Large Document Chunking**: Split very large documents into logical sections
2. **Cross-reference Linking**: Identify and preserve internal document relationships
3. **Content Enrichment**: Add computed metadata like word count, readability scores

#### Phase 4: Search and Retrieval Optimization
1. **Query Testing**: Test search effectiveness with common user questions
2. **Retrieval Tuning**: Optimize n_results and search parameters
3. **Result Ranking**: Implement relevance scoring based on metadata

### Technical Implementation Details

#### Document Processing Pipeline
```python
1. File Discovery: search_files() to find all .md files
2. Content Reading: read_text_file() for each document
3. Metadata Extraction: Parse file paths and content for metadata
4. Content Cleaning: Remove markup artifacts, normalize whitespace
5. Chunking: Split large documents if needed
6. ID Generation: Create unique, meaningful document IDs
7. Batch Ingestion: Add documents in batches for efficiency
```

#### Quality Assurance
- Validate all documents are successfully ingested
- Check for duplicate content
- Verify metadata completeness
- Test search functionality with representative queries

#### Maintenance Strategy
- Regular updates to reflect documentation changes
- Monitoring of collection size and performance
- Periodic re-indexing for optimization

### Expected Outcomes
- Comprehensive searchable knowledge base of NERSC documentation
- Efficient semantic search capabilities for user support
- Foundation for AI-assisted consulting and help systems
- Improved discoverability of relevant technical information

### Success Metrics
- Document coverage: 100% of markdown files successfully ingested
- Search relevance: High-quality results for common technical queries
- Response time: Sub-second search performance
- User satisfaction: Positive feedback from consulting team usage


## Detailed Processing Analysis

### File Count and Distribution
- **Total files to process**: 255 markdown files
- **Estimated total content**: ~2.3 MB of text content
- **Average file size**: ~9,200 characters per file

### Files by Section (Detailed Breakdown):
1. **development** (61 files) - Largest section
   - Compilers, build tools, programming models (MPI, OpenMP, CUDA)
   - Languages (Python, Julia, R, Rust)
   - Libraries (FFTW, LAPACK, HDF5, NetCDF)
   - Containers (Podman-hpc, Shifter)

2. **services** (31 files)
   - Jupyter notebooks, Spin platform
   - Superfacility API, databases
   - Data transfer tools (Globus, GridFTP)

3. **applications** (29 files)
   - Scientific software (AMBER, VASP, GROMACS, LAMMPS)
   - Quantum chemistry (NWChem, ORCA, Q-Chem)
   - Visualization (ParaView, VisIt)

4. **jobs** (25 files)
   - Slurm job scheduler usage
   - Workflow tools, monitoring, best practices

5. **performance** (21 files)
   - Optimization guides, readiness documentation

6. **tools** (21 files)
   - Debugging and performance analysis tools

7. **filesystems** (17 files)
   - Storage systems, data management policies

8. **Other sections** (90 files total)
   - Systems, machine learning, accounts, allocations, etc.

## Batch Processing Implementation Plan

### Batch Strategy
To ensure manageable processing within the 10-20 step limit per agent task, we will process the documentation in 6 distinct batches:

#### Batch 1: Core System and Getting Started (43 files)
**Agent Task Goal**: Process fundamental NERSC documentation
- root/ (4 files): index.md, getting-started.md, current.md, tips.md
- accounts/ (4 files): User account management
- beginner-guide/ (3 files): New user orientation  
- connect/ (5 files): Authentication and remote access
- environment/ (3 files): Shell setup and modules
- systems/ (6 files): Perlmutter architecture and timeline
- allocations/ (5 files): ERCAP and resource requests
- policies/ (4 files): Data and software policies
- iris/ (4 files): Project management system
- help/ (1 file): Acronyms
- analytics/ (2 files): Data analytics overview
- tutorials/ (3 files): Basic tutorials and playbooks

**Estimated processing time**: 8-15 minutes
**Key metadata focus**: User level (beginner), system basics, account management

#### Batch 2: Job Management and Workflows (25 files)
**Agent Task Goal**: Process all job-related documentation
- jobs/ (25 files): Complete Slurm documentation, workflows, examples, monitoring

**Estimated processing time**: 5-10 minutes  
**Key metadata focus**: Job management, scheduling, workflow tools

#### Batch 3: Development Environment - Core (31 files)
**Agent Task Goal**: Process core development tools and compilers
- development/compilers/ (~8 files): Base and wrapper compilers
- development/build-tools/ (~6 files): Autoconf, Make, CMake, Spack
- development/installing-software/ (~3 files): Software installation guides
- development/containers/ (~8 files): Podman-hpc and Shifter
- development/checkpoint-restart/ (~6 files): Checkpoint/restart mechanisms

**Estimated processing time**: 6-12 minutes
**Key metadata focus**: Development tools, compilation, containerization

#### Batch 4: Development Environment - Languages and Models (30 files)
**Agent Task Goal**: Process programming languages and models
- development/programming-models/ (~15 files): MPI, OpenMP, CUDA, Kokkos, etc.
- development/languages/ (~10 files): Python, Julia, R, Rust, IDL
- development/libraries/ (~5 files): FFTW, LAPACK, MKL, HDF5, NetCDF

**Estimated processing time**: 6-12 minutes
**Key metadata focus**: Programming languages, parallel programming, libraries

#### Batch 5: Applications and Machine Learning (35 files)
**Agent Task Goal**: Process scientific applications and ML frameworks
- applications/ (29 files): All scientific software documentation
- machinelearning/ (6 files): PyTorch, TensorFlow, distributed training

**Estimated processing time**: 7-14 minutes
**Key metadata focus**: Scientific applications, machine learning, GPU computing

#### Batch 6: Tools, Performance, Services, and Storage (91 files)
**Agent Task Goal**: Process remaining documentation
- tools/ (21 files): Debugging and performance tools
- performance/ (21 files): Optimization and readiness guides
- services/ (31 files): Jupyter, Spin, APIs, databases
- filesystems/ (17 files): Storage systems and data management
- Any remaining files

**Estimated processing time**: 15-25 minutes
**Key metadata focus**: Performance optimization, debugging, services, storage

### Batch Processing Workflow

Each batch processing task should follow this workflow:

1. **Setup Phase** (2-3 steps)
   - Check/create collection if first batch
   - Define batch file list
   - Initialize metadata extraction functions

2. **Processing Phase** (8-12 steps)
   - Read files in batch
   - Extract and clean content
   - Generate metadata for each file
   - Create unique document IDs
   - Process 8-12 files per step

3. **Ingestion Phase** (2-3 steps)
   - Add documents to Chroma collection in sub-batches
   - Validate successful ingestion
   - Report batch completion status

4. **Quality Check Phase** (1-2 steps)
   - Verify document count
   - Test sample queries on ingested content
   - Report any issues or errors

### Cross-Batch Coordination

- **Collection Name**: `nersc_documentation` (consistent across all batches)
- **Embedding Function**: `openai` or `jina` (decided in Batch 1, used consistently)
- **ID Format**: `{section}_{filename}_{hash}` for uniqueness
- **Progress Tracking**: Each batch reports completion and document count

### Success Metrics Per Batch
- All assigned files successfully processed (100% success rate)
- Metadata completeness (all required fields populated)
- No duplicate document IDs
- Sample query validation passes
- Processing time within estimated range

This batching approach ensures each agent task is manageable, focused, and can be completed within the 10-20 step limit while building toward the complete NERSC documentation knowledge base.


## Chunking Strategy for Large Files

### Analysis Results
After analyzing file lengths across the documentation, we found that **most files (90%+) are reasonably sized** and should be kept as single documents. However, a small number of large files will benefit from chunking for better search performance and retrieval accuracy.

### Chunking Criteria
- **Files >15,000 characters**: Definitely chunk by H2 sections
- **Files 8,000-15,000 characters with 3+ H2 sections**: Optional chunking 
- **Files <8,000 characters**: Keep as single documents

### Files Requiring Chunking

#### Large Files (Definite Chunking Required)
1. **performance/readiness.md** (80,281 chars, 13 H2 sections)
   - Chunk by H2 sections: "Introduction and Basic GPU Concepts", "Additional High-Level GPU Considerations", etc.
   - Each chunk will be 3,000-8,000 characters
   - Estimated chunks: 13-15 chunks

2. **applications/vasp/index.md** (36,010 chars, 8 H2 sections) 
   - Chunk by H2 sections for better application-specific retrieval
   - Estimated chunks: 8-10 chunks

3. **getting-started.md** (19,110 chars, 14 H2 sections)
   - Important beginner documentation - chunk for focused retrieval
   - Sections like "Computing Resources", "Storage Resources", "Getting Help"
   - Estimated chunks: 14-16 chunks

4. **tools/debug/ddt/index.md** (23,537 chars, 12 H2 sections)
   - DDT debugging tool documentation
   - Estimated chunks: 12-14 chunks

#### Medium Files (Optional Chunking)
1. **jobs/index.md** (14,846 chars, 8 H2 sections)
   - Could be chunked for better job-related query targeting
   - Decision: **Keep as single document** for now (close to threshold)

### Chunking Implementation Strategy

#### Impact on Processing
- **Total documents after chunking**: ~295-300 (from 255 base files)
- **4 large files** → **~50-55 chunks**
- **251 regular files** → **251 single documents**

#### Batch Processing Adjustments
The chunking will primarily affect these batches:
- **Batch 1**: getting-started.md chunking (+13 chunks)
- **Batch 5**: applications/vasp/index.md chunking (+8 chunks)  
- **Batch 6**: performance/readiness.md and tools/debug/ddt/index.md chunking (+25 chunks)

### Benefits of Chunking Strategy
1. **Improved Search Precision**: Users searching for specific topics get focused results
2. **Better Context Retrieval**: Embedding vectors capture more specific semantic meaning
3. **Manageable Chunk Sizes**: 3,000-8,000 character chunks are optimal for LLM context
4. **Maintained Relationships**: Chunk metadata preserves parent document relationships

### Quality Assurance for Chunked Documents
- Verify each chunk maintains coherent content
- Ensure section headers are preserved
- Test search performance on chunked vs. non-chunked versions
- Validate cross-references and links remain intact

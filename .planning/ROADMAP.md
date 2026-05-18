# ROADMAP — uasset_resolver

> Unreal Engine `.uasset` Blueprint parser — one command, structured output, no editor.

**Core Value:** 一条命令读取 .uasset 文件，输出蓝图节点的结构化表示（文本+JSON），无需打开 UE 编辑器。

**Granularity:** standard
**Total Phases:** 4
**Total v1 Requirements:** 12

---

## Phases

- [ ] **Phase 1: UE Headless Bridge** — Launch UE 5.7 headless mode, load .uasset file, verify Blueprint identification
- [ ] **Phase 2: Blueprint Node Extraction** — Extract EventGraph nodes, pins, connections, and canvas coordinates
- [ ] **Phase 3: Output Formatting** — Generate UE-style MD text output and structured JSON from extracted data
- [ ] **Phase 4: CLI & Validation** — Command-line interface, loading strategy fallback, cross-validate against reference

---

## Phase Details

### Phase 1: UE Headless Bridge

**Goal**: Python tool can launch UE 5.7 headless mode, load a .uasset file, and confirm whether it is a Blueprint asset.

**Depends on**: Nothing (first phase)

**Requirements**: PARSE-01, PARSE-02

**Success Criteria** (what must be TRUE):
  1. Running the Python tool launches UE 5.7 with `-unattended -NullRHI` flags and executes an embedded Python script
  2. Given a valid .uasset path, the tool loads the asset and correctly reports whether it is a Blueprint or not
  3. UE process exits cleanly after script execution (no hanging editor windows)

**Plans**: TBD

### Phase 2: Blueprint Node Extraction

**Goal**: From a loaded Blueprint asset, the tool extracts complete EventGraph structure including nodes, pins, connections, and canvas positions.

**Depends on**: Phase 1

**Requirements**: PARSE-03, PARSE-04, PARSE-05, PARSE-06

**Success Criteria** (what must be TRUE):
  1. Output contains all EventGraph nodes with their type, name, and function reference (for function nodes)
  2. Each node includes complete pin definitions: PinId, PinName, PinType, Direction, and LinkedTo references
  3. All node-to-node connections are captured, including both execution flow (exec pins) and data connections
  4. Each node has its canvas position (NodePosX, NodePosY) recorded

**Plans**: TBD

### Phase 3: Output Formatting

**Goal**: Extracted blueprint data is formatted as UE-style MD text and structured JSON, both readable and machine-consumable.

**Depends on**: Phase 2

**Requirements**: OUT-01, OUT-02

**Success Criteria** (what must be TRUE):
  1. MD output matches UE editor text format: `Begin Object Class=... Name=... End Object` blocks with all node fields
  2. JSON output contains a three-level structure: nodes → pins → connections, with all extracted data nested correctly
  3. Both formats contain the same data (field parity between MD and JSON)

**Plans**: TBD
**UI hint**: yes

### Phase 4: CLI & Validation

**Goal**: The tool provides a complete command-line experience with loading strategy fallback and verified output correctness.

**Depends on**: Phase 3

**Requirements**: OUT-03, LOAD-01, LOAD-02, VERIFY-01

**Success Criteria** (what must be TRUE):
  1. User can run a single CLI command with `--format md` or `--format json` to select output format
  2. User can pass a bare .uasset file path and it loads successfully; if loading fails, a clear message prompts for a UE project Content directory
  3. Running the tool on `BP_FirstPersonCharacter.uasset` produces output that matches key fields in `蓝图节点文本参考.md` (node count, node names, function references, pin structure)

**Plans**: TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. UE Headless Bridge | 0/0 | Not started | - |
| 2. Blueprint Node Extraction | 0/0 | Not started | - |
| 3. Output Formatting | 0/0 | Not started | - |
| 4. CLI & Validation | 0/0 | Not started | - |

---

## Coverage

| Requirement | Phase | Status |
|-------------|-------|--------|
| PARSE-01 | Phase 1 | Pending |
| PARSE-02 | Phase 1 | Pending |
| PARSE-03 | Phase 2 | Pending |
| PARSE-04 | Phase 2 | Pending |
| PARSE-05 | Phase 2 | Pending |
| PARSE-06 | Phase 2 | Pending |
| OUT-01 | Phase 3 | Pending |
| OUT-02 | Phase 3 | Pending |
| OUT-03 | Phase 4 | Pending |
| LOAD-01 | Phase 4 | Pending |
| LOAD-02 | Phase 4 | Pending |
| VERIFY-01 | Phase 4 | Pending |

**Mapped: 12/12**

### FEATURE SPEC: 000 - Project Common

**Objective:** To define the global rules, execution environment, and workflows for this project. This spec MUST be provided as context for *all* feature implementation tasks.

#### 1. Core Architectural Principles

* **Framework:** We use LangGraph exclusively.
* **State:** We use a single, unified `GraphState` TypedDict, defined in `app/graph/state.py`.
* **Routing:** All routing and classification is done with Pydantic tools bound to an LLM. We do not use `if/elif` on raw user text for routing.
* **Pausing:** We *only* use `interrupt_after` in the graph's `compile()` method to wait for user input. We do not use other pausing mechanisms.

#### 2. Execution Environment (Docker)

All development and testing commands **MUST** be executed inside the `backend` Docker container.

* **To Rebuild & Restart:**
    ```bash
    docker compose down && docker compose up -d --build
    ```
* **To Run Tests:** All `pytest` commands must be run this way.
    ```bash
    docker compose exec backend pytest [path/to/test_file.py]
    ```
* **To Run a Shell:**
    ```bash
    docker compose exec backend /bin/bash
    ```

#### 3. Workflow & Iteration

This is our mandatory development loop:

1.  **Implement:** Implement the new feature from its spec file (e.g., `00X-feature.md`).
2.  **Rebuild:** After the new code is written, **you MUST** rebuild the container to load the changes. Use the command: `docker compose down && docker compose up -d --build`.
3.  **Test:** Run the corresponding tests (our LangSmith evals or unit tests) using the `docker compose exec backend pytest ...` command.
4.  **Fix:** If tests fail, debug and fix the *code*. **After each code change, you MUST return to Step 2 (Rebuild)** before testing again.
5.  **Sync (Mandatory Final Step):** Once all tests pass, you **MUST** propose changes to the original feature spec file (e.g., `00X-feature.md`). These changes must sync the spec's logic to the final, working code. I will review and approve these "spec-sync" changes.
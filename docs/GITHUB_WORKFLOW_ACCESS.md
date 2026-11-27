# Repository workflow access — resolved on 2026-11-27

This concerns Arena's **repository Git connection**, not a chat-app connector.

After the latest user access update, pushing implementation commit `bfb6fcf` to the current
session branch succeeded. Both configured workflows actually started. Their first runs
failed at setup/test gates; those failures were subsequently repaired and **both workflows
now pass**, including actual Windows frozen execution. See
[the milestone report](../MILESTONE_REPORT.md). No further permission change is currently
requested. CI success and clean-machine acceptance remain separate requirements.

## Historical rejection and remediation

The ordinary baseline branch push had succeeded, but uploading the actual implementation
was previously rejected, including after an earlier access-update confirmation:

```text
refusing to allow a GitHub App to create or update workflow
`.github/workflows/build.yml` without `workflows` permission
```

At that time the remote `arena/4feb7a32-struct-ai` branch contained only the initial baseline.
A successful baseline push or repository-admin status alone did not establish workflow
permissions. This state was superseded by the successful implementation push above.

## Connection-side action if the error recurs

1. Reconnect/reauthorise the **repository connection** in Arena with permission to write
   repository contents **and workflows**.
2. If workflow permission is not offered, or reconnecting gives the same rejection, the
   Arena/GitHub integration administrator must ensure the app requests and receives
   `Workflows: write`. Changing application Python code cannot grant this permission.
3. After the actual connection change, retry only the session's current branch:

   ```sh
   git push origin arena/4feb7a32-struct-ai
   ```

Do not send passwords, personal access tokens, OAuth tokens or two-factor codes in chat.
Do not delete the required workflows or weaken the engineering/test gates to hide the error.
No force push or change to another branch is needed.

## Work that can proceed without a workflow upload

The source-only handoff ZIP supplied in the conversation contains the implementation,
not a Windows EXE. On a Windows build host with CPython 3.12.10 x64, extract it and run:

```bat
packaging\build_windows.bat
```

The build script must pass its tests and both actual frozen selftests. Then copy the whole
onedir output to a **separate clean Windows machine without Python** and follow
[the acceptance procedure](packaging-spike.md). Preserve the actual JSON reports, OS/build
identity, artifact hash and screenshots. A source archive alone proves none of those results.

Workflow access is now repaired and Windows CI passes. CI execution is not itself proof
of clean-machine acceptance. Binary artifact publication remains a separate reviewed opt-in;
no commercial redistribution permission is inferred from a successful build.

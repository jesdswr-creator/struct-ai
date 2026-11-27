# Repository workflow access — current external blocker

This concerns Arena's **repository Git connection**, not a chat-app connector.

The ordinary baseline branch push succeeded, but uploading the actual implementation was
rejected. The same rejection was returned after the user reported updating access:

```text
refusing to allow a GitHub App to create or update workflow
`.github/workflows/build.yml` without `workflows` permission
```

The remote `arena/4feb7a32-struct-ai` branch therefore still contains the initial README-only
baseline, not this implementation. A successful baseline push or repository-admin status
does not establish that the installation credential can modify workflows.

## Required connection-side action

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

Once workflow access is repaired, Windows CI can run too. CI execution is not itself proof
of clean-machine acceptance. Binary artifact publication remains a separate reviewed opt-in;
no commercial redistribution permission is inferred from a successful build.

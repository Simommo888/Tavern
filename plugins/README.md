# plugins

Future home for the LiveOS plugin system:

```text
Plugin Interface
↓
Plugin Manager
↓
Plugin Loader
↓
Plugin Implementation
```

Runtime plugin code currently remains in `apps/api/app/plugins/`; Phase 3 will consolidate this boundary.

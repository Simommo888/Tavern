# plugins 目录

LiveOS plugin system 的后续顶层边界：

```text
Plugin Interface
↓
Plugin Manager
↓
Plugin Loader
↓
Plugin Implementation
```

当前运行时插件代码仍位于 `apps/api/app/plugins/`；Phase 3 会进一步收敛该边界。

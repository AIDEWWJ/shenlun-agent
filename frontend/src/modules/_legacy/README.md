# Frontend Migration Notes

当前前端采用以下分层：

- `app/`: 入口、路由、全局配置、i18n 预留位
- `modules/`: 业务模块，内部统一使用 `pages/`、`components/`、`services/`、`types/`、`composables/`
- `features/`: 跨模块但不属于 shared 的业务组合能力
- `shared/`: 真正通用、无明确业务语义的基础能力

迁移约束：

- 不再新增 `hooks/`，Vue 侧统一使用 `composables/`
- 只有被两个及以上模块复用、且不携带业务语义的内容，才能进入 `shared/`
- 模块类型优先放模块自己的 `types/`
- 旧的 `src/App.vue`、`src/router/index.ts` 等根层文件仅保留为兼容入口

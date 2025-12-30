GitHub 上的 **分支（Branch）命名规范** 和 **提交（Commit）信息命名规范** 虽然没有强制标准，但社区和企业中普遍遵循一些最佳实践，以提高协作效率、代码可读性和自动化工具兼容性。以下是常用的规范建议：

---

## 一、分支（Branch）命名规范

### 常见命名模式
1. **功能分支（Feature Branch）**
   - 格式：`feature/<描述>`
   - 示例：`feature/user-login`, `feature/payment-integration`

2. **修复分支（Hotfix / Bugfix Branch）**
   - 格式：
     - 紧急线上修复：`hotfix/<描述>` 或 `hotfix/<issue编号>`
     - 一般 bug 修复：`bugfix/<描述>`
   - 示例：`hotfix/login-error`, `bugfix/typo-in-header`

3. **发布分支（Release Branch）**
   - 格式：`release/<版本号>`
   - 示例：`release/v1.2.0`

4. **开发主干（通常为默认分支）**
   - 常用名称：`main`（推荐）、`master`（旧习惯）

5. **其他用途**
   - 实验性功能：`experiment/<描述>` 或 `spike/<描述>`
   - 个人开发临时分支：`<用户名>/<描述>`（如 `alice/refactor-api`）

### 命名建议
- 使用 **小写字母**
- 使用 **连字符 `-`** 分隔单词（避免下划线 `_` 或空格）
- 避免特殊字符（如 `@#$%`）
- 尽量简短但具有语义
- 可包含 Jira/Ticket/Issue 编号（如 `feature/PROJ-123-add-cart`）

---

## 二、提交（Commit）信息命名规范

最广泛采用的是 **Conventional Commits** 规范（[conventionalcommits.org](https://www.conventionalcommits.org/)），它结构清晰，便于生成 CHANGELOG 和语义化版本（SemVer）。

### 基本格式
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### 常见 type 类型
| 类型 | 说明 |
|------|------|
| `feat` | 新功能（对应 SemVer 的 MINOR 版本） |
| `fix` | 修复 bug（对应 PATCH 版本） |
| `docs` | 文档更新 |
| `style` | 代码格式调整（不影响逻辑，如空格、分号） |
| `refactor` | 重构（既不是新功能也不是修复） |
| `perf` | 性能优化 |
| `test` | 添加或修改测试 |
| `build` | 构建系统或依赖更新 |
| `ci` | CI 配置或脚本变更 |
| `chore` | 杂项（如更新 .gitignore） |

### 示例
```text
feat(auth): add OAuth2 login support

fix(api): resolve null pointer in user endpoint

docs(readme): update installation instructions

refactor(cart): extract checkout logic to service class

chore: bump lodash from 4.17.20 to 4.17.21
```

### 提交信息书写建议
- **首行（标题）**：
  - 不超过 72 个字符
  - 使用祈使句（如 “add”, “fix”, “update” 而非 “added”, “fixed”）
  - 首字母小写
- **正文（Body）**（可选）：
  - 解释 **为什么** 修改，而不是 **做了什么**（代码已体现）
  - 换行空一行后开始
- **页脚（Footer）**（可选）：
  - 关联 Issue（如 `Closes #123` 或 `Fixes PROJ-456`）
  - Breaking Changes（重大变更需标注）

---

## 三、工具支持（可选但推荐）
- **Commitizen**：交互式生成符合规范的 commit
- **Husky + Commitlint**：在提交前校验 commit 格式
- **Semantic Release**：自动发布版本和生成 CHANGELOG

---

## 总结
| 项目 | 推荐规范 |
|------|----------|
| 分支命名 | `type/description`（如 `feature/user-profile`） |
| Commit 信息 | Conventional Commits（如 `feat(ui): add dark mode toggle`） |

遵循这些规范有助于团队协作、自动化流程（如 CI/CD、版本发布）和项目长期维护。

如需具体模板或配置示例（如 `.commitlintrc.js` 或 Git Hooks），也可以告诉我！
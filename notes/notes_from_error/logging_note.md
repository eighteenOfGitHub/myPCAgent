# 一、level等级介绍

在 Python 的 `logging` 模块配置中，**`level` 字段的作用是：设置该 logger 实例的最低日志记录级别（log level threshold）**。

---

### ✅ 简单说：
> **只有日志消息的级别 ≥ `logger.level` 时，这条日志才会被处理（输出到 handlers）。**

---

### 📌 日志级别（由低到高）：

| 级别        | 数值 | 用途说明 |
|-------------|------|--------|
| `NOTSET`    | 0    | 未设置，会继承父 logger 的级别 |
| `DEBUG`     | 10   | 调试信息，最详细 |
| `INFO`      | 20   | 一般信息，如“服务启动成功” |
| `WARNING`   | 30   | 警告，可能有问题但不影响运行 |
| `ERROR`     | 40   | 错误，功能失败 |
| `CRITICAL`  | 50   | 严重错误，程序可能崩溃 |

---

### 🔍 以你的配置为例：

```yaml
loggers:
  '':
    level: DEBUG
    handlers: [console, debug_file_handler, ...]
  core:
    level: DEBUG
    handlers: [console, debug_file_handler]
  services:
    level: INFO
    handlers: [console, info_file_handler]
```

#### 场景模拟：

假设你在代码中这样写日志：

```python
# core/some_module.py
logger = logging.getLogger("core.database")
logger.debug("Connecting to DB...")      # ✅ 会被记录（因为 core 的 level=DEBUG）
logger.info("Connected.")                # ✅

# services/user_service.py
logger = logging.getLogger("services.auth")
logger.debug("Token validation start")   # ❌ 不会被记录（因为 services 的 level=INFO，DEBUG < INFO）
logger.info("User logged in.")           # ✅
```

---

### ⚠️ 注意两点：

1. **Logger 是层级结构**  
   - `core.database` 是 `core` 的子 logger。
   - 如果 `core.database` 没有单独设置 `level`，它会**继承 `core` 的 level（DEBUG）**。
   - 如果你给 `core.database` 单独设了 `level: WARNING`，那它就用 WARNING，不再继承。

2. **Handler 也有自己的 level**  
   即使 logger 允许某条日志通过（比如 DEBUG），但如果某个 handler 的 level 是 `INFO`，那么 DEBUG 日志**不会从这个 handler 输出**。

   ```yaml
   handlers:
     console:
       level: INFO   # ← 即使 logger 是 DEBUG，console 也不会显示 DEBUG 日志！
   ```

   所以：**日志要最终输出，必须同时满足：**
   ```
   log_record.level >= logger.level
   AND
   log_record.level >= handler.level
   ```

---

### ✅ 总结

| 配置项 | 作用 |
|-------|------|
| `logger.level` | **过滤入口**：决定哪些日志能进入这个 logger 的处理流程 |
| `handler.level` | **过滤出口**：决定哪些日志能从这个 handler 输出（如控制台、文件） |

在你的配置中：
- `core` 设置为 `DEBUG` → 所有 `core.*` 模块的 DEBUG+ 日志都会被处理；
- `services` 设置为 `INFO` → `services.*` 模块的 DEBUG 日志会被直接丢弃，不进 handlers。

这让你可以**精细控制不同模块的日志详细程度**，非常实用！